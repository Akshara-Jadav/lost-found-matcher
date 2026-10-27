from datetime import date
from app.models import LostReport, FoundReport
from app.matcher import Matcher
from app.scorers import CategoryScorer


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


def test_similar_items_score_high():
    assert Matcher().score_pair(make_lost(), make_found()) >= 60


def test_different_item_scores_low():
    found = make_found(category="wallet", description="brown leather wallet",
                       color="brown", brand="")
    assert Matcher().score_pair(make_lost(), found) < 60


def test_score_never_exceeds_100():
    assert Matcher().score_pair(make_lost(), make_found()) <= 100


def test_best_match_comes_first():
    good = make_found(report_id=2)
    weaker = make_found(report_id=3, description="white sony earphones",
                        color="white", brand="sony")
    matches = Matcher().find_matches([make_lost()], [weaker, good])
    assert [m.found.id for m in matches] == [2, 3]


def test_matches_below_threshold_are_excluded():
    wallet = make_found(category="wallet", description="brown leather wallet",
                        color="brown", brand="")
    assert Matcher().find_matches([make_lost()], [wallet]) == []


def test_claimed_reports_are_ignored():
    found = make_found()
    found.status = "claimed"
    assert Matcher().find_matches([make_lost()], [found]) == []


def test_custom_scorer_list_can_be_plugged_in():
    matcher = Matcher(scorers=[CategoryScorer()])
    assert matcher.score_pair(make_lost(), make_found()) == 100.0


def test_explain_lists_every_scorer():
    breakdown = Matcher().explain(make_lost(), make_found())
    assert set(breakdown) == {"CategoryScorer", "TextScorer", "LocationScorer",
                              "DateScorer", "ColorBrandScorer"}