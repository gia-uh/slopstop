import json

from slopstop import check, cli

SLOP = "Great question! Caching is hard.\n\nIt may potentially fail. I hope this helps!\n"
CLEAN = "Caching is hard.\n\nIt may fail when two writers race.\n"


def test_exit_codes(tmp_path, capsys):
    (tmp_path / "a.md").write_text(SLOP)
    (tmp_path / "b.md").write_text(CLEAN)
    assert cli.main(["check", str(tmp_path / "a.md")]) == 1
    assert cli.main(["check", str(tmp_path / "b.md")]) == 0
    assert cli.main(["check", str(tmp_path / "missing.md")]) == 2
    out = capsys.readouterr().out
    assert "opener-filler" in out and "0 errors, 0 warnings in 1 file" in out


def test_warnings_do_not_fail(tmp_path):
    (tmp_path / "a.md").write_text("It works — but only on Linux.\n")
    assert cli.main(["check", str(tmp_path / "a.md")]) == 0


def test_json_has_columns_fixes_and_checks(tmp_path, capsys):
    (tmp_path / "a.md").write_text("Caching isn't a trick, it's a decision. It may potentially fail.\n")
    cli.main(["check", "--json", str(tmp_path / "a.md")])
    rep = json.loads(capsys.readouterr().out)[0]
    by = {f["rule"]: f for f in rep["findings"]}
    assert by["corrective"]["column"] == 9 and "gate" in by["corrective"]["check"]
    assert by["hedge-stack"]["replacement"] == "may" and "check" not in by["hedge-stack"]


def test_folder_scan(tmp_path, capsys):
    (tmp_path / "a.md").write_text(SLOP)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text(SLOP)
    (tmp_path / "a.orig.md").write_text(SLOP)
    assert cli.main(["check", str(tmp_path)]) == 1
    assert "in 2 files" in capsys.readouterr().out


def test_code_quotes_and_links_are_not_prose():
    raw = ("```\nGreat question! It may potentially fail.\n```\n\n"
           "> I hope this helps!\n\n"
           "See `It may potentially fail` and [the doc](https://x.dev/game-changer).\n")
    assert check.run(raw).findings == []


def test_allow_comment_covers_next_paragraph_only():
    raw = ("<!-- slopstop: allow hedge-stack -->\nIt may potentially fail.\n\n"
           "It may potentially fail.\n")
    rep = check.run(raw)
    assert [(f.rule, f.line) for f in rep.findings] == [("hedge-stack", 4)]


def test_off_on_region():
    raw = "<!-- slopstop: off -->\nGreat question! Fine.\n<!-- slopstop: on -->\n\nGreat question! Fine.\n"
    assert [f.line for f in check.run(raw).findings] == [5]


def test_config_found_upward(tmp_path):
    (tmp_path / "slopstop.toml").write_text('disable = ["opener-filler"]\n[levels]\nem-dash = "error"\n')
    (tmp_path / "d").mkdir()
    f = tmp_path / "d" / "a.md"
    f.write_text("Great question! It works — but only on Linux.\n")
    cfg = check.load_config(f.parent)
    rep = check.run(f.read_text(), cfg=cfg)
    assert [(x.rule, x.level) for x in rep.findings] == [("em-dash", "error")]


def test_config_in_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[tool.slopstop]\n[tool.slopstop.thresholds]\nlong-paragraph = 5\n')
    cfg = check.load_config(tmp_path)
    rep = check.run("One two three four five six seven.\n", cfg=cfg)
    assert [x.rule for x in rep.findings] == ["long-paragraph"]


def test_unknown_rule_in_config_is_usage_error(tmp_path):
    (tmp_path / "slopstop.toml").write_text('disable = ["no-such-rule"]\n')
    (tmp_path / "a.md").write_text(CLEAN)
    assert cli.main(["check", str(tmp_path / "a.md")]) == 2


def test_spanish_is_detected():
    raw = ("La caché es compartida por todos los procesos del servidor y por eso es rápida. "
           "Cabe destacar que la caché se vacía en cada escritura de los datos.\n")
    rep = check.run(raw)
    assert rep.lang == "es" and [f.rule for f in rep.findings] == ["meta-commentary"]


def test_fix_writes_orig_and_reaches_clean(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text(SLOP)
    assert cli.main(["fix", str(f)]) == 0
    assert (tmp_path / "a.orig.md").read_text() == SLOP
    assert f.read_text() == "Caching is hard.\n\nIt may fail.\n"
    assert cli.main(["check", str(f)]) == 0


def test_fix_dry_run_writes_nothing(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text(SLOP)
    cli.main(["fix", "--dry-run", str(f)])
    assert f.read_text() == SLOP and not (tmp_path / "a.orig.md").exists()
    assert "+It may fail." in capsys.readouterr().out


def test_fix_leaves_suggestions_unless_asked(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("It works — but only on Linux.\n")
    cli.main(["fix", str(f)])
    assert "—" in f.read_text()
    cli.main(["fix", "--suggested", str(f)])
    assert f.read_text() == "It works. But only on Linux.\n"


def test_fix_removes_a_line_left_empty(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# Title\n\nGreat question! Let's dive in.\n\nCaching is hard.\n")
    cli.main(["fix", str(f)])
    assert f.read_text() == "# Title\n\nCaching is hard.\n"


def test_rules_command(capsys):
    assert cli.main(["rules"]) == 0
    assert cli.main(["rules", "corrective"]) == 0
    assert cli.main(["rules", "nope"]) == 2
    assert "fires:" in capsys.readouterr().out


def test_fix_keeps_inline_code_inside_bold(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("Then **delete `cache/offset`** before you publish it.\n")
    cli.main(["fix", str(f)])
    assert f.read_text() == "Then delete `cache/offset` before you publish it.\n"


def test_curly_apostrophes_match():
    assert [x.rule for x in check.run("It’s worth noting that it fails.\n").findings] == ["meta-commentary"]


def test_fix_never_eats_masked_code(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("`host.com` — all of them return 403 errors today.\n\nThe example — `split` (for `A`).\n")
    cli.main(["fix", "--suggested", str(f)])
    out = f.read_text()
    assert "`host.com`" in out and "`split`" in out


def test_fix_leaves_code_spacing_alone(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("**Note:** run `set -a; . env` first. It may potentially fail.\n")
    cli.main(["fix", str(f)])
    assert f.read_text() == "Note: run `set -a; . env` first. It may fail.\n"


def test_rewrite_findings_say_to_keep_the_original(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text("Caching isn't a trick, it's a decision.\n")
    cli.main(["check", str(f)])
    assert f"cp {f} {tmp_path / 'a.orig.md'}" in capsys.readouterr().out


def test_quoted_phrases_are_mentions():
    raw = 'Fix turns "may potentially" into "may", and “I hope this helps!” goes.\n'
    assert check.run(raw).findings == []


def test_bold_lead_in_of_a_list_item_is_a_label():
    raw = "- **Never hiding.** No tool here helps hide provenance.\n- **Annoyance** matters.\n"
    assert check.run(raw).findings == []


def test_paths_are_not_slash_pairs():
    raw = "Copy skills/slopstop/ and src/rules into place, then read/write, plan/execute.\n"
    assert check.run(raw, cfg=check.Config(thresholds={"slash-pairs": 1})).findings[0].note == "2 word/word pairs"


def test_a_quote_may_wrap_across_lines():
    raw = 'Fix deletes "I hope\nthis helps!", and turns "may potentially"\ninto "may".\n'
    assert check.run(raw).findings == []
