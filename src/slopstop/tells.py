"""The tell catalog. Each tell measures one habit; bands come from a register.

A doc tell yields one Measure per text (a rate per 1000 words). A paragraph tell
yields one Measure per prose paragraph. Spans point at lines in the original file.
"""
import re
import statistics
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
    low_required: bool = False  # True only where falling below the band is itself a tell


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


CORRECTIVE = ["it isn't", "it's not", "that isn't", "that's not", "this isn't",
              "this is not", "it's the", "that's the", "it's also", "and yet"]
METAPHOR_NOUNS = ["substrate", "wedge", "vector", "locus", "vantage", "nexus", "primitive",
                  "harness", "surface", "bedrock", "scaffolding", "modality",
                  "ratchet", "endgame", "north star", "flywheel"]
CLOSERS = re.compile(r"^(in short|in sum|in summary|ultimately|in the end|overall|all in all|"
                     r"the bottom line|in conclusion|at the end of the day)\b", re.I)
SIGNPOSTS = re.compile(r"^(let's|let us|here's|here is|now,|first,|next,|finally,|to be clear|"
                       r"put simply|in other words|the key|the point is)", re.I)
TRIPLET = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? and [\w'-]+", re.I)
COLON = re.compile(r"\w:\s+[a-z]")
BOLD = re.compile(r"\*\*[^*\n]+\*\*")
HEADING = re.compile(r"^#{1,6}\s+\S")
NEVER = re.compile(r"(?!x)x")


def _phrase_re(phrase: str) -> str:
    return r"(?<!\w)" + r"\W+".join(map(re.escape, phrase.split())) + r"(?!\w)"


def _rate(raw: str, count: int) -> float:
    return round(count * 1000 / max(text.word_count(raw), 1), 2)


def _count_lines(raw: str, pattern: re.Pattern, lines=None) -> Measure:
    total, spans = 0, []
    for n, ln in (lines if lines is not None else text.prose_lines(raw)):
        k = len(pattern.findall(text.normalize(ln)))
        if k:
            total += k
            spans.append(Span(n, ln.strip()[:80]))
    return Measure(_rate(raw, total), tuple(spans))


def _all_lines(raw: str) -> list[tuple[int, str]]:
    """Every line outside frontmatter and code, for tells about headings and bold."""
    out, in_code = [], False
    m = text.FRONTMATTER.match(raw)
    skip = m.group(0).count("\n") if m else 0
    for i, ln in enumerate(raw.split("\n")):
        if i < skip:
            continue
        if text.FENCE.match(ln):
            in_code = not in_code
            continue
        if not in_code:
            out.append((i + 1, ln))
    return out


def _sentences_with_lines(raw: str) -> list[tuple[int, str]]:
    return [(n, s) for n, ln in text.prose_lines(raw)
            for s in text.split_sentences(text.strip_markdown(ln)) if text.tokenize(s)]


def _pattern(pattern: re.Pattern, all_lines: bool = False):
    return lambda raw, phrases: [_count_lines(raw, pattern, _all_lines(raw) if all_lines else None)]


def _list_measure(words: list[str]):
    pat = re.compile("|".join(_phrase_re(w) for w in words), re.I) if words else NEVER
    return lambda raw, phrases: [_count_lines(raw, pat)]


def _sentence_lengths(raw):
    return [(n, len(text.tokenize(s)), s) for n, s in _sentences_with_lines(raw)]


def _sentence_length(raw, phrases):
    sl = _sentence_lengths(raw)
    if not sl:
        return [Measure(0.0)]
    longest = sorted(sl, key=lambda x: -x[1])[:3]
    return [Measure(round(statistics.mean(x[1] for x in sl), 2),
                    tuple(Span(n, s[:80]) for n, _, s in sorted(longest)))]


def _sentence_spread(raw, phrases):
    sl = [x[1] for x in _sentence_lengths(raw)]
    return [Measure(round(statistics.pstdev(sl), 2) if len(sl) > 1 else 0.0)]


def _repeated_openers(raw, phrases):
    ss = _sentences_with_lines(raw)
    firsts = [text.tokenize(s)[0] for _, s in ss]
    hits = [ss[i] for i in range(1, len(ss)) if firsts[i] == firsts[i - 1]]
    pct = round(100 * len(hits) / max(len(ss), 1), 2)
    return [Measure(pct, tuple(Span(n, s[:80]) for n, s in hits))]


def _sentence_pattern(pattern: re.Pattern, last_in_paragraph: bool = False):
    def measure(raw, phrases):
        spans = []
        for p in text.paragraphs(raw):
            sents = text.split_sentences(text.strip_markdown(p.text))
            pick = sents[-1:] if last_in_paragraph else sents
            spans += [Span(p.line, s[:80]) for s in pick if pattern.match(text.normalize(s))]
        return [Measure(_rate(raw, len(spans)), tuple(spans))]
    return measure


def _overused(raw, phrases):
    return _list_measure(phrases)(raw, phrases)


# Uniform, choppy rhythm is a tell; too few em dashes, colons or headings is not.
LOW_IS_SLOP = {"sentence-length", "sentence-spread"}
NOTHING = "Below the register's $lo to $hi. Nothing to fix."

for name, allow, fn, what, high, low in [
    ("em-dash", "punctuation", _pattern(re.compile("\u2014")), "em dashes per 1000 words",
     "Replace the em dashes on lines $lines with periods or commas ($value per 1000 words; register $lo to $hi).",
     "This text has $value em dashes per 1000 words, below the register's $lo to $hi. Nothing to fix unless the author wants more."),
    ("mid-sentence-colon", "punctuation", _pattern(COLON), "colons joining two clauses, per 1000 words",
     "Rewrite the colons on lines $lines as two sentences or a comma ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("corrective", "span", _list_measure(CORRECTIVE), "corrective constructions (\"it's not X, it's Y\") per 1000 words",
     "On lines $lines, say what the thing is without first denying a reading nobody offered ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("metaphor-nouns", "span", _list_measure(METAPHOR_NOUNS), "abstract metaphor nouns (substrate, harness, surface) per 1000 words",
     "On lines $lines, replace the metaphor noun with the concrete word ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("headings", "span", _pattern(HEADING, all_lines=True), "headings per 1000 words",
     "Merge or remove headings on lines $lines; the register uses $lo to $hi per 1000 words and this text $value.",
     "This text has fewer headings than the register ($value against $lo to $hi). Add one only where a reader needs a landmark."),
    ("bold", "span", _pattern(BOLD, all_lines=True), "bold spans per 1000 words",
     "Remove the bold on lines $lines except where a reader must not miss the term ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("sentence-length", "span", _sentence_length, "mean words per sentence",
     "Sentences average $value words against the register's $lo to $hi. Split the longest ones, on lines $lines.",
     "Sentences average $value words against the register's $lo to $hi. Join short sentences that carry one thought."),
    ("sentence-spread", "span", _sentence_spread, "standard deviation of sentence length in words",
     "Sentence length varies more than the register ($value against $lo to $hi). Even out the extremes.",
     "Sentence lengths are too uniform ($value against the register's $lo to $hi). Vary them: some short, some long."),
    ("repeated-openers", "span", _repeated_openers, "percent of sentences opening with the previous sentence's first word",
     "Vary the openings of the sentences on lines $lines ($value% repeat; register $lo to $hi).",
     NOTHING),
    ("triplets", "span", _pattern(TRIPLET), "lists of three (\"X, Y, and Z\") per 1000 words",
     "On lines $lines, use the natural number of items instead of three ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("summary-closers", "span", _sentence_pattern(CLOSERS, last_in_paragraph=True), "paragraphs ending in a summary phrase, per 1000 words",
     "Cut the summary sentences that close the paragraphs at lines $lines ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("signposts", "span", _sentence_pattern(SIGNPOSTS), "signposting openers (\"Let's\", \"Here's\") per 1000 words",
     "Remove the signposting at the start of the sentences on lines $lines ($value per 1000 words; register $lo to $hi).",
     NOTHING),
    ("overused-phrases", "span", _overused, "phrases model text overuses against this register, per 1000 words",
     "Reword the overused phrases on lines $lines ($value per 1000 words; register $lo to $hi).",
     NOTHING),
]:
    _add(Tell(name, "doc", "two", allow, high, low, fn, what,
              low_required=name in LOW_IS_SLOP))
