"""Run the rule catalog over a text: findings with line, column, reason and fix."""
import json
import re
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

from slopstop import rules, text
from slopstop.rules import Doc, Finding, Line

SKIP_LINE = re.compile(r"^\s*(?:\||<|!\[|:::|>)")
MASK = [text.INLINE_CODE, re.compile(r"\]\([^)]*\)"), re.compile(r"https?://\S+"),
        text.HTML_COMMENT, re.compile(r"\$[^$\n]+\$")]
ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
LABEL = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\*\*[^*]+\*\*\s*[:.—-]")
HEADING = re.compile(r"^#{1,6}\s")
ALLOW = re.compile(r"<!--\s*slopstop:\s*(allow\s+([\w,\s-]+?)|off|on)\s*-->")


@dataclass
class Config:
    lang: str = "auto"
    disable: list[str] = field(default_factory=list)
    levels: dict[str, str] = field(default_factory=dict)
    thresholds: dict[str, int] = field(default_factory=dict)
    path: str | None = None


def load_config(start: Path, explicit: str | None = None) -> Config:
    """slopstop.toml, or [tool.slopstop] in pyproject.toml, from the file's folder upward."""
    if explicit:
        data, path = tomllib.loads(Path(explicit).read_text()), explicit
    else:
        data, path = {}, None
        for d in [start, *start.parents]:
            if (d / "slopstop.toml").is_file():
                data, path = tomllib.loads((d / "slopstop.toml").read_text()), str(d / "slopstop.toml")
                break
            pp = d / "pyproject.toml"
            if pp.is_file():
                tool = tomllib.loads(pp.read_text()).get("tool", {}).get("slopstop")
                if tool is not None:
                    data, path = tool, str(pp)
                    break
    known = {r.id for r in rules.load()}
    for key in ("disable",):
        bad = set(data.get(key, [])) - known
        if bad:
            raise ValueError(f"{path}: unknown rules in {key}: {', '.join(sorted(bad))}")
    for key in ("levels", "thresholds"):
        bad = set(data.get(key, {})) - known
        if bad:
            raise ValueError(f"{path}: unknown rules in [{key}]: {', '.join(sorted(bad))}")
    for rid, lvl in data.get("levels", {}).items():
        if lvl not in rules.LEVELS + ("off",):
            raise ValueError(f"{path}: level of {rid} must be error, warn or off, not {lvl!r}")
    return Config(data.get("lang", "auto"), list(data.get("disable", [])), dict(data.get("levels", {})),
                  dict(data.get("thresholds", {})), path)


class _RawMatch:
    """A match found on the masked line, whose groups read the line as written."""

    def __init__(self, m: re.Match, raw: str):
        self._m, self._raw = m, raw

    def group(self, i: int = 0) -> str:
        return self._raw[self._m.start(i):self._m.end(i)] if self._m.start(i) >= 0 else ""

    def start(self, i: int = 0) -> int:
        return self._m.start(i)

    def end(self, i: int = 0) -> int:
        return self._m.end(i)


def _masked(ln: str) -> str:
    """Same length as the line, so columns and groups map back to it."""
    ln = ln.replace("\u2019", "'")
    for pat in MASK:
        # NUL, not spaces: a pattern that eats whitespace must not eat masked code
        ln = pat.sub(lambda m: "\0" * len(m.group(0)), ln)
    return ln


def document(raw: str, lang: str = "auto") -> Doc:
    lines_raw = raw.split("\n")
    code, _ = text._scan(raw)
    fm = text.FRONTMATTER.match(raw)
    skip = fm.group(0).count("\n") if fm else 0
    lines = []
    for i, ln in enumerate(lines_raw):
        if i < skip or code[i] or not ln.strip() or SKIP_LINE.match(ln):
            continue
        lines.append(Line(i + 1, ln, _masked(ln), bool(HEADING.match(ln)), bool(ITEM.match(ln)),
                          bool(LABEL.match(ln))))
    if lang == "auto":
        lang = text.detect_lang(text.tokenize(text.strip_markdown(raw)))
    return Doc(raw, lang, lines, text.paragraphs(raw), text.sentences(raw))


