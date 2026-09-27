#!/usr/bin/env python3
"""ScaleCraft Scorer — score small-business leads for website/automation services.

Reads a leads CSV (name, city, website, phone, email, notes, ...) and scores
each 0-100 on how likely they need a new website or automation work. Fully
offline, stdlib-only.

Usage:
    python scalecraft-scorer.py --in leads.csv
    python scalecraft-scorer.py --in leads.csv --min-score 60 --out hot.json
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import re
import sys

# Signals that a business already invested in a good web presence.
NO_WEBSITE_PENALTY = 25          # no website = prime client
SOCIAL_ONLY_PENALTY = 15         # facebook/instagram link instead of real site
STALE_TLD_BONUS = 10             # .info/.biz/.net often dated sites
MODERN_TLD_BONUS = 0             # .io/.dev/.app suggests someone technical
GMAIL_YAHOO_PENALTY = 8          # free email = likely no web infrastructure
NOTE_KEYWORD_BONUS = 15          # notes mention pain points
NOTE_KEYWORDS = (
    "outdated", "no website", "paper", "manual", "spreadsheet",
    "old site", "needs website", "no booking", "by hand", "call to book",
)

MODERN_TLDS = (".io", ".dev", ".app", ".ai")
STALE_TLDS = (".info", ".biz", ".net", ".org")
SOCIAL_HOSTS = ("facebook.com", "instagram.com", "linktr.ee", "wa.me", "whatsapp.com")
MODERN_TLD_NOTE = "modern domain (technical owner, harder sell)"
STALE_TLD_BONUS = 10             # .info/.biz/.net often dated sites
CUSTOM_DOMAIN_PENALTY = 10       # already pays for web infrastructure = harder sell
GMAIL_YAHOO_PENALTY = 8          # free email = likely no web infrastructure


def normalize_website(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    url = re.sub(r"^https?://", "", url)
    return url.rstrip("/")


def score_lead(lead: dict) -> dict:
    """Score one lead dict. Returns {score, reasons}."""
    website = normalize_website(lead.get("website", ""))
    notes = (lead.get("notes") or "").lower()
    email = (lead.get("email") or "").strip().lower()
    reasons, score = [], 50

    if not website:
        score += NO_WEBSITE_PENALTY
        reasons.append("no website listed")
    else:
        host = website.split("/")[0]
        if any(host.endswith(s) or host == s for s in SOCIAL_HOSTS):
            score += SOCIAL_ONLY_PENALTY
            reasons.append("social page instead of real site")
        elif website.endswith(MODERN_TLDS):
            reasons.append(MODERN_TLD_NOTE)
        elif website.endswith(STALE_TLDS):
            score += STALE_TLD_BONUS
            reasons.append("dated domain choice")

    if email:
        domain = email.split("@")[-1]
        if domain in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
            score -= GMAIL_YAHOO_PENALTY
            reasons.append("free email provider")
        else:
            score -= CUSTOM_DOMAIN_PENALTY
            reasons.append("already pays for domain/email infrastructure")

    hits = [kw for kw in NOTE_KEYWORDS if kw in notes]
    if hits:
        score += NOTE_KEYWORD_BONUS
        reasons.append(f"pain keywords in notes: {', '.join(hits[:3])}")

    score = max(0, min(100, score))
    return {"name": lead.get("name", "?"), "score": score, "reasons": reasons}


def score_leads(leads: list[dict]) -> list[dict]:
    scored = [score_lead(l) for l in leads]
    scored.sort(key=lambda s: s["score"], reverse=True)
    for rank, s in enumerate(scored, 1):
        s["rank"] = rank
    return scored


def load_leads(path) -> list[dict]:
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return list(csv.DictReader(io.StringIO(text)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="scalecraft-scorer",
                                     description="Score leads for website/automation services.")
    parser.add_argument("--in", dest="infile", required=True, help="leads CSV or JSON")
    parser.add_argument("--min-score", type=int, default=0, help="only show leads at/above this score")
    parser.add_argument("--out", help="write JSON results to file")
    args = parser.parse_args(argv)

    try:
        leads = load_leads(args.infile)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not leads:
        print("error: no leads found in input", file=sys.stderr)
        return 1

    scored = [s for s in score_leads(leads) if s["score"] >= args.min_score]
    output = json.dumps(scored, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(output, encoding="utf-8")
        print(f"wrote {len(scored)} scored leads to {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
