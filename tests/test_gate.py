from conftest import human_text

from slopstop import cli, gate

SRC = human_text(1, paras=2)  # varied words, so no 30-word run repeats inside the source


def test_unchanged_output_passes():
    assert gate.check_output(SRC, SRC).ok


def test_empty_output_fails_with_reason():
    r = gate.check_output(SRC, "")
    assert not r.ok and "empty" in r.failures[0]


def test_duplicate_block_fails():
    r = gate.check_output(SRC, SRC + "\n" + SRC, ratio=(0.1, 9))
    assert any("repeated" in f for f in r.failures)


def test_unbalanced_fence_fails_only_when_source_balanced():
    assert not gate.check_output(SRC, SRC + "\n```\ncode\n").ok
    bad_src = SRC + "\n```\ncode\n"
    assert gate.check_output(bad_src, bad_src).ok


def test_meta_text_on_first_line_fails_unless_in_source():
    out = "Here is the rewritten essay:\n\n" + SRC
    assert any("addressed to the user" in f for f in gate.check_output(SRC, out).failures)
    src2 = "Here is the resolution I find plausible.\n\n" + SRC
    assert gate.check_output(src2, src2).ok


def test_length_ratio_band():
    r = gate.check_output(SRC, SRC.split("\n\n")[0] + "\n")
    assert any("length ratio" in f for f in r.failures)


def test_ends_mid_sentence_relative_to_source():
    cut = SRC.rstrip()[:-12]
    assert any("mid-sentence" in f for f in gate.check_output(SRC, cut, ratio=(0.1, 9)).failures)
    assert gate.check_output(cut, cut).ok


def test_placeholders_must_survive_once():
    src = SRC + "\n[CODE-1]\n"
    assert any("[CODE-1]" in f for f in gate.check_output(src, SRC).failures)
    assert any("[CODE-1]" in f for f in gate.check_output(src, src + "\n[CODE-1]\n", ratio=(0.1, 9)).failures)


def test_check_input_truncation():
    assert not gate.check_input("A sentence that stops in the").ok
    r = gate.check_input("speech has no final period", transcript=True)
    assert r.ok and r.warnings


def test_cli_gate_pass_fail_and_missing(tmp_path, capsys):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text(SRC)
    b.write_text("")
    assert cli.main(["gate", str(a), str(a)]) == 0
    assert cli.main(["gate", str(a), str(b)]) == 1
    assert "FAIL" in capsys.readouterr().out
    assert cli.main(["gate", str(tmp_path / "x.md")]) == 2
