---
date: 2026-10-02
status: in progress
spec: docs/superpowers/specs/2026-10-01-slopstop-design.md
issue: https://github.com/gia-uh/slopstop/issues/3
---

# slopstop tool v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the mechanical `slopstop` CLI (profile, detect with findings and instructions, gate, mask, unmask, check-quotes, instruct, blind), ship one register, and write the skill that drives it. This covers spec slices 1 to 5.

**Architecture:** A stdlib-only Python package under `src/slopstop/`. One module per command, sharing `text.py` (Markdown stripping, tokens, sentences, paragraphs with line numbers) and `tells.py` (the catalog). Registers are JSON files of counted percentiles. Instructions are `string.Template` files shipped as package data. The tool makes no model calls and keeps no state; the skill in `skills/slopstop/` tells the agent how to drive it.

**Tech Stack:** Python ≥3.11, standard library only at runtime, pytest for tests, uv for the environment and build (hatchling backend).

**Spec:** `docs/superpowers/specs/2026-10-01-slopstop-design.md`

## Global Constraints

- The tool makes no model calls and no network calls, and keeps no state between commands.
- Runtime dependencies: none beyond the Python standard library. Python ≥3.11.
- Given the same input and configuration, every command returns the same output.
- A finding is **required** outside the band holding 99% of the register's human texts (or paragraphs, for per-paragraph tells), **optional** outside the 90% band but inside the 99% one.
- Two-sided tells use `[p0.5, p99.5]` (required) and `[p5, p95]` (optional). Upper-only tells use `p99` and `p90`. A value exactly on a boundary is inside.
- Instructions never say who must do the work.
- Code, identifiers, messages, docs: English.
- Exit codes: 0 success/pass, 1 check failed or required findings present, 2 usage or input error (missing file, bad JSON). Never a traceback for a user error.
- `make test` is the gate; CI runs it.

## Review Focus

1. **Short texts.** A 60-word file: rate tells are skipped with a note naming the 150-word minimum; no required finding comes from noise; per-paragraph tells still run. Test in Task 3.
2. **Curly apostrophes.** "it’s not" (U+2019) counts as a corrective exactly like "it's not". Test in Task 4.
3. **Markdown apparatus.** Frontmatter, code fences, tables, lists and headings are excluded from prose measures, and every reported line number matches the original file. Test in Task 2 and Task 3.
4. **Blind packet with an unclosed fence.** A version ending inside a code block must not swallow the next version's heading. Test in Task 12.
5. **Gate on degenerate input.** An unchanged output passes every `--allow` kind; an empty output fails with a reason; a missing file exits 2 with a message, no traceback. Tests in Task 7 and Task 8.

## File structure

```
pyproject.toml                       package metadata, script entry, dev group
Makefile                             test target runs pytest + existing checks
src/slopstop/__init__.py             __version__
src/slopstop/cli.py                  argparse entry; one subparser per command
src/slopstop/text.py                 markdown stripping, tokens, sentences, paragraphs, language guess
src/slopstop/tells.py                Tell dataclass and CATALOG
src/slopstop/register.py             build/load registers, percentiles, holdout FP rate
src/slopstop/phrases.py              over-represented n-grams (port of bin/slopcheck profile)
src/slopstop/detect.py               findings, severity, instructions, text/JSON rendering
src/slopstop/gate.py                 structural checks, allow kinds, split checks
src/slopstop/mask.py                 code-block placeholders
src/slopstop/quotes.py               verify quotes in judge/critic JSON
src/slopstop/instruct.py             fill instruction templates
src/slopstop/instructions/*.md       split, dictation, restyle, judge, critic, polish
src/slopstop/blind.py                blind packets and rankings
src/slopstop/registers/apiad-blog-en.json   shipped register (counts only)
tests/conftest.py                    shared fixtures (synthetic texts, tiny registers)
tests/test_<module>.py               one test file per module
skills/slopstop/SKILL.md             the agent skill
skills/agent-clause.md               clause for CLAUDE.md / AGENTS.md
```

---

### Task 1: Package scaffold, text utilities, CLI skeleton

**Files:**
- Create: `pyproject.toml`, `src/slopstop/__init__.py`, `src/slopstop/cli.py`, `src/slopstop/text.py`, `tests/test_text.py`, `tests/test_cli.py`
- Modify: `Makefile`, `.gitignore`

**Interfaces:**
- Produces:
  - `text.strip_markdown(raw: str) -> str`
  - `text.tokenize(text: str) -> list[str]` (lowercased words; `’` normalized to `'`)
  - `text.split_sentences(text: str) -> list[str]`
  - `text.Paragraph(index: int, line: int, text: str, words: int)` frozen dataclass, `line` 1-based in the original file
  - `text.paragraphs(raw: str) -> list[Paragraph]` (prose paragraphs only)
  - `text.prose_lines(raw: str) -> list[tuple[int, str]]` (1-based line number, line text) for lines inside prose paragraphs
  - `text.word_count(raw: str) -> int`
  - `text.detect_lang(tokens: list[str]) -> str` (`"en"` or `"es"`)
  - `text.FENCE` compiled regex for fence lines; `text.fences_balanced(raw: str) -> bool`
  - `cli.main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "slopstop"
version = "0.1.0"
description = "Mechanical detection of AI slop, with instructions for the agent that fixes it"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
dependencies = []

[project.scripts]
slopstop = "slopstop.cli:main"

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/slopstop"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write the failing tests**

`tests/test_text.py`:

```python
from slopstop import text

DOC = """---
title: x
---

# A heading

First paragraph has five words.

```python
code = "not prose"
```

- a list item
| a | table |

Second paragraph, with it’s curly apostrophe.
Still the second paragraph.
"""


def test_paragraphs_skip_apparatus_and_keep_line_numbers():
    ps = text.paragraphs(DOC)
    assert [p.line for p in ps] == [7, 16]
    assert ps[0].words == 5
    assert ps[1].text.startswith("Second paragraph")
    assert ps[1].words == 10


def test_tokenize_normalizes_curly_apostrophe():
    assert text.tokenize("It’s not") == ["it's", "not"]


def test_strip_markdown_drops_code_and_frontmatter():
    s = text.strip_markdown(DOC)
    assert "code" not in s and "title" not in s and "A heading" in s


def test_split_sentences():
    assert text.split_sentences("One. Two? Three!") == ["One.", "Two?", "Three!"]


def test_fences_balanced():
    assert text.fences_balanced("```\nx\n```\n")
    assert not text.fences_balanced("```\nx\n")


def test_detect_lang():
    assert text.detect_lang(text.tokenize("el perro de la casa que es")) == "es"
    assert text.detect_lang(text.tokenize("the dog of the house that is")) == "en"


def test_prose_lines_numbers_match_file():
    lines = dict(text.prose_lines(DOC))
    assert lines[7] == "First paragraph has five words."
    assert 10 not in lines  # inside the code fence
```

`tests/test_cli.py`:

```python
from slopstop import __version__, cli


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_is_usage_error(capsys):
    assert cli.main([]) == 2
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_text.py tests/test_cli.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'slopstop'`.

- [ ] **Step 4: Implement `__init__.py`, `text.py`, `cli.py`**

`src/slopstop/__init__.py`:

```python
__version__ = "0.1.0"
```

`src/slopstop/text.py`:

```python
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
SENT_SPLIT = re.compile(r"(?<=[.!?\u2026])[\"'\u201d\u2019)]*\s+|\n{1,}")
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
    return unicodedata.normalize("NFC", s).replace("\u2019", "'")


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
    start = 0
    m = FRONTMATTER.match(raw)
    if m:
        start = m.group(0).count("\n")
    blocks, cur, cur_line, in_code = [], [], 0, False
    for i in range(start, len(lines)):
        ln = lines[i]
        if FENCE.match(ln):
            in_code = not in_code
            if cur:
                blocks.append((cur_line, cur)); cur = []
            continue
        if in_code or not ln.strip():
            if cur:
                blocks.append((cur_line, cur)); cur = []
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
```

`src/slopstop/cli.py`:

```python
"""slopstop command line. Each subcommand lives in its own module; this file only wires them."""
import argparse
import sys

from slopstop import __version__


class UsageError(Exception):
    """A user error: print the message and exit 2."""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopstop", description=__doc__)
    p.add_argument("--version", action="version", version=f"slopstop {__version__}")
    p.add_subparsers(dest="command")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if not getattr(args, "func", None):
        parser.print_usage(sys.stderr)
        return 2
    try:
        return args.func(args)
    except UsageError as e:
        print(f"slopstop: {e}", file=sys.stderr)
        return 2
```

- [ ] **Step 5: Update `Makefile` and `.gitignore`**

`Makefile`:

```makefile
.PHONY: test

# The gate: unit tests, then what the repo already promises.
test:
	uv run pytest -q
	python3 -m compileall -q experiments
	grep -q '^## Disclose your AI use$$' README.md
	grep -q '^## AI use in this repository$$' README.md
```

Append to `.gitignore`: `dist/` and `*.egg-info/`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_text.py tests/test_cli.py -q`
Expected: 9 passed.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock Makefile .gitignore src/slopstop/__init__.py src/slopstop/cli.py src/slopstop/text.py tests/test_text.py tests/test_cli.py
git commit -m "feat: package scaffold, text utilities and CLI skeleton"
```

---

### Task 2: The tell catalog, first tell (long paragraphs) and register building

**Files:**
- Create: `src/slopstop/tells.py`, `src/slopstop/register.py`, `tests/conftest.py`, `tests/test_register.py`

**Interfaces:**
- Consumes: `text.paragraphs`, `text.tokenize`, `text.strip_markdown`, `text.detect_lang`, `text.word_count`
- Produces:
  - `tells.Span(line: int, text: str)`; `tells.Measure(value: float, spans: tuple[Span, ...], where: str = "")`
  - `tells.Tell(name, unit, sided, allow, high, low, measure, describe)`, where `unit` is `"doc"` or `"paragraph"`, `sided` is `"two"` or `"upper"`, `allow` is a gate kind, `high`/`low` are `string.Template` strings (low is `None` for upper-only tells), `measure(raw: str, phrases: list[str]) -> list[Measure]`, `describe` a one-line definition
  - `tells.CATALOG: dict[str, Tell]`
  - `tells.MIN_WORDS = 150`
  - `register.percentile(values: list[float], q: float) -> float` (linear interpolation, q in [0, 1])
  - `register.QUANTILES = (0.005, 0.05, 0.5, 0.9, 0.95, 0.99, 0.995)` and band keys `"p0.5", "p5", "p50", "p90", "p95", "p99", "p99.5"`
  - `register.build(folder: Path, name: str, holdout: float = 0.2, phrases: list[dict] | None = None) -> dict`
  - `register.load(ref: str) -> dict` (a `.json` path, or a name looked up in `./registers/` then the package's `registers/`)
  - `register.split_holdout(files: list[Path], holdout: float) -> tuple[list[Path], list[Path]]`
  - Register JSON: `{"name", "lang", "texts", "holdout", "words", "tells": {name: {band keys..., "n": int}}, "phrases": [...], "false_positive_rate": float | None}`

- [ ] **Step 1: Write the shared fixtures**

`tests/conftest.py`:

```python
import random
from pathlib import Path

import pytest

WORDS = ("alpha beta gamma delta river stone light window table garden "
         "music paper engine market winter summer teacher student city road").split()


def human_text(seed: int, paras: int = 8) -> str:
    """Deterministic English-ish prose: short paragraphs, no slop tells."""
    rng = random.Random(seed)
    out = []
    for _ in range(paras):
        sents = []
        for _ in range(rng.randint(2, 4)):
            n = rng.randint(8, 20)
            body = " ".join(rng.choice(WORDS) for _ in range(n))
            sents.append(f"The {body} is in the house.")
        out.append(" ".join(sents))
    return "\n\n".join(out) + "\n"


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    d = tmp_path / "corpus"
    d.mkdir()
    for i in range(40):
        (d / f"post-{i:02d}.md").write_text(human_text(i))
    return d
```

- [ ] **Step 2: Write the failing tests**

`tests/test_register.py`:

```python
import json

from slopstop import register, tells


def test_percentile_interpolates():
    assert register.percentile([1, 2, 3, 4], 0.5) == 2.5
    assert register.percentile([5], 0.99) == 5


