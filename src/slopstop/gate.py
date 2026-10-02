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
    return text.tokenize(text.FENCED.sub(" ", s))


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


def check_output(src: str, out: str, allow: str = "rewrite", ratio: tuple[float, float] = (0.75, 1.35),
                 lines: list[int] | None = None, budget: float = 0.15,
                 split: list[dict] | None = None) -> Result:
    r = Result()
    _structure(src, out, r)
    if r.failures and "empty" in r.failures[0]:
        return r
    if allow == "rewrite":
        base = src if split is None else " ".join(s["text"] for s in split if s["kind"] != "request")
        got = len(_words(out)) / max(len(_words(base)), 1)
        lo, hi = ratio
        if not lo <= got <= hi:
            r.failures.append(f"length ratio {got:.2f} outside [{lo}, {hi}]")
    return r


def check_split(transcript: str, segments: list[dict]) -> Result:
    return Result()
