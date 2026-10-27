from app.text_utils import tokenize, jaccard, text_similarity


def test_tokenize_removes_punctuation_and_stopwords():
    assert tokenize("The Black case, with strap!") == {"black", "case", "strap"}


def test_jaccard_of_identical_sets_is_one():
    assert jaccard({"a", "b"}, {"a", "b"}) == 1.0


def test_jaccard_with_empty_set_is_zero():
    assert jaccard(set(), {"a"}) == 0.0


def test_word_order_does_not_matter():
    assert text_similarity("black boat earphones", "earphones boat black") > 0.95


def test_similar_descriptions_beat_different_ones():
    similar = text_similarity("black boat earphones", "boat earphones black case")
    different = text_similarity("black boat earphones", "brown leather wallet")
    assert similar > different


def test_empty_description_scores_zero():
    assert text_similarity("", "boat earphones") == 0.0