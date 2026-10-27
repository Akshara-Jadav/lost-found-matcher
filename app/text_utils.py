import re
from difflib import SequenceMatcher

STOPWORDS = {"the", "a", "an", "of", "with", "and", "in", "on",
             "my", "is", "it", "near", "has", "have", "i", "found", "lost"}


def tokenize(text):
    """Turn a description into a set of useful lowercase words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def jaccard(a, b):
    """Shared words divided by total unique words (0.0 to 1.0)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def text_similarity(text1, text2):
    """Combine word overlap with spelling closeness (0.0 to 1.0)."""
    s1, s2 = tokenize(text1), tokenize(text2)
    overlap = jaccard(s1, s2)
    ratio = SequenceMatcher(None, " ".join(sorted(s1)),
                            " ".join(sorted(s2))).ratio()
    return round(0.6 * overlap + 0.4 * ratio, 3)