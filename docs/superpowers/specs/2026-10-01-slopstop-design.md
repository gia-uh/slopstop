---
date: 2026-10-01
status: draft, awaiting review
---

# slopstop design

slopstop detects AI slop, rewrites AI-assisted prose into something better to
read, and attaches an honest account of how the text was made. This spec covers
the tools, the workflows they serve, and how we will know each one works. The
evidence behind every decision is in `docs/research/`, starting with the
synthesis.

## Constraints

These are the project's fixed constraints.

1. **Better writing, never hiding.** No feature optimizes against a detector or
   strips provenance. Every published AI-assisted text carries a disclosure.
2. **No training on one author's voice.** Voices drift across years and
   registers. Adapting to a register means profiling a folder of human-written
   examples.
3. **No watermarked tokens in published prose.** Every Claude model watermarks
   its text, and so do Gemini's consumer apps. They may research, outline,
   critique and fact-check, but the final sentences of published prose come
   from the author or from a model that applies no watermark.
4. **Cloud first.** Rewriting runs on cheap hosted models through any
   OpenAI-compatible gateway, such as OpenRouter, so it works without a local
   GPU. The same client talks to a local server (LM Studio, vLLM, Ollama) when
   one is available.
5. **The scope decides the process.** Docs and code prose get a quick check and
   automatic cleanup. Published prose gets the full workflow and the
   disclosure. When the class of a text is unclear, the tool asks the author.

## Three classes of text

Every task starts by putting the text in one class. The class decides the
workflow, the watermark rule and the disclosure.

| class | examples | how it is written | watermark rule | disclosure |
|---|---|---|---|---|
| authored | blog posts, books, papers, talks under the author's name | the author dictates or drafts; models translate, clean up and flag | applies | required: ideas, structure, claims and voice are the author's |
| generated | SOTA reviews, literature surveys published as AI-made | a model writes, the author reviews | applies | required: AI-generated, reviewed by the author |
| docs | READMEs, manuals, code comments, commit messages | anyone | does not apply | none |

The classification is an explicit step in the skill. The skill proposes a class with a one-line reason and asks the author whenever the text
could be published, a talk, a paper or a post, or whenever the path gives no
clear signal. The decision goes into the text's provenance record, so the
disclosure can later state it.

## Components

```
            ┌──────────── provenance record (.provenance.jsonl) ───────────┐
            │                                                              │
 text ──► classify ──► workflow ──► rewrite ──► gate ──► judge ──► detect ──► disclose ──► final text
                         │           (models)  (structure) (fidelity) (tells)    (clause)
                         └── dictation, author draft, AI draft, docs
```

### 1. `slopstop detect`

Finds the spans a reader would flag and says why. It returns a report of flagged
spans, each with the rule, the measured
human rate for that rule, and the text's own rate.

It runs three layers, cheapest first.

**Mechanical tells.** Standard library plus an optional spaCy parser. Each tell
has a human baseline rate taken from the active register profile, and a
two-sided band, so a text with too few em dashes is as visible as one with too
many. The first catalog:

- the corrective construction ("it isn't X, it's Y", "not X but Y"), ported
  from `sam-paech/not-x-but-y-bench`, MIT;
- em dashes, mid-sentence colons, heading and bold density;
- sentence-length mean and standard deviation, paragraph-length variation, and
  repeated sentence openers, the uniformity checks in `tbhb/vale-ai-tells`;
- triplets, summary closers at the end of a paragraph, and signposting
  openers;
- over-represented words and phrases, from a profile built with the
  `slopcheck` method used in the research (model text against human text on
  the same topics), which this slice ports into the package.

**Content critic.** A cheap model reads the text and quotes the passages that
make a claim without support: a generic statement standing in for a specific
fact, importance asserted with no evidence, a vague upbeat conclusion, one
point restated in several ways, an unsupported superlative. It quotes and never
scores. Every quote is matched against the text before it reaches the report,
and an earlier critic test found zero invented quotes across six documents
(`docs/research/2026-09-13-style-prompt-arms-experiment.md`).
This layer exists because the readers who catch AI text point at content as
often as at wording, and no counter can see content.

**Classifier probe.** Optional. Experiment 001 found that the best open
detector on the RAID leaderboard scores pre-LLM human essays as more AI-like
than uninstructed Claude essays. So a classifier is enabled for a register only
after it separates that register's human examples from model text at a
measured rate. Until then the report leaves it out. Pangram's API is a paid
option for the same probe.

