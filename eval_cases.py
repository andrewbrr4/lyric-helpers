"""
Run a fixed set of test cases through associate/contrast and print results.
Usage: python eval_cases.py
"""

from word_associations import associate, contrast

TEST_WORDS = ["heavy", "risky", "gentle", "fire", "lonely", "sharp"]
SURPRISE_LEVELS = [2, 5, 8]


def run():
    for word in TEST_WORDS:
        print(f"\n{'='*60}")
        print(f"  {word.upper()}")
        print(f"{'='*60}")

        for s in SURPRISE_LEVELS:
            results = associate(word, surprise=s, top_k=15)
            words_only = [w for w, _ in results]
            print(f"\n  associate(surprise={s}): {', '.join(words_only)}")

        results = contrast(word, top_k=15)
        words_only = [w for w, _ in results]
        print(f"\n  contrast: {', '.join(words_only)}")


if __name__ == "__main__":
    run()
