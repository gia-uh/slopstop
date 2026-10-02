import json

import pytest

from slopstop import cli, instruct
from slopstop.cli import UsageError

SEGS = [{"kind": "content", "text": "Slop is a human failure."},
        {"kind": "directive", "text": "the title is No Such Thing"},
        {"kind": "request", "text": "add examples from the literature"},
        {"kind": "content", "text": "Nobody is behind the model."}]


def test_prepared_dictation_inlines_directives_drops_requests():
    p = instruct.prepared_dictation(SEGS)
    assert "{{the title is No Such Thing}}" in p
    assert "literature" not in p


@pytest.fixture
def files(tmp_path):
    t = tmp_path / "note.md"
    t.write_text("Slop is a human failure. the title is No Such Thing add examples from the literature "
                 "Nobody is behind the model.\n")
    s = tmp_path / "note.split.json"
    s.write_text(json.dumps({"segments": SEGS}))
    o = tmp_path / "note.draft.md"
    o.write_text("# No Such Thing\n\nSlop is a human failure. Nobody is behind the model.\n")
    return t, s, o


def test_split_task_names_output_and_check(files):
    t, _, _ = files
    out = instruct.render("split", [str(t)])
    assert str(t.with_name("note.split.json")) in out
    assert f"slopstop gate {t} --split" in out
    assert "verbatim" in out.lower()


def test_dictation_task_carries_prepared_text_and_ratio(files):
    t, s, _ = files
    out = instruct.render("dictation", [str(t)], split=str(s))
    assert "{{the title is No Such Thing}}" in out and "literature" not in out
    assert "--ratio 0.35:1.25" in out and "--split" in out


def test_dictation_without_split_is_usage_error(files):
    t, _, _ = files
    with pytest.raises(UsageError):
        instruct.render("dictation", [str(t)])


def test_judge_with_split_lists_set_aside(files):
    t, s, o = files
    out = instruct.render("judge", [str(t), str(o)], split=str(s))
    assert "add examples from the literature" in out
    assert "slopstop check-quotes" in out and "--source" in out and "--output" in out


def test_every_task_ends_with_a_check(files):
    t, s, o = files
    for task, args in [("restyle", [t]), ("critic", [t]), ("polish", [t])]:
        out = instruct.render(task, [str(a) for a in args])
        assert "slopstop " in out.strip().splitlines()[-1]


def test_cli_wrong_file_count(files):
    t, _, _ = files
    assert cli.main(["instruct", "judge", str(t)]) == 2


def test_polish_task_carries_the_text_and_asks_for_it_back(files):
    t, _, _ = files
    out = instruct.render("polish", [str(t)])
    assert "Slop is a human failure." in out
    assert "cp " not in out and "in place" not in out
    assert "--allow polish --budget 0.15" in out.strip().splitlines()[-1]
