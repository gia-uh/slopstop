---
date: 2026-09-12
type: research-findings
status: complete
phase: 0
plan: "[[2026-09-12-llm-prose-quality-research-plan]]"
tags: [writing, llm, evaluation, unslop]
---

# Phase 0 findings: what Claude's prose actually overuses

Phase 0 of [[2026-09-12-llm-prose-quality-research-plan]]. Built the
measuring instrument, ran it, and audited the `unslop` skill against the
numbers it produced.

Tool: `bin/slopcheck`. Corpora and manifests:
`vault/Efforts/Areas/Writing/voice/corpus/slop/`. Profiles:
`vault/Efforts/Areas/Writing/voice/profiles/slop-en-*.json`.

## Headline

Rule 7 of `unslop` bans 16 words. Uninstructed Claude writes none of them,
in 12,221 words of blog-register prose. Alex's own published blog uses nine
of them, four at rates above 100 per million: crucial at 340, robust at 187,
enhance at 135, comprehensive at 104.

The rule that the data does confirm is rule 26, abstract metaphor nouns, at
2.7 to 8.2 times Alex's rate in vault prose. And the strongest signature in
the whole run has no rule at all: the contracted corrective, "it isn't X,
it's Y", at 22 to 52 times Alex's rate and 75 to 137 times general English.
Rule 9 aims at that idea and misses, because it bans the uncontracted forms
"not just" and "not only", which Alex uses more often than Claude does.

## Corpora

| corpus | docs | tokens | what it is |
|---|---|---|---|
| Alex | 146 | 288,150 | posts published under his byline on blog.apiad.net, 2023-01 to 2026-04 |
| general | 865 | 5,228,320 | everything in `vault/Sources/` that is not his blog |
| vault Claude | 475 | 555,640 | Wiki, design docs, research, SOTA reports, drafts, architecture docs |
| control Claude | 12 | 12,221 | generated for this run with an empty system prompt |

Alex's corpus came out of his Substack export, which was sitting unused as a
zip inside `vault/Sources/blog.apiad.net/`. It carries 146 posts against the
20 that had been pulled as individual sources, which is what made the
measurement possible at all.

The control corpus exists because of a confound that would otherwise have
sunk the headline. Every word of vault Claude prose was written under
`CLAUDE.md`, the `/revise` AI-tic catalog, and possibly an earlier `unslop`,
so "Claude never writes delve" could have meant "Claude was told not to".
The control calls `anthropic/claude-opus-5` through OpenRouter with no system
prompt and twelve prompts chosen to match Alex's real topics: binary search,
AI winter, the universe as a computer, the history of AI, diagrams in Python,
augmenting rather than automating your writing. Generator:
`.playground/slop-corpus/gen_control.py`.

## Result 1: the AI-vocabulary rule is aimed at a model that no longer exists

Rule 7 lists additionally, crucial, delve, enduring, enhance, fostering,
garner, interplay, intricate, landscape, pivotal, showcase, tapestry,
testament, underscore, vibrant.

In the control corpus all 16 score UNUSED: zero occurrences. In vault Claude
prose, seven score INVERTED, meaning Alex uses them more often than Claude
does, and the other nine are still absent. Not one term is confirmed in
either corpus.

Rates per million, Claude control against Alex:

| term | control | Alex | general |
|---|---|---|---|
| crucial | 0 | 340.1 | 65.2 |
| not only | 0 | 218.6 | 140.4 |
| enhance | 0 | 135.3 | 64.8 |
| comprehensive | 0 | 104.1 | 88.7 |
| additionally | 0 | 97.2 | 65.0 |
| landscape | 0 | 86.8 | 38.4 |
| numerous | 0 | 65.9 | 36.1 |
| delve | 0 | 48.6 | 1.5 |
| intricate | 0 | 41.6 | 11.5 |

These words were the signature of 2023-era ChatGPT. The list has been copied
forward since, and it now costs context in every session to forbid vocabulary
the model does not produce, while flagging Alex's own writing as slop if it
were ever run over his drafts.

## Result 2: the rule that holds is rule 26

Abstract metaphor nouns, measured on vault Claude prose against both
baselines. The rank column is the smaller of the two ratios, so a term counts
only if it is overused against Alex and against general English:

| term | rank | vs Alex | vs general | Claude/M | Alex/M |
|---|---|---|---|---|---|
| substrate | 8.15 | 8.15 | 17.60 | 205.2 | 24.3 |
| surface | 6.87 | 6.87 | 8.46 | 458.9 | 65.9 |
| harness | 6.53 | 15.19 | 6.53 | 593.9 | 38.2 |
| scaffolding | 5.34 | 9.42 | 5.34 | 73.8 | 6.9 |
| primitive | 5.24 | 16.44 | 5.24 | 129.6 | 6.9 |
| modality | 3.59 | 7.87 | 3.59 | 34.2 | 3.5 |
| ratchet | 2.72 | 10.00 | 2.72 | 9.0 | 0.0 |

Four other rule-26 terms come back INVERTED, including vector and paradigm,
which Alex uses at 198 and 423 per million. The rule is right about the habit
and wrong about part of its word list.

In the control corpus, where no instruction discouraged them, only vector is
confirmed and bedrock and substrate come in as strong-but-weak. So most of
rule 26's confirmed hits are a property of how Claude writes *in this
workspace*, about software, rather than of the model in general. That is
still the prose Alex reads, so the rule earns its place.

## Result 3: the strongest signature has no rule

The topic-matched phrase profile, control Claude against Alex, with general
English as a second baseline. Contractions dominate the top of the list:

