import argparse
import json

from .models import Ticket
from .pipeline import process

# USD per million tokens (input, output). Set these from the current price list before relying on the cost line.
PRICE = {"in": 1.0, "out": 5.0}


def main():
    ap = argparse.ArgumentParser(description="AI ServiceDesk Copilot")
    ap.add_argument("tickets", help="JSON file with tickets")
    ap.add_argument("--dry-run", action="store_true", help="no API calls, rule-based triage")
    ap.add_argument("--minutes-per-ticket", type=float, default=4.0,
                    help="your estimate of manual triage + first reply time per ticket")
    a = ap.parse_args()

    if a.dry_run:
        from .llm import RuleBased
        llm = RuleBased()
    else:
        from .llm import Claude
        llm = Claude()

    tickets = [Ticket(**t) for t in json.load(open(a.tickets, encoding="utf-8"))]
    results = [process(t, llm) for t in tickets]

    print(f"{'ID':<10}{'Category':<20}{'Priority':<10}{'Team':<19}Route")
    for r in results:
        t = r.triage
        print(f"{r.ticket.id:<10}{t.category:<20}{t.priority:<10}{t.team:<19}{'HUMAN' if r.route == 'human' else 'draft'}")
    for r in results:
        if r.draft:
            print(f"\n--- {r.ticket.id}: {r.ticket.subject}\n{r.draft}")

    tin = sum(r.usage["in"] for r in results)
    tout = sum(r.usage["out"] for r in results)
    auto = sum(r.route == "auto" for r in results)
    print("\nSummary")
    print(f"  Tickets: {len(results)}  ·  drafts: {auto}  ·  routed to human: {len(results) - auto}")
    print(f"  Tokens: {tin} in / {tout} out  ·  est. cost: ${(tin * PRICE['in'] + tout * PRICE['out']) / 1e6:.4f}")
    print(f"  Est. manual time saved: {len(results) * a.minutes_per_ticket:.0f} min (assumption: {a.minutes_per_ticket} min/ticket)")


if __name__ == "__main__":
    main()
