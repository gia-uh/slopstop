"""Verify the quotes an agent returns from a judge or critic task against the texts."""
import re

from slopstop import text as textmod
from slopstop.cli import UsageError

TARGET = {"dropped": "source", "invented": "output", "items": "text"}


def norm(s: str) -> str:
    return re.sub(r"\W+", " ", textmod.normalize(s).lower()).strip()


def check(data: dict, source: str | None, output: str | None, text: str | None) -> dict:
    if not isinstance(data, dict):
        raise UsageError("the quotes file must be a JSON object")
    texts = {"source": source, "output": output, "text": text}
    verified, bad = {}, 0
    for key, target in TARGET.items():
        if key not in data:
            continue
        hay = texts[target]
        if hay is None:
            raise UsageError(f"'{key}' quotes are checked against --{target}, which was not given")
        hay = norm(hay)
        kept = []
        items = data[key] or []
        if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
            raise UsageError(f"'{key}' must be a list of objects with a 'quote'")
        for item in items:
            q = norm(str(item.get("quote", "")))
            if q and q in hay:
                kept.append({**item, "verified": True})
            else:
                bad += 1
        verified[key] = kept
    return {"verified": verified, "unverified": bad}
