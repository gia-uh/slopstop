import json

from slopstop import register, tells


def test_percentile_interpolates():
    assert register.percentile([1, 2, 3, 4], 0.5) == 2.5
    assert register.percentile([5], 0.99) == 5


def test_long_paragraph_measures_each_paragraph():
    raw = "One two three.\n\nFour five six seven.\n"
    ms = tells.CATALOG["long-paragraph"].measure(raw, [])
    assert [m.value for m in ms] == [3, 4]
    assert ms[1].spans[0].line == 3 and ms[1].where == "¶2"


def test_build_register_has_bands_for_every_tell(corpus):
    reg = register.build(corpus, "test")
    assert reg["name"] == "test" and reg["lang"] == "en"
    assert reg["texts"] + reg["holdout"] == 40
    band = reg["tells"]["long-paragraph"]
    assert band["p50"] <= band["p90"] <= band["p99"]
    assert set(reg["tells"]) == set(tells.CATALOG)


def test_holdout_split_is_deterministic(corpus):
    files = sorted(corpus.glob("*.md"))
    a = register.split_holdout(files, 0.2)
    b = register.split_holdout(list(reversed(files)), 0.2)
    assert [f.name for f in a[1]] == [f.name for f in b[1]]
    assert 0 < len(a[1]) < len(files)


def test_load_by_path_and_name(corpus, tmp_path, monkeypatch):
    reg = register.build(corpus, "mine")
    regs = tmp_path / "registers"
    regs.mkdir()
    (regs / "mine.json").write_text(json.dumps(reg))
    monkeypatch.chdir(tmp_path)
    assert register.load("mine")["name"] == "mine"
    assert register.load(str(regs / "mine.json"))["name"] == "mine"
