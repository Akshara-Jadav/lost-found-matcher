from datetime import date
from typing import Literal

from pydantic import (BaseModel, ConfigDict, Field,
                      field_validator, model_validator)

from app.scorers import NEARBY

# Suggested lists (the form no longer forces these)
Category = Literal["id_card", "phone", "bottle", "earphones", "wallet",
                   "keys", "bag", "books", "calculator", "other"]

KNOWN_LOCATIONS = set(NEARBY) | {p for places in NEARBY.values() for p in places}


class ReportCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    kind: Literal["lost", "found"]
    category: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=5, max_length=300)
    location: str = Field(min_length=2, max_length=60)
    event_date: date
    contact: str = Field(min_length=5, max_length=50)
    color: str = ""
    brand: str = ""
    verification_question: str = ""
    verification_answer: str = ""

    @field_validator("category", "location")
    @classmethod
    def clean_and_check_text(cls, v):
        v = " ".join(v.lower().split())        # lowercase, tidy the spaces
        if not any(ch.isalpha() for ch in v):
            raise ValueError("Please use words, for example 'wallet' or 'library'")
        return v

    @field_validator("event_date")
    @classmethod
    def date_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v

    @model_validator(mode="after")
    def found_reports_need_verification(self):
        if self.kind == "found" and not (self.verification_question
                                         and self.verification_answer):
            raise ValueError("Found reports need a verification question and answer")
        return self


class ClaimRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    lost_id: int
    found_id: int
    answer: str = Field(min_length=1)