**Registers.** A register is a folder of human-written texts: an author's own blog,
formal academic papers, a personal essay collection, by any author.
`slopstop profile <folder> --name <register>` counts the rates and writes
`registers/<name>.json`. The file holds counts, never the texts, so a profile
can be committed even when its source cannot. Each register records its own
false-positive rate: the share of its human texts the detector would flag.
Phase 0 showed why the baseline has to be human writing in the same register
and on comparable topics. Without that, the list ranks topics rather than
habits, and generic lists flag the author's own words.

### 2. `slopstop rewrite`

One command, four modes, each matching a workflow. Every mode records what it
did in the provenance record and refuses a watermarking model as the author of
final text in the authored and generated classes.

- **`dictation`**, authored class. Input is a voice transcript in any
  language, often the author's first language rather than the target one.
  It runs in two steps, because a transcript mixes the text with things the
  author says about the text.

  1. **Split.** A model, Claude included, labels every passage of the
     transcript as one of three kinds. *Content* is the text itself.
     *Directives* steer its surface and stay anchored where they were
     spoken: "the next part is a short paragraph", "make this a list of
     todos", "the title is...", "keep it short", "keep the swearing".
     *Agent requests* ask someone to do work: "add examples from the
     literature", "first transcribe this and then let's discuss". The split
     writes no published sentence, so the watermark rule does not bind it.
     Its output is saved next to the provenance record, where the author
     can read what was set aside.
  2. **Rewrite.** A non-watermarking model rewrites the content in the
     target language and the author's voice. It may fix grammar, remove
     disfluencies and correct names that speech-to-text misheard ("Charge
     EPT" is ChatGPT), and it applies the directives. Where the author
     describes what the piece should argue, it states the argument directly.
     It never sees the agent requests, so it adds no claim, example or
     section the author did not dictate.

  Then `judge` compares the result against the content alone and lists any
  dropped or invented claims for the author to settle. Experiment 001 is why
  the split comes first. Given the whole transcript in one pass, one model
  kept the author's framing as prose, one cut a framing paragraph and lost
  the claims inside it, and one printed "First transcribe this..." as part of
  the post. The judge, given the same transcript, counted every instruction
  as a dropped claim.
- **`polish`**, authored class. Input is the author's own draft. The model proposes
  edits as a diff, and a mechanical budget caps the share of tokens it may
  change. The author accepts each hunk. A prompt saying "grammar only" cannot do this
  job, because models given that instruction still raised adjective use by 40%
  to 87% and changed meaning.
- **`restyle`**, generated class. Input is a draft from any model, Claude
  included. A non-watermarking model rewrites it, `judge` checks fidelity,
  `detect` flags what remains, and only the flagged spans go back for a local
  rewrite. The loop stops when the report is clean or after three rounds, and
  the report says which.
- **`clean`**, docs class. `detect` flags spans and a cheap model fixes them in
  place. Changes within the budget apply without asking.

Every mode hands its output to a structural gate before the judge sees it.
The gate is deterministic and compares the output with the input. Fences
must balance, no paragraph block may repeat, the length ratio must sit inside
the band measured for the mode, no meta-text may leak in ("Here is the
rewritten essay"), and every placeholder must come back. A failure gets one
retry and then stops the run with the reason. The same gate runs on inputs, so
a truncated source is reported before any model reads it. Code blocks never
reach a model: `rewrite` swaps each one for a placeholder and restores it
afterwards. In experiment 001 the gate would have caught every failure that no
metric and no judge saw: an empty output, a post printed twice, an unclosed
code fence, and two source essays cut off mid-sentence. These checks are not
tells, because no human writes a post twice at a measurable rate, so they live
here and not in `detect`.

Models are chosen per mode in `slopstop.toml`. A model registry records each
model's watermark status with its source and date, because that status changes,
as Anthropic's rollout of its watermark to older Claude models showed in 2026. Defaults come
from experiment 001, which picked `deepseek/deepseek-v4-pro` for both
dictation and restyle, with `qwen/qwen3.7-flash` as the fallback.

### 3. `slopstop judge`

Lists what a rewrite dropped from its source and what it invented, each with a
verbatim quote that is checked against the text. It reports and never scores.
Translation, rephrasing and merging do not count as changes.

### 4. Provenance and `slopstop disclose`

Every text the tools touch gets a sidecar, `<file>.provenance.jsonl`, one line
per step: who acted (the author, or a model id), the operation, hashes of input and
output, the class, and a timestamp. `disclose` renders the clause from that
record using a template per class. It refuses when an authored or generated
text's final version came out of a watermarking model after the author's last edit,
because the clause would then be describing the wrong text.

Draft templates, which each author should rewrite in their own words:

> **Authored.** I wrote this with AI assistance. I dictated the draft in
> {language}; {model} translated it and cleaned it up, and I edited and reviewed
> the result. The ideas, structure, claims and voice are mine.

> **Generated.** This review was generated with AI. {model} drafted it from
> sources that {research model} gathered, and I reviewed and edited it. I am
> responsible for its claims.

### 5. Skills and the CLAUDE.md clause

One Claude Code skill, `slopstop`, carries the workflows. It covers classifying
the text, routing to the right `rewrite` mode, running `detect`, and emitting
the disclosure. A short clause in the agent instructions (CLAUDE.md or AGENTS.md) does what a skill
cannot. It tells every session that Claude never writes the final sentences of
authored or generated prose, and that any text that might be published goes
through the classification step.

Dictation arrives through whatever speech-to-text tool the author already uses,
so slopstop takes a transcript and
does not record audio.

### 6. Experiments

Every workflow is an experiment until the numbers say otherwise. An experiment
holds the topic set fixed and measures each arm with the same instruments:
detector report, judge, sentence statistics, cost, and a blind read.
`slopstop blind` builds an anonymized side-by-side packet and records which
version the author picks. In the earlier experiments, two blind reads by the
author both chose the passage closest to their own measured profile over the
cleanest one. That result has n=2, and the blind read is the instrument every
earlier experiment lacked.

## Package shape

A uv Python package with a `slopstop` CLI. The mechanical core uses only the
standard library, as `slopcheck` does today. Optional extras add spaCy
(`[nlp]`), torch and transformers for the classifier probe (`[classifier]`),
and an OpenAI-compatible client for OpenRouter and LM Studio (`[llm]`).
Configuration is one `slopstop.toml`. Register profiles live in `registers/`.

## How we know it works

- Every tell has a fixture that must fire and one that must not, and each
  fixture is broken on purpose once to confirm the test fails.
- Each register's false-positive rate on held-out human texts is measured and
  stored in its profile. The detector reports it with every result.
- A benchmark set of human texts and model rewrites on the same topics gives
  each tell a precision and recall, so a tell that stops discriminating shows
  up as a number rather than an opinion.
- Rewrite modes are measured on three things: judge counts, the change in
  detector findings, and edit distance. Blind reads decide between workflows.

## Slices

Each slice ends with something a writer can run on a real text.

1. **Detector, mechanical layer.** Port `slopcheck`, add the tell catalog with
   spans, `profile` for registers, and Markdown and JSON reports. Ship two
   registers: one author's published blog and a public pre-2022 essay
   collection. Done when `slopstop detect post.md` flags spans on a model
   draft, flags few on held-out human posts from the same register, and that
   false-positive rate is recorded.
2. **Rewrite, judge and disclose for docs and generated text.** `clean` and
   `restyle` on the models experiment 001 picks, the structural gate,
   provenance, and `disclose`.
3. **The authored workflow.** `dictation` with its split, `polish` with the
   diff budget, the skill, and the agent-instructions clause.
4. **Content critic and classifier probe**, with the calibration gate.
5. **Experiment 002.** Dictation, against a frontier-model draft plus
   restyle, against an author's draft plus polish, on the same topics, with
   blind reads.
6. **Languages beyond English.** A register and a tell catalog per language,
   found by profiling human and model text in that language rather than by
   translating English lists. Spanish comes first.

## Non-goals

- Lowering detector scores, or any feature whose purpose is to make AI text
  pass as human.
- Fine-tuning on one author's writing.
- A general prose linter. Vale, proselint and rift already exist, and slopstop
  can feed them rules.
- Publishing private texts. Authors' voice notes and drafts stay local, and
  only counts derived from them may be committed.

## Open questions

- Which public pre-2022 essay corpus has a license that allows redistributing
  derived counts.
- Whether the content critic should run on a cheap model or on Claude. Its
  quotes are never published, so the watermark rule does not bind it, but a
  model judging prose may prefer its own style.
- How much of the authored workflow belongs in the terminal versus in an
  editor, which decides how `polish` shows hunks for acceptance.
