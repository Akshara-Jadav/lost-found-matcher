from datetime import date


class Report:
    """Base class: everything lost and found reports have in common."""

    kind = "report"

    def __init__(self, report_id, category, description, location,
                 event_date, contact, color="", brand=""):
        self.id = report_id
        self.category = category.lower().strip()
        self.description = description.strip()
        self.location = location.lower().strip()
        self.event_date = event_date          # a datetime.date object
        self.contact = contact
        self.color = color.lower().strip()
        self.brand = brand.lower().strip()
        self.status = "open"                  # open / claimed / closed

    def to_dict(self):
        """Turn the report into a plain dictionary (needed for saving to JSON)."""
        return {
            "id": self.id,
            "kind": self.kind,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "event_date": self.event_date.isoformat(),
            "contact": self.contact,
            "color": self.color,
            "brand": self.brand,
            "status": self.status,
        }

    def __str__(self):
        return (f"[{self.kind.upper()} #{self.id}] {self.category}: "
                f"{self.description} ({self.location}, {self.event_date})")


class LostReport(Report):
    kind = "lost"


class FoundReport(Report):
    kind = "found"

    def __init__(self, *args, verification_question="",
                 verification_answer="", **kwargs):
        super().__init__(*args, **kwargs)
        self.verification_question = verification_question
        self.verification_answer = verification_answer.lower().strip()

    def check_answer(self, answer):
        """True if the claimer knows the secret detail only the owner would know."""
        return answer.lower().strip() == self.verification_answer

    def to_dict(self):
        data = super().to_dict()              # reuse the parent's dictionary
        data["verification_question"] = self.verification_question
        data["verification_answer"] = self.verification_answer
        return data