| phrase | vs Alex | vs general | Claude/M | Alex/M |
|---|---|---|---|---|
| it isn't | 51.6 | 117.6 | 409.1 | 6.9 |
| it's also | 41.3 | 105.8 | 327.3 | 6.9 |
| it's the | 30.0 | 103.2 | 654.6 | 20.8 |
| a handful | 28.8 | 32.9 | 327.3 | 10.4 |
| that's the | 22.9 | 136.6 | 736.4 | 31.2 |
| that's not | 21.6 | 74.8 | 245.5 | 10.4 |
| this isn't | 6.6 | 89.3 | 327.3 | 48.6 |

Read together these are one move: deny the obvious reading, then supply the
real one. "It isn't a database, it's a log." The model reaches for it to open
paragraphs, to close them, and to define any term it introduces.

Rule 9 was written for this and catches the wrong surface form. Its two
terms, "not just" and "not only", are both INVERTED: Alex writes them at 219
per million each, Claude at 198 and 31.

`slopcheck` now tracks the contracted forms as a named group so later runs
measure whether the habit moves.

## Result 4: punctuation and formatting

Per 1000 words, control Claude against Alex:

| marker | Alex | Claude | ratio |
|---|---|---|---|
| heading count | 0.51 | 5.24 | 10.1 |
| en dash | 0.19 | 0.90 | 4.5 |
| mid-sentence colon | 1.79 | 6.63 | 3.7 |
| em dash | 4.02 | 8.02 | 2.0 |
| exclamation | 1.19 | 0.08 | 0.1 |
| mean sentence length | 18.16 | 14.08 | 0.8 |

Em dashes run at twice Alex's rate in uninstructed Claude and at five times
his rate in vault prose, which is 20.2 per 1000 words. Rule 13 holds. So does
rule 14 on colons. Claude also writes headings ten times as often and
sentences four words shorter, and almost never uses an exclamation mark where
Alex uses one every 840 words.

Two markers cannot be measured with these corpora and should not be read from
the table. Bold spans come out at zero for Alex because his text arrives as
Substack HTML and the converter drops `<strong>`. Curly quotes come out at
11.9 per 1000 for Alex and zero for Claude because Substack's renderer
inserts them. Rules 15 and 19 are untested, not disproven.

## Verification

Three paths were mutation-tested by injecting known slop into one of Alex's
posts, confirming with `cmp` that the file actually changed, and rerunning:

- The audit reported the injected counts exactly: substrate 0 to 10,
  scaffolding 0 to 2, primitive 0 to 2, surface 1 to 7.
- The em-dash marker moved from 3.858 to 4.847 per 1000 words.
- The document score moved from 339.505 to 355.605.

A byte-identical copy of the clean file scored identically on all three, so
the numbers depend on the text rather than on the filename or the run.

## What went wrong on the way, and why it matters for Phase 1

The first two runs ranked "hopper week", "the compendium", "external loop"
and "government data integration" at the top. Those are topics, not habits.
The ratio between two corpora measures what they are about whenever they are
about different things, and no filter fixes that. Three changes were needed:
a proper-noun filter that uses casing away from sentence starts, a second
human baseline so a phrase has to be overused against general English as well
as against Alex, and finally a model corpus generated on Alex's own topics.
Only the third one actually worked.

Phase 1 must therefore generate its four conditions on the same prompt set,
never compare pre-existing corpora. The instrument only reads style when
topic is held fixed.

## What this changes

Proposed edits to `unslop`, for review before anything is applied:

1. Delete rule 7's word list. Zero of 16 terms are confirmed in either Claude
   corpus, and nine of them appear in Alex's own published writing.
2. Replace rule 9's terms with the contracted corrective, which is the same
   idea at the surface form the model actually produces.
3. Keep rule 26. Cut paradigm, which Alex writes at 423 per million against
   Claude's 82 to 163 with or without the rule. Keep vector: see the
   correction below.
4. Keep rules 13 and 14. Both are confirmed at 2.0 and 3.7 times.
5. Leave rules 15 and 19 alone, and note in the skill that they are unmeasured
   until a corpus of Alex's raw markdown exists.

The mechanical half of what survives belongs in `rift` rather than in a skill
that costs context every session. `bin/slopcheck audit` is already the check;
a `forbid` rule per confirmed term is the enforcement.

## Correction, same day: which corpus decides whether a rule earns its place

The first version of this document proposed cutting vector from rule 26,
because vault Claude prose uses it at 74 per million against Alex's 198.
Re-running the audit after the edit showed the opposite in the control
corpus: uninstructed Claude writes vector at 573 per million, 2.9 times
Alex's rate and 5.8 times general English.

A term that looks harmless in vault prose and heavy in the control is a term
the rule is already suppressing. Cutting it would undo the win and the effect
would be invisible, because the evidence for keeping it only exists in prose
written without the rule.

So the corpus that decides a rule's fate is the uninstructed control, never
the instructed vault. Checked against that standard:

- Rule 7's sixteen terms are UNUSED in the control, so nothing is being
  suppressed and the removal stands.
- Paradigm is INVERTED in both corpora, so no rule is holding it down and the
  cut stands.
- Vector is restored.
- Surface, primitive, scaffolding, modality and ratchet are confirmed in vault
  prose and unused in the control. That is topic dependence rather than
  suppression: they are how Claude writes about software, which is most of
  what Alex reads. They stay.

## Limits

The Alex baseline is his published writing from 2023 to 2026, and the later
posts may be LLM-assisted to an unknown degree. That makes every
overrepresentation number here a lower bound.

The control corpus is 12,221 tokens from a single generation with default
sampling. It is enough to establish that a term is absent and not enough to
rank two terms that both appear.

The general baseline includes LLM-written web content, which again pushes
ratios down rather than up.

Nothing here measures whether the confirmed habits are what Alex is reacting
to when he reads Claude prose and finds it bad. That is Phase 1.
