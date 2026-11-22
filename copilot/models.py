from dataclasses import dataclass, field

CATEGORIES = ["Account & password", "Network", "Printer", "Access", "Security",
              "Onboarding", "Software", "Meeting room AV", "Other"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]
TEAMS = ["1st line", "2nd line", "Network", "Security", "Access management", "AV team"]


@dataclass
class Ticket:
    id: str
    subject: str
    body: str


@dataclass
class Triage:
    category: str
    priority: str
    team: str
    escalate: bool
    reason: str = ""
    confidence: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "Triage":
        cat = d.get("category") if d.get("category") in CATEGORIES else "Other"
        pri = d.get("priority") if d.get("priority") in PRIORITIES else "Medium"
        team = d.get("team") if d.get("team") in TEAMS else "1st line"
        try:
            conf = max(0.0, min(1.0, float(d.get("confidence", 0))))
        except (TypeError, ValueError):
            conf = 0.0
        return cls(cat, pri, team, bool(d.get("escalate", False)), str(d.get("reason", "")), conf)


@dataclass
class Result:
    ticket: Ticket
    triage: Triage
    route: str                      # "human" or "auto"
    draft: str | None = None
    usage: dict = field(default_factory=lambda: {"in": 0, "out": 0})
