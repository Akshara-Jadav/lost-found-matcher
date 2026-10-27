import pytest
from datetime import date
from app.models import LostReport, FoundReport
from app.scorers import (Scorer, CategoryScorer, LocationScorer,
                         DateScorer, ColorBrandScorer)


def make_lost(**kw):
    d = dict(report_id=1, category="earphones", description="black boat earphones",
             location="library", event_date=date(2026, 10, 1),
             contact="9999999999", color="black", brand="boat")
    d.update(kw)
    return LostReport(**d)


def make_found(**kw):
    d = dict(report_id=2, category="earphones", description="boat earphones black",
             location="library", event_date=date(2026, 10, 2),
             contact="8888888888", color="black", brand="boat")
    d.update(kw)
    return FoundReport(**d)


def test_same_category_scores_one():
    assert CategoryScorer().score(make_lost(), make_found()) == 1.0


def test_different_category_scores_zero():
    assert CategoryScorer().score(make_lost(), make_found(category="wallet")) == 0.0


def test_same_location_scores_one():
    assert LocationScorer().score(make_lost(), make_found()) == 1.0


def test_nearby_location_scores_half():
    assert LocationScorer().score(make_lost(), make_found(location="canteen")) == 0.5


def test_far_location_scores_zero():
    assert LocationScorer().score(make_lost(), make_found(location="hostel")) == 0.0


def test_found_before_lost_scores_zero():
    found = make_found(event_date=date(2026, 9, 20))
    assert DateScorer().score(make_lost(), found) == 0.0


def test_found_next_day_scores_one():
    assert DateScorer().score(make_lost(), make_found()) == 1.0


def test_color_and_brand_scoring():
    scorer = ColorBrandScorer()
    assert scorer.score(make_lost(), make_found()) == 1.0
    assert scorer.score(make_lost(), make_found(brand="sony")) == 0.5
    assert scorer.score(make_lost(), make_found(color="red", brand="sony")) == 0.0


def test_scorer_base_class_cannot_be_used_directly():
    with pytest.raises(TypeError):
        Scorer()

def test_category_typo_still_matches():
    assert CategoryScorer().score(make_lost(), make_found(category="earphone")) == 1.0


def test_location_typo_still_matches():
    assert LocationScorer().score(make_lost(), make_found(location="libary")) == 1.0