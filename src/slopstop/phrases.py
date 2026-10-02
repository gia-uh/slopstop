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
    topics: dict[str, set] = {}
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
            for g in seen:
                topics.setdefault(g, set()).add(f.stem)
    proper = {t for t, c in tok.items() if c >= 3 and cap[t] / c >= 0.6}
    return counts, docs, topics, proper, max(total, 1)


def build(human: Path, models: list[Path], max_n: int = 3, min_count: int = 3,
          min_docs: int = 2, min_topics: int = 3, min_ratio: float = 5.0, top: int = 200) -> list[dict]:
    """min_topics counts distinct file names: model folders that write on the same topics
    share file names, so a phrase seen under one name only is that topic's vocabulary."""
    hc, _, _, hp, ht = _corpus([human], max_n)
    mc, md, mt_topics, mp, mt = _corpus(models, max_n)
    proper = hp | mp
    kept = []
    for g, c in mc.items():
        if c < min_count or md[g] < min_docs or len(mt_topics[g]) < min_topics:
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
