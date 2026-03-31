# Concreteness Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional `concreteness` kwarg to `associate()` that filters results by Brysbaert et al. concreteness ratings.

**Architecture:** Download and vendor the Brysbaert TSV (~1.5MB) in `data/`. Load it at module init into a dict. Apply as a boolean mask in the existing filtering pipeline when the kwarg is set.

**Tech Stack:** Python stdlib `csv` module for loading. No new dependencies.

---

### Task 1: Download and vendor the Brysbaert concreteness data

**Files:**
- Create: `data/concreteness_brysbaert.tsv`

- [ ] **Step 1: Create the data directory**

```bash
mkdir -p data
```

- [ ] **Step 2: Download the Brysbaert TSV**

```bash
curl -L -o data/concreteness_brysbaert.tsv \
  "https://raw.githubusercontent.com/ArtsEngine/concreteness/master/Concreteness_ratings_Brysbaert_et_al_BRM.txt"
```

- [ ] **Step 3: Verify the download**

```bash
head -3 data/concreteness_brysbaert.tsv
wc -l data/concreteness_brysbaert.tsv
```

Expected: First line is a header with columns including `Word` and `Conc.M`. File should have ~40k lines.

- [ ] **Step 4: Commit**

```bash
git add data/concreteness_brysbaert.tsv
git commit -m "Add Brysbaert et al. concreteness ratings data"
```

---

### Task 2: Add concreteness data loader to `word_associations.py`

**Files:**
- Modify: `word_associations.py:1-16` (imports and config section)
- Modify: `word_associations.py:119-128` (module-level init section)

- [ ] **Step 1: Add `csv` import**

Add `import csv` to the imports at the top of `word_associations.py` (after `import re`, line 1):

```python
import csv
import re
from pathlib import Path
```

- [ ] **Step 2: Add the data file path constant**

After `EMBEDDINGS_CACHE` (line 15), add:

```python
CONCRETENESS_DATA = Path(__file__).parent / "data" / "concreteness_brysbaert.tsv"
```

- [ ] **Step 3: Add the loader function**

After the `_load_or_build_embeddings` function (after line 116), add:

```python
def _load_concreteness() -> dict[str, float]:
    """Load Brysbaert et al. concreteness ratings from vendored TSV."""
    ratings = {}
    with open(CONCRETENESS_DATA, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            word = row["Word"].strip().lower()
            ratings[word] = float(row["Conc.M"])
    return ratings
```

- [ ] **Step 4: Add module-level init call**

After `VOCAB_EMBEDDINGS = _embeddings` (line 127), add:

```python
CONCRETENESS_RATINGS = _load_concreteness()
```

- [ ] **Step 5: Verify it loads**

```bash
python -c "from word_associations import CONCRETENESS_RATINGS; print(len(CONCRETENESS_RATINGS)); print(CONCRETENESS_RATINGS.get('hammer')); print(CONCRETENESS_RATINGS.get('freedom'))"
```

Expected: ~40k entries. `hammer` should be high (4.5+). `freedom` should be low (1-2ish).

- [ ] **Step 6: Commit**

```bash
git add word_associations.py
git commit -m "Add Brysbaert concreteness data loader"
```

---

### Task 3: Add `concreteness` kwarg and filtering to `associate()`

**Files:**
- Modify: `word_associations.py:285-348` (the `associate()` function)

- [ ] **Step 1: Update the function signature**

Change line 285 from:

```python
def associate(word: str, surprise: int = 5, top_k: int = 20) -> list[tuple[str, float]]:
```

to:

```python
def associate(word: str, surprise: int = 5, top_k: int = 20, concreteness: int | None = None) -> list[tuple[str, float]]:
```

- [ ] **Step 2: Update the docstring**

Replace the existing docstring (lines 286-296) with:

```python
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
```

- [ ] **Step 3: Add concreteness validation and threshold calculation**

After the surprise clamp (line 297 `surprise = max(1, min(10, surprise))`), add:

```python
    if concreteness is not None:
        concreteness = max(1, min(10, concreteness))
        conc_threshold = 1.5 + (concreteness - 1) * (3.0 / 9)
```

- [ ] **Step 4: Add concreteness mask step**

After the antonym filtering block (after line 324, before the synonym ceiling block), add:

```python
    # Filter by concreteness rating when requested
    if concreteness is not None:
        candidate_indices = np.where(mask)[0]
        for i in candidate_indices:
            w_str = str(VOCAB_WORDS[i])
            rating = CONCRETENESS_RATINGS.get(w_str)
            if rating is None or rating < conc_threshold:
                mask[i] = False
```

- [ ] **Step 5: Verify basic functionality**

```bash
python -c "
from word_associations import associate
# No concreteness filter (baseline)
base = associate('fire', surprise=5, top_k=10)
print('No filter:', [w for w, _ in base])

# High concreteness filter
concrete = associate('fire', surprise=5, top_k=10, concreteness=8)
print('Concreteness=8:', [w for w, _ in concrete])

# Very high concreteness filter
very_concrete = associate('fire', surprise=5, top_k=10, concreteness=10)
print('Concreteness=10:', [w for w, _ in very_concrete])
"
```

Expected: Higher concreteness values should return more tangible/sensory words and fewer abstract ones. The filtered lists should be subsets or near-subsets of the unfiltered list.

- [ ] **Step 6: Commit**

```bash
git add word_associations.py
git commit -m "Add concreteness kwarg to associate()"
```

---

### Task 4: Update `eval_cases.py`

**Files:**
- Modify: `eval_cases.py`

- [ ] **Step 1: Replace `eval_cases.py` contents**

Replace the full file with:

```python
"""
Run a fixed set of test cases through associate and print results.
Usage: python eval_cases.py
"""

from word_associations import associate

TEST_WORDS = ["money", "risky", "gentle", "fire", "lonely", "sharp"]
SURPRISE_LEVELS = [2, 5, 8]
CONCRETENESS_LEVELS = [None, 3, 7, 10]


def run():
    for word in TEST_WORDS:
        print(f"\n{'='*60}")
        print(f"  {word.upper()}")
        print(f"{'='*60}")

        for s in SURPRISE_LEVELS:
            results = associate(word, surprise=s, top_k=15)
            words_only = [w for w, _ in results]
            print(f"\n  associate(surprise={s}): {', '.join(words_only)}")

        for c in CONCRETENESS_LEVELS:
            label = str(c) if c is not None else "None"
            results = associate(word, surprise=5, top_k=15, concreteness=c)
            words_only = [w for w, _ in results]
            print(f"\n  associate(surprise=5, concreteness={label}): {', '.join(words_only)}")


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run eval_cases.py**

```bash
python eval_cases.py
```

Expected: Each word shows results for surprise levels (unchanged from before) plus concreteness levels. Higher concreteness values should visibly shift results toward tangible/sensory words.

- [ ] **Step 3: Commit**

```bash
git add eval_cases.py
git commit -m "Add concreteness levels to eval_cases.py"
```

---

### Task 5: Update README

**Files:**
- Modify: `README.md:17`

- [ ] **Step 1: Update the future ideas section**

Change line 17 from:

```markdown
- **Concrete/sensory word bias** -- Use concreteness ratings (e.g. Brysbaert et al.) to bias toward tangible, imagistic words over abstract ones
```

to:

```markdown
- ~~**Concrete/sensory word bias**~~ -- Implemented: `concreteness` kwarg (1-10) filters by Brysbaert et al. concreteness ratings
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Mark concreteness filter as implemented in README"
```
