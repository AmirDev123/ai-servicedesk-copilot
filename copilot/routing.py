"""Deterministic safety rules applied AFTER the model's triage.

The model suggests; these rules decide. Anything critical, security-related,
about access to data, or low-confidence goes to a human without an AI reply.
"""
from .models import Triage

ALWAYS_HUMAN_CATEGORIES = {"Security", "Access"}
MIN_CONFIDENCE = 0.6


def route(t: Triage) -> str:
    if t.priority == "Critical":
        return "human"
    if t.escalate:
        return "human"
    if t.category in ALWAYS_HUMAN_CATEGORIES:
        return "human"
    if t.confidence < MIN_CONFIDENCE:
        return "human"
    return "auto"
