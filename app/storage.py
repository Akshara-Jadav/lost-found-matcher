import json
from datetime import date, timedelta
from pathlib import Path

from app.models import LostReport, FoundReport


def report_from_dict(data):
    """Turn a saved dictionary back into a LostReport or FoundReport."""
    data = dict(data)                        # make a copy
    kind = data.pop("kind")                  # take these out of the copy
    report_id = data.pop("id")
    status = data.pop("status")
    data["event_date"] = date.fromisoformat(data["event_date"])   # text -> date

    if kind == "lost":
        report = LostReport(report_id, **data)
    else:
        report = FoundReport(report_id, **data)

    report.status = status
    return report


class ReportStore:
    def __init__(self, path="data/reports.json"):
        self.path = Path(path)
        self.reports = {}        # {id: report}
        self.next_id = 1
        self._load()

    def add(self, kind, **fields):
        classes = {"lost": LostReport, "found": FoundReport}
        if kind not in classes:
            raise ValueError(f"Unknown kind: {kind}")
        report = classes[kind](self.next_id, **fields)
        self.reports[report.id] = report
        self.next_id += 1
        self._save()
        return report

    def get(self, report_id):
        return self.reports.get(report_id)

    def list(self, kind=None, status=None):
        return [r for r in self.reports.values()
                if (kind is None or r.kind == kind)
                and (status is None or r.status == status)]

    def update_status(self, report_id, status):
        report = self.get(report_id)
        if report is None:
            raise KeyError(f"No report with id {report_id}")
        report.status = status
        self._save()

    def expire_old(self, days=30, today=None):
        """Mark open reports older than `days` as expired. Returns how many."""
        today = today or date.today()
        cutoff = today - timedelta(days=days)
        count = 0
        for report in self.reports.values():
            if report.status == "open" and report.event_date < cutoff:
                report.status = "expired"
                count += 1
        if count:
            self._save()
        return count

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in self.reports.values()]
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load(self):
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as f:
            saved = json.load(f)
        for item in saved:
            report = report_from_dict(item)
            self.reports[report.id] = report
        if self.reports:
            self.next_id = max(self.reports) + 1