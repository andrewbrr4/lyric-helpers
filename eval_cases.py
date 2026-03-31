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
