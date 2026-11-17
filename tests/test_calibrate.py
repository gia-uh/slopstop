from pathlib import Path

from slopstop import calibrate, cli, rules

DOCS = Path(__file__).parent.parent / "docs"


def _para(words: int) -> str:
    return " ".join(["The cache holds one value."] * (words // 5))


def test_threshold_is_strictest_that_fits(tmp_path):
    # ten files: nine with 100-word paragraphs, one with a 300-word paragraph
    raws = [_para(100) + "\n\n" + _para(100) + "\n"] * 9 + [_para(300) + "\n"]
    res = calibrate.measure(raws, "t", share=0.1)
    assert res["thresholds"]["long-paragraph"]["suggested"] == 100
    res = calibrate.measure(raws, "t", share=0.0)
    assert res["thresholds"]["long-paragraph"]["suggested"] == 300


def test_fire_shares(tmp_path):
    raws = ["Great question! " + _para(200) + "\n"] + [_para(200) + "\n"] * 3
    res = calibrate.measure(raws, "t")
    assert res["files"] == 4 and res["rules"]["opener-filler/en"]["share"] == 0.25


def test_write_config_keeps_other_settings(tmp_path):
    cfg = tmp_path / "slopstop.toml"
    cfg.write_text('disable = ["em-dash"]\n[levels]\nhype = "warn"\n[thresholds]\nflat-rhythm = 5\n')
    calibrate.write_config(cfg, {"long-paragraph": 150})
    import tomllib
    data = tomllib.loads(cfg.read_text())
    assert data == {"disable": ["em-dash"], "levels": {"hype": "warn"},
                    "thresholds": {"flat-rhythm": 5, "long-paragraph": 150}}


def test_calibrate_cli(tmp_path, capsys):
    (tmp_path / "set").mkdir()
    for i in range(3):
        (tmp_path / "set" / f"{i}.md").write_text(_para(200) + "\n")
    out = tmp_path / "cal.json"
    assert cli.main(["calibrate", str(tmp_path / "set"), "--out", str(out), "--write",
                     str(tmp_path / "slopstop.toml")]) == 0
    assert out.exists() and "[thresholds]" in (tmp_path / "slopstop.toml").read_text()
    assert cli.main(["calibrate", str(tmp_path / "missing")]) == 2


def test_every_tuned_rule_has_a_threshold():
    for r in rules.load():
        assert (r.tune is None) == (r.threshold is None), r.id


def test_rules_doc_is_current():
    cals = [__import__("json").loads((DOCS / "calibration" / f"{s}.json").read_text())
            for s in ("en-human", "en-agent", "es-human", "es-agent")]
    assert (DOCS / "rules.md").read_text() == calibrate.rules_markdown(cals), "run make rules-doc"
