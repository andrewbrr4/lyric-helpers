import csv
import re
from pathlib import Path

import numpy as np
from wordfreq import top_n_list, zipf_frequency
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import SnowballStemmer
from sentence_transformers import SentenceTransformer

# ── Configuration ──────────────────────────────────────────────────────────────

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = Path(__file__).parent / "cache"
EMBEDDINGS_CACHE = CACHE_DIR / "vocab_embeddings.npz"
CONCRETENESS_DATA = Path(__file__).parent / "data" / "concreteness_brysbaert.tsv"

N_WORDS = 100_000
MIN_ZIPF = 3.5
MAX_ZIPF = 6.5

# Words that are measurement units, abbreviations, or have no evocative quality.
BLOCKLIST = {
    # Measurement units and abbreviations
    "lbs", "lb", "kg", "cm", "mm", "ft", "oz", "mg", "ml", "km", "mph", "hrs",
    "etc", "ie", "eg", "vs", "aka", "amt", "qty", "avg", "approx", "misc",
    # Technical/bureaucratic jargon
    "documentation", "registry", "intervals", "config", "parameter", "parameters",
    "corresponding", "respective", "applicable", "furthermore", "therefore",
    "potentially", "appropriate", "recommended", "suitable",
    "hereby", "thereof", "herein", "wherein", "therein",
    # Informal contractions
    "doin", "gonna", "gotta", "wanna", "aint",
    "could", "would", "should",
    # Generic/abstract words with no emotional or sensory quality
    "things", "thing", "actions", "action", "edited", "intended", "considering",
    "regarding", "consisting",
    "permitted", "prohibited", "specified", "indicated", "designated",
    "obtained", "required", "provided", "included", "involved",
    "based", "related", "associated", "referred", "considered",
    "particularly", "specifically", "respectively", "accordingly",
    "previously", "subsequently", "approximately", "essentially",
    # More generic/abstract words
    "extremely", "practically", "basically", "sized", "bigger", "smaller",
    "possible", "impossible", "plausible", "unlikely", "likely",
    # Functional/procedural words with no sensory quality
    "several", "multiple", "various", "written", "wrote", "participating",
    "modified", "feasible", "suggested", "volunteer", "legitimate",
    "operated", "identified", "established", "implemented",
    "additional", "available", "determine", "maintained",
    # More low-evocative function words
    "might", "gives", "give", "better", "worse", "along", "everybody",
    "contacted", "hon", "bad", "good", "gets", "got", "makes",
    "come", "came", "goes", "went", "done", "taken",
    # Filler/function words
    "fairly", "distinctly", "vary", "optional", "created", "use",
    "considerations", "product", "allows", "allowed",
    "mmm", "hmm", "huh", "lol", "btw", "mid",
    # Financial/technical jargon
    "holdings", "economists", "investor", "pricing", "fees",
    # Crude words that aren't evocative
    "dick", "fetish",
    # More bland/functional words
    "phone", "loses", "emphasis", "carefully", "slightly",
    "respectable", "prestigious", "garner", "fashioned",
    "matched", "eaten", "men", "important", "special",
    # More low-evocative/generic
    "posting", "anime", "publicity", "looking", "feeling",
    "america", "faa", "val", "bert", "atm",
    "emotionally", "school", "television", "earned",
    "tolerate", "gay", "identify", "possibly", "finely",
    "economically", "consequently", "consequences",
}

# ── Vocabulary ─────────────────────────────────────────────────────────────────

def _normalize(word: str) -> str:
    return re.sub(r"[^a-z]", "", word.lower())


def _build_vocab() -> list[str]:
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)
    stop = set(stopwords.words("english"))

    vocab = list(dict.fromkeys(
        w for raw in top_n_list("en", N_WORDS)
        if 3 <= len(w := _normalize(raw)) <= 20
    ))

    return [
        w for w in vocab
        if w not in stop
        and w not in BLOCKLIST
        and MIN_ZIPF <= zipf_frequency(w, "en") <= MAX_ZIPF
    ]


