"""Deterministic checks of a model's output against its input.

The agent runs a gate after every rewrite or fix. --allow declares what the change may
touch, and the gate verifies it instead of trusting the model to follow the instruction.
"""
import difflib
import re
from dataclasses import dataclass, field

from slopstop import text

PLACEHOLDER = re.compile(r"\[CODE-\d+\]")
META = re.compile(r"^\s*(here is|here's|sure[,!]|certainly|below is|i hope this|let me know|"
                  r"note:|this rewrite|the rewritten|rewritten (essay|version|text))", re.I)
END_OK = re.compile(r"[.!?…:\"”’)\]*_]$")
REPEAT_RUN = 30


@dataclass
class Result:
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def _words(s: str) -> list[str]:
    return text.tokenize(text.drop_code(s))


def _all_tokens(s: str) -> list[str]:
    """Every word and number, code included, lowercased: what a fix must not change."""
    return re.findall(r"\w+", text.normalize(s).lower())


def ends_mid_sentence(s: str) -> bool:
    s = s.rstrip()
    if not s:
        return False
    if not text.fences_balanced(s):
        return True
    last = s.splitlines()[-1].strip()
    if re.match(r"^([#|>*-]|\d+\.|```|~~~|\[CODE-\d+\])", last):
        return False
    return not END_OK.search(last)


def repeated_run(s: str, n: int = REPEAT_RUN) -> str | None:
    w = _words(s)
    seen: dict[str, int] = {}
    for i in range(len(w) - n + 1):
        k = " ".join(w[i:i + n])
        if k in seen and i - seen[k] >= n:
            return k
        seen.setdefault(k, i)
    return None


def check_input(raw: str, transcript: bool = False) -> Result:
    r = Result()
    problems = []
    if not text.fences_balanced(raw):
        problems.append("unbalanced code fence: the text ends inside a code block")
    if ends_mid_sentence(raw):
        problems.append(f"ends mid-sentence: '...{raw.rstrip()[-50:]}'")
    (r.warnings if transcript else r.failures).extend(problems)
    return r


def _structure(src: str, out: str, r: Result) -> None:
    if len(_words(out)) < 30 and len(_words(src)) >= 30:
        r.failures.append(f"empty or near-empty output ({len(_words(out))} words)")
        return
    if not text.fences_balanced(out) and text.fences_balanced(src):
        r.failures.append("unbalanced code fence")
    run = repeated_run(out)
    if run and not repeated_run(src):
        r.failures.append(f"repeated block: '{run[:60]}...'")
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    for ln in lines[:1] + lines[-1:]:
        if META.search(ln) and ln.strip()[:40].lower() not in src.lower():
            r.failures.append(f"line addressed to the user: '{ln.strip()[:60]}'")
    if ends_mid_sentence(out) and not ends_mid_sentence(src):
        r.failures.append(f"ends mid-sentence: '...{out.rstrip()[-50:]}'")
    for p in sorted(set(PLACEHOLDER.findall(src))):
        if out.count(p) != 1:
            r.failures.append(f"placeholder {p} appears {out.count(p)} times, expected once")


SPAN_RATIO = (0.5, 1.5)


def _span_failures(src: str, out: str, allowed: set[int]) -> list[str]:
    """Only the listed source lines may change; blank lines are free.

    Each changed region must keep half to one and a half times the words of the
    lines it replaces, and no new non-blank line may appear, so a span fix cannot
    blank a paragraph or invent one next to an allowed line.
    """
    a, b = src.splitlines(), out.splitlines()
    names = ",".join(map(str, sorted(allowed))) or "none"
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        old = [i for i in range(i1, i2) if a[i].strip()]
        new = [ln for ln in b[j1:j2] if ln.strip()]
        outside = [i + 1 for i in old if i + 1 not in allowed]
        if outside:
            return [f"--allow span: line {outside[0]} changed but only lines {names} may"]
        if not old and new:
            return [f"--allow span: new text inserted near line {i1 + 1}: '{new[0][:60]}'"]
        ow, nw = sum(len(_all_tokens(a[i])) for i in old), sum(len(_all_tokens(ln)) for ln in new)
        if ow and not SPAN_RATIO[0] <= nw / ow <= SPAN_RATIO[1]:
            return [f"--allow span: lines {old[0] + 1}-{old[-1] + 1} went from {ow} to {nw} words; "
                    f"a span fix keeps {SPAN_RATIO[0]:.0%} to {SPAN_RATIO[1]:.0%} of them"]
    return []


