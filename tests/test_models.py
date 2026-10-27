from datetime import date
from app.models import LostReport, FoundReport


def make_found():
    return FoundReport(2, "Earphones", "boat earphones black", "Library",
                       date(2026, 10, 2), "8888888888",
                       verification_question="Sticker?",
                       verification_answer="Hello Kitty")


def test_category_and_location_are_cleaned():
    lost = LostReport(1, " Earphones ", "black earphones", " Library ",
                      date(2026, 10, 1), "9999999999")
    assert lost.category == "earphones"
    assert lost.location == "library"


def test_correct_answer_is_accepted_ignoring_case():
    assert make_found().check_answer("  hello KITTY ") is True


def test_wrong_answer_is_rejected():
    assert make_found().check_answer("star") is False