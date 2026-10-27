from datetime import date
from app.reports import reports_to_csv
from app.storage import ReportStore


def lost_fields(**changes):
    data = dict(category="earphones", description="black boat earphones",
                location="library", event_date=date(2026, 10, 1),
                contact="9999999999", color="black", brand="boat")
    data.update(changes)
    return data


def test_expire_old_marks_only_old_open_reports(tmp_path):
    store = ReportStore(tmp_path / "r.json")
    store.add("lost", **lost_fields(event_date=date(2026, 8, 1)))
    store.add("lost", **lost_fields(event_date=date(2026, 10, 5)))
    count = store.expire_old(days=30, today=date(2026, 10, 10))
    assert count == 1
    assert store.get(1).status == "expired"
    assert store.get(2).status == "open"


def test_expire_leaves_claimed_reports_alone(tmp_path):
    store = ReportStore(tmp_path / "r.json")
    store.add("lost", **lost_fields(event_date=date(2026, 8, 1)))
    store.update_status(1, "claimed")
    assert store.expire_old(days=30, today=date(2026, 10, 10)) == 0
    assert store.get(1).status == "claimed"


def test_csv_has_header_and_rows_but_no_contact(tmp_path):
    store = ReportStore(tmp_path / "r.json")
    store.add("lost", **lost_fields())
    text = reports_to_csv(store.list())
    lines = text.strip().splitlines()
    assert lines[0].startswith("id,kind")
    assert len(lines) == 2
    assert "9999999999" not in text