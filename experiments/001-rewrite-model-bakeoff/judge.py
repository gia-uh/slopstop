#!/usr/bin/env python3
"""Fidelity check: list what each rewrite dropped from its source and what it invented.

A detector that quotes, never a quality score. Quotes are verified against the
texts before they count. Writes judge/<model-slug>/<input>.json.
"""
import json, re, sys, time, concurrent.futures as cf
from pathlib import Path
import urllib.request

ROOT = Path(__file__).parent
import os
KEY = os.environ["JUDGE_API_KEY"]
JUDGE = os.environ.get("JUDGE_MODEL", "deepseek-v4-pro")
# Any OpenAI-compatible endpoint. The 2026-10-01 run used OpenCode Zen.
URL = os.environ.get("JUDGE_URL", "https://opencode.ai/zen/v1/chat/completions")

PROMPT = """You compare a SOURCE text with a REWRITE of it. The source may be a Spanish or English voice transcript, or an English draft; the rewrite is English prose.

List:
1. "dropped": distinct ideas, claims, examples or opinions present in the SOURCE that are missing from the REWRITE. Ignore filler, repetition and false starts.
2. "invented": distinct claims, facts, examples, anecdotes or opinions in the REWRITE that are not in the SOURCE. Rephrasing, translation and merging of existing points do not count.

For each item give a short description and an exact quote (5-25 words, copied verbatim) from the text where it appears: from the SOURCE for dropped items, from the REWRITE for invented items.

Answer with JSON only: {"dropped": [{"what": "...", "quote": "..."}], "invented": [{"what": "...", "quote": "..."}]}

SOURCE:
<<<
%s
>>>

REWRITE:
<<<
%s
>>>"""

norm = lambda s: re.sub(r"\W+", " ", s.lower()).strip()


def call(prompt):
    body = {"model": JUDGE, "messages": [{"role": "user", "content": prompt}], "max_tokens": 12000,
            "temperature": 0}
    for _ in range(3):
        try:
            req = urllib.request.Request(URL,
                data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": "slopstop-bakeoff/0.1"})
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            txt = d["choices"][0]["message"]["content"]
            txt = txt[txt.find("{"): txt.rfind("}") + 1]
            return json.loads(txt)
        except Exception as e:  # noqa: BLE001
            err = str(e); time.sleep(3)
    raise RuntimeError(err)


def job(out_md):
    slug, stem = out_md.parent.name, out_md.stem
    dest = ROOT / "judge" / slug / f"{stem}.json"
    if dest.exists():
        return "skip", slug, stem
    src = (ROOT / "inputs" / f"{stem}.md").read_text()
    rew = out_md.read_text()
    try:
        r = call(PROMPT % (src, rew))
    except Exception as e:  # noqa: BLE001
        return f"FAIL {e}", slug, stem
    ns, nr = norm(src), norm(rew)
    for k, hay in (("dropped", ns), ("invented", nr)):
        items = r.get(k) or []
        for it in items:
            it["verified"] = bool(norm(it.get("quote", ""))) and norm(it.get("quote", "")) in hay
        r[k] = items
        r[k + "_n"] = sum(it["verified"] for it in items)
        r[k + "_unverified"] = sum(not it["verified"] for it in items)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(r, indent=1, ensure_ascii=False))
    return "ok", slug, stem


if __name__ == "__main__":
    outs = sorted((ROOT / "outputs").glob("*/*.md"))
    with cf.ThreadPoolExecutor(8) as ex:
        for st, slug, stem in ex.map(job, outs):
            print(st[:4], slug, stem, st[4:][:150], flush=True)
    print("ALLDONE", flush=True)
