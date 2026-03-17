import re
from pathlib import Path

import numpy as np
from wordfreq import top_n_list, zipf_frequency
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sentence_transformers import SentenceTransformer

# ── Configuration ──────────────────────────────────────────────────────────────

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = Path(__file__).parent / "cache"
EMBEDDINGS_CACHE = CACHE_DIR / "vocab_embeddings.npz"

N_WORDS = 100_000
MIN_ZIPF = 3.5
MAX_ZIPF = 6.5

# ── Vocabulary ─────────────────────────────────────────────────────────────────

def _normalize(word: str) -> str:
    return re.sub(r"[^a-z]", "", word.lower())


def _build_vocab() -> list[str]:
    nltk.download("stopwords", quiet=True)
    stop = set(stopwords.words("english"))

    vocab = list(dict.fromkeys(
        w for raw in top_n_list("en", N_WORDS)
        if 2 <= len(w := _normalize(raw)) <= 20
    ))

    return [
        w for w in vocab
        if w not in stop and MIN_ZIPF <= zipf_frequency(w, "en") <= MAX_ZIPF
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


# ── Module-level init (runs once on import) ────────────────────────────────────

_stemmer = SnowballStemmer("english")
_words_list = _build_vocab()
_model = SentenceTransformer(MODEL_NAME)
_embeddings = _load_or_build_embeddings(_words_list, _model)

VOCAB_WORDS = np.array(_words_list)
VOCAB_EMBEDDINGS = _embeddings

# ── Internal helpers ───────────────────────────────────────────────────────────

def _embed(word: str) -> np.ndarray:
    """Get the embedding for a word, encoding on the fly if not in vocab."""
    idx = np.where(VOCAB_WORDS == word.lower())[0]
    if len(idx) > 0:
        return VOCAB_EMBEDDINGS[idx[0]]
    return _model.encode([word], convert_to_numpy=True, normalize_embeddings=True)[0]


def _dedup_by_stem(words, sims, target_word: str):
    """Keep only the highest-similarity word per stem, excluding the target's stem."""
    target_stem = _stemmer.stem(target_word)
    seen_stems = set()
    out_words, out_sims = [], []
    for w, s in zip(words, sims):
        stem = _stemmer.stem(w)
        if stem == target_stem or stem in seen_stems:
            continue
        seen_stems.add(stem)
        out_words.append(w)
        out_sims.append(s)
    return out_words, out_sims


# ── Public API ─────────────────────────────────────────────────────────────────

def associate(word: str, surprise: int = 5, top_k: int = 40) -> list[tuple[str, float]]:
    """
    Find words associated with `word`.

    Args:
        word: the seed word
        surprise: 1-10 dial. 1 = near-synonyms, 10 = far-flung but still connected.
        top_k: max number of results to return

    Returns:
        List of (word, similarity) sorted by descending similarity.
    """
    surprise = max(1, min(10, surprise))

    # Map surprise 1-10 to a similarity window.
    # 1 → [0.65, 0.85] (close synonyms)
    # 10 → [0.20, 0.40] (distant but still related)
    high = 0.85 - (surprise - 1) * 0.05
    low = high - 0.20

    target_vec = _embed(word)
    target_lower = word.lower()

    sims = VOCAB_EMBEDDINGS @ target_vec
    mask = (sims >= low) & (sims <= high) & (VOCAB_WORDS != target_lower)

    order = np.argsort(-sims[mask])
    sorted_words = VOCAB_WORDS[mask][order]
    sorted_sims = sims[mask][order]

    deduped_words, deduped_sims = _dedup_by_stem(sorted_words, sorted_sims, word)
    return [(w, float(s)) for w, s in zip(deduped_words[:top_k], deduped_sims[:top_k])]
