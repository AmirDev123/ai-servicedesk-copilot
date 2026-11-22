import json
import re

from .models import CATEGORIES, PRIORITIES, TEAMS, Ticket, Triage

TRIAGE_MODEL = "claude-haiku-5-5"   # fast and cheap: most of the volume
DRAFT_MODEL = "claude-sonnet-5-5"   # stronger: only for safe tickets

TRIAGE_PROMPT = f"""You are the triage engine of a Norwegian IT service desk.
Read the ticket and answer ONLY with JSON:
{{"category": one of {CATEGORIES},
 "priority": one of {PRIORITIES},
 "team": one of {TEAMS},
 "escalate": true/false,
 "reason": "one short sentence",
 "confidence": number 0-1}}
Rules: many users affected or work stopped = Critical. Possible compromised account or phishing =
Security, Critical, escalate. Access to data = Access management and escalate (needs manager approval).
Deadline within an hour = at least High."""

DRAFT_PROMPT = """You are a friendly, precise IT service desk agent. Write a reply draft in Norwegian (bokmål).
Max 120 words. Confirm the problem, give 2-4 numbered steps the user can try now, say what the
service desk does next. Never ask for passwords. Do not promise what you do not know.
Sign "Hilsen IT ServiceDesk". Reply with the text only."""


def _parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


class Claude:
    def __init__(self):
        import anthropic
        self.client = anthropic.Anthropic()

    def triage(self, t: Ticket) -> tuple[Triage, dict]:
        msg = self.client.messages.create(
            model=TRIAGE_MODEL, max_tokens=300, system=TRIAGE_PROMPT,
            messages=[{"role": "user", "content": f"Subject: {t.subject}\n\n{t.body}"}],
        )
        tri = Triage.from_dict(_parse_json(msg.content[0].text))
        return tri, {"in": msg.usage.input_tokens, "out": msg.usage.output_tokens}

    def draft(self, t: Ticket, tri: Triage) -> tuple[str, dict]:
        msg = self.client.messages.create(
            model=DRAFT_MODEL, max_tokens=500, system=DRAFT_PROMPT,
            messages=[{"role": "user", "content":
                       f"Ticket: {t.subject}\n{t.body}\n\nTriage: {tri.category}, {tri.priority}, team {tri.team}"}],
        )
        return msg.content[0].text.strip(), {"in": msg.usage.input_tokens, "out": msg.usage.output_tokens}


class RuleBased:
    """Offline fallback for --dry-run: keyword triage, no API calls, no drafts."""
    KEYWORDS = [
        ("Security", "Critical", "Security", ["phishing", "lenke", "mistenkelig", "passordet før"]),
        ("Network", "Critical", "Network", ["nettverk", "mangler nett", "personer berørt"]),
        ("Access", "Medium", "Access management", ["tilgang"]),
        ("Account & password", "High", "1st line", ["passord", "logget inn", "logge inn"]),
        ("Printer", "Low", "1st line", ["skriver"]),
        ("Onboarding", "Medium", "1st line", ["ny ansatt", "starter mandag", "ny konsulent"]),
        ("Meeting room AV", "High", "AV team", ["projektor", "møterom", "hdmi"]),
        ("Software", "Medium", "2nd line", ["excel", "fryser", "programvare"]),
    ]

    def triage(self, t: Ticket):
        text = (t.subject + " " + t.body).lower()
        for cat, pri, team, words in self.KEYWORDS:
            if any(w in text for w in words):
                return Triage(cat, pri, team, cat == "Security", "keyword match (dry run)", 0.7), {"in": 0, "out": 0}
        return Triage("Other", "Medium", "1st line", False, "no keyword match (dry run)", 0.3), {"in": 0, "out": 0}

    def draft(self, t, tri):
        return "(dry run: no draft generated)", {"in": 0, "out": 0}
