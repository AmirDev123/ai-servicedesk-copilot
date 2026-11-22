from copilot.models import Triage
from copilot.routing import route


def t(**kw):
    base = dict(category="Printer", priority="Low", team="1st line", escalate=False, reason="", confidence=0.9)
    base.update(kw)
    return Triage(**base)


def test_safe_ticket_gets_draft():
    assert route(t()) == "auto"


def test_critical_goes_to_human():
    assert route(t(priority="Critical")) == "human"


def test_security_always_human_even_if_model_says_low():
    assert route(t(category="Security", priority="Low")) == "human"


def test_access_always_human():
    assert route(t(category="Access")) == "human"


def test_low_confidence_goes_to_human():
    assert route(t(confidence=0.3)) == "human"


def test_invalid_model_output_is_sanitised():
    tri = Triage.from_dict({"category": "Banana", "priority": "URGENT!!", "confidence": "x"})
    assert (tri.category, tri.priority, tri.confidence) == ("Other", "Medium", 0.0)
