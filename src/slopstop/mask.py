"""Swap fenced code blocks for placeholders so code never reaches a rewriting model."""
from slopstop import text
from slopstop.cli import UsageError


def mask(raw: str) -> tuple[str, dict[str, str]]:
    lines = raw.split("\n")
    blocks: dict[str, str] = {}
    out, i = [], 0
    for start, end in text.code_blocks(raw):
        out += lines[i:start]
        key = f"[CODE-{len(blocks) + 1}]"
        blocks[key] = "\n".join(lines[start:end + 1])
        out.append(key)
        i = end + 1
    out += lines[i:]
    return "\n".join(out), blocks


def unmask(s: str, blocks: dict[str, str]) -> str:
    for key, block in blocks.items():
        n = s.count(key)
        if n != 1:
            raise UsageError(f"placeholder {key} appears {n} times, expected once")
        s = s.replace(key, block)
    return s
