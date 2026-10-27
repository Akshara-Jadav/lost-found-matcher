import pytest
from datetime import date, timedelta
from app.models import LostReport, FoundReport
from app.matcher import Matcher
from app.scorers import LocationScorer, DateScorer


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


def test_empty_description_does_not_crash():
    score = Matcher().score_pair(make_lost(description=""), make_found())
    assert 0 <= score <= 100


def test_description_of_only_filler_words_does_not_crash():
    score = Matcher().score_pair(make_lost(description="the a of"), make_found())
    assert 0 <= score <= 100


def test_unknown_locations():
    scorer = LocationScorer()
    assert scorer.score(make_lost(location="zzz"), make_found(location="yyy")) == 0.0
    assert scorer.score(make_lost(location="zzz"), make_found(location="zzz")) == 1.0


@pytest.mark.parametrize("gap, expected", [
    (0, 1.0), (1, 1.0), (2, 0.6), (7, 0.6), (8, 0.3), (30, 0.3), (31, 0.0),
])
def test_date_score_boundaries(gap, expected):
    found = make_found(event_date=date(2026, 10, 1) + timedelta(days=gap))
    assert DateScorer().score(make_lost(), found) == expected


def test_threshold_is_inclusive():
    matches = Matcher(threshold=100).find_matches([make_lost()], [make_found()])
    assert len(matches) == 1


def test_results_are_sorted_best_first():
    lost = [make_lost(report_id=i, description=f"black boat earphones {i}")
            for i in range(1, 6)]
    found = [make_found(report_id=10 + i,
                        event_date=date(2026, 10, 1) + timedelta(days=i * 3))
             for i in range(5)]
    scores = [m.score for m in Matcher().find_matches(lost, found)]
    assert len(scores) > 1
    assert scores == sorted(scores, reverse=True)