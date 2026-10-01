# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "transformers>=4.44", "numpy"]
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# ///
"""Score files with an open AI-text classifier, paragraph by paragraph.

usage: uv run detect.py MODEL_ID OUT.json FILE...
Writes {file: {"doc": p_ai_mean_weighted, "paras": [p_ai, ...]}}.
"""
import json, re, sys
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_id, out = sys.argv[1], Path(sys.argv[2])
files = sys.argv[3:]
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSequenceClassification.from_pretrained(model_id).eval()
labels = {i: l.lower() for i, l in model.config.id2label.items()}
ai_idx = next((i for i, l in labels.items() if any(k in l for k in ("ai", "machine", "fake", "generated", "1"))), 1)
print("labels", labels, "ai_idx", ai_idx, file=sys.stderr)

FM = re.compile(r"\A---\n.*?\n---\n", re.S)


def paras(text):
    text = FM.sub("", text)
    ps = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 25]
    return ps or [text.strip()]


res = json.loads(out.read_text()) if out.exists() else {}
with torch.no_grad():
    for f in files:
        if f in res:
            continue
        ps = paras(Path(f).read_text(errors="replace"))
        probs, weights = [], []
        for i in range(0, len(ps), 8):
            enc = tok(ps[i:i + 8], truncation=True, max_length=512, padding=True, return_tensors="pt")
            p = torch.softmax(model(**enc).logits, -1)[:, ai_idx].tolist()
            probs += p
        weights = [len(p.split()) for p in ps]
        doc = sum(p * w for p, w in zip(probs, weights)) / sum(weights)
        res[f] = {"doc": round(doc, 4), "paras": [round(p, 4) for p in probs]}
        out.write_text(json.dumps(res, indent=0))
print("done", len(res), file=sys.stderr)
