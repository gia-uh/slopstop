#!/usr/bin/env python3
"""One row per model, split by task (rewrite of Claude prose / dictation to prose)."""
import importlib.machinery, importlib.util, json, statistics, sys
from pathlib import Path

W = Path("/home/apiad/Workspace")
spec = importlib.util.spec_from_loader("sc", importlib.machinery.SourceFileLoader("sc", str(W / "bin/slopcheck")))
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
CORR = sc.UNSLOP_TERMS["9 corrective definition"]
NOUNS = sc.UNSLOP_TERMS["26 abstract metaphor nouns"]
ROOT = Path(__file__).parent
DET = json.loads((ROOT / "det-tmr.json").read_text()) if (ROOT / "det-tmr.json").exists() else {}


def metrics(p):
    raw = p.read_text(encoding="utf-8", errors="replace")
    pr = sc.strip_markdown(raw); w = sc.tokenize(pr); n = max(len(w), 1)
    mk = sc.count_markers(raw, pr, w)
    c, _, _ = sc.count_terms([str(p)], CORR + NOUNS)
    return {"words": len(w), "em": mk["em_dash"], "corr": sum(c[t] for t in CORR) / n * 1000,
            "nouns": sum(c[t] for t in NOUNS) / n * 1000, "colon": mk["mid_sentence_colon"],
            "slen": mk["sentence_len_mean"], "sd": mk["sentence_len_stdev"]}


def row(files, slug=None):
    v = []
    for f in files:
        m = metrics(f)
        m["det"] = DET.get(str(f), {}).get("doc")
        meta = f.with_suffix(".json")
        if meta.exists():
            u = json.loads(meta.read_text()).get("usage") or {}
            m["cost"] = (u.get("cost") or 0) / max(m["words"], 1) * 1000
        j = ROOT / "judge" / f.parent.name / f"{f.stem}.json"
        if j.exists():
            jd = json.loads(j.read_text()); m["drop"] = jd["dropped_n"]; m["inv"] = jd["invented_n"]
        v.append(m)
    mean = lambda k: statistics.mean([x[k] for x in v if x.get(k) is not None]) if any(x.get(k) is not None for x in v) else float("nan")
    return len(v), {k: mean(k) for k in ("words", "em", "corr", "nouns", "colon", "slen", "sd", "det", "drop", "inv", "cost")}


COLS = ("words", "em", "corr", "nouns", "colon", "slen", "sd", "det", "drop", "inv", "cost")
FMT = {"words": "{:6.0f}", "cost": "{:7.4f}", "det": "{:5.2f}", "drop": "{:5.1f}", "inv": "{:5.1f}"}


def show(title, prefix):
    print(f"\n## {title}\n")
    print("| model | n | " + " | ".join(COLS) + " |")
    print("|" + "---|" * (len(COLS) + 2))
    rows = []
    for d in sorted((ROOT / "outputs").iterdir()):
        files = sorted(d.glob(f"{prefix}*.md"))
        if files:
            rows.append((d.name.replace("__", "/"), *row(files)))
    src = sorted((ROOT / "inputs").glob(f"{prefix}*.md"))
    rows.append(("**input**", *row(src)))
    for name, n, r in rows:
        print(f"| {name} | {n} | " + " | ".join(FMT.get(k, "{:5.2f}").format(r[k]) for k in COLS) + " |")


alex = sorted((W / "vault/Efforts/Areas/Writing/voice/corpus/slop/alex-en").glob("*.md"))
n, a = row(alex)
print("Alex published (%d posts): " % n + ", ".join(f"{k}={a[k]:.2f}" for k in ("em", "corr", "nouns", "colon", "slen", "sd")))
show("Rewrite of uninstructed Claude essays", "claude-")
show("Dictation to English prose", "dict-")
