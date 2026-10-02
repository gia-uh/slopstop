import json

import pytest

from slopstop import cli, detect, register, tells

BAND = {"p0.5": 1.0, "p5": 2.0, "p50": 5.0, "p90": 8.0, "p95": 9.0, "p99": 10.0, "p99.5": 11.0}


def tell(sided):
    return tells.Tell("t", "doc", sided, "span", "high", "low", lambda r, p: [])


@pytest.mark.parametrize("sided,value,expected", [
    ("upper", 10.0, "optional"), ("upper", 8.0, None), ("upper", 8.5, "optional"), ("upper", 10.5, "required"),
    ("two", 11.0, "optional"), ("two", 9.5, "optional"), ("two", 11.5, "required"),
    ("two", 1.5, "optional"), ("two", 0.5, "optional"), ("two", 5.0, None),
])
def test_severity_bands(sided, value, expected):
    assert detect.severity(tell(sided), value, BAND) == expected


def test_orig_path():
    assert detect.orig_path("dir/post.md") == "dir/post.orig.md"


def wall(words: int) -> str:
    return "The " + " ".join(["stone"] * (words - 1)) + ".\n"


def test_wall_of_text_is_required_with_instruction(corpus):
    reg = register.build(corpus, "t")
    rep = detect.detect(wall(600), reg, "post.md")
    f = [x for x in rep["findings"] if x["tell"] == "long-paragraph"][0]
    assert f["severity"] == "required"
    assert "Insert paragraph breaks only" in f["instruction"]
    assert f["check"] == "slopstop gate post.orig.md post.md --allow breaks"
    assert f["spans"][0]["line"] == 1


def test_short_text_skips_rate_tells_with_note(corpus):
    reg = register.build(corpus, "t")
    rep = detect.detect("A short note of a few words.\n", reg, "n.md")
    assert any("150" in n for n in rep["notes"])
    assert all(tells.CATALOG[f["tell"]].unit == "paragraph" for f in rep["findings"])


def test_language_mismatch_is_noted(corpus):
    reg = register.build(corpus, "t")
    es = "El perro de la casa que es muy grande y la mesa de la cocina. " * 30
    rep = detect.detect(es, reg, "es.md")
    assert any("language" in n for n in rep["notes"])


def test_cli_profile_then_detect(corpus, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["profile", str(corpus), "--name", "mine"]) == 0
    assert (tmp_path / "registers" / "mine.json").exists()
    post = tmp_path / "post.md"
    post.write_text(wall(600))
    assert cli.main(["detect", str(post), "--register", "mine"]) == 1
    out = capsys.readouterr().out
    assert "required" in out and "cp " in out
    assert cli.main(["detect", str(post), "--register", "mine", "--json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert "long-paragraph" in {f["tell"] for f in data["findings"]}


def test_cli_detect_missing_file_exits_2(tmp_path, capsys):
    assert cli.main(["detect", str(tmp_path / "nope.md"), "--register", "x"]) == 2
    assert "nope.md" in capsys.readouterr().err


def test_degenerate_band_is_skipped_with_note(corpus):
    reg = register.build(corpus, "t")
    reg["tells"]["bold"] = {k: 0.0 for k in reg["tells"]["bold"]} | {"n": 40}
    raw = "Some **bold** words here. " * 60
    rep = detect.detect(raw, reg, "b.md")
    assert "bold" not in {f["tell"] for f in rep["findings"]}
    assert any("bold" in n and "not measurable" in n for n in rep["notes"])


def test_low_side_is_optional_unless_the_tell_says_low_is_slop():
    em = tells.CATALOG["em-dash"]
    spread = tells.CATALOG["sentence-spread"]
    assert detect.severity(em, 0.5, BAND) == "optional"        # below p0.5: fewer em dashes is not slop
    assert detect.severity(spread, 0.5, BAND) == "required"    # too-uniform sentences is
    assert detect.severity(em, 11.5, BAND) == "required"
