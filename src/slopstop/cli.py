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


def cmd_gate(args) -> int:
    from slopstop import gate
    src = read(args.source)
    if args.output is None:
        r = gate.check_input(src)
    else:
        lo, _, hi = args.ratio.partition(":")
        try:
            ratio = (float(lo), float(hi))
            lines = [int(x) for x in args.lines.split(",")] if args.lines else None
        except ValueError as e:
            raise UsageError(f"bad --ratio or --lines: {e}") from e
        r = gate.check_output(src, read(args.output), args.allow, ratio, lines, args.budget)
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
    if not isinstance(blocks, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in blocks.items()):
        raise UsageError(f"{args.code} must map placeholders to code blocks, as 'slopstop mask' writes it")
    out = mask.unmask(read(args.file), blocks)
    if args.o:
        Path(args.o).write_text(out)
    else:
        print(out, end="")
    return 0


def _files(paths: list[str]) -> list[Path]:
    out = []
    for p in map(Path, paths):
        if p.is_dir():
            out += sorted(x for x in p.rglob("*") if x.suffix in (".md", ".txt") and ".orig." not in x.name)
        elif p.is_file():
            out.append(p)
        else:
            raise UsageError(f"no such file: {p}")
    return out


def _config(path: Path, explicit: str | None):
    from slopstop import check
    try:
        return check.load_config(path.parent.resolve(), explicit)
    except (ValueError, OSError) as e:
        raise UsageError(str(e)) from e


def cmd_check(args) -> int:
    from slopstop import check
    only = set(args.rules.split(",")) if args.rules else None
    reps = []
    for f in _files(args.paths):
        cfg = _config(f, args.config)
        rep = check.run(read(str(f)), str(f), cfg, args.lang, only)
        if args.level == "error":
            rep.findings = [x for x in rep.findings if x.level == "error"]
        reps.append(rep)
    print(check.to_json(reps) if args.json else check.render_text(reps), end="\n" if args.json else "")
    return 1 if any(r.errors for r in reps) else 0


def cmd_fix(args) -> int:
    import difflib
    from slopstop import check, fix
    kinds = ("auto", "suggest") if args.suggested else ("auto",)
    total = 0
    for f in _files(args.paths):
        raw = read(str(f))
        new, applied = fix.apply(raw, kinds, _config(f, args.config), args.lang)
        total += len(applied)
        if args.dry_run:
            sys.stdout.writelines(difflib.unified_diff(raw.splitlines(True), new.splitlines(True),
                                                       str(f), str(f) + " (fixed)"))
            continue
        if applied:
            Path(check.orig_path(str(f))).write_text(raw, encoding="utf-8")
            f.write_text(new, encoding="utf-8")
        for a in applied:
            print(f"{f}:{a.line}:{a.start + 1}  {a.rule:<16} {json.dumps(a.text.strip()[:60], ensure_ascii=False)}"
                  f" -> {json.dumps(a.replacement, ensure_ascii=False) if a.replacement else 'deleted'}")
    print(f"{total} edits" + (" (dry run)" if args.dry_run else ""), file=sys.stderr)
    return 0


def cmd_calibrate(args) -> int:
    from slopstop import calibrate
    folder = Path(args.folder)
    if not folder.is_dir():
        raise UsageError(f"no such folder: {args.folder}")
    res = calibrate.measure(calibrate.files_in(folder), args.name or folder.name, args.share)
    if not res["files"]:
        raise UsageError(f"no file of {calibrate.MIN_WORDS} words or more in {args.folder}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1) if args.json else calibrate.render_text(res), end="\n" if args.json else "")
    if args.write:
        got = {k: v["suggested"] for k, v in res["thresholds"].items() if v["suggested"] is not None}
        calibrate.write_config(Path(args.write), got)
        print(f"{args.write}: {len(got)} thresholds written", file=sys.stderr)
    return 0


def cmd_rules(args) -> int:
    from slopstop import rules
    if args.markdown:
        from slopstop import calibrate
        cals = [json.loads(read(p)) for p in args.calibration]
        print(calibrate.rules_markdown(cals), end="")
        return 0
    cat = rules.load()
    pick = [r for r in cat if not args.id or r.id == args.id]
    if not pick:
        raise UsageError(f"no rule {args.id}; run 'slopstop rules' for the list")
    for r in pick:
        if args.id:
            print(f"{r.id} ({r.lang}, {r.level}, {r.kind}{f', threshold {r.threshold}' if r.threshold else ''})")
            print(f"  why: {r.why}\n  fix: {r.todo}")
            for x in r.fires:
                print(f"  fires: {x[:100]}")
            for x in r.quiet:
                print(f"  quiet: {x[:100]}")
        else:
            print(f"{r.id:<17} {r.lang:<4} {r.level:<6} {r.kind:<8} {r.why}")
    print(f"{len(pick)} rules")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopstop", description="A linter for the habits that make model-written prose annoying to read, with the fixes.")
    p.add_argument("--version", action="version", version=f"slopstop {__version__}")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("check", help="findings, reasons and fixes for texts; exit 1 while errors remain")
    s.add_argument("paths", nargs="+", help="files or folders (.md, .txt)")
    s.add_argument("--json", action="store_true")
    s.add_argument("--lang", choices=["en", "es"])
    s.add_argument("--rules", help="comma-separated rule ids to run")
    s.add_argument("--level", choices=["error", "warn"], default="warn", help="error: report errors only")
    s.add_argument("--config", help="a slopstop.toml to use instead of searching upward")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("fix", help="apply the mechanical fixes in place, keeping FILE.orig")
    s.add_argument("paths", nargs="+")
    s.add_argument("--suggested", action="store_true", help="also apply suggested replacements")
    s.add_argument("--dry-run", action="store_true", help="print a diff instead of writing")
    s.add_argument("--lang", choices=["en", "es"])
    s.add_argument("--config")
    s.set_defaults(func=cmd_fix)

    s = sub.add_parser("calibrate", help="how often each rule fires on a folder of good prose, and thresholds that fit")
    s.add_argument("folder")
    s.add_argument("--name", help="the set's name in the output (default: the folder's name)")
    s.add_argument("--share", type=float, default=0.05, help="share of files a tuned threshold may flag")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="also write the JSON result to this file")
    s.add_argument("--write", help="merge the suggested thresholds into this slopstop.toml")
    s.set_defaults(func=cmd_calibrate)

    s = sub.add_parser("rules", help="list the rules, or show one with its examples")
    s.add_argument("id", nargs="?")
    s.add_argument("--markdown", action="store_true", help="the rules table, with calibration columns")
    s.add_argument("--calibration", nargs="*", default=[], help="calibration JSON files for --markdown")
    s.set_defaults(func=cmd_rules)

    s = sub.add_parser("gate", help="check a model's output against its source, or an input alone")
    s.add_argument("source")
    s.add_argument("output", nargs="?")
    s.add_argument("--allow", default="rewrite", choices=["rewrite", "breaks", "punctuation", "span", "polish"])
    s.add_argument("--ratio", default="0.75:1.35", help="length band for --allow rewrite, LO:HI")
    s.add_argument("--lines", help="for --allow span: comma-separated source lines that may change")
    s.add_argument("--budget", type=float, default=0.15, help="for --allow polish: share of words that may change")
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
