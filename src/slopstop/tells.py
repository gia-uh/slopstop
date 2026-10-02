"""The tell catalog. Each tell measures one habit; bands come from a register.

A doc tell yields one Measure per text (a rate per 1000 words). A paragraph tell
yields one Measure per prose paragraph. Spans point at lines in the original file.
"""
from dataclasses import dataclass, field
from typing import Callable

from slopstop import text

MIN_WORDS = 150


@dataclass(frozen=True)
class Span:
    line: int
    text: str


@dataclass(frozen=True)
class Measure:
    value: float
    spans: tuple[Span, ...] = ()
    where: str = ""


@dataclass(frozen=True)
class Tell:
    name: str
    unit: str
    sided: str
    allow: str
    high: str
    low: str | None
    measure: Callable[[str, list[str]], list[Measure]] = field(repr=False)
    describe: str = ""


def _long_paragraph(raw: str, phrases: list[str]) -> list[Measure]:
    return [Measure(p.words, (Span(p.line, p.text.split("\n")[0][:80]),), f"¶{p.index}")
            for p in text.paragraphs(raw)]


CATALOG: dict[str, Tell] = {}


def _add(t: Tell) -> None:
    CATALOG[t.name] = t


_add(Tell(
    "long-paragraph", "paragraph", "upper", "breaks",
    high="Split $where ($value words; register p99 $p99, median $p50) at the points where "
         "the argument moves on. Insert paragraph breaks only.",
    low=None, measure=_long_paragraph,
    describe="words in a prose paragraph; only the top end is bounded",
))
