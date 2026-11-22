from .models import Result, Ticket
from .routing import route


def process(ticket: Ticket, llm) -> Result:
    tri, u1 = llm.triage(ticket)
    r = Result(ticket, tri, route(tri))
    r.usage = dict(u1)
    if r.route == "auto":
        r.draft, u2 = llm.draft(ticket, tri)
        r.usage["in"] += u2["in"]
        r.usage["out"] += u2["out"]
    return r
