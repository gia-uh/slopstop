"""Agent-written JSON that is valid JSON but the wrong shape exits 2 with a message."""
import json

import pytest

from slopstop import cli


@pytest.fixture
def note(tmp_path):
    t = tmp_path / "t.md"
    t.write_text("A transcript with a few words in it for the test to use.\n")
    return t


def run(capsys, argv):
    rc = cli.main(argv)
    return rc, capsys.readouterr().err


def test_check_quotes_with_string_items(tmp_path, note, capsys):
    j = tmp_path / "j.json"
    j.write_text(json.dumps({"dropped": ["a bare string"]}))
    rc, err = run(capsys, ["check-quotes", str(j), "--source", str(note)])
    assert rc == 2 and "slopstop:" in err


@pytest.mark.parametrize("segments", [[{"kind": "content"}], ["just a string"], {"kind": "content"}])
def test_split_with_bad_segments(tmp_path, note, capsys, segments):
    s = tmp_path / "s.json"
    s.write_text(json.dumps({"segments": segments}))
    assert run(capsys, ["gate", str(note), "--split", str(s)])[0] == 2
    assert run(capsys, ["gate", str(note), str(note), "--split", str(s)])[0] == 2
    assert run(capsys, ["instruct", "dictation", str(note), "--split", str(s)])[0] == 2


def test_unmask_with_a_list(tmp_path, note, capsys):
    c = tmp_path / "c.json"
    c.write_text(json.dumps(["[CODE-1]"]))
    assert run(capsys, ["unmask", str(note), "--code", str(c)])[0] == 2


def test_register_without_tells(tmp_path, note, capsys):
    r = tmp_path / "r.json"
    r.write_text(json.dumps({"name": "x"}))
    assert run(capsys, ["detect", str(note), "--register", str(r)])[0] == 2
