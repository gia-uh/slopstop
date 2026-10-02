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


def test_phrase_from_a_single_topic_is_excluded(tmp_path):
    # Same topic (file stem) in several model folders: a topic phrase, not a habit.
    h = write(tmp_path / "h", HUMAN + " odd degree and the vertex count. ", 4)
    models = []
    for arm in ("a", "b", "c"):
        d = tmp_path / arm
        d.mkdir()
        (d / "graphs.md").write_text("The odd degree is quiet. " * 40)
        models.append(d)
    grams = [p["gram"] for p in phrases.build(h, models)]
    assert not any("odd" in g for g in grams), grams
