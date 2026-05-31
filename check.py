#!/usr/bin/env python3
"""Check the Royal Eagle royal-tea page for changes; emit a human-readable diff
to stdout when anything changed, otherwise exit silently.

The HTML is server-rendered enough that a plain GET is sufficient — no headless
browser needed. We track two things per visible event:
  * the slug (e.g. royal-tea-time-2026-06-09-11-00)
  * whether a "Sold Out" badge is attached to it

State lives in ./state.json so the workflow can commit it back between runs.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

URL = "https://www.theroyaleagle.net/royal-tea"
STATE_PATH = Path(__file__).parent / "state.json"
UA = "Mozilla/5.0 (royal-tea-watch; +https://github.com/fgregg/royal-tea-watch)"
SLUG_RE = re.compile(r"royal-tea-time-\d{4}-(\d{2})-(\d{2})-\d{2}-\d{2}")
# Wix Events renders the Sold Out ribbon immediately before the card's date
# label, e.g.  <div>Sold Out</div></div></div><div ... data-hook="ev-date">
# <span ...>Tue, Jun 09</span>.  Capture the date label that follows.
SOLDOUT_RE = re.compile(
    r"Sold Out</div>.{0,200}?data-hook=\"ev-date\"[^>]*>\s*"
    r"<span[^>]*>[^,]+,\s*([A-Z][a-z]{2})\s+(\d{1,2})</span>",
    re.DOTALL,
)
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def extract(html: str) -> dict[str, dict]:
    """Return {slug: {"sold_out": bool}}.

    Slug appears many times per page (image link, button link, schema, etc.) so
    we collect the unique set, then attribute "Sold Out" by parsing the date
    label that Wix renders adjacent to the ribbon and matching month/day back
    to the slug.
    """
    by_md: dict[tuple[int, int], str] = {}
    for m in SLUG_RE.finditer(html):
        by_md[(int(m.group(1)), int(m.group(2)))] = m.group(0)
    events: dict[str, dict] = {slug: {"sold_out": False} for slug in by_md.values()}
    for m in SOLDOUT_RE.finditer(html):
        mon = MONTHS.get(m.group(1))
        day = int(m.group(2))
        slug = by_md.get((mon, day)) if mon else None
        if slug:
            events[slug]["sold_out"] = True
    return events


def diff(old: dict, new: dict) -> list[str]:
    msgs: list[str] = []
    old_set, new_set = set(old), set(new)
    for s in sorted(new_set - old_set):
        status = "SOLD OUT" if new[s]["sold_out"] else "AVAILABLE"
        msgs.append(f"NEW DATE ({status}): {s}")
    for s in sorted(old_set - new_set):
        msgs.append(f"REMOVED: {s}")
    for s in sorted(new_set & old_set):
        if old[s]["sold_out"] and not new[s]["sold_out"]:
            msgs.append(f"OPENED UP: {s}")
        elif not old[s]["sold_out"] and new[s]["sold_out"]:
            msgs.append(f"NOW SOLD OUT: {s}")
    return msgs


def main() -> int:
    html = fetch()
    new = extract(html)
    old = {}
    if STATE_PATH.exists():
        old = json.loads(STATE_PATH.read_text()).get("events", {})
    msgs = diff(old, new)
    STATE_PATH.write_text(json.dumps({"events": new}, indent=2, sort_keys=True) + "\n")
    if msgs:
        print("\n".join(msgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
