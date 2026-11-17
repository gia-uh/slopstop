---
name: slopstop
description: Use after writing or rewriting any prose people will read (posts, docs, READMEs, reports, emails, chapters), in English or Spanish, before handing it over. Runs the slopstop linter, applies its mechanical fixes, rewrites only the lines it names, and loops until no error is left.
---

# slopstop

The `slopstop` CLI finds the habits that make model-written prose annoying to
read and says how to fix each one. It calls no model: you do the rewriting, and
it checks your work. Install it with
`uv tool install git+https://github.com/gia-uh/slopstop`.

## The loop

1. `slopstop check draft.md`. Exit 0 means no error is left: stop. Exit 1
   lists each finding with its line, the reason and the fix. Use `--json` if
   you parse it.
2. `slopstop fix draft.md`. It applies every `auto` fix in place (deleting
   filler, removing bold from running prose, dropping a doubled hedge) and
   keeps the original as `draft.orig.md`. Add `--suggested` to also take the
   suggested replacements, such as an em dash turned into a period; read the
   lines it reports and undo any that changed the meaning.
3. `cp draft.md draft.orig.md`, then take the first remaining `rewrite`
   finding and do what its `fix:` line says, on the lines it names and nowhere
   else.
4. Run the `check:` command the finding printed
   (`slopstop gate draft.orig.md draft.md --allow span --lines N`). If it
   fails, `cp draft.orig.md draft.md` and try once more; if it fails again,
   leave the finding for the author.
5. Back to step 1. Line numbers move after every edit, so always start from a
   fresh `check`.

Stop at exit 0, or after three rounds with errors still listed, and tell the
author which errors are left. Warnings never fail `check`: list them for the
author in one line each and fix the ones they pick.

## Rules for the rewriting

- Keep every claim, number, name and quotation. A fix removes a habit, never
  content.
- Never touch code, quoted text, or anything inside a block quote to satisfy a
  rule. slopstop already skips them; if a finding still points at something
  that must stay, keep it with an allow comment, `<!-- slopstop: allow
  rule-id -->` on its own line before the paragraph, and say why.
- `slopstop rules` lists every rule; `slopstop rules <id>` shows one with
  examples of what it flags and what it leaves alone.

## Configuration

A project sets its own levels, disabled rules and thresholds in
`slopstop.toml` (or `[tool.slopstop]` in `pyproject.toml`), found from the
file's folder upward:

```toml
disable = ["em-dash"]

[levels]
metaphor-noun = "error"

[thresholds]
long-paragraph = 200
```

`slopstop calibrate <folder of good prose> --write slopstop.toml` sets the
thresholds from writing the project considers good.
