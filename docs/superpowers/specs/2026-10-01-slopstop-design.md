---
date: 2026-10-01
status: implemented (slices 1-5) 2026-10-02
---

# slopstop design

slopstop has two parts. The tool is a mechanical command-line program. It
encodes the rules for finding AI slop and the human baselines those rules are
measured against, it checks texts against them, and it tells an agent what to
fix and how the fix will be checked. The skills are instructions for an agent
(Claude Code, OpenCode, or agents orchestrated by aegis) that does the actual
work: reading, rewriting, judging, looping until the text is clean, and
disclosing how the text was made. The skills live in this repository so users
can copy them, and they call the tool.

The tool makes no model calls, holds no workflow and chooses no model. Every
command either measures a text or prints instructions for the agent built for
that text. The agent drives: it runs a command, reads the findings and
instructions, does the work itself or hands it to another model, and runs the
check the instructions name. Everything that needs judgment or discipline
belongs to the skills.

The evidence behind each decision is in `docs/research/`, starting with the
synthesis, and in `experiments/`.

## Constraints

1. **Better writing, never hiding.** Nothing optimizes against a detector or
   hides how a text was made. Every published AI-assisted text carries a
   disclosure.
2. **No training on one author's voice.** A style is learned by counting
   rates in a folder of human-written texts.
3. **No watermarked tokens in published prose.** Every Claude model and
   Gemini's consumer apps watermark their text. They may split, outline,
   critique and check, but the final sentences of published prose come from
   the author or from a model that applies no watermark.
4. **The tool is mechanical.** It makes no model calls and keeps no state
   between commands. Given the same input and configuration, every command
   returns the same output. The rules live in
   code and data files that can be tested, versioned and diffed.
5. **Every rule carries its measurement.** A tell enters the catalog with the
   human rate it was measured against and the experiment that justified it.

## Part 1: the tool

A uv Python package with a `slopstop` CLI. The core uses only the standard
library. An optional `[nlp]` extra adds spaCy for tells that need a parser.

Commands fall into two kinds. Measuring commands (`profile`, `detect`, `gate`,
`mask`, `unmask`, `check-quotes`, `blind`) compute a result. Instructing
commands (`detect` again, and `instruct`) print a task for the agent, built
for the text in hand: what to do, where, the measured reason, the output
format, and the command that will check the result. The instructions never
say who must do the work; that is the skill's decision.

### `slopstop profile <folder> --name <register>`

Counts the rates of every tell in a folder of human-written texts and writes
`registers/<name>.json`: per-tell rates, percentiles and the false-positive
rate of the catalog on those texts. The file holds counts, never the texts, so
a register can be committed when its source cannot. Phase 0 showed the
baseline has to be human writing in the same register on comparable topics.
Without that, the catalog ranks topics instead of habits and flags the
author's own words.

### `slopstop detect <file> --register <name>`

Prints the findings and, for each one, the instruction to fix it. A finding
names the span, the tell, the register's rate and the text's rate. Its
instruction says what to change there and which `gate --allow` kind will
check the change. Each finding is marked:

- **required** when the text falls outside the band that holds 99% of the
  register's human texts (or paragraphs, for tells counted per paragraph);
- **optional** when it falls outside the 90% band but inside the 99% one.

For example:

```
required  ¶3  long-paragraph  177 words; register p99 112, median 43
  Split ¶3 at the points where the argument moves on. Insert paragraph
  breaks only. Check: slopstop gate post.orig.md post.md --allow breaks
optional  em-dash  11.2 per 1000 words; register 90% band 0 to 9.5
  Replace the em dashes at lines 4, 12, 31 with periods or commas.
  Check: slopstop gate post.orig.md post.md --allow punctuation
```

The paragraph numbers are measured on the author's 147 posts, and so is the
em-dash band: 90% of the posts run between 0 and 9.5 per 1000 words, and 99%
under 13.6. `--json` gives the same content for a script. Each tell has a two-sided band,
so a text with too few em dashes is as visible as one with too many. The first
catalog:

- the corrective construction ("it isn't X, it's Y"), ported from
  `sam-paech/not-x-but-y-bench`, MIT;
