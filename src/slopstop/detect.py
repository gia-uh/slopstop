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
    if value > band[rhi] or (value < band[rlo] and tell.low_required):
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
    lo_key, hi_key = ("p0.5", "p99.5") if sev == "required" else ("p5", "p95")
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
        if band["p0.5"] == band["p99.5"]:
            notes.append(f"{name} is not measurable on register {reg['name']}: every human text "
                         f"there has the same value ({band['p50']}), so it was skipped.")
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
