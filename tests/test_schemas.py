import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from app.schemas import ReportCreate, ClaimRequest, KNOWN_LOCATIONS

PLACE = sorted(KNOWN_LOCATIONS)[0]      # any valid place from your NEARBY list


def valid_lost(**changes):
    data = dict(kind="lost", category="earphones",
                description="black boat earphones", location=PLACE,
                event_date=date(2026, 10, 1), contact="9999999999")
    data.update(changes)
    return data


def test_valid_lost_report_is_accepted():
    report = ReportCreate(**valid_lost())
    assert report.kind == "lost"


def test_location_is_cleaned_and_lowercased():
    report = ReportCreate(**valid_lost(location=f"  {PLACE.upper()}  "))
    assert report.location == PLACE


def test_any_typed_location_is_accepted():
    report = ReportCreate(**valid_lost(location="  The Sports   Complex "))
    assert report.location == "the sports complex"



def test_future_date_is_rejected():
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        ReportCreate(**valid_lost(event_date=tomorrow))


def test_category_without_letters_is_rejected():
    with pytest.raises(ValidationError):
        ReportCreate(**valid_lost(category="123"))


def test_too_short_description_is_rejected():
    with pytest.raises(ValidationError):
        ReportCreate(**valid_lost(description="hi"))


def test_found_report_without_verification_is_rejected():
    with pytest.raises(ValidationError):
        ReportCreate(**valid_lost(kind="found"))


def test_found_report_with_verification_is_accepted():
    report = ReportCreate(**valid_lost(kind="found",
                                       verification_question="Sticker?",
                                       verification_answer="Hello Kitty"))
    assert report.kind == "found"


def test_claim_needs_a_non_empty_answer():
    with pytest.raises(ValidationError):
        ClaimRequest(lost_id=1, found_id=2, answer="   ")