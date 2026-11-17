"""Every rule's own examples: what must fire, what must stay quiet, what fix must produce."""
import pytest

from slopstop import check, fix, rules

CATALOG = rules.load()
IDS = sorted({r.id for r in CATALOG})


def _lang(r: rules.Rule) -> str:
    return "en" if r.lang == "any" else r.lang


def _only(r: rules.Rule) -> check.Config:
    return check.Config(disable=[i for i in IDS if i != r.id])


def _cases(attr):
    return [pytest.param(r, ex, id=f"{r.id}-{r.lang}-{i}") for r in CATALOG for i, ex in enumerate(getattr(r, attr))]


def test_every_rule_has_examples():
    for r in CATALOG:
        assert r.fires and r.quiet, f"{r.id} ({r.lang}) needs fires and quiet examples"
        assert r.why.endswith(".") and r.todo.endswith("."), r.id
        if r.kind in ("auto", "suggest"):
            assert r.fixes, f"{r.id} ({r.lang}) has a replacement and needs fixes examples"


@pytest.mark.parametrize("rule,example", _cases("fires"))
def test_fires(rule, example):
    rep = check.run(example, cfg=_only(rule), lang=_lang(rule))
    assert [f.rule for f in rep.findings] and {f.rule for f in rep.findings} == {rule.id}, example


@pytest.mark.parametrize("rule,example", _cases("quiet"))
def test_quiet(rule, example):
    rep = check.run(example, cfg=_only(rule), lang=_lang(rule))
    assert rep.findings == [], [f.text for f in rep.findings]


@pytest.mark.parametrize("rule,pair", _cases("fixes"))
def test_fixes(rule, pair):
    before, after = pair
    out, applied = fix.apply(before, ("auto", "suggest"), _only(rule), _lang(rule))
    assert applied and out == after


@pytest.mark.parametrize("rule,pair", _cases("fixes"))
def test_fix_touches_only_its_lines(rule, pair):
    before = "Untouched first line.\n\n" + pair[0] + "\n\nUntouched last line.\n"
    out, _ = fix.apply(before, ("auto", "suggest"), _only(rule), _lang(rule))
    assert out.startswith("Untouched first line.\n\n") and out.endswith("\n\nUntouched last line.\n")


def test_rule_ids_are_kebab_case():
    for r in CATALOG:
        assert r.id == r.id.lower() and " " not in r.id
