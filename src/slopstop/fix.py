"""Apply the replacements that findings carry. Every edit stays inside one line."""
from slopstop.check import Config, run
from slopstop.rules import Finding


def _join(left: str, rep: str, right: str) -> str:
    """Splice a replacement in, fixing only the spaces at its two edges."""
    if rep == "":
        if not right.strip() or right[:1] in ".,;:!?":
            left = left.rstrip(" \t")
        elif not left.strip() or left.endswith((" ", "\t")):
            right = right.lstrip(" \t")
    return left + rep + right


def apply(raw: str, kinds: tuple[str, ...] = ("auto",), cfg: Config | None = None,
          lang: str | None = None) -> tuple[str, list[Finding]]:
    """The text with every applicable replacement made, and the findings applied."""
    rep = run(raw, cfg=cfg, lang=lang)
    lines = raw.split("\n")
    by_line: dict[int, list[Finding]] = {}
    for f in rep.findings:
        if f.kind in kinds and f.replacement is not None and f.end > f.start:
            by_line.setdefault(f.line, []).append(f)
    applied, emptied = [], set()
    for n, fs in by_line.items():
        fs.sort(key=lambda f: (f.start, -f.end))
        keep, last = [], -1
        for f in fs:
            if f.start >= last:
                keep.append(f)
                last = f.end
        ln = lines[n - 1]
        for f in reversed(keep):
            ln = _join(ln[:f.start], f.replacement, ln[f.end:])
            applied.append(f)
        if ln.strip() in ("", "-", "*", "+") and lines[n - 1].strip():
            emptied.add(n)
        lines[n - 1] = ln
    kept: list[str] = []
    drop_blank = False
    for i, ln in enumerate(lines, 1):
        if i in emptied:
            # a line that held only deleted sentences goes, with one blank line next to it
            drop_blank = not kept or not kept[-1].strip()
            continue
        if drop_blank and not ln.strip():
            drop_blank = False
            continue
        drop_blank = False
        kept.append(ln)
    applied.sort(key=lambda f: (f.line, f.start))
    return "\n".join(kept), applied
