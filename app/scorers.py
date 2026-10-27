from difflib import SequenceMatcher
from abc import ABC, abstractmethod
from app.text_utils import text_similarity

# Edit this to match YOUR campus: which places are close to each other.
NEARBY = {
    "library": {"canteen", "admin block"},
    "canteen": {"library", "ground"},
    "ground": {"canteen", "hostel"},
    "hostel": {"ground"},
    "admin block": {"library"},
}

def closeness(a, b):
    """How similar two short words are, from 0.0 to 1.0 (typo tolerant)."""
    a = a.replace("_", " ").strip().lower()
    b = b.replace("_", " ").strip().lower()
    return SequenceMatcher(None, a, b).ratio()


class Scorer(ABC):
    """Base class: every scorer has a weight and a score() method."""

    weight = 0

    @abstractmethod
    def score(self, lost, found):
        """Return a number between 0.0 and 1.0."""


class CategoryScorer(Scorer):
    weight = 30

    def score(self, lost, found):
        ratio = closeness(lost.category, found.category)
        if ratio >= 0.85:          # same word, maybe a typo or a plural
            return 1.0
        if ratio >= 0.7:           # similar words, e.g. headphones / earphones
            return 0.5
        return 0.0

class TextScorer(Scorer):
    weight = 30

    def score(self, lost, found):
        return text_similarity(lost.description, found.description)


class LocationScorer(Scorer):
    weight = 20

    def score(self, lost, found):
        if lost.location == found.location:
            return 1.0
        near_lost = NEARBY.get(lost.location, set())
        near_found = NEARBY.get(found.location, set())
        if found.location in near_lost or lost.location in near_found:
            return 0.5
        if closeness(lost.location, found.location) >= 0.85:
            return 1.0             # same place with a spelling mistake
        return 0.0


class DateScorer(Scorer):
    weight = 15

    def score(self, lost, found):
        days = (found.event_date - lost.event_date).days
        if days < 0:            # found before it was lost: impossible
            return 0.0
        if days <= 1:
            return 1.0
        if days <= 7:
            return 0.6
        if days <= 30:
            return 0.3
        return 0.0


class ColorBrandScorer(Scorer):
    weight = 5

    def score(self, lost, found):
        points = 0.0
        if lost.color and lost.color == found.color:
            points += 0.5
        if lost.brand and lost.brand == found.brand:
            points += 0.5
        return points