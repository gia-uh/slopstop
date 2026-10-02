"""Tasks for the agent, built for the files in hand. The tool never runs them."""
from importlib import resources
from pathlib import Path
from string import Template

from slopstop import text
from slopstop.cli import UsageError
from slopstop.detect import orig_path

TASKS = {"split": 1, "dictation": 1, "restyle": 1, "judge": 2, "critic": 1, "polish": 1}


def _read(p: str) -> str:
    if not Path(p).is_file():
        raise UsageError(f"no such file: {p}")
    return Path(p).read_text(encoding="utf-8", errors="replace")


def _segments(split: str | None) -> list[dict]:
    if not split:
        raise UsageError("this task needs --split, the JSON written by 'instruct split'")
    from slopstop.cli import load_split
    return load_split(split)


def prepared_dictation(segments: list[dict]) -> str:
    parts = [s["text"].strip() if s["kind"] == "content" else "{{" + s["text"].strip() + "}}"
             for s in segments if s["kind"] != "request"]
    return " ".join(parts)


def _sibling(path: str, suffix: str) -> str:
    p = Path(path)
    return str(p.with_name(f"{p.stem}{suffix}"))


def render(task: str, files: list[str], split: str | None = None, budget: float = 0.15) -> str:
    if task not in TASKS:
        raise UsageError(f"unknown task {task!r}; one of {', '.join(TASKS)}")
    if len(files) != TASKS[task]:
        raise UsageError(f"'instruct {task}' takes {TASKS[task]} file(s), got {len(files)}")
    f = files[0]
    raw = _read(f)
    v = {"file": f, "words": text.word_count(raw), "text": raw.strip()}
    if task == "split":
        v["out"] = _sibling(f, ".split.json")
    elif task == "dictation":
        prepared = prepared_dictation(_segments(split))
        v.update(split=split, out=_sibling(f, ".draft.md"), text=prepared,
                 words=len(text.tokenize(prepared)))
    elif task == "restyle":
        v["out"] = _sibling(f, ".restyled.md")
    elif task == "critic":
        v["out"] = _sibling(f, ".critic.json")
    elif task == "polish":
        v.update(orig=orig_path(f), budget=budget, budget_pct=f"{budget:.0%}")
    elif task == "judge":
        out_text = _read(files[1])
        v.update(source=f, output=files[1], source_text=raw.strip(), output_text=out_text.strip(),
                 out=_sibling(files[1], ".judge.json"), set_aside="", set_aside_rule="")
        if split:
            aside = [s["text"] for s in _segments(split) if s["kind"] != "content"]
            v["set_aside_rule"] = (" Passages listed under SET ASIDE were removed on purpose; "
                                   "do not report them as dropped.")
            v["set_aside"] = "\nSET ASIDE:\n\n" + "\n".join(f"- {a}" for a in aside) + "\n"
    tmpl = resources.files("slopstop").joinpath("instructions", f"{task}.md").read_text()
    return Template(tmpl).substitute(v)
