# Word Association Eval Criteria

## What makes a good result?

### Low surprise (1-3): a Roget's-style thesaurus
Results are closely related--synonyms are allowed within this range. For instance, in this range, "heavy" might return:

- weight
- pounds
- burden

### Medium surprise (4-6): semantic jumps
Results are related, but not obviously so. We are outside the range of synonyms/thesaurus lookups, but still grounded by an identifiable connection. In this range "ocean" might return:

- storm (storms come from the ocean)
- summertime (ocean/summer both associated with beach days)
- adventure (thinking a sailor on the seven seas)

### High surprise (7-10): impressionistic poetry
At this range, we can allow results to get a bit more avant-garde. Results in this range should *feel* connected, but in a way that a reader might not be able to explicitly name. Subconscious and novel connections can be discovered here. Results for "memory" might look like:

- mold (vague feelings of aging, time)
- august (summer ending, phases of the year/of life)
- toothache (pain, childhood)

At this range, it is expected that there may be some nonsense, but there also might be something truly special.

## What makes a bad result?

- Morphological variants of the seed word (heavily, heavier) -- these waste slots
- Measurement units, abbreviations, technical terms (lbs, lb, kg)
- Proper nouns (names, places, brands) unless they carry strong connotation
- Words with no emotional or sensory quality (intervals, documentation, registry)
- Near-duplicates in the same result set (thin/thinner, strong/stronger)
- Opposites are discouraged for the time being--"happy" should ideally not return "sad"

## Other requirements:
- Part of speech filter should accurately filter results
- Different ranges of concreteness filters should behave as expected 
