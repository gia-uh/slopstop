"""Swap fenced code blocks for placeholders so code never reaches a rewriting model."""
import re

from slopstop.cli import UsageError

BLOCK = re.compile(r"^(```|~~~)[^\n]*\n.*?^\1[ \t]*$", re.S | re.M)


def mask(raw: str) -> tuple[str, dict[str, str]]:
    blocks: dict[str, str] = {}

    def swap(m: re.Match) -> str:
        key = f"[CODE-{len(blocks) + 1}]"
        blocks[key] = m.group(0)
        return key

    return BLOCK.sub(swap, raw), blocks


def unmask(s: str, blocks: dict[str, str]) -> str:
    for key, block in blocks.items():
        n = s.count(key)
        if n != 1:
            raise UsageError(f"placeholder {key} appears {n} times, expected once")
        s = s.replace(key, block)
    return s
