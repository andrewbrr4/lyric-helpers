# Word Association Eval Criteria

## What makes a good result?

### Part of speech filtering
- Part of speech filter should accurately filter based on words' *common usage*, not on whether a word technically has a synset of that POS in WordNet. A human user should look at the result and immediately read each word as the requested POS. Examples of what this rules out:
  - Gerunds like "digging", "glowing", "striking" should not appear under `pos="noun"`, even though WordNet has nominalized senses ("excavation", "radiance", "hit") for them.
  - Denominal verbs like "rabbit", "water", "oil", "bale" should not appear under `pos="verb"`, even though WordNet has verb senses like "to hunt rabbits" or "to provide with water".
  - Apply this principle to all four POS values (noun, verb, adjective, adverb).

### The surprise setting
#### Low surprise (1-3): a Roget's-style thesaurus
Results are closely related--synonyms are allowed within this range. For instance, in this range, "heavy" might return:

- weight
- pounds
- burden

For different part-of-speech filter values we might see:
*noun*: weight, pounds, burden
*verb*: sag, weigh, pull
*adjective*: massive, dragging

#### Medium surprise (4-6): semantic jumps
Results are related, but not obviously so. We are outside the range of synonyms/thesaurus lookups, but still grounded by an identifiable connection. In this range "ocean" might return:

- storm (storms come from the ocean)
- summertime (ocean/summer both associated with beach days)
- adventure (thinking a sailor on the seven seas)

For different part-of-speech filter values we might see:
*noun*: storm, summertime, adventure
*verb*: rage, flood, churn
*adjective*: stormy, deep

#### High surprise (7-10): impressionistic poetry
At this range, we can allow results to get a bit more avant-garde. Results in this range should *feel* connected, but in a way that a reader might not be able to explicitly name. Subconscious and novel connections can be discovered here. Results for "memory" might look like:

- mold (vague feelings of aging, time)
- august (summer ending, phases of the year/of life)
- toothache (pain, childhood)

At this range, it is expected that there may be some nonsense, but there also might be something truly special.

For different part-of-speech filter values we might see:
*noun*: mold, august, toothache
*verb*: ache, pull, bite
*adjective*: moldy, painted

### Other requirements:
- Different ranges of concreteness filters should behave as expected.
- No one filter should degrade the performance of another filter -- adding a POS filter should not give us worse matches for our surprise filter or visa-versa etc.
- Few or no results are preferable to bad results.

## What makes a bad result?

- Morphological variants of the seed word (heavily, heavier) -- these waste slots
- Measurement units, abbreviations, technical terms (lbs, lb, kg)
- Proper nouns (names, places, brands) unless they carry strong connotation
- Words with no emotional or sensory quality (intervals, documentation, registry)
- Near-duplicates in the same result set (thin/thinner, strong/stronger)
- Opposites are discouraged for the time being--"happy" should ideally not return "sad"
