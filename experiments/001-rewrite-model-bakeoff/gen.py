#!/usr/bin/env python3
"""Rewrite bake-off: every model rewrites every input with one fixed prompt per task.

outputs/<model-slug>/<input>.md plus <input>.json (usage, cost, latency, error).
Skips outputs that already exist, so a rerun only fills gaps.
"""
import json, os, sys, time, concurrent.futures as cf
from pathlib import Path
import urllib.request

ROOT = Path(__file__).parent
KEY = os.environ.get("OPENROUTER_API_KEY") or Path(os.environ["OPENROUTER_KEY_FILE"]).read_text().strip()

MODELS = [
    "deepseek/deepseek-v4-flash", "deepseek/deepseek-v4-pro", "deepseek/deepseek-v4.1-flash",
    "qwen/qwen3.7-flash", "qwen/qwen3.8-flash", "qwen/qwen3-235b-a22b-2507",
    "mistralai/mistral-small-2603", "mistralai/mistral-medium-3.1", "mistralai/mistral-large-2512",
    "google/gemma-4-31b-it", "moonshotai/kimi-k2.6", "z-ai/glm-5.3-flash", "minimax/minimax-m3",
    "openai/gpt-oss-120b", "xiaomi/mimo-v2.6-flash", "cohere/command-a-plus",
    "thinkingmachines/inkling-small", "nousresearch/hermes-4-405b", "thedrummer/cydonia-24b-v4.1",
    "anthropic/claude-sonnet-5.5",  # reference only: watermarked, never a candidate
]

PROMPT_DICTATION = """Below is a voice transcript the author dictated. It may be in Spanish or English, and it contains speech-to-text errors, repetitions and false starts.

Turn it into English prose for a blog post, in the author's own voice. Use only the ideas in the transcript, in the order he gave them. Keep his examples, his opinions and his phrasing wherever it survives translation. Remove repetitions, false starts and filler, and fix obvious transcription errors. Where he describes what the post should say ("I want to argue that..."), write the post itself, making those points directly in the first person. Do not add claims, examples, headings, or a conclusion he did not dictate.

Output only the prose.

TRANSCRIPT:
"""

PROMPT_REWRITE = """Below is a draft essay. Rewrite it so it reads like a thoughtful human author wrote it: plain words, sentences of varied length, concrete statements, a direct and personal tone.

Keep every claim, example and step of the argument, in the same order. Do not add facts, examples or anecdotes that are not in the draft.

Output only the rewritten essay as plain paragraphs.

DRAFT:
"""


def call(model, prompt):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 6000, "temperature": 0.7, "usage": {"include": True},
            "reasoning": {"enabled": False}}
    last = ""
    for attempt in range(3):
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json"})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(json.dumps(d["error"])[:400])
            text = d["choices"][0]["message"].get("content") or ""
            if not text.strip():
                raise RuntimeError("empty content")
            return text, {"latency_s": round(time.time() - t, 1), "usage": d.get("usage"), "error": None}
        except Exception as e:  # noqa: BLE001 — record and retry, then give up loudly
            err = getattr(e, "read", lambda: b"")().decode(errors="replace")[:400] or str(e)
            # Some reasoning-only models reject reasoning.enabled=false; retry with it dropped.
            if "reasoning" in err.lower() and "reasoning" in body:
                body.pop("reasoning")
                continue
            last = err
            time.sleep(3)
    return None, {"latency_s": None, "usage": None, "error": last}


def job(model, inp):
    slug = model.replace("/", "__")
    out = ROOT / "outputs" / slug / f"{inp.stem}.md"
    if out.exists():
        return model, inp.stem, "skip"
    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = (PROMPT_DICTATION if inp.stem.startswith("dict-") else PROMPT_REWRITE) + inp.read_text()
    text, meta = call(model, prompt)
    meta["model"] = model
    (out.with_suffix(".json")).write_text(json.dumps(meta, indent=1))
    if text is None:
        return model, inp.stem, "FAIL " + meta["error"][:120]
    out.write_text(text.strip() + "\n")
    return model, inp.stem, "ok"


if __name__ == "__main__":
    models = sys.argv[1:] or MODELS
    inputs = sorted((ROOT / "inputs").glob("*.md"))
    jobs = [(m, i) for m in models for i in inputs]
    with cf.ThreadPoolExecutor(12) as ex:
        for model, stem, status in ex.map(lambda a: job(*a), jobs):
            print(f"{status[:4]:4s} {model} {stem} {status[4:]}", flush=True)
    print("ALLDONE", flush=True)
