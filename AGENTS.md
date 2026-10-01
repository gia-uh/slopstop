# slopstop

slopstop researches how to detect and fix AI slop, and it is the toolkit its
authors use to do it: detect, flag, rewrite and disclose. It serves Alex Piad
and the GIA-UH group first, as writers who publish AI-assisted English and
Spanish prose, and anyone who wants AI-assisted writing that reads well and is
honest about how it was made.

This file changes when the goals change. Nothing in it should be made false by
a commit that adds code, an experiment or a report.

## The rules the project serves

- **Better writing, never hiding.** No tool here optimizes against an AI
  detector, removes provenance, or helps pass AI-assisted text off as
  unassisted. A detector is an instrument for finding bad spans. A stealth
  feature would contradict the README's promise and the research, which found
  that evasion and quality pull in opposite directions.
- **Disclosure travels with the text.** A workflow that produces published
  prose records which steps a model performed and emits the disclosure from
  that record, so the clause describes what actually happened.
- **No watermarked tokens in published prose.** Final prose comes from the
  author or from a model that applies no watermark. Every Claude model and
  Gemini's consumer apps watermark their text, so they may outline, critique
  and fact-check but never write a published sentence. Docs and code prose are
  exempt from this rule.
- **No training on one author's voice.** Voices drift across years and
  registers. A register is adapted by profiling a folder of human-written
  examples, which is counting and needs no gradient step.
- **Every rule carries its measurement.** A check enters the detector with the
  human baseline it was measured against and the experiment that justified it.
  The September experiments showed that unmeasured rules flag the author's own
  vocabulary and that forbid lists backfire.

## What done means

For a tool: it runs on a real text the way a writer would run it, its checks
have been broken on purpose to confirm they fire, and its false-positive rate
on human writing in the target register is measured and recorded.

For an experiment: its folder holds the code, the method, the numbers and the
conclusion, and anyone can rerun it from the README given the same inputs.

## Where everything lives

| tier | holds |
|---|---|
| `AGENTS.md` | goals, rules, what done means |
| `DESIGN.md` | architecture and the reason for each boundary (once the design is approved) |
| `docs/research/` | literature reports and findings, dated, frozen once complete |
| `docs/superpowers/specs/`, `docs/superpowers/plans/` | design specs and implementation plans |
| `experiments/NNN-<slug>/` | one experiment per folder: code, method, results |
| `know-how/` | one procedure per job, each opening with a `when:` line |
| `Makefile` | every mechanical check |

## Working here

- `make test` is the gate. Run it verbatim and read its exit code directly.
- `grep -m1 -H '^when:' know-how/*.md` prints the know-how menu.
- Changes land through issue, branch, PR and green CI. Trivial edits go
  straight to `main`.
