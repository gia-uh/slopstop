"""The rule catalog: what a rule is, the document it reads, and the finding it reports.

A rule either matches a pattern on each prose line (`pattern`) or reads the
whole document (`scan`). Every rule carries examples that must fire, examples
that must stay quiet and, for rules with a replacement, the exact text `fix`
must produce. tests/test_rules.py runs them all.
"""
import re
from dataclasses import dataclass, field
from typing import Callable

from slopstop import text

LEVELS = ("error", "warn")
KINDS = ("auto", "suggest", "rewrite")


@dataclass(frozen=True)
class Line:
    n: int          # 1-based line number in the file
    raw: str        # the line as written
    scan: str       # normalized, with code, URLs, link targets and comments blanked; same length
    heading: bool
    item: bool      # a list item
    label: bool     # a list item that opens with "**Label**:"


@dataclass(frozen=True)
class Finding:
    rule: str
    level: str
    kind: str
    line: int
    start: int      # 0-based column, in the line as written
    end: int
    text: str
    why: str
    todo: str
    replacement: str | None = None
    note: str = ""


@dataclass
class Doc:
    raw: str
    lang: str
    lines: list[Line]
    paragraphs: list[text.Paragraph]
    sentences: list[text.Sentence]

    def __post_init__(self):
        self._by_n = {ln.n: ln for ln in self.lines}
        self._para: dict[int, str] = {}

    def line(self, n: int) -> Line | None:
        return self._by_n.get(n)

    def para_scan(self, p: text.Paragraph) -> str:
        """A prose paragraph's masked text, its lines joined by spaces."""
        if p.line not in self._para:
            span = range(p.line, p.line + p.text.count("\n") + 1)
            self._para[p.line] = " ".join(self._by_n[n].scan for n in span if n in self._by_n)
        return self._para[p.line]


@dataclass(frozen=True)
class Rule:
    id: str
    lang: str                       # "en", "es" or "any"
    level: str
    kind: str
    why: str
    todo: str
    pattern: re.Pattern | None = None
    replace: Callable[[re.Match, Line], str | None] | str | None = None
    scan: Callable[["Doc", "Rule", int | None], list[Finding]] | None = None
    threshold: int | None = None
    tune: tuple[int, int] | None = None   # candidate thresholds for calibrate, inclusive
    tune_up: bool = False                 # True when a higher threshold flags more, not less
    skip: Callable[[Line], bool] | None = None
    fires: tuple[str, ...] = ()
    quiet: tuple[str, ...] = ()
    fixes: tuple[tuple[str, str], ...] = field(default=())

    def finding(self, line: int, start: int, end: int, txt: str, replacement: str | None = None,
                note: str = "", level: str | None = None) -> Finding:
        return Finding(self.id, level or self.level, self.kind, line, start, end, txt, self.why, self.todo,
                       replacement, note)


CATALOG: list[Rule] = []


def add(rule: Rule) -> Rule:
    assert rule.level in LEVELS and rule.kind in KINDS, rule.id
    CATALOG.append(rule)
    return rule


def phrases(*items: str) -> str:
    """An alternation of literal phrases; any run of spaces or punctuation matches between words."""
    return "|".join(r"\W+".join(map(re.escape, p.split())) for p in items)


# Where a sentence may begin inside a line: line start, after end punctuation, after a list marker.
SENT_START = r"(?:^|(?<=[.!?]\s)|(?<=[.!?]\s\s)|(?<=^[-*+]\s)|(?<=^\d\.\s)|(?<=^\d\d\.\s))"


def sentence_from(items: str) -> re.Pattern:
    """A whole sentence that opens with one of the phrases, with the space after it."""
    return re.compile(SENT_START + r"(?:" + items + r")[^.!?\n]*[.!?]*[ \t]*", re.I)


def load() -> list[Rule]:
    """Import every rule module once and return the catalog."""
    from slopstop.rules import marks, phrases_en, phrases_es, shape  # noqa: F401
    return CATALOG
