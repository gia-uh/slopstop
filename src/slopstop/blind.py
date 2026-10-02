"""Anonymized side-by-side packets for a blind read, and the reader's ranking."""
import random
from pathlib import Path

from slopstop import text
from slopstop.cli import UsageError


def _closed(body: str) -> str:
    body = body.rstrip() + "\n"
    closer = text.open_fence(body)
    return body + closer + "\n" if closer else body


def packet(paths: list[str], seed: int, title: str) -> tuple[str, dict]:
    order = list(paths)
    random.Random(seed).shuffle(order)
    names = {f"V{i}": p for i, p in enumerate(order, 1)}
    parts = [f"# Blind read: {title}\n",
             f"{len(order)} versions of the same text, in random order. Read them as a reader "
             "would, then rank them best to worst with a sentence on each. "
             "Record the ranking with: slopstop blind record <key> \"V2>V1=V3\"\n"]
    for v, p in names.items():
        parts.append(f"---\n\n## {v}\n\n{_closed(Path(p).read_text(encoding='utf-8', errors='replace'))}")
    return "\n".join(parts), {"seed": seed, "versions": names}


def record(key: dict, ranking: str) -> dict:
    tiers, seen = [], set()
    for tier in ranking.replace(" ", "").split(">"):
        names = [n for n in tier.split("=") if n]
        for n in names:
            if n not in key["versions"]:
                raise UsageError(f"unknown version {n}; the packet has {', '.join(key['versions'])}")
            if n in seen:
                raise UsageError(f"{n} is ranked twice")
            seen.add(n)
        tiers.append([key["versions"][n] for n in names])
    return {**key, "ranking": tiers}
