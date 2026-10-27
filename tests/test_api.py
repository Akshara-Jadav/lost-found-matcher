import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app, get_store
from app.schemas import KNOWN_LOCATIONS
from app.storage import ReportStore

PLACE = sorted(KNOWN_LOCATIONS)[0]      # any valid place from your NEARBY list


@pytest.fixture
def client(tmp_path):
    store = ReportStore(tmp_path / "reports.json")      # temporary store
    app.dependency_overrides[get_store] = lambda: store
    main.failed_attempts.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def lost_payload(**changes):
    data = dict(kind="lost", category="earphones",
                description="black boat earphones", location=PLACE,
                event_date="2026-10-01", contact="9999999999",
                color="black", brand="boat")
    data.update(changes)
    return data


def found_payload(**changes):
    data = dict(kind="found", category="earphones",
                description="boat earphones black", location=PLACE,
                event_date="2026-10-02", contact="8888888888",
                color="black", brand="boat",
                verification_question="Sticker?",
                verification_answer="Hello Kitty")
    data.update(changes)
    return data


def add_pair(client):
    client.post("/reports", json=lost_payload())     # becomes id 1
    client.post("/reports", json=found_payload())    # becomes id 2


def claim(client, answer, lost_id=1, found_id=2):
    return client.post("/claim", json={"lost_id": lost_id,
                                       "found_id": found_id,
                                       "answer": answer})


def test_create_report_hides_contact(client):
    response = client.post("/reports", json=lost_payload())
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert "contact" not in response.json()


def test_invalid_report_returns_422(client):
    response = client.post("/reports", json=lost_payload(description="hi"))
    assert response.status_code == 422


def test_unknown_report_returns_404(client):
    assert client.get("/reports/99").status_code == 404


def test_list_can_filter_by_kind(client):
    add_pair(client)
    response = client.get("/reports", params={"kind": "found"})
    assert len(response.json()) == 1


def test_matches_are_returned_for_a_lost_report(client):
    add_pair(client)
    matches = client.get("/reports/1/matches").json()
    assert len(matches) == 1
    assert matches[0]["found_id"] == 2
    assert matches[0]["score"] >= 60


def test_wrong_claim_answer_is_rejected(client):
    add_pair(client)
    response = claim(client, "star")
    assert response.status_code == 403
    assert "8888888888" not in response.text


def test_correct_claim_reveals_contact_and_closes_reports(client):
    add_pair(client)
    response = claim(client, "hello kitty")
    assert response.status_code == 200
    assert response.json()["finder_contact"] == "8888888888"
    assert client.get("/reports/1").json()["status"] == "claimed"


def test_three_wrong_answers_block_further_attempts(client):
    add_pair(client)
    for _ in range(3):
        assert claim(client, "wrong").status_code == 403
    assert claim(client, "hello kitty").status_code == 429


def test_claiming_a_closed_report_returns_409(client):
    add_pair(client)
    claim(client, "hello kitty")
    assert claim(client, "hello kitty").status_code == 409


def test_claim_with_swapped_kinds_returns_400(client):
    add_pair(client)
    assert claim(client, "hello kitty", lost_id=2, found_id=1).status_code == 400


def test_claim_with_unknown_ids_returns_404(client):
    assert claim(client, "anything", lost_id=7, found_id=8).status_code == 404


def test_stats_counts_reports(client):
    add_pair(client)
    stats = client.get("/stats").json()
    assert stats["total"] == 2
    assert stats["lost"] == 1
    assert stats["found"] == 1
    assert stats["items_recovered"] == 0

def test_export_csv_endpoint(client):
    add_pair(client)
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "9999999999" not in response.text
    assert len(response.text.strip().splitlines()) == 3


def test_expire_endpoint(client):
    add_pair(client)
    response = client.post("/admin/expire", params={"days": 0})
    assert response.json()["expired"] == 2

def test_claim_below_80_percent_is_rejected(client):
    client.post("/reports", json=lost_payload())
    client.post("/reports", json=found_payload(category="wallet",
                                               description="brown leather wallet",
                                               color="brown", brand=""))
    response = claim(client, "hello kitty")
    assert response.status_code == 403
    assert "8888888888" not in response.text