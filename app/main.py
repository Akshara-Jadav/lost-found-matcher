from collections import Counter
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Response

from app.logger import get_logger
from app.matcher import Matcher
from app.schemas import ClaimRequest, ReportCreate
from app.storage import ReportStore
from app.reports import reports_to_csv

MAX_WRONG_ATTEMPTS = 3
CLAIM_MIN_SCORE = 80

app = FastAPI(title="Campus Lost & Found Matcher")
_store = ReportStore("data/reports.json")
matcher = Matcher()
log = get_logger()
failed_attempts = {}          # {found_id: number of wrong answers so far}


def get_store():
    return _store


def public_view(report):
    """Report details that are safe to show to anyone."""
    data = report.to_dict()
    data.pop("contact", None)               # revealed only after a valid claim
    data.pop("verification_answer", None)   # never shown
    return data


@app.post("/reports", status_code=201)
def create_report(payload: ReportCreate, db: ReportStore = Depends(get_store)):
    fields = payload.model_dump()
    kind = fields.pop("kind")
    if kind == "lost":                      # lost reports don't use these
        fields.pop("verification_question")
        fields.pop("verification_answer")
    report = db.add(kind, **fields)
    log.info("New %s report #%s (%s at %s)",
             report.kind, report.id, report.category, report.location)
    return public_view(report)


@app.get("/reports")
def list_reports(kind: Literal["lost", "found"] | None = None,
                 status: str | None = None,
                 db: ReportStore = Depends(get_store)):
    return [public_view(r) for r in db.list(kind=kind, status=status)]


@app.get("/reports/{report_id}")
def get_report(report_id: int, db: ReportStore = Depends(get_store)):
    report = db.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return public_view(report)


@app.get("/reports/{report_id}/matches")
def get_matches(report_id: int, db: ReportStore = Depends(get_store)):
    report = db.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.kind == "lost":
        matches = matcher.find_matches([report], db.list("found", "open"))
    else:
        matches = matcher.find_matches(db.list("lost", "open"), [report])

    log.info("Matches requested for report #%s: %s found",
             report_id, len(matches))
    return [{**m.to_dict(), "why": matcher.explain(m.lost, m.found)}
            for m in matches]


@app.post("/claim")
def claim_item(request: ClaimRequest, db: ReportStore = Depends(get_store)):
    lost = db.get(request.lost_id)
    found = db.get(request.found_id)

    if lost is None or found is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if lost.kind != "lost" or found.kind != "found":
        raise HTTPException(status_code=400,
                            detail="A claim needs one lost and one found report")
    if lost.status != "open" or found.status != "open":
        raise HTTPException(status_code=409,
                            detail="One of these reports is already closed")

    if failed_attempts.get(found.id, 0) >= MAX_WRONG_ATTEMPTS:
        log.warning("Claim blocked for found #%s: too many wrong answers", found.id)
        raise HTTPException(status_code=429,
                            detail="Too many wrong answers for this item")
    score = matcher.score_pair(lost, found)
    if score < CLAIM_MIN_SCORE:
        log.warning("Claim refused: lost #%s and found #%s match only %s%%",
                    lost.id, found.id, score)
        raise HTTPException(
            status_code=403,
            detail=f"These reports are not similar enough to claim "
                   f"(a claim needs at least a {CLAIM_MIN_SCORE}% match).")

    if not found.check_answer(request.answer):
        failed_attempts[found.id] = failed_attempts.get(found.id, 0) + 1
        left = MAX_WRONG_ATTEMPTS - failed_attempts[found.id]
        log.warning("Wrong claim answer for found #%s (lost #%s), %s attempts left",
                    found.id, lost.id, left)
        raise HTTPException(status_code=403,
                            detail=f"Wrong answer. {left} attempts left.")

    db.update_status(lost.id, "claimed")
    db.update_status(found.id, "claimed")
    failed_attempts.pop(found.id, None)
    log.info("Claim verified: lost #%s <-> found #%s", lost.id, found.id)
    return {"message": "Claim verified", "finder_contact": found.contact}


@app.get("/stats")
def stats(db: ReportStore = Depends(get_store)):
    reports = db.list()
    by_status = Counter(r.status for r in reports)
    return {
        "total": len(reports),
        "lost": len(db.list(kind="lost")),
        "found": len(db.list(kind="found")),
        "open": by_status["open"],
        "claimed": by_status["claimed"],
        "items_recovered": len(db.list(kind="found", status="claimed")),
        "claim_min_score": CLAIM_MIN_SCORE,
    }

@app.post("/admin/expire")
def expire_old_reports(days: int = Query(30, ge=0),
                       db: ReportStore = Depends(get_store)):
    count = db.expire_old(days=days)
    log.info("Expired %s reports older than %s days", count, days)
    return {"expired": count}


@app.get("/export/csv")
def export_csv(db: ReportStore = Depends(get_store)):
    text = reports_to_csv(db.list())
    return Response(content=text, media_type="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=reports.csv"})