"""Registers: per-tell percentiles counted over a folder of human-written texts."""
import hashlib
import json
from pathlib import Path

from slopstop import tells, text
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
            any(f["severity"] == "required"
                for f in detect(h.read_text(errors="replace"), reg, str(h))["findings"])
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