- em dashes, mid-sentence colons, heading and bold density;
- sentence-length mean and spread, and repeated sentence openers;
- **long paragraphs**: any paragraph above the register's 99th percentile.
  The author's 147 published posts have a median paragraph of 43 words and a
  99th percentile of 112; dictation rewrites ran to 177 words and one to a
  single 1535-word paragraph. Only the top end is bounded, because a bound on
  variation rewards uniform paragraphs, which read as machine output
  (rift's `max-paragraph-length` makes the same choice);
- triplets, summary closers and signposting openers;
- over-represented words and phrases, from a profile of model text against
  human text on the same topics, ported from the workspace's `slopcheck`.

Counting cannot see content, and readers who catch AI text point at content
as often as at wording. That reading is the agent's job, through
`slopstop instruct critic`, below.

No classifier ships. Experiment 001 found that the two best open detectors on
the RAID leaderboard score pre-LLM human essays as more AI-like than
uninstructed Claude essays.

### `slopstop gate <source> <output> --allow <kind>`

Structural checks of a model's output against its input, for the agent to run
after every rewrite or fix. The output fails if code fences are unbalanced, a
30-word run repeats, the length ratio leaves the band for the kind of change,
the first or last line is addressed to the user ("Here is the rewritten
essay") and the source does not contain it, a placeholder is missing, or it
ends mid-sentence when the source did not. `slopstop gate <source>` alone
checks an input for truncation before any model reads it; on transcripts that
check only warns, because speech has no final period. `slopstop gate
<transcript> --split <split.json>` checks that a split's passages are verbatim
and cover the whole transcript in order.

`--allow` declares what the change may touch, and the gate verifies it:

| kind | may change | verified by |
|---|---|---|
| `breaks` | paragraph breaks only | the word sequence is identical |
| `punctuation` | punctuation only | the word sequence is identical, ignoring punctuation |
| `span` | the flagged spans only | everything outside them is identical |
| `rewrite` | anything | the structural checks and the length band |

The model is never trusted to follow the instruction. In the smoke test one
of seven paragraph-splitting calls changed words anyway and was rejected.

On experiment 001's 102 outputs the gate flagged 7, all real: two posts
printed twice, two outputs that stopped partway, and three essays padded by
36 to 83 percent, where models had written their own endings to truncated
sources. The fidelity judge missed all seven, because it counts claims.

### `slopstop mask` and `slopstop unmask`

`mask` swaps every code block for a placeholder such as `[CODE-1]` and writes
the blocks to a side file; `unmask` puts them back. Code never reaches a
rewriting model, and `gate` checks every placeholder survived.

### `slopstop check-quotes <json> --source <file> --output <file>`

Verifies the quotes in a judge's or critic's JSON against the texts and marks
each item verified or not. Unverified items are dropped from what the author
sees.

### `slopstop instruct <task> <files>`

Prints the task for the agent, built for these files from templates in
`instructions/`, versioned with the rules they serve. Each one ends with the
output format and the check to run next.

- `split <transcript>`: label each passage as content, directive or request,
  copied verbatim, and write `<transcript>.split.json`. Check:
  `slopstop gate <transcript> --split <transcript>.split.json`, which
  confirms the passages are verbatim and cover the whole transcript.
- `dictation <split.json>`: rewrite the content with the directives applied
  where they were spoken, in the author's voice, fixing grammar and misheard
  names, directives included, and adding nothing. Check: `gate --allow
  rewrite`.
- `restyle <file>`: rewrite a model's draft keeping every claim, with code
  masked. Check: `gate --allow rewrite`.
- `judge <source> <output> [--set-aside <split.json>]`: list what the output
  dropped outside the set-aside passages and what it invented, with verbatim
  quotes. Check: `check-quotes`.
- `critic <file>`: quote the passages that make a claim without support (a
  generic statement standing in for a specific fact, importance asserted
  without evidence, one point restated several ways). Quote, never score.
  Check: `check-quotes`.

### `slopstop blind`

Builds an anonymized side-by-side packet from several versions of a text and
records which one the author picks. Every earlier experiment lacked this
instrument.

## Part 2: the skills

The skills live in `skills/` and are written for Claude Code; the same text
works as OpenCode instructions or as an aegis agent prompt. They choose the
models and the runner. Experiment 001 recommends `deepseek-v4-pro` for every
rewrite, with `qwen3.7-flash` as the fallback, reached through whatever the
user has: OpenRouter, OpenCode Zen, a local server, or an aegis queue.

### Classify first

Every task starts by putting the text in a class, because the class decides
the workflow, whether the watermark rule applies and what the disclosure
says.

| class | examples | how it is written | watermark rule | disclosure |
|---|---|---|---|---|
| authored | posts, books, papers, talks | the author dictates or drafts; models translate, clean up and flag | applies | ideas, structure, claims and voice are the author's |
| generated | literature reviews published as AI-made | a model writes, the author reviews | applies | AI-generated, reviewed by the author |
| docs | READMEs, comments, commit messages | anyone | does not apply | none |

The skill proposes a class with a one-line reason and asks the author when
the text could be published or the path gives no clear signal.

### Dictation

A transcript mixes the text with things the author says about the text.

1. `slopstop gate <transcript>` warns if it is cut off.
2. **Split.** Any agent, Claude included, follows `slopstop instruct
   split`. Content is what a reader should read; a directive steers
   form where it was spoken ("the title is...", "make this a list", "keep
   the swearing"); a request asks for work ("add examples from the
   literature", "first transcribe this and let's discuss"). The skill shows
   the author what was set aside.
3. **Rewrite.** A non-watermarking model rewrites the content with the
   directives in place, following `slopstop instruct dictation`. It never sees the
   requests. `gate --allow rewrite` checks the result.
4. **Judge.** The agent follows `slopstop instruct judge` with the full
   transcript and the set-aside passages, so anything dropped outside that
   list is reported. A
   mistake in the split stays visible this way; in the smoke test, the split
   set aside two of the author's open questions as requests.
5. **Detect and fix**, below.

Given a whole transcript in one pass, experiment 001's models kept the
author's framing as prose, cut a framing paragraph with the claims in it, or
printed "First transcribe this..." as part of the post. In the smoke test the
split covered all three transcripts verbatim and no request reached the prose.

### Restyle, polish and clean

- **Restyle**, generated class: `mask`, `instruct restyle`, `gate`, `unmask`,
  judge, then detect and fix.
- **Polish**, authored class: the model proposes edits to the author's draft
  as a diff, a budget caps the share of tokens it may change, and the author
  accepts each hunk. A "grammar only" prompt cannot do this job; models given
  it still raised adjective use by 40 to 87 percent and changed meaning.
- **Clean**, docs class: detect, fix the flagged spans, gate, apply.

### Detect and fix

The agent runs `slopstop detect`, carries out each required instruction,
and runs the check the instruction names; a rejected fix gets one retry. The
skill decides which optional findings to take, or asks the author. The loop
stops when no required finding is left or after three rounds, and the skill
tells the author which. In the smoke test two rounds brought every dictation
paragraph under the register's 99th percentile. Two of the three dictation
outputs also ran at 13.7 and 14.9 em dashes per 1000 words, above the
register's 99% band, so they would get required em-dash findings.

### Disclosure and the watermark rule

These are discipline, so they live in the skill and in a short clause for the
agent instructions (CLAUDE.md or AGENTS.md):

- Claude never writes the final sentences of authored or generated prose.
- Any text that might be published goes through classification.
- The skill keeps a note of which model did each step, and at the end writes
  the disclosure from a template for the class, which each author rewrites
  in their own words:

> **Authored.** I wrote this with AI assistance. I dictated the draft in
> {language}; {model} translated it and cleaned it up, and I edited and
> reviewed the result. The ideas, structure, claims and voice are mine.

> **Generated.** This review was generated with AI. {model} drafted it from
> sources that {research model} gathered, and I reviewed and edited it. I am
> responsible for its claims.

## Experiments

Every workflow is an experiment until the numbers say otherwise. An
experiment holds the topic set fixed and measures each arm with the same
instruments: the detector report, the gate, the judge, sentence statistics,
cost, and a blind read. Experiment 001 chose the rewrite models, and a
smoke test on 2026-10-02 exercised prototypes of the gate, masking, the split
and the paragraph fix on its data.

## How we know it works

- Every tell and every gate check has a fixture that must fire and one that
  must not, and each fixture is broken once on purpose to confirm the test
  fails.
- Each register's false-positive rate on held-out human texts is stored in
  the profile, and `detect` prints it with every result.
- A benchmark of human texts and model rewrites on the same topics gives each
  tell a precision and recall.
- The gate's false positives are counted on the outputs of every new
  experiment. On experiment 001 none of its 7 flags was false.

## Slices

Each slice ends with something a writer can run on a real text.

1. **Detect and profile.** The mechanical catalog with spans, `profile`, and
   two registers: one author's published blog and a public pre-2022 essay
   collection. Done when `slopstop detect post.md` flags a model draft, flags
   few held-out human posts, and that rate is recorded.
2. **Gate, mask, check-quotes and the instructions.** Done when the 102
   outputs of experiment 001 reproduce the smoke test's 7 flags, and every
   `detect` finding prints an instruction whose check passes on a correct fix
   and fails on a wrong one.
3. **The skills.** Dictation, restyle and clean, the fix loop, disclosure, and
   the agent-instructions clause, run end to end on one runner.
4. **Polish**, with the diff budget.
5. **The critic**: `instruct critic` and its use in the skills, with the
   quotes checked.
6. **Experiment 002.** Dictation, against a frontier draft plus restyle,
   against an author's draft plus polish, on the same topics, with blind
   reads.
7. **Languages beyond English**, Spanish first: a register and a tell catalog
   per language, found by profiling, not by translating English lists.

## Non-goals

- Lowering detector scores, or any feature whose purpose is to make AI text
  pass as human.
- Calling a model, running a workflow or choosing a model inside the tool.
- Fine-tuning on one author's writing.
- A general prose linter. Vale, proselint and rift exist, and a register can
  be exported as rules for them.
- Publishing private texts. Voice notes and drafts stay local; only counts
  derived from them are committed.

## Open questions

- Which public pre-2022 essay corpus allows redistributing derived counts.
- Whether the skills should hand the critic's reading to a non-Claude model.
  Its quotes are never published, so the watermark rule does not bind it, but
  a model judging prose may prefer its own style.
- How `polish` shows hunks for acceptance: in the terminal or in an editor.
