"""NHANES PAQ-aligned activity feature construction for web input."""

import math
from typing import NamedTuple


# key, participation, days/week, minutes/day, MET factor
DOMAINS = (
    ("vigorous_work", "PAQ605", "PAQ610", "PAD615", 8),
    ("moderate_work", "PAQ620", "PAQ625", "PAD630", 4),
    ("transport", "PAQ635", "PAQ640", "PAD645", 4),
    ("vigorous_recreation", "PAQ650", "PAQ655", "PAD660", 8),
    ("moderate_recreation", "PAQ665", "PAQ670", "PAD675", 4),
)


class ActivityInputError(ValueError):
    """Invalid, incomplete, or contradictory activity answers."""

    def __init__(self, code, domain=None):
        self.code = code
        self.domain = domain
        super().__init__(f"{code}: {domain}" if domain else code)


class ActivityFeatures(NamedTuple):
    met_min_week: float
    log_met: float


def build_activity_features(answers):
    """Build exactly the two training features from five nonoverlapping PAQ domains.

    Each domain has status yes/no/unknown/refused and, for yes, days (1..7) and
    minutes per day (0 < minutes < 1440). Missing/unknown answers fail closed.
    Training's median imputer is retained in the model but is not invoked for
    an incomplete web questionnaire.
    """
    if not isinstance(answers, dict):
        raise ActivityInputError("missing")

    expected = {domain[0] for domain in DOMAINS}
    if set(answers) != expected:
        raise ActivityInputError("missing")

    total_met = 0.0
    total_minutes = 0.0
    for key, _, _, _, met in DOMAINS:
        answer = answers[key]
        if not isinstance(answer, dict):
            raise ActivityInputError("missing", key)
        status = answer.get("status")
        days = answer.get("days")
        minutes = answer.get("minutes")
        if status in (None, "unknown", "refused"):
            raise ActivityInputError("missing", key)
        if status == "no":
            if days not in (None, 0) or minutes not in (None, 0):
                raise ActivityInputError("contradictory", key)
            continue
        if status != "yes":
            raise ActivityInputError("invalid", key)
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 7:
            raise ActivityInputError("days", key)
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)):
            raise ActivityInputError("minutes", key)
        if not math.isfinite(minutes) or not 0 < minutes < 1440:
            raise ActivityInputError("minutes", key)
        total_minutes += days * minutes
        total_met += days * minutes * met

    # Weekly minutes across disjoint domains cannot exceed seven full days.
    if total_minutes > 7 * 1440:
        raise ActivityInputError("weekly_total")
    return ActivityFeatures(float(total_met), math.log1p(total_met))
