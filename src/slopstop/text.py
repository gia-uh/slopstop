"""Text handling shared by every command: Markdown stripping, tokens, sentences, paragraphs.

Ported from the workspace's bin/slopcheck so rates match the September experiments.
"""
import re
import unicodedata
from dataclasses import dataclass

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
INLINE_CODE = re.compile(r"`[^`\n]+`")
DIV_FENCE = re.compile(r"^:::+.*$", re.M)
HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
WIKILINK = re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]")
FOOTNOTE_REF = re.compile(r"\[\^[^\]]+\]")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$", re.M)
LIST_MARK = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+", re.M)
QUOTE_MARK = re.compile(r"^\s*>\s?", re.M)
HEADING_MARK = re.compile(r"^#{1,6}\s+", re.M)
EMPH_MARK = re.compile(r"(\*\*|__|\*|_)")
SENT_SPLIT = re.compile(r"(?<=[.!?…])[\"'”’)]*\s+|\n{1,}")
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?", re.UNICODE)
APPARATUS = re.compile(r"^\s*([#|>!<]|[-*+]\s|\d+\.\s|:::)")

ES_MARKERS = {"de", "la", "el", "que", "en", "y", "los", "las", "un", "una",
              "por", "para", "con", "se", "su", "del", "es", "no", "lo", "al"}
EN_MARKERS = {"the", "of", "and", "to", "in", "is", "that", "it", "for",
              "with", "as", "on", "this", "are", "but", "from", "you", "be"}


@dataclass(frozen=True)
class Sentence:
    par: int
    line: int
    text: str


@dataclass(frozen=True)
class Paragraph:
    index: int
    line: int
    text: str
    words: int


def normalize(s: str) -> str:
    return unicodedata.normalize("NFC", s).replace("’", "'")


def _scan(raw: str) -> tuple[list[bool], str | None]:
    """Per line, whether it belongs to a fenced code block (fence lines included).

    A fence closes only with the same character, at least as long as the opener,
    as CommonMark has it; returns the closing marker of a fence left open.
    """
    flags, opener = [], None
    for ln in raw.split("\n"):
        m = FENCE_LINE.match(ln)
        if opener is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                opener = m.group(1)
                flags.append(True)
            else:
                flags.append(False)
        else:
            flags.append(True)
            if m and m.group(1)[0] == opener[0] and len(m.group(1)) >= len(opener) and not m.group(2).strip():
                opener = None
    return flags, opener


def open_fence(raw: str) -> str | None:
    return _scan(raw)[1]


def code_blocks(raw: str) -> list[tuple[int, int]]:
    """0-based (first, last) line indices of each fenced block, fences included."""
    flags, _ = _scan(raw)
    lines = raw.split("\n")
    out, start, opener = [], None, None
    for i, (ln, code) in enumerate(zip(lines, flags)):
        if code and start is None:
            start, opener = i, FENCE_LINE.match(ln).group(1)
        elif start is not None:
            m = FENCE_LINE.match(ln)
            if m and m.group(1)[0] == opener[0] and len(m.group(1)) >= len(opener) and not m.group(2).strip():
                out.append((start, i))
                start = None
    return out


def drop_code(raw: str) -> str:
    """The text with every fenced code line blanked, line count kept."""
    flags, _ = _scan(raw)
    return "\n".join("" if c else ln for ln, c in zip(raw.split("\n"), flags))


def strip_markdown(raw: str) -> str:
    """Return prose with markup, code, tables and apparatus removed."""
    t = FRONTMATTER.sub("", drop_code(raw))
    for pat, rep in ((HTML_COMMENT, " "), (DIV_FENCE, " "), (TABLE_ROW, " "),
                     (IMAGE, " "), (LINK, r"\1"), (FOOTNOTE_REF, " "), (INLINE_CODE, " "),
                     (HTML_TAG, " ")):
        t = pat.sub(rep, t)
    t = WIKILINK.sub(lambda m: m.group(2) or m.group(1), t)
    for pat in (HEADING_MARK, QUOTE_MARK, LIST_MARK, EMPH_MARK):
        t = pat.sub("", t)
    return re.sub(r"^\s*[-*_]{3,}\s*$", " ", t, flags=re.M)


def tokenize(s: str) -> list[str]:
    return WORD.findall(normalize(s).lower())


def split_sentences(s: str) -> list[str]:
    return [x.strip() for x in SENT_SPLIT.split(s) if x and x.strip()]


def word_count(raw: str) -> int:
    return len(tokenize(strip_markdown(raw)))


def fences_balanced(raw: str) -> bool:
    return open_fence(raw) is None


def detect_lang(tokens: list[str]) -> str:
    es = sum(t in ES_MARKERS for t in tokens)
    en = sum(t in EN_MARKERS for t in tokens)
    return "es" if es > en else "en"


def _prose_blocks(raw: str) -> list[tuple[int, list[str]]]:
    """Runs of prose lines as (first line number, lines).

    Classified line by line: blank lines, code, headings, list items (and their
    indented continuations), tables, quotes and HTML end a run and are left out.
    """
    lines = raw.split("\n")
    flags, _ = _scan(raw)
    m = FRONTMATTER.match(raw)
    start = m.group(0).count("\n") if m else 0
    blocks, cur, cur_line, prev_apparatus = [], [], 0, False
    for i in range(start, len(lines)):
        ln = lines[i]
        apparatus = bool(APPARATUS.match(ln)) or (prev_apparatus and ln.startswith((" ", "\t")) and ln.strip())
        if flags[i] or not ln.strip() or apparatus:
            if cur:
                blocks.append((cur_line, cur))
                cur = []
            prev_apparatus = bool(apparatus)
            continue
        prev_apparatus = False
        if not cur:
            cur_line = i + 1
        cur.append(ln)
    if cur:
        blocks.append((cur_line, cur))
    return blocks


def paragraphs(raw: str) -> list[Paragraph]:
    out = []
    for n, b in _prose_blocks(raw):
        t = "\n".join(b)
        out.append(Paragraph(len(out) + 1, n, t, len(tokenize(strip_markdown(t)))))
    return out


def prose_lines(raw: str) -> list[tuple[int, str]]:
    return [(n + k, ln) for n, b in _prose_blocks(raw) for k, ln in enumerate(b)]


def sentences(raw: str) -> list[Sentence]:
    """Sentences of each prose paragraph, hard wraps ignored, each mapped to its starting line."""
    out = []
    for p in paragraphs(raw):
        lines = p.text.split("\n")
        starts, pos = [], 0
        for ln in lines:
            starts.append(pos)
            pos += len(ln) + 1
        joined = " ".join(lines)
        cursor = 0
        for s in split_sentences(joined):
            at = joined.find(s, cursor)
            cursor = at + len(s)
            k = max(i for i, st in enumerate(starts) if st <= at)
            clean = strip_markdown(s).strip()
            if tokenize(clean):
                out.append(Sentence(p.index, p.line + k, clean))
    return out
