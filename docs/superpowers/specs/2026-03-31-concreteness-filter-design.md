# Concreteness Filter for `associate()`

## Summary

Add an optional `concreteness` kwarg (1-10) to `associate()` that filters results by how concrete/sensory the words are, using Brysbaert et al. concreteness ratings.

## Signature

```python
def associate(
    word: str,
    surprise: int = 5,
    top_k: int = 20,
    concreteness: int | None = None,
) -> list[tuple[str, float]]:
```

- `concreteness=None` (default): no filtering, existing behavior unchanged.
- `concreteness=1`: minimal filter (~1.5 Brysbaert threshold), allows nearly everything.
- `concreteness=10`: strict filter (~4.5 Brysbaert threshold), only very concrete/sensory words.

## Data Source

Brysbaert et al. concreteness ratings (~40k English words, rated 1-5 scale where 1=abstract, 5=concrete). Loaded at module init into a `dict[str, float]` mapping word to rating.

## Kwarg-to-Threshold Mapping

Linear interpolation from the 1-10 kwarg to the 1-5 Brysbaert scale:

```
min_score = 1.5 + (concreteness - 1) * (3.0 / 9)
```

| kwarg | min Brysbaert score |
|-------|-------------------|
| 1     | 1.50              |
| 5     | 2.83              |
| 10    | 4.50              |

## Filtering Behavior

- Applied as a boolean mask step, alongside existing similarity/antonym filters.
- Words **not present** in the Brysbaert dataset are **excluded** when `concreteness` is set.
- When `concreteness is None`, no filtering at all -- words pass regardless of rating or dataset presence.

## Existing Length Penalty

The word-length penalty at surprise >= 7 (lines 332-338) is kept as-is. It's cheap, complementary, and doesn't conflict with the new filter.

## Implementation Steps

1. Obtain and bundle Brysbaert concreteness data (CSV) in the project.
2. Add loader at module init to build `CONCRETENESS_RATINGS: dict[str, float]`.
3. Add `concreteness` kwarg to `associate()` with validation (clamp 1-10, None passthrough).
4. Add mask step: if `concreteness` is not None, exclude words without a rating and words below the computed threshold.
5. Update README future ideas to reflect this is implemented.
6. Update `eval_cases.py` to test concreteness at different settings (e.g. `None`, `3`, `7`, `10`) across the existing test words, so results can be evaluated in future ralph loops.
