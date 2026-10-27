import pytest
from datetime import date
from app.storage import ReportStore


def lost_fields():
    return dict(category="earphones", description="black boat earphones",
                location="library", event_date=date(2026, 10, 1),
                contact="9999999999", color="black", brand="boat")


def found_fields():
    return dict(category="earphones", description="boat earphones black",
                location="library", event_date=date(2026, 10, 2),
                contact="8888888888", color="black", brand="boat",
                verification_question="Sticker?",
                verification_answer="Hello Kitty")


def test_add_assigns_incrementing_ids(tmp_path):
    store = ReportStore(tmp_path / "reports.json")
    a = store.add("lost", **lost_fields())
    b = store.add("found", **found_fields())
    assert (a.id, b.id) == (1, 2)


def test_get_returns_report_or_none(tmp_path):
    store = ReportStore(tmp_path / "reports.json")
    store.add("lost", **lost_fields())
    assert store.get(1).kind == "lost"
    assert store.get(99) is None


def test_list_filters_by_kind_and_status(tmp_path):
    store = ReportStore(tmp_path / "reports.json")
    store.add("lost", **lost_fields())
    store.add("found", **found_fields())
    store.add("found", **found_fields())
    store.update_status(3, "claimed")
    assert len(store.list()) == 3
    assert len(store.list(kind="found")) == 2
    assert len(store.list(kind="found", status="open")) == 1


def test_data_survives_restart(tmp_path):
    path = tmp_path / "reports.json"
    store = ReportStore(path)
    store.add("lost", **lost_fields())
    store.add("found", **found_fields())
    store.update_status(1, "claimed")

    again = ReportStore(path)
    assert len(again.list()) == 2
    assert again.get(1).status == "claimed"
    assert again.get(1).event_date == date(2026, 10, 1)
    assert again.get(2).check_answer("hello kitty") is True


def test_ids_continue_after_restart(tmp_path):
    path = tmp_path / "reports.json"
    ReportStore(path).add("lost", **lost_fields())
    again = ReportStore(path)
    assert again.add("lost", **lost_fields()).id == 2


def test_missing_file_starts_empty(tmp_path):
    store = ReportStore(tmp_path / "does_not_exist.json")
    assert store.list() == []


def test_unknown_kind_raises_error(tmp_path):
    store = ReportStore(tmp_path / "reports.json")
    with pytest.raises(ValueError):
        store.add("stolen", **lost_fields())