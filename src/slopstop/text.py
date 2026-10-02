"""Text handling shared by every command: Markdown stripping, tokens, sentences, paragraphs.

Ported from the workspace's bin/slopcheck so rates match the September experiments.
"""
import re
import unicodedata
from dataclasses import dataclass

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE = re.compile(r"^\s*(```|~~~)", re.M)
FENCED = re.compile(r"^(```|~~~).*?^\1.*?$", re.S | re.M)
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
NON_PROSE_START = re.compile(r"^\s*([#|>!<]|[-*+]\s|\d+\.\s|:::|```|~~~)")

ES_MARKERS = {"de", "la", "el", "que", "en", "y", "los", "las", "un", "una",
              "por", "para", "con", "se", "su", "del", "es", "no", "lo", "al"}
EN_MARKERS = {"the", "of", "and", "to", "in", "is", "that", "it", "for",
              "with", "as", "on", "this", "are", "but", "from", "you", "be"}


@dataclass(frozen=True)
class Paragraph:
    index: int
    line: int
    text: str
    words: int


def normalize(s: str) -> str:
    return unicodedata.normalize("NFC", s).replace("’", "'")


def strip_markdown(raw: str) -> str:
    """Return prose with markup, code, tables and apparatus removed."""
    t = FRONTMATTER.sub("", raw)
    for pat, rep in ((FENCED, " "), (HTML_COMMENT, " "), (DIV_FENCE, " "), (TABLE_ROW, " "),
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
    return len(FENCE.findall(raw)) % 2 == 0


def detect_lang(tokens: list[str]) -> str:
    es = sum(t in ES_MARKERS for t in tokens)
    en = sum(t in EN_MARKERS for t in tokens)
    return "es" if es > en else "en"


def _prose_blocks(raw: str) -> list[tuple[int, list[str]]]:
    """Runs of non-blank prose lines as (first line number, lines)."""
    lines = raw.split("\n")
    m = FRONTMATTER.match(raw)
    start = m.group(0).count("\n") if m else 0
    blocks, cur, cur_line, in_code = [], [], 0, False
    for i in range(start, len(lines)):
        ln = lines[i]
        if FENCE.match(ln):
            in_code = not in_code
            if cur:
                blocks.append((cur_line, cur))
                cur = []
            continue
        if in_code or not ln.strip():
            if cur:
                blocks.append((cur_line, cur))
                cur = []
            continue
        if not cur:
            cur_line = i + 1
        cur.append(ln)
    if cur:
        blocks.append((cur_line, cur))
    return [(n, b) for n, b in blocks if not NON_PROSE_START.match(b[0])]


def paragraphs(raw: str) -> list[Paragraph]:
    out = []
    for n, b in _prose_blocks(raw):
        t = "\n".join(b)
        out.append(Paragraph(len(out) + 1, n, t, len(tokenize(strip_markdown(t)))))
    return out


def prose_lines(raw: str) -> list[tuple[int, str]]:
    return [(n + k, ln) for n, b in _prose_blocks(raw) for k, ln in enumerate(b)]