def test_long_paragraph_measures_each_paragraph():
    raw = "One two three.\n\nFour five six seven.\n"
    ms = tells.CATALOG["long-paragraph"].measure(raw, [])
    assert [m.value for m in ms] == [3, 4]
    assert ms[1].spans[0].line == 3 and ms[1].where == "¶2"


def test_build_register_has_bands_for_every_tell(corpus):
    reg = register.build(corpus, "test")
    assert reg["name"] == "test" and reg["lang"] == "en"
    assert reg["texts"] + reg["holdout"] == 40
    band = reg["tells"]["long-paragraph"]
    assert band["p50"] <= band["p90"] <= band["p99"]
    assert set(reg["tells"]) == set(tells.CATALOG)


def test_holdout_split_is_deterministic(corpus):
    files = sorted(corpus.glob("*.md"))
    a = register.split_holdout(files, 0.2)
    b = register.split_holdout(list(reversed(files)), 0.2)
    assert [f.name for f in a[1]] == [f.name for f in b[1]]
    assert 0 < len(a[1]) < len(files)


def test_load_by_path_and_name(corpus, tmp_path, monkeypatch):
    reg = register.build(corpus, "mine")
    regs = tmp_path / "registers"
    regs.mkdir()
    (regs / "mine.json").write_text(json.dumps(reg))
    monkeypatch.chdir(tmp_path)
    assert register.load("mine")["name"] == "mine"
    assert register.load(str(regs / "mine.json"))["name"] == "mine"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_register.py -q`
Expected: FAIL with `ImportError` for `register` / `tells`.

- [ ] **Step 4: Implement `tells.py` with the first tell**

```python
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
```

- [ ] **Step 5: Implement `register.py`**

```python
"""Registers: per-tell percentiles counted over a folder of human-written texts."""
import hashlib
import json
from pathlib import Path

from slopstop import text, tells
from slopstop.cli import UsageError

QUANTILES = (0.005, 0.05, 0.5, 0.9, 0.95, 0.99, 0.995)
KEYS = ("p0.5", "p5", "p50", "p90", "p95", "p99", "p99.5")
PACKAGE_REGISTERS = Path(__file__).parent / "registers"


def percentile(values: list[float], q: float) -> float:
    v = sorted(values)
    if not v:
        return 0.0
    i = q * (len(v) - 1)
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 3)


def split_holdout(files: list[Path], holdout: float) -> tuple[list[Path], list[Path]]:
    """Held-out set chosen by a hash of the file name, so it never depends on order."""
    cut = int(holdout * 100)
    held = [f for f in files if int(hashlib.sha1(f.name.encode()).hexdigest(), 16) % 100 < cut]
    train = [f for f in files if f not in held]
    return sorted(train), sorted(held)


def measure_all(files: list[Path], phrases: list[str]) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {n: [] for n in tells.CATALOG}
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        long_enough = text.word_count(raw) >= tells.MIN_WORDS
        for name, t in tells.CATALOG.items():
            if t.unit == "doc" and not long_enough:
                continue
            values[name].extend(m.value for m in t.measure(raw, phrases))
    return values


def bands(values: dict[str, list[float]]) -> dict[str, dict]:
    return {name: {**{k: percentile(v, q) for k, q in zip(KEYS, QUANTILES)}, "n": len(v)}
            for name, v in values.items()}


def build(folder: Path, name: str, holdout: float = 0.2, phrases: list[dict] | None = None) -> dict:
    files = sorted(p for p in Path(folder).rglob("*.md") if p.is_file())
    if not files:
        raise UsageError(f"no .md files under {folder}")
    train, held = split_holdout(files, holdout)
    plist = [p["gram"] for p in (phrases or [])]
    toks = [t for f in train for t in text.tokenize(text.strip_markdown(f.read_text(errors="replace")))]
    reg = {
        "name": name,
        "lang": text.detect_lang(toks),
        "texts": len(train),
        "holdout": len(held),
        "words": len(toks),
        "tells": bands(measure_all(train, plist)),
        "phrases": phrases or [],
        "false_positive_rate": None,
    }
    if held:
        from slopstop.detect import detect  # imported late: detect depends on register
        flagged = sum(
            any(f["severity"] == "required" for f in detect(h.read_text(errors="replace"), reg, str(h))["findings"])
            for h in held)
        reg["false_positive_rate"] = round(flagged / len(held), 3)
    return reg


def load(ref: str) -> dict:
    candidates = [Path(ref)] if ref.endswith(".json") else [
        Path("registers") / f"{ref}.json", PACKAGE_REGISTERS / f"{ref}.json"]
    for c in candidates:
        if c.is_file():
            try:
                return json.loads(c.read_text())
            except json.JSONDecodeError as e:
                raise UsageError(f"register {c} is not valid JSON: {e}") from e
    raise UsageError(f"no register {ref!r} (looked in ./registers and the package)")
```

`build` imports `detect`, which Task 3 creates. Until then, guard the FP block so Task 2's tests pass: write it as above and create a minimal `src/slopstop/detect.py` now:

```python
"""Findings against a register. Filled in by Task 3."""


def detect(raw: str, reg: dict, file: str) -> dict:
    return {"findings": []}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_register.py -q`
Expected: 5 passed.

- [ ] **Step 7: Commit**

```bash
git add src/slopstop/tells.py src/slopstop/register.py src/slopstop/detect.py tests/conftest.py tests/test_register.py
git commit -m "feat: tell catalog with long-paragraph tell, register building"
```

---

### Task 3: `detect` and `profile` end to end

The thinnest usable slice: `slopstop profile <folder> --name x` then `slopstop detect post.md --register x` prints findings with instructions.

**Files:**
- Modify: `src/slopstop/detect.py`, `src/slopstop/cli.py`
- Create: `tests/test_detect.py`

**Interfaces:**
- Consumes: `register.build`, `register.load`, `tells.CATALOG`, `tells.MIN_WORDS`, `text.word_count`, `text.tokenize`, `text.strip_markdown`, `text.detect_lang`
- Produces:
  - `detect.severity(tell: Tell, value: float, band: dict) -> str | None` (`"required"`, `"optional"`, `None`)
  - `detect.orig_path(file: str) -> str` (`post.md` → `post.orig.md`)
  - `detect.detect(raw: str, reg: dict, file: str) -> dict` with keys `file, words, register, false_positive_rate, notes: list[str], findings: list[dict]`; each finding has `tell, severity, value, where, band (dict), spans (list of {line, text}), instruction, check`
  - `detect.render_text(report: dict) -> str`
  - CLI: `slopstop profile FOLDER --name NAME [--out PATH] [--model FOLDER ...] [--holdout 0.2]` writes JSON (default `registers/NAME.json`), prints a one-line summary; `slopstop detect FILE --register REF [--json]` exits 1 if any finding is required, else 0.

- [ ] **Step 1: Write the failing tests**

`tests/test_detect.py`:

```python
import json

import pytest

from slopstop import cli, detect, register, tells

BAND = {"p0.5": 1.0, "p5": 2.0, "p50": 5.0, "p90": 8.0, "p95": 9.0, "p99": 10.0, "p99.5": 11.0}


def tell(sided):
    return tells.Tell("t", "doc", sided, "span", "high", "low", lambda r, p: [])


@pytest.mark.parametrize("sided,value,expected", [
    ("upper", 10.0, "optional"), ("upper", 8.0, None), ("upper", 8.5, "optional"), ("upper", 10.5, "required"),
    ("two", 11.0, None), ("two", 9.5, "optional"), ("two", 11.5, "required"),
    ("two", 1.5, "optional"), ("two", 0.5, "required"), ("two", 5.0, None),
])
def test_severity_bands(sided, value, expected):
    assert detect.severity(tell(sided), value, BAND) == expected


def test_orig_path():
    assert detect.orig_path("dir/post.md") == "dir/post.orig.md"


def wall(words: int) -> str:
    return "The " + " ".join(["stone"] * (words - 1)) + ".\n"


def test_wall_of_text_is_required_with_instruction(corpus):
    reg = register.build(corpus, "t")
    rep = detect.detect(wall(600), reg, "post.md")
    f = [x for x in rep["findings"] if x["tell"] == "long-paragraph"][0]
    assert f["severity"] == "required"
    assert "Insert paragraph breaks only" in f["instruction"]
    assert f["check"] == "slopstop gate post.orig.md post.md --allow breaks"
    assert f["spans"][0]["line"] == 1


def test_short_text_skips_rate_tells_with_note(corpus):
    reg = register.build(corpus, "t")
    rep = detect.detect("A short note of a few words.\n", reg, "n.md")
    assert any("150" in n for n in rep["notes"])
    assert all(tells.CATALOG[f["tell"]].unit == "paragraph" for f in rep["findings"])


def test_language_mismatch_is_noted(corpus):
    reg = register.build(corpus, "t")
    es = "El perro de la casa que es muy grande y la mesa de la cocina. " * 30
    rep = detect.detect(es, reg, "es.md")
    assert any("language" in n for n in rep["notes"])