def _suppressed(raw: str) -> dict[int, set[str] | None]:
    """Per line, the rules allowed there (None means every rule is off)."""
    out: dict[int, set[str] | None] = {}
    lines = raw.split("\n")
    off = False
    pending: set[str] | None = set()
    in_para = False
    for i, ln in enumerate(lines, 1):
        m = ALLOW.search(ln)
        if m and m.group(1) == "off":
            off = True
        elif m and m.group(1) == "on":
            off = False
        elif m:
            pending = {x.strip() for x in m.group(2).replace(",", " ").split() if x.strip()}
            in_para = False
            continue
        if off:
            out[i] = None
            continue
        if pending:
            if ln.strip():
                in_para = True
                out[i] = set(pending)
            elif in_para:
                pending, in_para = set(), False
    return out


@dataclass
class Report:
    file: str
    lang: str
    words: int
    findings: list[Finding]

    @property
    def errors(self) -> int:
        return sum(f.level == "error" for f in self.findings)


def run(raw: str, file: str = "-", cfg: Config | None = None, lang: str | None = None,
        only: set[str] | None = None) -> Report:
    cfg = cfg or Config()
    doc = document(raw, lang or cfg.lang)
    sup = _suppressed(raw)
    found: list[Finding] = []
    for r in rules.load():
        if r.lang not in (doc.lang, "any") or r.id in cfg.disable or (only and r.id not in only):
            continue
        level = cfg.levels.get(r.id, r.level)
        if level == "off":
            continue
        hits: list[Finding] = []
        if r.pattern is not None:
            for ln in doc.lines:
                if r.skip and r.skip(ln):
                    continue
                for m in r.pattern.finditer(ln.scan):
                    if not m.group(0).strip():
                        continue
                    rep = r.replace(_RawMatch(m, ln.raw), ln) if callable(r.replace) else r.replace
                    hits.append(r.finding(ln.n, m.start(), m.end(), ln.raw[m.start():m.end()], rep))
        if r.scan is not None:
            hits += r.scan(doc, r, cfg.thresholds.get(r.id, r.threshold))
        for f in hits:
            allowed = sup.get(f.line, set())
            if allowed is None or r.id in allowed:
                continue
            found.append(f if f.level == level else Finding(**{**asdict(f), "level": level}))
    found.sort(key=lambda f: (f.line, f.start, f.rule))
    return Report(file, doc.lang, text.word_count(raw), found)


def orig_path(file: str) -> str:
    p = Path(file)
    return str(p.with_name(f"{p.stem}.orig{p.suffix}"))


def _fix_text(f: Finding) -> str:
    if f.kind == "rewrite" or f.replacement is None:
        return f"rewrite: {f.todo}"
    if f.replacement == "":
        return f"{f.kind}: delete"
    return f"{f.kind}: {json.dumps(f.replacement, ensure_ascii=False)}"


def gate_command(f: Finding, file: str) -> str:
    return f"slopstop gate {orig_path(file)} {file} --allow span --lines {f.line}"


def render_text(reps: list[Report]) -> str:
    out = []
    errors = warns = auto = sug = 0
    for rep in reps:
        for f in rep.findings:
            out.append(f"{rep.file}:{f.line}:{f.start + 1}  {f.level:<5}  {f.rule:<16} "
                       f"{json.dumps(f.text.strip()[:80], ensure_ascii=False)}"
                       + (f"  ({f.note})" if f.note else ""))
            out.append(f"  why: {f.why}")
            out.append(f"  fix: {_fix_text(f)}")
            if f.kind == "rewrite" or f.replacement is None:
                out.append(f"  check: {gate_command(f, rep.file)}")
            errors += f.level == "error"
            warns += f.level == "warn"
            auto += f.kind == "auto" and f.replacement is not None
            sug += f.kind == "suggest" and f.replacement is not None
    rewrites = [rep.file for rep in reps if any(f.kind == "rewrite" or f.replacement is None for f in rep.findings)]
    for file in rewrites:
        out.append(f"Before a rewrite, keep the current text for its check: cp {file} {orig_path(file)}")
    out.append(f"{errors} errors, {warns} warnings in {len(reps)} file{'s' * (len(reps) != 1)}; "
               f"{auto} fixable with fix, {sug} more with fix --suggested")
    return "\n".join(out) + "\n"


def to_json(reps: list[Report]) -> str:
    def one(rep: Report) -> dict:
        fs = []
        for f in rep.findings:
            d = asdict(f)
            d["column"] = f.start + 1
            d["fix"] = _fix_text(f)
            if f.kind == "rewrite" or f.replacement is None:
                d["check"] = gate_command(f, rep.file)
            fs.append(d)
        return {"file": rep.file, "lang": rep.lang, "words": rep.words, "errors": rep.errors,
                "findings": fs}
    return json.dumps([one(r) for r in reps], indent=1, ensure_ascii=False)