def _load_or_build_embeddings(
    words: list[str], model: SentenceTransformer
) -> np.ndarray:
    CACHE_DIR.mkdir(exist_ok=True)

    if EMBEDDINGS_CACHE.exists():
        data = np.load(EMBEDDINGS_CACHE, allow_pickle=True)
        if data["words"].tolist() == words:
            return data["embeddings"]

    embeddings = model.encode(
        words,
        batch_size=256,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    np.savez(EMBEDDINGS_CACHE, words=np.array(words), embeddings=embeddings)
    return embeddings


def _load_concreteness() -> dict[str, float]:
    """Load Brysbaert et al. concreteness ratings from vendored TSV."""
    ratings = {}
    with open(CONCRETENESS_DATA, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            word = row["Word"].strip().lower()
            ratings[word] = float(row["Conc.M"])
    return ratings


# ── Module-level init (runs once on import) ────────────────────────────────────

_stemmer = SnowballStemmer("english")
_words_list = _build_vocab()
_model = SentenceTransformer(MODEL_NAME)
_embeddings = _load_or_build_embeddings(_words_list, _model)

VOCAB_WORDS = np.array(_words_list)
VOCAB_EMBEDDINGS = _embeddings
CONCRETENESS_RATINGS = _load_concreteness()

# ── Internal helpers ───────────────────────────────────────────────────────────

def _embed(word: str) -> np.ndarray:
    """Get the embedding for a word, encoding on the fly if not in vocab."""
    idx = np.where(VOCAB_WORDS == word.lower())[0]
    if len(idx) > 0:
        return VOCAB_EMBEDDINGS[idx[0]]
    return _model.encode([word], convert_to_numpy=True, normalize_embeddings=True)[0]


def _root_form(word: str) -> str:
    """Aggressive normalization for dedup: strip suffixes then prefixes."""
    # First try the stemmer
    stem = _stemmer.stem(word)
    # Also try suffix stripping for cases the stemmer misses
    bases = _strip_suffixes(word)
    # Use shortest base as the canonical form (most reduced)
    candidates = {stem} | bases
    root = min(candidates, key=len)
    if len(root) < 3:
        root = stem
    # Strip common prefixes
    for prefix in ("un", "re", "over", "under", "out"):
        if root.startswith(prefix) and len(root) > len(prefix) + 2:
            return root[len(prefix):]
    return root


_COMMON_SUFFIXES = (
    "ly", "ily", "ally", "ially", "ically",
    "er", "or", "ier", "eer",
    "est", "iest",
    "ing", "ting", "ning",
    "ed", "ied", "ted",
    "ness", "ment", "ful", "less",
    "ity", "ous", "ive", "tion", "ation",
    "en", "ened", "ening",
    "ish", "like", "ward", "wise",
    "s", "es",
)


def _strip_suffixes(word: str) -> set[str]:
    """Return all possible bases of a word by stripping known suffixes."""
    bases = {word}
    for suffix in _COMMON_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            base = word[:-len(suffix)]
            bases.add(base)
            # Handle doubled consonants: "thinner" → "thinn" → "thin"
            if len(base) >= 4 and base[-1] == base[-2] and base[-1].isalpha():
                bases.add(base[:-1])
    return bases


def _shared_prefix_len(a: str, b: str) -> int:
    """Return the length of the shared prefix between two strings."""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def _is_morphological_variant(word: str, target: str) -> bool:
    """Check if word is a morphological variant of target (or vice versa)."""
    if word.startswith(target) or target.startswith(word):
        return True

    # Check if stripping suffixes from either word produces an overlap
    word_bases = _strip_suffixes(word)
    target_bases = _strip_suffixes(target)
    if word_bases & target_bases:
        return True
    for wb in word_bases:
        for tb in target_bases:
            if wb.startswith(tb) or tb.startswith(wb):
                return True

    # Shared prefix heuristic: if 75%+ of the shorter word matches, likely variant
    prefix_len = _shared_prefix_len(word, target)
    min_len = min(len(word), len(target))
    if min_len >= 4 and prefix_len / min_len >= 0.75:
        return True

    return False


_ANTONYM_PAIRS = {
    frozenset(p) for p in [
        ("safe", "risky"), ("safe", "dangerous"), ("safe", "unsafe"),
        ("gentle", "rough"), ("gentle", "harsh"), ("gentle", "fierce"), ("gentle", "violent"),
        ("sharp", "blunt"), ("sharp", "dull"), ("sharp", "smooth"),
        ("heavy", "light"), ("heavy", "lightweight"), ("heavy", "thin"), ("heavy", "weak"),
        ("lonely", "social"), ("lonely", "popular"),
        ("hot", "cold"), ("big", "small"), ("fast", "slow"),
        ("happy", "sad"), ("good", "bad"), ("strong", "weak"),
        ("hard", "soft"), ("dark", "bright"), ("loud", "quiet"),
        ("rich", "poor"), ("old", "young"), ("tall", "short"),
        ("brave", "cowardly"), ("calm", "anxious"),
        ("gentle", "aggressive"), ("gentle", "cruel"), ("gentle", "brutal"),
        ("gentle", "vulgar"), ("gentle", "lethal"), ("gentle", "threatening"),
        ("gentle", "abused"), ("gentle", "rude"),
        ("sharp", "soft"), ("sharp", "fuzzy"),
        ("lonely", "connected"), ("lonely", "surrounded"),
        ("risky", "harmless"), ("risky", "safe"),
        ("gentle", "strong"), ("gentle", "loud"), ("gentle", "intense"),
        ("gentle", "hostile"), ("gentle", "nasty"), ("gentle", "vicious"),
        ("lonely", "happy"), ("lonely", "cheerful"), ("lonely", "joyful"),
        ("lonely", "busy"), ("lonely", "gathering"), ("lonely", "together"),
        ("gentle", "unpleasant"), ("gentle", "painful"), ("gentle", "discomfort"),
        ("fire", "water"), ("fire", "ice"),
    ]
}


def _get_antonyms(word: str) -> set[str]:
    """Get antonyms from WordNet + curated pairs."""
    antonyms = set()
    # WordNet antonyms
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            for ant in lemma.antonyms():
                antonyms.add(ant.name().replace("_", " ").lower())
    # Curated pairs
    word_lower = word.lower()
    for pair in _ANTONYM_PAIRS:
        if word_lower in pair:
            antonyms |= pair - {word_lower}
    return antonyms


def _dedup_by_stem(words, sims, target_word: str):
    """Keep only the highest-similarity word per stem, excluding the target's variants."""
    target_stem = _stemmer.stem(target_word)
    target_root = _root_form(target_word)
    target_lower = target_word.lower()
    seen_stems = set()
    out_words, out_sims = [], []
    for w, s in zip(words, sims):
        stem = _stemmer.stem(w)
        root = _root_form(w)
        if stem == target_stem or root == target_root:
            continue
        if _is_morphological_variant(w, target_lower):
            continue
        if root in seen_stems:
            continue
        seen_stems.add(root)
        out_words.append(w)
        out_sims.append(s)
    return out_words, out_sims


# ── Public API ─────────────────────────────────────────────────────────────────

def associate(word: str, surprise: int = 5, top_k: int = 20, concreteness: int | None = None) -> list[tuple[str, float]]:
    """
    Find words associated with `word`.

    Args:
        word: the seed word
        surprise: 1-10 dial. 1 = near-synonyms, 10 = far-flung but still connected.
        top_k: max number of results to return
        concreteness: 1-10 dial or None. When set, filters to words above a
            minimum concreteness threshold (Brysbaert et al. ratings).
            1 = barely filters, 10 = only very concrete/sensory words.
            Words without a concreteness rating are excluded when set.

    Returns:
        List of (word, similarity) sorted by descending similarity.
    """
    surprise = max(1, min(10, surprise))

    if concreteness is not None:
        concreteness = max(1, min(10, concreteness))
        conc_threshold = 1.5 + (concreteness - 1) * (3.0 / 9)

    # Map surprise 1-10 to a similarity window with descending-similarity ranking.
    # Adaptive width: wider at low surprise (more synonyms available),
    # narrower at high surprise (more selective/poetic).
    high = 0.85 - (surprise - 1) * 0.063
    width = 0.27 - (surprise - 1) * 0.006  # 0.27 at s=1, 0.216 at s=10
    low = max(0.10, high - width)

    target_vec = _embed(word)
    target_lower = word.lower()

    sims = VOCAB_EMBEDDINGS @ target_vec
    mask = (sims >= low) & (sims <= high) & (VOCAB_WORDS != target_lower)

    # Filter antonyms using WordNet
    antonyms = _get_antonyms(word)
    if antonyms:
        candidate_indices = np.where(mask)[0]
        for i in candidate_indices:
            w_str = str(VOCAB_WORDS[i])
            if w_str in antonyms:
                mask[i] = False
                continue
            for ant in antonyms:
                if _is_morphological_variant(w_str, ant):
                    mask[i] = False
                    break

    # Filter by concreteness rating when requested
    if concreteness is not None:
        candidate_indices = np.where(mask)[0]
        for i in candidate_indices:
            w_str = str(VOCAB_WORDS[i])
            rating = CONCRETENESS_RATINGS.get(w_str)
            if rating is None or rating < conc_threshold:
                mask[i] = False

    # For surprise >= 4, exclude obvious synonyms (high similarity words)
    # to ensure results feel like genuine semantic jumps, not thesaurus entries.
    if surprise >= 4:
        synonym_ceiling = 0.52  # Words above this are "synonyms"
        mask = mask & (sims < synonym_ceiling)

    if surprise >= 7:
        # At high surprise, mildly penalize long abstract words (>8 chars).
        # This favors concrete/sensory vocabulary over clinical/abstract terms.
        candidate_indices = np.where(mask)[0]
        word_lengths = np.array([len(str(VOCAB_WORDS[i])) for i in candidate_indices])
        length_penalty = np.maximum(0, (word_lengths - 8.0) * 0.005)
        scores = sims[candidate_indices] - length_penalty
        order = np.argsort(-scores)
        sorted_words = VOCAB_WORDS[candidate_indices[order]]
        sorted_sims = sims[candidate_indices[order]]
    else:
        order = np.argsort(-sims[mask])
        sorted_words = VOCAB_WORDS[mask][order]
        sorted_sims = sims[mask][order]

    deduped_words, deduped_sims = _dedup_by_stem(sorted_words, sorted_sims, word)
    return [(w, float(s)) for w, s in zip(deduped_words[:top_k], deduped_sims[:top_k])]