def test_cli_profile_then_detect(corpus, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["profile", str(corpus), "--name", "mine"]) == 0
    assert (tmp_path / "registers" / "mine.json").exists()
    post = tmp_path / "post.md"
    post.write_text(wall(600))
    assert cli.main(["detect", str(post), "--register", "mine"]) == 1
    out = capsys.readouterr().out
    assert "required" in out and "cp " in out
    assert cli.main(["detect", str(post), "--register", "mine", "--json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert "long-paragraph" in {f["tell"] for f in data["findings"]}


def test_cli_detect_missing_file_exits_2(tmp_path, capsys):
    assert cli.main(["detect", str(tmp_path / "nope.md"), "--register", "x"]) == 2
    assert "nope.md" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_detect.py -q`
Expected: FAIL (`severity` and `orig_path` missing, CLI has no subcommands).

- [ ] **Step 3: Implement `detect.py`**

```python
"""Findings against a register, each with an instruction for the agent and the check that verifies it."""
import json
from pathlib import Path
from string import Template

from slopstop import tells, text

TWO = (("p0.5", "p99.5"), ("p5", "p95"))


def severity(tell: tells.Tell, value: float, band: dict) -> str | None:
    if tell.sided == "upper":
        if value > band["p99"]:
            return "required"
        return "optional" if value > band["p90"] else None
    (rlo, rhi), (olo, ohi) = TWO
    if value > band[rhi] or value < band[rlo]:
        return "required"
    if value > band[ohi] or value < band[olo]:
        return "optional"
    return None


def orig_path(file: str) -> str:
    p = Path(file)
    return str(p.with_name(f"{p.stem}.orig{p.suffix}"))


def _lines(spans) -> str:
    return ",".join(str(s.line) for s in spans)


def _finding(t: tells.Tell, m: tells.Measure, sev: str, band: dict, file: str) -> dict:
    lo_key, hi_key = (("p0.5", "p99.5") if sev == "required" else ("p5", "p95"))
    high = t.sided == "upper" or m.value > band[hi_key]
    tmpl = t.high if high or t.low is None else t.low
    lines = _lines(m.spans)
    instruction = Template(tmpl).safe_substitute(
        value=round(m.value, 2), where=m.where or "the text", lines=lines or "throughout",
        lo=band[lo_key], hi=band[hi_key], **{k.replace(".", "_"): v for k, v in band.items()})
    check = f"slopstop gate {orig_path(file)} {file} --allow {t.allow}"
    if t.allow == "span" and lines:
        check += f" --lines {lines}"
    return {
        "tell": t.name, "severity": sev, "value": round(m.value, 2), "where": m.where,
        "band": {k: band[k] for k in band if k != "n"},
        "spans": [{"line": s.line, "text": s.text} for s in m.spans],
        "instruction": instruction, "check": check,
    }


def detect(raw: str, reg: dict, file: str) -> dict:
    words = text.word_count(raw)
    notes = []
    lang = text.detect_lang(text.tokenize(text.strip_markdown(raw)))
    if words >= tells.MIN_WORDS and lang != reg.get("lang", "en"):
        notes.append(f"The text looks {lang} but register {reg['name']} is {reg.get('lang')}; "
                     "the language may decide these findings more than the habits do.")
    if words < tells.MIN_WORDS:
        notes.append(f"{words} words is under the {tells.MIN_WORDS}-word minimum for rate tells; "
                     "only per-paragraph tells ran.")
    phrases = [p["gram"] for p in reg.get("phrases", [])]
    findings = []
    for name, t in tells.CATALOG.items():
        band = reg["tells"].get(name)
        if not band or not band.get("n") or (t.unit == "doc" and words < tells.MIN_WORDS):
            continue
        for m in t.measure(raw, phrases):
            sev = severity(t, m.value, band)
            if sev:
                findings.append(_finding(t, m, sev, band, file))
    findings.sort(key=lambda f: (f["severity"] != "required", f["spans"][0]["line"] if f["spans"] else 0))
    return {"file": file, "words": words, "register": reg["name"],
            "false_positive_rate": reg.get("false_positive_rate"), "notes": notes, "findings": findings}


def render_text(rep: dict) -> str:
    out = [f"{rep['file']}: {rep['words']} words against register {rep['register']}"]
    if rep["false_positive_rate"] is not None:
        out.append(f"(this register flags {rep['false_positive_rate']:.0%} of its own held-out human "
                   "texts with a required finding)")
    out += rep["notes"]
    if not rep["findings"]:
        out.append("No findings.")
        return "\n".join(out) + "\n"
    out.append(f"Before fixing, keep the original: cp {rep['file']} {orig_path(rep['file'])}")
    for f in rep["findings"]:
        where = f" {f['where']}" if f["where"] else ""
        out.append(f"\n{f['severity']:<9}{where}  {f['tell']}  {f['value']}")
        out.append(f"  {f['instruction']}")
        out.append(f"  Check: {f['check']}")
    req = sum(f["severity"] == "required" for f in rep["findings"])
    out.append(f"\n{req} required, {len(rep['findings']) - req} optional.")
    return "\n".join(out) + "\n"


def to_json(rep: dict) -> str:
    return json.dumps(rep, indent=1, ensure_ascii=False)
```

- [ ] **Step 4: Wire `profile` and `detect` into `cli.py`**

Add helpers and subparsers. Replace `build_parser` and add command functions:

```python
import json
from pathlib import Path


def read(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise UsageError(f"no such file: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


def cmd_profile(args) -> int:
    from slopstop import phrases, register
    folder = Path(args.folder)
    if not folder.is_dir():
        raise UsageError(f"no such folder: {args.folder}")
    plist = phrases.build(folder, [Path(m) for m in args.model]) if args.model else None
    reg = register.build(folder, args.name, args.holdout, plist)
    out = Path(args.out or f"registers/{args.name}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    fp = reg["false_positive_rate"]
    print(f"{out}: {reg['texts']} texts, {reg['words']} words, {len(reg['phrases'])} phrases, "
          f"false-positive rate {fp if fp is not None else 'n/a'} on {reg['holdout']} held-out texts")
    return 0


def cmd_detect(args) -> int:
    from slopstop import detect, register
    raw = read(args.file)
    rep = detect.detect(raw, register.load(args.register), args.file)
    print(detect.to_json(rep) if args.json else detect.render_text(rep), end="" if not args.json else "\n")
    return 1 if any(f["severity"] == "required" for f in rep["findings"]) else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopstop", description="Mechanical AI-slop detection with instructions for the agent that fixes it.")
    p.add_argument("--version", action="version", version=f"slopstop {__version__}")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("profile", help="count a register from a folder of human-written texts")
    s.add_argument("folder")
    s.add_argument("--name", required=True)
    s.add_argument("--out")
    s.add_argument("--model", action="append", default=[], help="folder of model text on the same topics, for the phrase list")
    s.add_argument("--holdout", type=float, default=0.2)
    s.set_defaults(func=cmd_profile)

    s = sub.add_parser("detect", help="findings and fix instructions for one text")
    s.add_argument("file")
    s.add_argument("--register", required=True)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_detect)
    return p
```

`cmd_profile` imports `phrases`, created in Task 5. Until then, create `src/slopstop/phrases.py` with:

```python
"""Over-represented phrases. Filled in by Task 5."""


def build(human, models):
    return []
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_detect.py tests/test_register.py -q`
Expected: all pass. A value on a boundary is inside: 10.0 equals p99, so it is optional, not required.

- [ ] **Step 6: Break it on purpose**

Change `value > band["p99"]` to `value >= band["p0.5"]` in `severity`, run `uv run pytest tests/test_detect.py -q`, confirm failures, restore.

- [ ] **Step 7: Commit**

```bash
git add src/slopstop/detect.py src/slopstop/cli.py src/slopstop/phrases.py tests/test_detect.py
git commit -m "feat: detect and profile commands with required/optional findings"
```

---

### Task 4: The rest of the mechanical catalog

**Files:**
- Modify: `src/slopstop/tells.py`
- Create: `tests/test_tells.py`

**Interfaces:**
- Consumes: `text.*`, `tells.Tell`, `tells.Measure`, `tells.Span`
- Produces: catalog entries named exactly `em-dash`, `mid-sentence-colon`, `corrective`, `metaphor-nouns`, `headings`, `bold`, `sentence-length`, `sentence-spread`, `repeated-openers`, `triplets`, `summary-closers`, `signposts`, `overused-phrases`. All are `unit="doc"`, `sided="two"`. Allow kinds: `punctuation` for em-dash and mid-sentence-colon; `span` for the rest. Each measure returns a single `Measure` whose value is a rate per 1000 words (percent of sentences for `repeated-openers`, words for `sentence-length` and `sentence-spread`).

- [ ] **Step 1: Write the failing tests**

`tests/test_tells.py`:

```python
import pytest

from slopstop import tells

FILLER = " ".join(["The river runs by the stone house in the morning light."] * 20)


def one(name, raw, phrases=()):
    [m] = tells.CATALOG[name].measure(raw, list(phrases))
    return m


def per_k(count, raw):
    from slopstop import text
    return round(count * 1000 / text.word_count(raw), 2)


def test_em_dash_rate_and_lines():
    raw = FILLER + "\n\nA thought — and another — here.\n"
    m = one("em-dash", raw)
    assert m.value == per_k(2, raw) and [s.line for s in m.spans] == [3]


def test_em_dash_ignores_code():
    raw = FILLER + "\n\n```\na — b\n```\n"
    assert one("em-dash", raw).value == 0


def test_corrective_counts_curly_apostrophe():
    raw = FILLER + "\n\nIt’s not a bug. It's not a feature. That's the point.\n"
    assert one("corrective", raw).value == per_k(3, raw)


def test_mid_sentence_colon_only_lowercase_continuation():
    raw = FILLER + "\n\nOne thing: it works. A list:\n\n- item\n"
    assert one("mid-sentence-colon", raw).value == per_k(1, raw)


def test_metaphor_nouns():
    raw = FILLER + "\n\nThe substrate is a harness on a surface.\n"
    assert one("metaphor-nouns", raw).value == per_k(3, raw)


def test_headings_and_bold():
    raw = "# Title\n\n## Part\n\n" + FILLER + "\n\nSome **bold** and **more**.\n"
    assert one("headings", raw).value == per_k(2, raw)
    assert one("bold", raw).value == per_k(2, raw)


def test_sentence_length_and_spread():
    raw = "One two three. One two three four five six seven.\n"
    assert one("sentence-length", raw).value == 5.0
    assert one("sentence-spread", raw).value == 2.0


def test_repeated_openers_percent():
    raw = "The cat sat. The dog ran. A bird flew. The end came.\n"
    assert one("repeated-openers", raw).value == 25.0  # 1 of 4 sentences repeats its predecessor's opener


def test_triplets():
    raw = FILLER + "\n\nWe want speed, clarity, and joy.\n"
    assert one("triplets", raw).value == per_k(1, raw)


def test_summary_closers_and_signposts():
    raw = FILLER + "\n\nWe built it. In short, it works.\n\nLet's look at it. Here's why.\n"
    assert one("summary-closers", raw).value == per_k(1, raw)
    assert one("signposts", raw).value == per_k(2, raw)


def test_overused_phrases_uses_register_list():
    raw = FILLER + "\n\nAt its core the idea is simple. At its core it works.\n"
    assert one("overused-phrases", raw, ["at its core"]).value == per_k(2, raw)
    assert one("overused-phrases", raw, []).value == 0


@pytest.mark.parametrize("name", list(tells.CATALOG))
def test_every_tell_has_instructions_and_description(name):
    t = tells.CATALOG[name]
    assert t.high and t.describe
    assert (t.low is None) == (t.sided == "upper")
    assert t.allow in {"breaks", "punctuation", "span", "rewrite"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tells.py -q`
Expected: FAIL with `KeyError: 'em-dash'`.

- [ ] **Step 3: Implement the measures in `tells.py`**

Append after the long-paragraph tell:

```python
import re
import statistics

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


def _phrase_re(phrase: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + r"\W+".join(map(re.escape, phrase.split())) + r"(?!\w)", re.I)


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
    start = text.FRONTMATTER.match(raw)
    skip = start.group(0).count("\n") if start else 0
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


def _em_dash(raw, phrases):
    return [_count_lines(raw, re.compile("\u2014"))]


def _colon(raw, phrases):
    return [_count_lines(raw, COLON)]


def _list_measure(words):
    pat = re.compile("|".join(_phrase_re(w).pattern for w in words), re.I) if words else re.compile(r"(?!x)x")
    return lambda raw, phrases: [_count_lines(raw, pat)]


def _headings(raw, phrases):
    return [_count_lines(raw, HEADING, [(n, l) for n, l in _all_lines(raw)])]


def _bold(raw, phrases):
    return [_count_lines(raw, BOLD, _all_lines(raw))]


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


def _sentence_pattern(pattern, last_in_paragraph=False):
    def measure(raw, phrases):
        spans = []
        for p in text.paragraphs(raw):
            sents = text.split_sentences(text.strip_markdown(p.text))
            pick = sents[-1:] if last_in_paragraph else sents
            spans += [Span(p.line, s[:80]) for s in pick if pattern.match(text.normalize(s))]
        return [Measure(_rate(raw, len(spans)), tuple(spans))]
    return measure


def _triplets(raw, phrases):
    return [_count_lines(raw, TRIPLET)]


def _overused(raw, phrases):
    return _list_measure(phrases)(raw, phrases)


for name, allow, fn, what, high, low in [
    ("em-dash", "punctuation", _em_dash, "em dashes per 1000 words",
     "Replace the em dashes on lines $lines with periods or commas ($value per 1000 words; register $lo to $hi).",
     "This text has $value em dashes per 1000 words, below the register's $lo to $hi. Nothing to fix unless the author wants more."),
    ("mid-sentence-colon", "punctuation", _colon, "colons joining two clauses, per 1000 words",
     "Rewrite the colons on lines $lines as two sentences or a comma ($value per 1000 words; register $lo to $hi).",
     "This text has $value mid-sentence colons per 1000 words, below the register's $lo to $hi. Nothing to fix."),
    ("corrective", "span", _list_measure(CORRECTIVE), "corrective constructions (\"it's not X, it's Y\") per 1000 words",
     "On lines $lines, say what the thing is without first denying a reading nobody offered ($value per 1000 words; register $lo to $hi).",
     "This text has $value correctives per 1000 words, below the register's $lo to $hi. Nothing to fix."),
    ("metaphor-nouns", "span", _list_measure(METAPHOR_NOUNS), "abstract metaphor nouns (substrate, harness, surface) per 1000 words",
     "On lines $lines, replace the metaphor noun with the concrete word ($value per 1000 words; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
    ("headings", "span", _headings, "headings per 1000 words",
     "Merge or remove headings on lines $lines; the register uses $lo to $hi per 1000 words and this text $value.",
     "This text has fewer headings than the register ($value against $lo to $hi). Add one only where a reader needs a landmark."),
    ("bold", "span", _bold, "bold spans per 1000 words",
     "Remove the bold on lines $lines except where a reader must not miss the term ($value per 1000 words; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
    ("sentence-length", "span", _sentence_length, "mean words per sentence",
     "Sentences average $value words against the register's $lo to $hi. Split the longest ones, on lines $lines.",
     "Sentences average $value words against the register's $lo to $hi. Join short sentences that carry one thought."),
    ("sentence-spread", "span", _sentence_spread, "standard deviation of sentence length in words",
     "Sentence length varies more than the register ($value against $lo to $hi). Even out the extremes.",
     "Sentence lengths are too uniform ($value against the register's $lo to $hi). Vary them: some short, some long."),
    ("repeated-openers", "span", _repeated_openers, "percent of sentences opening with the previous sentence's first word",
     "Vary the openings of the sentences on lines $lines ($value% repeat; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
    ("triplets", "span", _triplets, "lists of three (\"X, Y, and Z\") per 1000 words",
     "On lines $lines, use the natural number of items instead of three ($value per 1000 words; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
    ("summary-closers", "span", _sentence_pattern(CLOSERS, last_in_paragraph=True), "paragraphs ending in a summary phrase, per 1000 words",
     "Cut the summary sentences that close the paragraphs at lines $lines ($value per 1000 words; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
    ("signposts", "span", _sentence_pattern(SIGNPOSTS), "signposting openers (\"Let's\", \"Here's\") per 1000 words",
     "Remove the signposting at the start of the sentences on lines $lines ($value per 1000 words; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
    ("overused-phrases", "span", _overused, "phrases model text overuses against this register, per 1000 words",
     "Reword the overused phrases on lines $lines ($value per 1000 words; register $lo to $hi).",
     "Below the register's $lo to $hi. Nothing to fix."),
]:
    _add(Tell(name, "doc", "two", allow, high, low, fn, what))
```

Move the `import re` and `import statistics` lines to the top of the module with the other imports.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tells.py -q`
Expected: all pass. If `test_repeated_openers_percent` gives a different value, check that `_sentences_with_lines` splits "The cat sat. The dog ran. A bird flew. The end came." into four sentences; "The dog ran." repeats "the" from "The cat sat.", so 1 of 4.

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: all pass (registers now carry bands for 14 tells).

- [ ] **Step 6: Commit**

```bash
git add src/slopstop/tells.py tests/test_tells.py
git commit -m "feat: mechanical tell catalog (punctuation, correctives, rhythm, structure, phrases)"
```

---

### Task 5: Over-represented phrases in `profile`

**Files:**
- Modify: `src/slopstop/phrases.py`
- Create: `tests/test_phrases.py`

**Interfaces:**
- Consumes: `text.tokenize`, `text.strip_markdown`, `text.split_sentences`, `text.WORD`, `text.normalize`
- Produces: `phrases.build(human: Path, models: list[Path], max_n: int = 3, min_count: int = 3, min_docs: int = 2, min_ratio: float = 5.0, top: int = 200) -> list[dict]`, each `{"gram": str, "ratio": float, "model_pm": float, "human_pm": float}`, sorted by ratio descending. Excludes n-grams containing a proper noun (capitalized at least 60% of the time away from a sentence start in either corpus) or a word the human corpus uses fewer than 3 times (topic words). Excludes an n-gram when a longer kept n-gram containing it explains at least 80% of its occurrences.

- [ ] **Step 1: Write the failing test**

`tests/test_phrases.py`:

```python
from pathlib import Path

from slopstop import phrases

HUMAN = "The house is quiet. We read at night. The garden is green and the road is long. " * 30
MODEL = ("At its core the house is quiet. At its core we read at night. "
         "Paris is lovely. The garden is green. ") * 30


def write(d: Path, body: str, n: int):
    d.mkdir()
    for i in range(n):
        (d / f"{i}.md").write_text(body)
    return d


def test_overused_phrase_found_topic_and_names_excluded(tmp_path):
    h = write(tmp_path / "h", HUMAN + " core at its own pace. ", 4)
    m = write(tmp_path / "m", MODEL, 4)
    grams = [p["gram"] for p in phrases.build(h, [m])]
    assert "at its core" in grams
    assert not any("paris" in g for g in grams)       # proper noun
    assert "at its" not in grams                       # explained by the longer phrase
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_phrases.py -q`
Expected: FAIL (`build` returns `[]`).

- [ ] **Step 3: Implement `phrases.py`**

```python
"""Phrases model text overuses against a register's human texts.

A port of bin/slopcheck's profile (Antislop method, arXiv:2510.15061), reduced to what
detect needs: n-gram rates per million in both corpora, ranked by smoothed ratio.
"""
from collections import Counter
from pathlib import Path

from slopstop import text

SMOOTH_PM = 1.0


def _corpus(folders: list[Path], max_n: int):
    counts, docs, cap, tok = Counter(), Counter(), Counter(), Counter()
    total = 0
    for folder in folders:
        for f in sorted(Path(folder).rglob("*.md")):
            prose = text.strip_markdown(f.read_text(encoding="utf-8", errors="replace"))
            seen = set()
            for sent in text.split_sentences(prose):
                toks = text.tokenize(sent)
                surface = text.WORD.findall(text.normalize(sent))
                for i, t in enumerate(toks[1:], 1):
                    tok[t] += 1
                    if i < len(surface) and surface[i][:1].isupper():
                        cap[t] += 1
                total += len(toks)
                for n in range(1, max_n + 1):
                    for i in range(len(toks) - n + 1):
                        g = " ".join(toks[i:i + n])
                        counts[g] += 1
                        seen.add(g)
            docs.update(seen)
    proper = {t for t, c in tok.items() if c >= 3 and cap[t] / c >= 0.6}
    return counts, docs, proper, max(total, 1)


def build(human: Path, models: list[Path], max_n: int = 3, min_count: int = 3,
          min_docs: int = 2, min_ratio: float = 5.0, top: int = 200) -> list[dict]:
    hc, _, hp, ht = _corpus([human], max_n)
    mc, md, mp, mt = _corpus(models, max_n)
    proper = hp | mp
    kept = []
    for g, c in mc.items():
        if c < min_count or md[g] < min_docs:
            continue
        toks = g.split()
        if any(t in proper for t in toks) or any(hc.get(t, 0) < 3 for t in toks):
            continue
        m_pm, h_pm = c / mt * 1e6, hc.get(g, 0) / ht * 1e6
        ratio = (m_pm + SMOOTH_PM) / (h_pm + SMOOTH_PM)
        if ratio >= min_ratio:
            kept.append({"gram": g, "ratio": round(ratio, 2), "model_pm": round(m_pm, 2),
                         "human_pm": round(h_pm, 2), "_count": c})
    longer: Counter = Counter()
    for e in kept:
        toks = e["gram"].split()
        if len(toks) > 1:
            longer[" ".join(toks[:-1])] += e["_count"]
            longer[" ".join(toks[1:])] += e["_count"]
    out = [e for e in kept if longer[e["gram"]] < 0.8 * e["_count"]]
    out.sort(key=lambda e: (-e["ratio"], e["gram"]))
    for e in out:
        del e["_count"]
    return out[:top]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_phrases.py -q`
Expected: PASS. If "at its core" is excluded as a topic word, check that the human fixture includes "core", "at" and "its" at least 3 times each (it repeats 4 files × 1 = 4 times).

- [ ] **Step 5: Commit**

```bash
git add src/slopstop/phrases.py tests/test_phrases.py
git commit -m "feat: over-represented phrase list in profile (port of slopcheck)"
```

---

### Task 6: `gate` structural checks and input checks

**Files:**
- Create: `src/slopstop/gate.py`, `tests/test_gate.py`
- Modify: `src/slopstop/cli.py`

**Interfaces:**
- Consumes: `text.FENCE`, `text.fences_balanced`, `text.tokenize`, `text.FENCED`
- Produces:
  - `gate.Result(failures: list[str], warnings: list[str])` dataclass with `ok` property
  - `gate.check_input(raw: str, transcript: bool = False) -> Result`
  - `gate.check_output(src: str, out: str, allow: str = "rewrite", ratio: tuple[float, float] = (0.75, 1.35), lines: list[int] | None = None, budget: float = 0.15, split: list[dict] | None = None) -> Result`
  - `gate.PLACEHOLDER = re.compile(r"\[CODE-\d+\]")`
  - CLI: `slopstop gate SOURCE [OUTPUT] [--allow KIND] [--ratio LO:HI] [--lines 1,2] [--budget F] [--split JSON] [--transcript]`; prints `PASS` or `FAIL` with one reason per line, warnings prefixed `warning:`; exit 0 on pass, 1 on fail.

- [ ] **Step 1: Write the failing tests**

`tests/test_gate.py`:

```python
from conftest import human_text

from slopstop import cli, gate

SRC = human_text(1, paras=2)  # varied words, so no 30-word run repeats inside the source


def test_unchanged_output_passes():
    assert gate.check_output(SRC, SRC).ok


def test_empty_output_fails_with_reason():
    r = gate.check_output(SRC, "")
    assert not r.ok and "empty" in r.failures[0]


def test_duplicate_block_fails():
    r = gate.check_output(SRC, SRC + "\n" + SRC, ratio=(0.1, 9))
    assert any("repeated" in f for f in r.failures)


def test_unbalanced_fence_fails_only_when_source_balanced():
    assert not gate.check_output(SRC, SRC + "\n```\ncode\n").ok
    bad_src = SRC + "\n```\ncode\n"
    assert gate.check_output(bad_src, bad_src).ok


def test_meta_text_on_first_line_fails_unless_in_source():
    out = "Here is the rewritten essay:\n\n" + SRC
    assert any("addressed to the user" in f for f in gate.check_output(SRC, out).failures)
    src2 = "Here is the resolution I find plausible.\n\n" + SRC
    assert gate.check_output(src2, src2).ok


def test_length_ratio_band():
    r = gate.check_output(SRC, SRC.split("\n\n")[0] + "\n")
    assert any("length ratio" in f for f in r.failures)


def test_ends_mid_sentence_relative_to_source():
    cut = SRC.rstrip()[:-12]
    assert any("mid-sentence" in f for f in gate.check_output(SRC, cut, ratio=(0.1, 9)).failures)
    assert gate.check_output(cut, cut).ok


def test_placeholders_must_survive_once():
    src = SRC + "\n[CODE-1]\n"
    assert any("[CODE-1]" in f for f in gate.check_output(src, SRC).failures)
    assert any("[CODE-1]" in f for f in gate.check_output(src, src + "\n[CODE-1]\n", ratio=(0.1, 9)).failures)


def test_check_input_truncation():
    assert not gate.check_input("A sentence that stops in the").ok
    r = gate.check_input("speech has no final period", transcript=True)
    assert r.ok and r.warnings


def test_cli_gate_pass_fail_and_missing(tmp_path, capsys):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text(SRC)
    b.write_text("")
    assert cli.main(["gate", str(a), str(a)]) == 0
    assert cli.main(["gate", str(a), str(b)]) == 1
    assert "FAIL" in capsys.readouterr().out
    assert cli.main(["gate", str(tmp_path / "x.md")]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gate.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `gate.py` (structural part)**

```python
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
END_OK = re.compile(r"[.!?\u2026:\"\u201d\u2019)\]*_]$")
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
```

- [ ] **Step 4: Wire the CLI**

In `cli.py` add:

```python
def cmd_gate(args) -> int:
    from slopstop import gate
    src = read(args.source)
    split = None
    if args.split:
        try:
            split = json.loads(read(args.split))["segments"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise UsageError(f"{args.split} is not a split file with a 'segments' list: {e}") from e
    if args.output is None:
        r = gate.check_split(src, split) if split is not None else gate.check_input(src, args.transcript)
    else:
        lo, _, hi = args.ratio.partition(":")
        try:
            ratio = (float(lo), float(hi))
            lines = [int(x) for x in args.lines.split(",")] if args.lines else None
        except ValueError as e:
            raise UsageError(f"bad --ratio or --lines: {e}") from e
        r = gate.check_output(src, read(args.output), args.allow, ratio, lines, args.budget, split)
    for w in r.warnings:
        print(f"warning: {w}")
    print("PASS" if r.ok else "FAIL")
    for f in r.failures:
        print(f"  {f}")
    return 0 if r.ok else 1
```

and in `build_parser`:

```python
    s = sub.add_parser("gate", help="check a model's output against its source, or an input alone")
    s.add_argument("source")
    s.add_argument("output", nargs="?")
    s.add_argument("--allow", default="rewrite", choices=["rewrite", "breaks", "punctuation", "span", "polish"])
    s.add_argument("--ratio", default="0.75:1.35", help="length band for --allow rewrite, LO:HI")
    s.add_argument("--lines", help="for --allow span: comma-separated source lines that may change")
    s.add_argument("--budget", type=float, default=0.15, help="for --allow polish: share of words that may change")
    s.add_argument("--split", help="split JSON from 'instruct split'")
    s.add_argument("--transcript", action="store_true", help="input is a transcript: truncation only warns")
    s.set_defaults(func=cmd_gate)
```

`check_split` is added in Task 8; until then add a stub to `gate.py`:

```python
def check_split(transcript: str, segments: list[dict]) -> Result:
    return Result()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_gate.py -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/slopstop/gate.py src/slopstop/cli.py tests/test_gate.py
git commit -m "feat: gate structural checks and input truncation check"
```

---

### Task 7: `gate --allow` kinds

**Files:**
- Modify: `src/slopstop/gate.py`
- Create: `tests/test_gate_allow.py`

**Interfaces:**
- Produces: `check_output` enforces `breaks` (whitespace-split token sequence identical), `punctuation` (lowercase word sequence identical), `span` (no change outside `lines`, 1-based source line numbers; insertions only adjacent to an allowed line), `polish` (share of changed words ≤ `budget`), `rewrite` (length band, Task 6).

- [ ] **Step 1: Write the failing tests**

`tests/test_gate_allow.py`:

```python
from slopstop import gate

SRC = "One idea here. Another idea there, and a third.\nSecond line stays.\nThird line too.\n"


def test_every_kind_passes_unchanged():
    for kind in ("rewrite", "breaks", "punctuation", "span", "polish"):
        assert gate.check_output(SRC, SRC, kind, lines=[1]).ok, kind


def test_breaks_only():
    ok = "One idea here.\n\nAnother idea there, and a third.\nSecond line stays.\nThird line too.\n"
    assert gate.check_output(SRC, ok, "breaks").ok
    bad = ok.replace("Another", "A different")
    assert any("breaks" in f for f in gate.check_output(SRC, bad, "breaks").failures)


def test_punctuation_only():
    ok = SRC.replace(", and", ". And")
    assert gate.check_output(SRC, ok, "punctuation").ok
    bad = SRC.replace("idea there", "thought there")
    assert any("punctuation" in f for f in gate.check_output(SRC, bad, "punctuation").failures)


def test_span_only_listed_lines():
    ok = SRC.replace("Third line too.", "Third line, rewritten.")
    assert gate.check_output(SRC, ok, "span", lines=[3]).ok
    r = gate.check_output(SRC, ok, "span", lines=[1])
    assert any("line 3" in f for f in r.failures)


def test_polish_budget():
    small = SRC.replace("idea there", "idea over there")
    assert gate.check_output(SRC, small, "polish", budget=0.15).ok
    big = "Totally new words replace everything here now.\nSecond line stays.\nThird line too.\n"
    assert any("budget" in f for f in gate.check_output(SRC, big, "polish", budget=0.15).failures)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gate_allow.py -q`
Expected: FAIL on breaks, punctuation, span and polish.

- [ ] **Step 3: Implement the kinds** (append to `check_output` before `return r`)

```python
    if allow == "breaks" and src.split() != out.split():
        r.failures.append("--allow breaks: words or punctuation changed; only paragraph breaks may change")
    elif allow == "punctuation" and _words(src) != _words(out):
        r.failures.append("--allow punctuation: words changed; only punctuation may change")
    elif allow == "span":
        allowed = set(lines or [])
        a, b = src.splitlines(), out.splitlines()
        for op, i1, i2, _, _ in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            touched = set(range(i1 + 1, i2 + 1)) or {i1, i1 + 1}
            outside = sorted(touched - allowed)
            if outside and not (op == "insert" and touched & allowed):
                r.failures.append(f"--allow span: line {outside[0]} changed but only lines "
                                  f"{','.join(map(str, sorted(allowed))) or 'none'} may")
                break
    elif allow == "polish":
        a, b = _words(src), _words(out)
        changed = 1 - difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()
        if changed > budget:
            r.failures.append(f"--allow polish: {changed:.0%} of words changed, over the {budget:.0%} budget")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_gate.py tests/test_gate_allow.py -q`
Expected: all pass.

- [ ] **Step 5: Break it on purpose**

Replace `src.split() != out.split()` with `False`, run `uv run pytest tests/test_gate_allow.py -q`, confirm `test_breaks_only` fails, restore.

- [ ] **Step 6: Commit**

```bash
git add src/slopstop/gate.py tests/test_gate_allow.py
git commit -m "feat: gate --allow kinds verify what a fix may change"
```

---

### Task 8: `gate` with a dictation split

**Files:**
- Modify: `src/slopstop/gate.py`
- Create: `tests/test_gate_split.py`

**Interfaces:**
- Consumes: split JSON `{"segments": [{"kind": "content" | "directive" | "request", "text": str}]}`
- Produces:
  - `gate.overlap(span: str, hay: str, n: int = 8) -> float` share of the span's n-word windows found verbatim in `hay`
  - `gate.check_split(transcript: str, segments: list[dict]) -> Result`: fails on an unknown kind, on a passage that is not verbatim (overlap < 0.9 at n=5), or on coverage < 0.98 (share of the transcript's 5-word windows found in the joined passages)
  - `check_output(..., split=...)` additionally fails when a request of 6+ words leaks into the output (overlap ≥ 0.3)

- [ ] **Step 1: Write the failing tests**

`tests/test_gate_split.py`:

```python
from slopstop import gate

T = ("I want to argue that slop is a human failure and not a machine one. "
     "First transcribe this and then let's discuss how we improve this blog post. "
     "Keep it short. Nobody is behind the model, there is nothing it is like to be it.")
SEGS = [
    {"kind": "content", "text": "I want to argue that slop is a human failure and not a machine one."},
    {"kind": "request", "text": "First transcribe this and then let's discuss how we improve this blog post."},
    {"kind": "directive", "text": "Keep it short."},
    {"kind": "content", "text": "Nobody is behind the model, there is nothing it is like to be it."},
]


def test_good_split_passes():
    assert gate.check_split(T, SEGS).ok


def test_missing_passage_fails_coverage():
    r = gate.check_split(T, SEGS[:1] + SEGS[2:])
    assert any("coverage" in f for f in r.failures)


def test_paraphrased_passage_fails_verbatim():
    segs = [dict(s) for s in SEGS]
    segs[0]["text"] = "The author argues slop comes from people rather than machines entirely."
    assert any("verbatim" in f for f in gate.check_split(T, segs).failures)


def test_unknown_kind_fails():
    segs = [dict(s) for s in SEGS]
    segs[2]["kind"] = "note"
    assert any("kind" in f for f in gate.check_split(T, segs).failures)


def test_leaked_request_fails_output():
    out = ("Slop is a human failure, not a machine one. Nobody is behind the model. " * 2 +
           "First transcribe this and then let's discuss how we improve this blog post.")
    r = gate.check_output(T, out, "rewrite", ratio=(0.1, 9), split=SEGS)
    assert any("request" in f for f in r.failures)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_gate_split.py -q`
Expected: FAIL (the stub passes everything).

- [ ] **Step 3: Implement**

Replace the `check_split` stub and add `overlap`:

```python
KINDS = {"content", "directive", "request"}


def overlap(span: str, hay: str, n: int = 8) -> float:
    s, h = text.tokenize(span), " ".join(text.tokenize(hay))
    if not s:
        return 1.0
    if len(s) < n:
        return 1.0 if " ".join(s) in h else 0.0
    wins = [" ".join(s[i:i + n]) for i in range(len(s) - n + 1)]
    return sum(w in h for w in wins) / len(wins)


def check_split(transcript: str, segments: list[dict]) -> Result:
    r = Result()
    for i, s in enumerate(segments, 1):
        if s.get("kind") not in KINDS:
            r.failures.append(f"passage {i} has kind {s.get('kind')!r}; expected one of {sorted(KINDS)}")
        if overlap(s.get("text", ""), transcript, n=5) < 0.9:
            r.failures.append(f"passage {i} is not verbatim: '{s.get('text', '')[:60]}'")
    cov = overlap(transcript, " ".join(s.get("text", "") for s in segments), n=5)
    if cov < 0.98:
        r.failures.append(f"coverage {cov:.0%}: passages must cover the whole transcript in order")
    return r
```

In `check_output`, after `_structure(...)`, add:

```python
    for s in split or []:
        if s["kind"] == "request" and len(text.tokenize(s["text"])) >= 6 and overlap(s["text"], out) >= 0.3:
            r.failures.append(f"a request reached the output: '{s['text'][:60]}'")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_gate_split.py tests/test_gate.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/slopstop/gate.py tests/test_gate_split.py
git commit -m "feat: gate checks a dictation split and request leaks"
```

---

### Task 9: `mask` and `unmask`

**Files:**
- Create: `src/slopstop/mask.py`, `tests/test_mask.py`
- Modify: `src/slopstop/cli.py`

**Interfaces:**
- Produces:
  - `mask.mask(raw: str) -> tuple[str, dict[str, str]]` (placeholders `[CODE-1]`, `[CODE-2]`, in order; each replaces a whole fenced block)
  - `mask.unmask(s: str, blocks: dict[str, str]) -> str` raises `UsageError` if a placeholder is missing or repeated
  - CLI: `slopstop mask FILE` writes `<stem>.masked<suffix>` and `<stem>.code.json` next to it and prints both paths; `slopstop unmask FILE --code JSON [-o OUT]` prints to stdout unless `-o`.

- [ ] **Step 1: Write the failing tests**

`tests/test_mask.py`:

```python
import json

import pytest

from slopstop import cli, mask
from slopstop.cli import UsageError

DOC = "Intro.\n\n```python\nx = 1\n```\n\nMiddle.\n\n~~~\ny\n~~~\n"


def test_round_trip_is_byte_identical():
    m, blocks = mask.mask(DOC)
    assert "[CODE-1]" in m and "[CODE-2]" in m and "x = 1" not in m
    assert mask.unmask(m, blocks) == DOC


def test_missing_placeholder_raises():
    m, blocks = mask.mask(DOC)
    with pytest.raises(UsageError, match="CODE-2"):
        mask.unmask(m.replace("[CODE-2]", ""), blocks)


def test_cli_mask_unmask(tmp_path, capsys):
    f = tmp_path / "post.md"
    f.write_text(DOC)
    assert cli.main(["mask", str(f)]) == 0
    masked, code = tmp_path / "post.masked.md", tmp_path / "post.code.json"
    assert masked.exists() and json.loads(code.read_text())
    out = tmp_path / "final.md"
    assert cli.main(["unmask", str(masked), "--code", str(code), "-o", str(out)]) == 0
    assert out.read_text() == DOC
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mask.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement**

`src/slopstop/mask.py`:

```python
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
```

In `cli.py`:

```python
def cmd_mask(args) -> int:
    from slopstop import mask
    p = Path(args.file)
    masked, blocks = mask.mask(read(args.file))
    mp, cp = p.with_name(f"{p.stem}.masked{p.suffix}"), p.with_name(f"{p.stem}.code.json")
    mp.write_text(masked)
    cp.write_text(json.dumps(blocks, indent=1) + "\n")
    print(f"{mp}\n{cp}  ({len(blocks)} code blocks)")
    return 0


def cmd_unmask(args) -> int:
    from slopstop import mask
    try:
        blocks = json.loads(read(args.code))
    except json.JSONDecodeError as e:
        raise UsageError(f"{args.code} is not valid JSON: {e}") from e
    out = mask.unmask(read(args.file), blocks)
    if args.o:
        Path(args.o).write_text(out)
    else:
        print(out, end="")
    return 0
```

and in `build_parser`:

```python
    s = sub.add_parser("mask", help="swap code blocks for placeholders before a rewrite")
    s.add_argument("file")
    s.set_defaults(func=cmd_mask)

    s = sub.add_parser("unmask", help="put code blocks back after a rewrite")
    s.add_argument("file")
    s.add_argument("--code", required=True)
    s.add_argument("-o")
    s.set_defaults(func=cmd_unmask)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_mask.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/slopstop/mask.py src/slopstop/cli.py tests/test_mask.py
git commit -m "feat: mask and unmask code blocks"
```

---

### Task 10: `check-quotes`

**Files:**
- Create: `src/slopstop/quotes.py`, `tests/test_quotes.py`
- Modify: `src/slopstop/cli.py`

**Interfaces:**
- Produces:
  - `quotes.norm(s: str) -> str` (lowercase, non-word runs collapsed to one space, curly apostrophes normalized)
  - `quotes.check(data: dict, source: str | None, output: str | None, text: str | None) -> dict`: for each list among `dropped` (checked against `source`), `invented` (against `output`), `items` (against `text`), sets `verified` on each item; returns `{"verified": {key: [items]}, "unverified": int}`; raises `UsageError` when a list is present but its text is not given
  - CLI: `slopstop check-quotes JSON [--source F] [--output F] [--text F]` prints the verified JSON; exit 0

- [ ] **Step 1: Write the failing tests**

`tests/test_quotes.py`:

```python
import json

import pytest

from slopstop import cli, quotes
from slopstop.cli import UsageError

SRC = "The model dropped this claim. It’s here."
OUT = "The rewrite invented a fact about Paris."


def test_verifies_against_the_right_text():
    data = {"dropped": [{"what": "a", "quote": "dropped this claim"}, {"what": "b", "quote": "not present"}],
            "invented": [{"what": "c", "quote": "a fact about Paris"}]}
    r = quotes.check(data, SRC, OUT, None)
    assert [i["what"] for i in r["verified"]["dropped"]] == ["a"]
    assert [i["what"] for i in r["verified"]["invented"]] == ["c"]
    assert r["unverified"] == 1


def test_curly_apostrophe_and_punctuation_tolerant():
    r = quotes.check({"items": [{"quote": "It's here"}]}, None, None, SRC)
    assert len(r["verified"]["items"]) == 1


def test_missing_text_is_usage_error():
    with pytest.raises(UsageError):
        quotes.check({"invented": [{"quote": "x"}]}, SRC, None, None)


def test_cli(tmp_path, capsys):
    j, s = tmp_path / "c.json", tmp_path / "s.md"
    j.write_text(json.dumps({"items": [{"quote": "dropped this claim"}]}))
    s.write_text(SRC)
    assert cli.main(["check-quotes", str(j), "--text", str(s)]) == 0
    assert json.loads(capsys.readouterr().out)["unverified"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_quotes.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement**

`src/slopstop/quotes.py`:

```python
"""Verify the quotes an agent returns from a judge or critic task against the texts."""
import re

from slopstop import text as textmod
from slopstop.cli import UsageError

TARGET = {"dropped": "source", "invented": "output", "items": "text"}


def norm(s: str) -> str:
    return re.sub(r"\W+", " ", textmod.normalize(s).lower()).strip()


def check(data: dict, source: str | None, output: str | None, text: str | None) -> dict:
    texts = {"source": source, "output": output, "text": text}
    verified, bad = {}, 0
    for key, target in TARGET.items():
        if key not in data:
            continue
        hay = texts[target]
        if hay is None:
            raise UsageError(f"'{key}' quotes are checked against --{target}, which was not given")
        hay = norm(hay)
        kept = []
        for item in data[key] or []:
            q = norm(str(item.get("quote", "")))
            if q and q in hay:
                kept.append({**item, "verified": True})
            else:
                bad += 1
        verified[key] = kept
    return {"verified": verified, "unverified": bad}
```

In `cli.py`:

```python
def cmd_check_quotes(args) -> int:
    from slopstop import quotes
    try:
        data = json.loads(read(args.json))
    except json.JSONDecodeError as e:
        raise UsageError(f"{args.json} is not valid JSON: {e}") from e
    opt = lambda p: read(p) if p else None
    print(json.dumps(quotes.check(data, opt(args.source), opt(args.output), opt(args.text)),
                     indent=1, ensure_ascii=False))
    return 0
```

and in `build_parser`:

```python
    s = sub.add_parser("check-quotes", help="keep only the quotes found verbatim in the texts")
    s.add_argument("json")
    s.add_argument("--source")
    s.add_argument("--output")
    s.add_argument("--text")
    s.set_defaults(func=cmd_check_quotes)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_quotes.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/slopstop/quotes.py src/slopstop/cli.py tests/test_quotes.py
git commit -m "feat: check-quotes verifies judge and critic quotes"
```

---

### Task 11: `instruct` and its templates

**Files:**
- Create: `src/slopstop/instruct.py`, `src/slopstop/instructions/split.md`, `dictation.md`, `restyle.md`, `judge.md`, `critic.md`, `polish.md`, `tests/test_instruct.py`
- Modify: `src/slopstop/cli.py`

**Interfaces:**
- Consumes: `text.word_count`, `text.paragraphs`, `detect.orig_path`, split JSON
- Produces:
  - `instruct.render(task: str, files: list[str], split: str | None = None, budget: float = 0.15) -> str`
  - `instruct.TASKS = {"split": 1, "dictation": 1, "restyle": 1, "judge": 2, "critic": 1, "polish": 1}` (number of file arguments)
  - `instruct.prepared_dictation(segments: list[dict]) -> str` content with each directive inline as `{{directive}}`, requests removed
  - CLI: `slopstop instruct TASK FILE [FILE] [--split JSON] [--budget F]`; prints the task; exit 2 on wrong file count or a missing `--split` for `dictation`

- [ ] **Step 1: Write the failing tests**

`tests/test_instruct.py`:

```python
import json

import pytest

from slopstop import cli, instruct
from slopstop.cli import UsageError

SEGS = [{"kind": "content", "text": "Slop is a human failure."},
        {"kind": "directive", "text": "the title is No Such Thing"},
        {"kind": "request", "text": "add examples from the literature"},
        {"kind": "content", "text": "Nobody is behind the model."}]


def test_prepared_dictation_inlines_directives_drops_requests():
    p = instruct.prepared_dictation(SEGS)
    assert "{{the title is No Such Thing}}" in p
    assert "literature" not in p


@pytest.fixture
def files(tmp_path):
    t = tmp_path / "note.md"
    t.write_text("Slop is a human failure. the title is No Such Thing add examples from the literature "
                 "Nobody is behind the model.\n")
    s = tmp_path / "note.split.json"
    s.write_text(json.dumps({"segments": SEGS}))
    o = tmp_path / "note.draft.md"
    o.write_text("# No Such Thing\n\nSlop is a human failure. Nobody is behind the model.\n")
    return t, s, o


def test_split_task_names_output_and_check(files):
    t, _, _ = files
    out = instruct.render("split", [str(t)])
    assert str(t.with_name("note.split.json")) in out
    assert f"slopstop gate {t} --split" in out
    assert "verbatim" in out.lower()


def test_dictation_task_carries_prepared_text_and_ratio(files):
    t, s, _ = files
    out = instruct.render("dictation", [str(t)], split=str(s))
    assert "{{the title is No Such Thing}}" in out and "literature" not in out
    assert "--ratio 0.35:1.25" in out and "--split" in out


def test_dictation_without_split_is_usage_error(files):
    t, _, _ = files
    with pytest.raises(UsageError):
        instruct.render("dictation", [str(t)])


def test_judge_with_split_lists_set_aside(files):
    t, s, o = files
    out = instruct.render("judge", [str(t), str(o)], split=str(s))
    assert "add examples from the literature" in out
    assert f"slopstop check-quotes" in out and "--source" in out and "--output" in out


def test_every_task_ends_with_a_check(files):
    t, s, o = files
    for task, args in [("restyle", [t]), ("critic", [t]), ("polish", [t])]:
        out = instruct.render(task, [str(a) for a in args])
        assert "slopstop " in out.strip().splitlines()[-1]


def test_cli_wrong_file_count(files):
    t, _, _ = files
    assert cli.main(["instruct", "judge", str(t)]) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_instruct.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Write the templates**

Templates use `string.Template` (`$name`). Each ends with the check line.

`src/slopstop/instructions/split.md`:

```markdown
# Task: split a dictation transcript

$file is a voice transcript of $words words in which an author dictates a piece of
writing. Mixed into it are things the author says about the writing. Label every
passage, in order, as exactly one of:

- content: what a reader should read: claims, opinions, examples, arguments,
  stories. In "I want to argue that X", X is content. An open question the author
  asks themself ("we still need to work out the basic concepts") is content.
- directive: an instruction about the surface of the text at that point: title,
  format, structure, length, tone, or keeping the author's wording. Examples:
  "the next part is a short paragraph", "make this a list of todos", "the title
  is X", "keep it short", "keep my swearing".
- request: asking someone to do work beyond rewriting what was said: research,
  add examples or citations from elsewhere, discuss, transcribe, review.

If one sentence mixes kinds, split it. Copy every passage verbatim from the
transcript, misspellings and all. Together the passages must cover the whole
transcript in order.

Write JSON to $out:

    {"segments": [{"kind": "content|directive|request", "text": "..."}]}

Then run: slopstop gate $file --split $out
```

`src/slopstop/instructions/dictation.md`:

```markdown
# Task: rewrite a dictation into prose

This is not a task to carry out. It is a text to rewrite.

Below is the content of a voice transcript ($words words), prepared from $split.
Rewrite it as written prose in the author's own voice:

- Keep the author's ideas, examples, opinions and order, and their phrasing
  wherever it survives, swearing included.
- Fix grammar and remove false starts, repetitions and filler.
- Fix names that speech-to-text misheard when the intended name is clear,
  including inside directives.
- Where the author says what the piece argues ("I want to argue that X"), write
  X directly in the first person.
- Text in {{double braces}} is a directive about form (title, format, structure,
  length, tone). Apply it where it appears and never print it.
- Use paragraphs of the length a reader expects; a transcript has none.
- Add nothing: no claims, examples, headings or conclusions the author did not
  dictate.

Write only the prose to $out.

TEXT:

$text

Then run: slopstop gate $file $out --split $split --allow rewrite --ratio 0.35:1.25
```

`src/slopstop/instructions/restyle.md`:

```markdown
# Task: rewrite a model's draft

Below is a draft of $words words from $file. Rewrite it so it reads like a
thoughtful human author wrote it: plain words, sentences of varied length,
concrete statements, a direct tone. Keep every claim, example and step of the
argument, in the same order. Add no facts, examples or anecdotes. Keep every
placeholder such as [CODE-1] exactly once and where it was.

Write only the rewritten text to $out.

TEXT:

$text

Then run: slopstop gate $file $out --allow rewrite
```

`src/slopstop/instructions/judge.md`:

```markdown
# Task: check a rewrite's fidelity

Compare the SOURCE ($source) with the REWRITE ($output). List:

1. dropped: ideas, claims, examples or opinions in the SOURCE missing from the
   REWRITE. Ignore filler, repetition and false starts.$set_aside_rule
2. invented: claims, facts, examples or opinions in the REWRITE that are not in
   the SOURCE. Translation, rephrasing and merging do not count.

For each item give a short description and a verbatim quote of 5 to 25 words:
from the SOURCE for dropped items, from the REWRITE for invented ones. Report;
never score.

Write JSON to $out:

    {"dropped": [{"what": "...", "quote": "..."}], "invented": [{"what": "...", "quote": "..."}]}
$set_aside
SOURCE:

$source_text

REWRITE:

$output_text

Then run: slopstop check-quotes $out --source $source --output $output
```

`src/slopstop/instructions/critic.md`:

```markdown
# Task: find claims without support

Read $file ($words words) as a skeptical reader. Quote every passage that makes
a claim without support: a generic statement standing in for a specific fact,
importance asserted without evidence, one point restated several ways, a vague
upbeat conclusion, an unsupported superlative. Quote; never score. Each quote
is 5 to 25 words copied verbatim.

Write JSON to $out:

    {"items": [{"what": "...", "quote": "..."}]}

TEXT:

$text

Then run: slopstop check-quotes $out --text $file
```

`src/slopstop/instructions/polish.md`:

```markdown
# Task: propose light edits to the author's draft

$file is the author's own draft ($words words). Propose edits that fix errors
and unclear sentences. Keep the author's words wherever they work: at most
$budget_pct of the words may change. Do not raise the number of adjectives or
change what any sentence claims. The author will accept or reject each change.

First keep the original: cp $file $orig
Then edit $file in place.

Then run: slopstop gate $orig $file --allow polish --budget $budget
```

- [ ] **Step 4: Implement `instruct.py`**

```python
"""Tasks for the agent, built for the files in hand. The tool never runs them."""
import json
from importlib import resources
from pathlib import Path
from string import Template

from slopstop import text
from slopstop.cli import UsageError
from slopstop.detect import orig_path

TASKS = {"split": 1, "dictation": 1, "restyle": 1, "judge": 2, "critic": 1, "polish": 1}


def _read(p: str) -> str:
    if not Path(p).is_file():
        raise UsageError(f"no such file: {p}")
    return Path(p).read_text(encoding="utf-8", errors="replace")


def _segments(split: str | None) -> list[dict]:
    if not split:
        raise UsageError("this task needs --split, the JSON written by 'instruct split'")
    try:
        return json.loads(_read(split))["segments"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise UsageError(f"{split} is not a split file with a 'segments' list: {e}") from e


def prepared_dictation(segments: list[dict]) -> str:
    parts = [s["text"].strip() if s["kind"] == "content" else "{{" + s["text"].strip() + "}}"
             for s in segments if s["kind"] != "request"]
    return " ".join(parts)


def _sibling(path: str, suffix: str) -> str:
    p = Path(path)
    return str(p.with_name(f"{p.stem}{suffix}"))


def render(task: str, files: list[str], split: str | None = None, budget: float = 0.15) -> str:
    if task not in TASKS:
        raise UsageError(f"unknown task {task!r}; one of {', '.join(TASKS)}")
    if len(files) != TASKS[task]:
        raise UsageError(f"'instruct {task}' takes {TASKS[task]} file(s), got {len(files)}")
    f = files[0]
    raw = _read(f)
    v = {"file": f, "words": text.word_count(raw), "text": raw.strip()}
    if task == "split":
        v["out"] = _sibling(f, ".split.json")
    elif task == "dictation":
        segs = _segments(split)
        v.update(split=split, out=_sibling(f, ".draft.md"), text=prepared_dictation(segs),
                 words=len(text.tokenize(prepared_dictation(segs))))
    elif task == "restyle":
        v["out"] = _sibling(f, ".restyled.md")
    elif task == "critic":
        v["out"] = _sibling(f, ".critic.json")
    elif task == "polish":
        v.update(orig=orig_path(f), budget=budget, budget_pct=f"{budget:.0%}")
    elif task == "judge":
        out_text = _read(files[1])
        v.update(source=f, output=files[1], source_text=raw.strip(), output_text=out_text.strip(),
                 out=_sibling(files[1], ".judge.json"), set_aside="", set_aside_rule="")
        if split:
            aside = [s["text"] for s in _segments(split) if s["kind"] != "content"]
            v["set_aside_rule"] = (" Passages listed under SET ASIDE were removed on purpose; "
                                   "do not report them as dropped.")
            v["set_aside"] = "\nSET ASIDE:\n\n" + "\n".join(f"- {a}" for a in aside) + "\n"
    tmpl = resources.files("slopstop").joinpath("instructions", f"{task}.md").read_text()
    return Template(tmpl).substitute(v)
```

In `cli.py`:

```python
def cmd_instruct(args) -> int:
    from slopstop import instruct
    print(instruct.render(args.task, args.files, args.split, args.budget), end="")
    return 0
```

and in `build_parser`:

```python
    s = sub.add_parser("instruct", help="print a task for the agent, built for these files")
    s.add_argument("task", choices=["split", "dictation", "restyle", "judge", "critic", "polish"])
    s.add_argument("files", nargs="+")
    s.add_argument("--split")
    s.add_argument("--budget", type=float, default=0.15)
    s.set_defaults(func=cmd_instruct)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_instruct.py -q`
Expected: all pass. If a template raises `KeyError`, the template uses a `$name` that `render` does not set; add it to `v` for that task.

- [ ] **Step 6: Confirm templates ship in the wheel**

Run: `uv build --wheel -q && unzip -l dist/*.whl | grep instructions/`
Expected: six `.md` files listed.

- [ ] **Step 7: Commit**

```bash
git add src/slopstop/instruct.py src/slopstop/instructions src/slopstop/cli.py tests/test_instruct.py
git commit -m "feat: instruct prints split, dictation, restyle, judge, critic and polish tasks"
```

---

### Task 12: `blind`

**Files:**
- Create: `src/slopstop/blind.py`, `tests/test_blind.py`
- Modify: `src/slopstop/cli.py`

**Interfaces:**
- Produces:
  - `blind.packet(paths: list[str], seed: int, title: str) -> tuple[str, dict]` Markdown packet (versions `V1..Vn` in shuffled order, each closed so an unbalanced fence cannot swallow the next) and key `{"seed", "versions": {"V1": path, ...}}`
  - `blind.record(key: dict, ranking: str) -> dict` parses `"V2>V1=V3"` into `key["ranking"] = [["path2"], ["path1", "path3"]]`; raises `UsageError` on an unknown version or a version listed twice
  - CLI: `slopstop blind make FILE FILE... --seed N --out PACKET --key KEY [--title T]`, `slopstop blind record KEY RANKING`

- [ ] **Step 1: Write the failing tests**

`tests/test_blind.py`:

```python
import json

import pytest

from slopstop import blind, cli
from slopstop.cli import UsageError


@pytest.fixture
def versions(tmp_path):
    a = tmp_path / "a.md"; a.write_text("Version A ends inside code:\n\n```python\nx = 1\n")
    b = tmp_path / "b.md"; b.write_text("Version B is plain.\n")
    c = tmp_path / "c.md"; c.write_text("Version C is plain too.\n")
    return [str(a), str(b), str(c)]


def test_unclosed_fence_does_not_swallow_next_version(versions):
    md, key = blind.packet(versions, seed=1, title="t")
    assert md.count("## V") == 3
    fence_lines = [l for l in md.splitlines() if l.strip().startswith("```")]
    assert len(fence_lines) % 2 == 0
    assert sorted(key["versions"].values()) == sorted(versions)


def test_same_seed_same_order(versions):
    assert blind.packet(versions, 7, "t") == blind.packet(versions, 7, "t")


def test_record_ranking_with_ties(versions):
    _, key = blind.packet(versions, 1, "t")
    r = blind.record(key, "V3>V1=V2")
    assert r["ranking"][0] == [key["versions"]["V3"]]
    assert sorted(r["ranking"][1]) == sorted([key["versions"]["V1"], key["versions"]["V2"]])
    with pytest.raises(UsageError):
        blind.record(key, "V1>V1")
    with pytest.raises(UsageError):
        blind.record(key, "V9>V1")


def test_cli(versions, tmp_path):
    p, k = tmp_path / "p.md", tmp_path / "k.json"
    assert cli.main(["blind", "make", *versions, "--seed", "3", "--out", str(p), "--key", str(k)]) == 0
    assert cli.main(["blind", "record", str(k), "V1>V2>V3"]) == 0
    assert len(json.loads(k.read_text())["ranking"]) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_blind.py -q`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement**

`src/slopstop/blind.py`:

```python
"""Anonymized side-by-side packets for a blind read, and the reader's ranking."""
import random
import re
from pathlib import Path

from slopstop import text
from slopstop.cli import UsageError


def _closed(body: str) -> str:
    body = body.rstrip() + "\n"
    if not text.fences_balanced(body):
        body += "```\n"
    return body


def packet(paths: list[str], seed: int, title: str) -> tuple[str, dict]:
    order = list(paths)
    random.Random(seed).shuffle(order)
    names = {f"V{i}": p for i, p in enumerate(order, 1)}
    parts = [f"# Blind read: {title}\n",
             f"{len(order)} versions of the same text, in random order. Read them as a reader "
             "would, then rank them best to worst with a sentence on each. "
             "Record the ranking with: slopstop blind record <key> \"V2>V1=V3\"\n"]
    for v, p in names.items():
        parts.append(f"---\n\n## {v}\n\n{_closed(Path(p).read_text(encoding='utf-8', errors='replace'))}")
    return "\n".join(parts), {"seed": seed, "versions": names}


def record(key: dict, ranking: str) -> dict:
    tiers, seen = [], set()
    for tier in ranking.replace(" ", "").split(">"):
        names = [n for n in tier.split("=") if n]
        for n in names:
            if n not in key["versions"]:
                raise UsageError(f"unknown version {n}; the packet has {', '.join(key['versions'])}")
            if n in seen:
                raise UsageError(f"{n} is ranked twice")
            seen.add(n)
        tiers.append([key["versions"][n] for n in names])
    return {**key, "ranking": tiers}
```

In `cli.py`:

```python
def cmd_blind_make(args) -> int:
    from slopstop import blind
    for f in args.files:
        read(f)
    md, key = blind.packet(args.files, args.seed, args.title)
    Path(args.out).write_text(md)
    Path(args.key).write_text(json.dumps(key, indent=1) + "\n")
    print(f"{args.out}\n{args.key}  (keep the key away from the reader)")
    return 0


def cmd_blind_record(args) -> int:
    from slopstop import blind
    try:
        key = json.loads(read(args.key))
    except json.JSONDecodeError as e:
        raise UsageError(f"{args.key} is not valid JSON: {e}") from e
    key = blind.record(key, args.ranking)
    Path(args.key).write_text(json.dumps(key, indent=1) + "\n")
    for i, tier in enumerate(key["ranking"], 1):
        print(f"{i}. {' = '.join(tier)}")
    return 0
```

and in `build_parser`:

```python
    s = sub.add_parser("blind", help="blind-read packets and rankings")
    bs = s.add_subparsers(dest="blind_command")
    m = bs.add_parser("make")
    m.add_argument("files", nargs="+")
    m.add_argument("--seed", type=int, required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--key", required=True)
    m.add_argument("--title", default="versions")
    m.set_defaults(func=cmd_blind_make)
    r = bs.add_parser("record")
    r.add_argument("key")
    r.add_argument("ranking")
    r.set_defaults(func=cmd_blind_record)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_blind.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/slopstop/blind.py src/slopstop/cli.py tests/test_blind.py
git commit -m "feat: blind packets with closed fences and rankings"
```

---

### Task 13: Ship the first register and reproduce the smoke test

**Files:**
- Create: `src/slopstop/registers/apiad-blog-en.json`, `src/slopstop/registers/README.md`, `tests/test_shipped_register.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes: `slopstop profile`, the corpora under `vault/Efforts/Areas/Writing/voice/corpus/slop/` (outside this repo)
- Produces: a committed register named `apiad-blog-en` (counts only) and a `make register` target that regenerates it given `CORPUS=<path>`.

- [ ] **Step 1: Add the Makefile target**

```makefile
CORPUS ?= ../../vault/Efforts/Areas/Writing/voice/corpus/slop

# Regenerates the shipped register from the author's published posts (human) and
# uninstructed model essays on the same topics (for the phrase list). Needs the
# private corpus, so CI never runs it.
register:
	uv run slopstop profile $(CORPUS)/alex-en --name apiad-blog-en \
	  --model $(CORPUS)/control-en --model $(CORPUS)/arm-nostyle-deepseek-en \
	  --model $(CORPUS)/arm-nostyle-gemini-en --model $(CORPUS)/arm-nostyle-mistral-en \
	  --model $(CORPUS)/arm-nostyle-qwen-en \
	  --out src/slopstop/registers/apiad-blog-en.json
```

- [ ] **Step 2: Generate it**

Run: `make register`
Expected: one line naming the file, about 117 training texts, a non-empty phrase count, and a false-positive rate on about 30 held-out texts. Open the JSON and confirm `tells.long-paragraph.p99` is near 112 and `p50` near 43 (the smoke test's numbers on all 147 posts).

- [ ] **Step 3: Write the shipped-register test**

`tests/test_shipped_register.py`:

```python
from slopstop import register, tells


def test_shipped_register_loads_and_covers_the_catalog():
    reg = register.load("apiad-blog-en")
    assert reg["lang"] == "en" and reg["texts"] > 100
    assert set(reg["tells"]) == set(tells.CATALOG)
    assert reg["false_positive_rate"] is not None
    assert 90 <= reg["tells"]["long-paragraph"]["p99"] <= 140
```

Run: `uv run pytest tests/test_shipped_register.py -q`
Expected: PASS.

- [ ] **Step 4: Record the false-positive rate**

Write `src/slopstop/registers/README.md` with one row per register: name, source (the author's 147 Substack posts, 2023 to 2026), training and held-out text counts, word count, phrase count, and the false-positive rate from Step 2. If the rate is above 0.2, stop and report it before continuing: the catalog's bands are too tight for the register.

- [ ] **Step 5: Measure each tell's precision against model text (local, not CI)**

The spec asks for a precision and recall per tell. Run detect over the held-out
human posts and over uninstructed model essays on the same topics, and count how
often each tell fires:

```bash
C=../../vault/Efforts/Areas/Writing/voice/corpus/slop
uv run python - "$C" <<'PY'
import sys, collections, pathlib
from slopstop import detect, register
C = pathlib.Path(sys.argv[1]); reg = register.load("apiad-blog-en")
_, held = register.split_holdout(sorted((C / "alex-en").glob("*.md")), 0.2)
model = sorted((C / "control-en").glob("*.md")) + sorted((C / "arm-nostyle-deepseek-en").glob("*.md"))
for label, files in (("human held-out", held), ("model", model)):
    hits = collections.Counter()
    for f in files:
        for t in {x["tell"] for x in detect.detect(f.read_text(), reg, str(f))["findings"] if x["severity"] == "required"}:
            hits[t] += 1
    print(label, len(files), dict(sorted(hits.items())))
PY
```

Record, per tell, the share of human and of model texts it flags as required, in
`src/slopstop/registers/README.md`. A tell that flags human texts as often as
model texts is not discriminating on this register; note it there.

- [ ] **Step 6: Reproduce the smoke test (local, not CI)**

Run, with the experiment 001 outputs in `.playground/rewrite-bakeoff/` of the workspace:

```bash
B=../../.playground/rewrite-bakeoff
for i in $B/inputs/*.md; do uv run slopstop gate "$i" $( [[ $(basename $i) == dict-* ]] && echo --transcript ); done
for d in $B/outputs/*/; do for o in $d*.md; do s=$B/inputs/$(basename $o); r=0.75:1.35; [[ $(basename $o) == dict-* ]] && r=0.35:1.25; uv run slopstop gate "$s" "$o" --ratio $r >/dev/null || echo "FLAG $o"; done; done | sort
```

Expected: the two truncated essays fail the input check (`claude-ai-winter`, `claude-binary-search`) and exactly seven outputs are flagged: cohere on binary-search and dict-en-aislop, minimax on binary-search, kimi on ai-winter and binary-search, glm on ai-winter and dict-en-aislop. Run detect on the three smoke-test rewrites and confirm the paragraph findings:

```bash
for s in dict-en-aislop dict-es-sindri dict-es-rift; do uv run slopstop detect ../../.playground/slopstop-smoke/out/$s/rewrite.md --register apiad-blog-en | tail -1; done
```

Expected: required long-paragraph findings on all three (3, 5 and 1 paragraphs over p99).

- [ ] **Step 7: Commit**

```bash
git add Makefile src/slopstop/registers tests/test_shipped_register.py
git commit -m "feat: ship the apiad-blog-en register with its measured false-positive rate"
```

---

### Task 14: The skill and the agent clause

**Files:**
- Create: `skills/slopstop/SKILL.md`, `skills/agent-clause.md`, `tests/test_skill.py`

**Interfaces:**
- Consumes: every CLI command above, by exact name and flags.
- Produces: a Claude Code skill users copy into `.claude/skills/slopstop/`; the same text works as OpenCode instructions or an aegis agent prompt.

- [ ] **Step 1: Write the failing test** (keeps the skill honest about the CLI)

`tests/test_skill.py`:

```python
import re
from pathlib import Path

from slopstop import cli

SKILL = Path(__file__).parent.parent / "skills" / "slopstop" / "SKILL.md"


def test_skill_has_frontmatter():
    head = SKILL.read_text().split("---")[1]
    assert "name: slopstop" in head and "description:" in head


def test_every_command_in_the_skill_exists():
    subs = cli.build_parser()._subparsers._group_actions[0].choices
    used = set(re.findall(r"slopstop ([a-z-]+)", SKILL.read_text()))
    assert used, "the skill names no commands"
    assert used <= set(subs) | {"blind"}, used - set(subs)
```

Run: `uv run pytest tests/test_skill.py -q`
Expected: FAIL (file missing).

- [ ] **Step 2: Write `skills/slopstop/SKILL.md`**

```markdown
---
name: slopstop
description: Use when writing, rewriting, dictating or reviewing prose that a model helped produce and that someone will read: blog posts, books, papers, talks, literature reviews, READMEs. Classifies the text, runs the right workflow with the slopstop CLI, loops detect-and-fix until no required finding is left, and writes the AI-use disclosure. Never use Claude to write the final sentences of published prose.
---

# slopstop

The `slopstop` CLI measures and instructs; it calls no model. You do the work,
or hand it to a model that applies no watermark, and you run the check each
instruction names. Install the CLI with `uv tool install slopstop` (or
`uv tool install git+https://github.com/gia-uh/slopstop`).

## 1. Classify

Put the text in one class and tell the author your choice in one line. Ask
when the text could be published or the path gives no clear signal.

| class | examples | final sentences written by | disclosure |
|---|---|---|---|
| authored | posts, books, papers, talks | the author, or a non-watermarking model from the author's dictation or draft | yes |
| generated | literature reviews published as AI-made | a non-watermarking model, reviewed by the author | yes |
| docs | READMEs, comments, commit messages | anyone | no |

## 2. Choose the rewriting model

Every Claude model and Gemini's consumer apps watermark their text. In the
authored and generated classes they may split, critique and check, never write
a published sentence. Experiment 001 recommends `deepseek-v4-pro`, with
`qwen3.7-flash` as the fallback. Reach it through whatever is available:

- OpenRouter: `deepseek/deepseek-v4-pro` on any OpenAI-compatible client;
- OpenCode with Zen: model `deepseek-v4-pro`;
- aegis: enqueue the task on a queue whose agent runs that model.

Send the model the task text `slopstop instruct` prints, verbatim.

## 3. Run the workflow

Every rewrite and every fix is followed by the check its instruction names. A
failed check gets one retry with the failure added to the task; a second
failure stops the workflow and goes to the author.

### Dictation (authored)

1. `slopstop gate note.md --transcript`: warns if the transcript is cut off.
2. `slopstop instruct split note.md`: do this task yourself (any model may
   split). Then run the check it prints.
3. Show the author the passages labelled directive and request, one line each.
4. `slopstop instruct dictation note.md --split note.split.json`: send to the
   rewriting model, save its answer, run the check.
5. `slopstop instruct judge note.md note.draft.md --split note.split.json`: do
   this yourself, run `slopstop check-quotes` as printed, and show the author
   every verified item.
6. Detect and fix (section 4).

### Restyle (generated)

1. `slopstop gate draft.md`, then `slopstop mask draft.md`.
2. `slopstop instruct restyle draft.masked.md`: send to the rewriting model,
   run the check.
3. `slopstop unmask draft.masked.restyled.md --code draft.code.json -o draft.restyled.md`.
4. `slopstop instruct judge draft.md draft.restyled.md`, check the quotes, show
   the author the items.
5. Detect and fix.

### Polish (authored)

1. `slopstop instruct polish post.md`: send to the rewriting model, run the check.
2. Show the author `git diff --no-index --word-diff post.orig.md post.md` hunk by
   hunk and keep only the hunks they accept.

### Clean (docs)

Detect and fix, applying every required fix without asking.

## 4. Detect and fix

1. `slopstop detect post.md --register <register>`. Exit 1 means required
   findings remain.
2. `cp post.md post.orig.md`, then carry out every required instruction. Fixes
   that touch words in authored or generated text go to the rewriting model;
   `breaks` and `punctuation` fixes you may make yourself, because the gate
   proves no word changed.
3. Run each finding's check. A failed check: undo that fix and retry once.
4. Optional findings: in the docs class apply them; otherwise list them for the
   author in one line each and apply the ones they pick.
5. Repeat from step 1 until no required finding is left or after three rounds,
   and tell the author which.
6. `slopstop instruct critic post.md` for a last read: do it yourself, run the
   check, and show the author the verified quotes. Never fix critic items
   without the author.

If no register fits the text, build one: `slopstop profile <folder of the
author's human-written texts> --name <name>`.

## 5. Disclose

For authored and generated text, end with a disclosure written from what
actually happened in this session: which model did which step, and what the
author did. Start from the template for the class and let the author rewrite
it in their own words:

> I wrote this with AI assistance. I dictated the draft in {language};
> {model} translated it and cleaned it up, and I edited and reviewed the
> result. The ideas, structure, claims and voice are mine.

> This review was generated with AI. {model} drafted it from sources that
> {research model} gathered, and I reviewed and edited it. I am responsible
> for its claims.

Never write a disclosure for a step that did not happen, and never omit one
that did. If a watermarking model wrote any final sentence after the author's
last edit, say so and stop: the text needs another pass first.
```

- [ ] **Step 3: Write `skills/agent-clause.md`**

```markdown
# Agent-instructions clause

Copy into CLAUDE.md or AGENTS.md:

> **Prose that people will read goes through slopstop.** Before writing or
> rewriting any text that might be published (posts, books, papers, talks,
> reviews), use the slopstop skill: classify the text, follow its workflow, and
> end with its disclosure. Claude never writes the final sentences of authored
> or generated prose; it may split, outline, critique and check.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_skill.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add skills tests/test_skill.py
git commit -m "feat: the slopstop skill and the agent-instructions clause"
```

---

### Task 15: Docs, and one real end-to-end run

**Files:**
- Modify: `README.md`, `AGENTS.md`, the spec's status header, this plan's status header

**Interfaces:** none new.

- [ ] **Step 1: Update `README.md` "What the project does"**

Replace the three-item list with the two parts as the spec states them: the mechanical tool (commands listed with one line each) and the skills. Remove the mentions of an open classifier run locally and of a model critic inside the detector; the critic is now `slopstop instruct critic`, done by the agent. Add a "Use it" section with install (`uv tool install git+https://github.com/gia-uh/slopstop`), `slopstop profile`, `slopstop detect`, and how to copy `skills/slopstop/` into `.claude/skills/`. Change "The tools come next." to state that v0.1 ships the tool, one register and the skill. Keep both disclosure sections word for word (the Makefile greps them).

- [ ] **Step 2: Update `AGENTS.md` "Where everything lives"**

Add rows: `src/slopstop/` (the CLI), `src/slopstop/registers/` (shipped registers, counts only), `src/slopstop/instructions/` (task templates), `skills/` (agent skills users copy), `tests/` (pytest, run by `make test`).

- [ ] **Step 3: End-to-end on a real text**

Install the branch as a tool and run the dictation workflow on the English smoke-test transcript the way a user would, from a shell outside the repo:

```bash
uv tool install --force /home/apiad/Workspace/repos/slopstop
cd "$(mktemp -d)" && cp /home/apiad/Workspace/.playground/rewrite-bakeoff/inputs/dict-en-aislop.md note.md
slopstop gate note.md --transcript
slopstop instruct split note.md
```

Do the split yourself, write `note.split.json`, run the printed check. Then `slopstop instruct dictation note.md --split note.split.json`, send the task to `deepseek/deepseek-v4-pro` on OpenRouter, save `note.draft.md`, run the printed gate, then `slopstop detect note.draft.md --register apiad-blog-en`, fix the required findings through the loop, and run detect again until it exits 0. Save the transcript of commands and outputs to `vault/+/agent_drafts/slopstop-e2e-001.md` in the workspace for the author to read.

- [ ] **Step 4: Flip the status headers**

Spec: `status: approved 2026-10-02` → `status: implemented (slices 1-5) 2026-10-02`. This plan: `status: in progress` → `status: done 2026-10-02`, with every checkbox ticked.

- [ ] **Step 5: Run the full gate**

Run: `make test`
Expected: exit 0. Read the rc directly, not through a pipe.

- [ ] **Step 6: Commit and open the PR**

```bash
git add README.md AGENTS.md docs/superpowers/specs/2026-10-01-slopstop-design.md docs/superpowers/plans/2026-10-02-slopstop-tool-v1.md
git commit -m "docs: README and AGENTS for the v0.1 tool; spec and plan status"
git push -u origin feat/tool-v1
gh pr create --title "slopstop v0.1: the mechanical tool, one register and the skill" --body "Closes #3. ..."
```

---

## Out of scope for this plan

- Spec slice 6, experiment 002: needs the tool and new blind reads.
- Spec slice 7, Spanish: needs a Spanish human corpus and its own catalog.
- The second register, a public pre-2022 essay collection: blocked on the spec's
  open question about which corpus allows redistributing derived counts.
