"""Punctuation and formatting rules, for any language."""
import re

from slopstop.rules import Doc, Line, Rule, add

END = re.compile(r"[.!?](?=\s|$)")


def _sentence_bounds(s: str, at: int) -> tuple[int, int]:
    """Start and end of the sentence around column `at` within one line."""
    starts = [m.end() for m in END.finditer(s[:at])]
    m = END.search(s, at)
    return (starts[-1] if starts else 0), (m.end() if m else len(s))


def _em_dash(m: re.Match, ln: Line) -> str | None:
    """A pair inside one sentence becomes commas, a dash before a list a colon, any other a period.

    The match includes the letter after the dash (group 1), so a period can capitalize it.
    """
    s, nxt = ln.scan, m.group(1)
    lo, hi = _sentence_bounds(s, m.start())
    dashes = [d.start() for d in re.finditer("—", s[lo:hi])]
    if len(dashes) == 2 and len(s[lo + dashes[0]:lo + dashes[1]].split()) <= 12:
        return ", " + nxt
    rest = s[m.start(1):hi]
    if not rest.strip() or len(dashes) > 2:
        return None
    if rest.count(",") >= 2 or len(rest.split()) <= 3:
        return ": " + nxt
    return ". " + nxt.upper() if nxt.isalpha() else None


add(Rule(
    "em-dash", "any", "warn", "suggest",
    why="An em dash joining two thoughts; a period, comma or colon says which relation is meant.",
    todo="Use the suggested punctuation, or rewrite the sentence.",
    pattern=re.compile(r"[ \t]*—[ \t]*(\w?)"),
    replace=_em_dash,
    fires=("It works — but only on Linux.",),
    quiet=("It works, but only on Linux.", "The range 1990–2000 is fine."),
    fixes=(("It works — but only on Linux.", "It works. But only on Linux."),
           ("The tool — a small script — runs nightly.", "The tool, a small script, runs nightly."),
           ("It has three parts — lexer, parser, and checker.", "It has three parts: lexer, parser, and checker.")),
))


def _bold_skip(ln: Line) -> bool:
    return ln.heading or ln.label or bool(re.fullmatch(r"\s*(?:[-*+]\s+)?\*\*[^*]+\*\*:?\s*", ln.raw))


add(Rule(
    "bold-spray", "any", "error", "auto",
    why="Bold inside running prose makes every marked phrase shout, so none stands out.",
    todo="Remove the bold.",
    pattern=re.compile(r"\*\*([^*\n]+)\*\*"),
    replace=lambda m, ln: m.group(1),
    skip=_bold_skip,
    fires=("A **stale cache** can serve wrong data.",),
    quiet=("A stale cache can serve wrong data.", "- **Speed**: reads are fast.", "**Step one**"),
    fixes=(("A **stale cache** can serve wrong data.", "A stale cache can serve wrong data."),),
))

add(Rule(
    "emoji", "any", "error", "auto",
    why="Emoji in prose or headings are decoration that carries no information.",
    todo="Delete the emoji.",
    pattern=re.compile("[ \t]?[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF☀-⛿✅❌✨⭐]️?"),
    replace="",
    fires=("Getting started \U0001F680",),
    quiet=("Getting started",),
    fixes=(("Done! \U0001F389 Next step.", "Done! Next step."),),
))

add(Rule(
    "arrow-prose", "any", "warn", "rewrite",
    why="An arrow standing in for a verb makes the reader guess which verb.",
    todo="Write the verb the arrow stands for.",
    pattern=re.compile(r"(?<=\w)\s*(?:→|->|=>)\s*(?=\w)"),
    fires=("The draft → review → merge loop.",),
    quiet=("The draft goes to review, then to merge.",),
))


def _density(pattern: re.Pattern, what: str):
    def scan(doc: Doc, rule: Rule, threshold: int | None) -> list:
        out = []
        for p in doc.paragraphs:
            k = len(pattern.findall(doc.para_scan(p)))
            if k >= threshold:
                out.append(rule.finding(p.line, 0, 0, p.text.split("\n")[0][:80], note=f"{k} {what}"))
        return out
    return scan


for rid, pat, what, why, todo, fire, quiet in [
    ("semicolon-spray", re.compile(r";"), "semicolons",
     "Clauses chained with semicolons make the reader hold several claims at once.",
     "Split the chain into sentences.",
     "This is X; that is Y; the rest is Z; and so on.", "This is X. That is Y."),
    ("aside-spray", re.compile(r"\([^()]{20,}\)"), "long parenthetical asides",
     "Many long asides interrupt the sentence they sit in.",
     "Keep the asides that matter, as sentences.",
     "It runs (on every commit, by default) and logs (to a file under var/log) and retries "
     "(three times, with backoff) until done.", "It runs on every commit (by default)."),
    ("colon-spray", re.compile(r"[^\W\d_]:[ \t]+\w"), "colons inside sentences",
     "Colon after colon turns prose into a list of reveals.",
     "Say it in plain sentences.",
     "The fix: invalidate. The cost: a miss. The catch: races.", "We fixed it: we invalidate on write."),
    ("slash-pairs", re.compile(r"\b[^\W\d_]{2,}/[^\W\d_]{2,}\b"), "word/word pairs",
     "Slash pairs leave the reader to decide whether the writer meant and, or, or both.",
     "Pick one word, or write \"and\" or \"or\".",
     "The read/write path, the plan/execute split and the agent/human loop.", "Reads and writes share a path."),
]:
    add(Rule(rid, "any", "warn", "rewrite", why=why, todo=todo, scan=_density(pat, what),
             threshold=2 if rid == "slash-pairs" else 3, tune=(1, 20),
             fires=(fire,), quiet=(quiet,)))
