from app.scorers import (CategoryScorer, TextScorer, LocationScorer,
                         DateScorer, ColorBrandScorer)


class Match:
    """One suggested pairing of a lost report and a found report."""

    def __init__(self, lost, found, score):
        self.lost = lost
        self.found = found
        self.score = score

    def __lt__(self, other):              # lets sorted() rank matches by score
        return self.score < other.score

    def to_dict(self):
        return {"lost_id": self.lost.id,
                "found_id": self.found.id,
                "score": self.score}

    def __str__(self):
        return f"Lost #{self.lost.id} <-> Found #{self.found.id}: {self.score}"


class Matcher:
    """Combines all scorers into a single 0-100 match score."""

    def __init__(self, scorers=None, threshold=60):
        self.scorers = scorers or [CategoryScorer(), TextScorer(),
                                   LocationScorer(), DateScorer(),
                                   ColorBrandScorer()]
        self.threshold = threshold

    def score_pair(self, lost, found):
        total_weight = sum(s.weight for s in self.scorers)
        earned = sum(s.weight * s.score(lost, found) for s in self.scorers)
        return round(earned / total_weight * 100, 1)

    def explain(self, lost, found):
        """Points each scorer contributed (shows WHY a pair matched)."""
        total_weight = sum(s.weight for s in self.scorers)
        return {type(s).__name__: round(s.weight * s.score(lost, found)
                                        / total_weight * 100, 1)
                for s in self.scorers}

    def find_matches(self, lost_reports, found_reports):
        matches = []
        for lost in lost_reports:
            if lost.status != "open":
                continue
            for found in found_reports:
                if found.status != "open":
                    continue
                score = self.score_pair(lost, found)
                if score >= self.threshold:
                    matches.append(Match(lost, found, score))
        return sorted(matches, reverse=True)      # best match first