"""slopstop command line. Each subcommand lives in its own module; this file only wires them."""
import argparse
import json
import sys
from pathlib import Path

from slopstop import __version__


class UsageError(Exception):
    """A user error: print the message and exit 2."""


def read(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise UsageError(f"no such file: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


def cmd_profile(args) -> int:
    from slopstop import phrases, register
    folder = Path(args.folder)
    if not folder.is_dir():
        raise UsageError(f"no such folder: {args.folder}")
    plist = phrases.build(folder, [Path(m) for m in args.model]) if args.model else None
    reg = register.build(folder, args.name, args.holdout, plist)
    out = Path(args.out or f"registers/{args.name}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    fp = reg["false_positive_rate"]
    print(f"{out}: {reg['texts']} texts, {reg['words']} words, {len(reg['phrases'])} phrases, "
          f"false-positive rate {fp if fp is not None else 'n/a'} on {reg['holdout']} held-out texts")
    return 0


def cmd_detect(args) -> int:
    from slopstop import detect, register
    raw = read(args.file)
    rep = detect.detect(raw, register.load(args.register), args.file)
    print(detect.to_json(rep) if args.json else detect.render_text(rep), end="" if not args.json else "\n")
    return 1 if any(f["severity"] == "required" for f in rep["findings"]) else 0


def cmd_gate(args) -> int:
    from slopstop import gate
    src = read(args.source)
    split = None
    if args.split:
        try:
            split = json.loads(read(args.split))["segments"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise UsageError(f"{args.split} is not a split file with a 'segments' list: {e}") from e
    if args.output is None:
        r = gate.check_split(src, split) if split is not None else gate.check_input(src, args.transcript)
    else:
        lo, _, hi = args.ratio.partition(":")
        try:
            ratio = (float(lo), float(hi))
            lines = [int(x) for x in args.lines.split(",")] if args.lines else None
        except ValueError as e:
            raise UsageError(f"bad --ratio or --lines: {e}") from e
        r = gate.check_output(src, read(args.output), args.allow, ratio, lines, args.budget, split)
    for w in r.warnings:
        print(f"warning: {w}")
    print("PASS" if r.ok else "FAIL")
    for f in r.failures:
        print(f"  {f}")
    return 0 if r.ok else 1


def cmd_mask(args) -> int:
    from slopstop import mask
    p = Path(args.file)
    masked, blocks = mask.mask(read(args.file))
    mp, cp = p.with_name(f"{p.stem}.masked{p.suffix}"), p.with_name(f"{p.stem}.code.json")
    mp.write_text(masked)
    cp.write_text(json.dumps(blocks, indent=1) + "\n")
    print(f"{mp}\n{cp}  ({len(blocks)} code blocks)")
    return 0


def cmd_unmask(args) -> int:
    from slopstop import mask
    try:
        blocks = json.loads(read(args.code))
    except json.JSONDecodeError as e:
        raise UsageError(f"{args.code} is not valid JSON: {e}") from e
    out = mask.unmask(read(args.file), blocks)
    if args.o:
        Path(args.o).write_text(out)
    else:
        print(out, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopstop", description="Mechanical AI-slop detection with instructions for the agent that fixes it.")
    p.add_argument("--version", action="version", version=f"slopstop {__version__}")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("profile", help="count a register from a folder of human-written texts")
    s.add_argument("folder")
    s.add_argument("--name", required=True)
    s.add_argument("--out")
    s.add_argument("--model", action="append", default=[], help="folder of model text on the same topics, for the phrase list")
    s.add_argument("--holdout", type=float, default=0.2)
    s.set_defaults(func=cmd_profile)

    s = sub.add_parser("detect", help="findings and fix instructions for one text")
    s.add_argument("file")
    s.add_argument("--register", required=True)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_detect)

    s = sub.add_parser("gate", help="check a model's output against its source, or an input alone")
    s.add_argument("source")
    s.add_argument("output", nargs="?")
    s.add_argument("--allow", default="rewrite", choices=["rewrite", "breaks", "punctuation", "span", "polish"])
    s.add_argument("--ratio", default="0.75:1.35", help="length band for --allow rewrite, LO:HI")
    s.add_argument("--lines", help="for --allow span: comma-separated source lines that may change")
    s.add_argument("--budget", type=float, default=0.15, help="for --allow polish: share of words that may change")
    s.add_argument("--split", help="split JSON from 'instruct split'")
    s.add_argument("--transcript", action="store_true", help="input is a transcript: truncation only warns")
    s.set_defaults(func=cmd_gate)

    s = sub.add_parser("mask", help="swap code blocks for placeholders before a rewrite")
    s.add_argument("file")
    s.set_defaults(func=cmd_mask)

    s = sub.add_parser("unmask", help="put code blocks back after a rewrite")
    s.add_argument("file")
    s.add_argument("--code", required=True)
    s.add_argument("-o")
    s.set_defaults(func=cmd_unmask)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if not getattr(args, "func", None):
        parser.print_usage(sys.stderr)
        return 2
    try:
        return args.func(args)
    except UsageError as e:
        print(f"slopstop: {e}", file=sys.stderr)
        return 2