def check_output(src: str, out: str, allow: str = "rewrite", ratio: tuple[float, float] = (0.75, 1.35),
                 lines: list[int] | None = None, budget: float = 0.15,
                 split: list[dict] | None = None) -> Result:
    r = Result()
    _structure(src, out, r)
    for s in split or []:
        if s["kind"] == "request" and len(text.tokenize(s["text"])) >= 6 and overlap(s["text"], out) >= 0.3:
            r.failures.append(f"a request reached the output: '{s['text'][:60]}'")
    if r.failures and "empty" in r.failures[0]:
        return r
    if allow == "rewrite":
        base = src if split is None else " ".join(s["text"] for s in split if s["kind"] != "request")
        got = len(_words(out)) / max(len(_words(base)), 1)
        lo, hi = ratio
        if not lo <= got <= hi:
            r.failures.append(f"length ratio {got:.2f} outside [{lo}, {hi}]")
    elif allow == "breaks" and src.split() != out.split():
        r.failures.append("--allow breaks: words or punctuation changed; only paragraph breaks may change")
    elif allow == "punctuation" and _all_tokens(src) != _all_tokens(out):
        r.failures.append("--allow punctuation: words changed; only punctuation may change")
    elif allow == "span":
        r.failures += _span_failures(src, out, set(lines or []))
    elif allow == "polish":
        changed = 1 - difflib.SequenceMatcher(a=_all_tokens(src), b=_all_tokens(out), autojunk=False).ratio()
        if changed > budget:
            r.failures.append(f"--allow polish: {changed:.0%} of words changed, over the {budget:.0%} budget")
    return r


KINDS = {"content", "directive", "request"}


def overlap(span: str, hay: str, n: int = 8) -> float:
    """Share of the span's n-word windows found verbatim in hay."""
    s, h = text.tokenize(span), " ".join(text.tokenize(hay))
    if not s:
        return 1.0
    if len(s) < n:
        return 1.0 if " ".join(s) in h else 0.0
    wins = [" ".join(s[i:i + n]) for i in range(len(s) - n + 1)]
    return sum(w in h for w in wins) / len(wins)


def check_split(transcript: str, segments: list[dict]) -> Result:
    """Each passage must continue the transcript exactly where the previous one ended.

    One cursor over the transcript's words checks verbatim copying, full coverage
    and order at once; punctuation and case may differ, words may not.
    """
    r = Result()
    words = _all_tokens(transcript)
    cursor = 0
    for i, s in enumerate(segments, 1):
        if s.get("kind") not in KINDS:
            r.failures.append(f"passage {i} has kind {s.get('kind')!r}; expected one of {sorted(KINDS)}")
        p = _all_tokens(str(s.get("text", "")))
        if not p:
            r.failures.append(f"passage {i} is empty")
            continue
        if words[cursor:cursor + len(p)] != p:
            got = " ".join(words[cursor:cursor + 8])
            r.failures.append(f"passage {i} does not continue the transcript verbatim (text edited, "
                              f"missing or out of order): expected '{got}...', got '{' '.join(p[:8])}...'")
            return r
        cursor += len(p)
    if cursor < len(words):
        r.failures.append(f"coverage: the passages stop at word {cursor} of {len(words)}; "
                          f"missing '{' '.join(words[cursor:cursor + 8])}...'")
    return r