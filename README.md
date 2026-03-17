# lyric-helpers

A repo for various jupyter notebooks, functions and classes with the common theme of using NLP/AI technologies to assist with song lyric writing.

Uses the conda environment `lyrics-helpers`.

## Notebooks

### word_associations.ipynb

Finds words that are semantically similar--but not *too* similar--to the target word. The purpose is not just to serve as a simple thesaurus for substituting specific words in a line (though that is a potential use case), but for more broad lyrical brainstorming and for building word-banks around a particular concept.

Features a "surprise" dial: low surprise gives near-synonyms, high surprise gives unexpected but still connected associations--the sweet spot for creative writing. Also includes a contrast mode that surfaces conceptual opposites for lyrical tension.

#### Future ideas

- **Multi-word concept blending** -- Input 2+ seed words and find words near their centroid in embedding space (e.g. "ocean" + "grief" surfaces words evoking both)
- **Phonetic/rhyme-aware filtering** -- Layer sound similarity (via CMU Pronouncing Dictionary) on top of semantic similarity to find words that rhyme *and* relate
- **Syllable count filtering** -- Filter results by syllable count to fit a specific meter or melodic rhythm
- **Concrete/sensory word bias** -- Use concreteness ratings (e.g. Brysbaert et al.) to bias toward tangible, imagistic words over abstract ones
- **Thematic clustering** -- Cluster results into sub-themes (e.g. "risky" → {danger/fear}, {gambling/chance}, {adventure/thrill}) to reveal different lyrical angles
- **Word bank accumulation & export** -- Build up vocabulary across multiple queries and export to a file for a songwriting session