---
date: 2026-09-13
type: research-findings
status: complete
tags: [writing, llm, evaluation, unslop, rift]
---

# What a style prompt buys, and what it costs

Eleven generation arms over the same twelve prompts, measured mechanically
against 147 of Alex's published posts. Companion to
[[2026-09-12-llm-prose-quality-research-brief]],
[[2026-09-12-slop-profile-phase-0-findings]] and
[[2026-09-13-two-pass-caveman-drafting-experiment]].

**Three results.** A style prompt buys compliance on what it names and pays in
sentence-length variance and word count. On a weak model the forbid list
inverts and multiplies the banned words 39-fold. And extended thinking buys
nothing measurable on a writing task, at eight times the latency.

## Design

All arms write the same twelve blog topics, chosen to match Alex's real
subjects. Nine of eleven write from an identical Claude-generated outline whose
format forbids colons and dashes *in the outline*, closing the syntax leak found
on 2026-09-13.

The style prompt is built from the phase-0 measurements: Alex's own rates, the
audited noun list, the contracted corrective. It names em dashes, the
corrective and the metaphor nouns, and says **nothing** about mid-sentence
colons or heading density, so those are a transfer test rather than an
obedience test.

Generators in `.playground/slop-corpus/`, corpora under
`vault/Efforts/Areas/Writing/voice/corpus/slop/`.

## The table

Rates per 1000 words. `slen` is mean sentence length, `sd` its standard
deviation.

| arm | n | words | em/1k | corr | nouns | colon | slen | sd |
|---|---|---|---|---|---|---|---|---|
| opus API, no outline, no style | 12 | 1018 | 8.00 | 2.94 | 0.83 | 7.00 | 13.79 | 9.51 |
| gemini, outline, no style | 12 | 1116 | 5.04 | 0.00 | 0.42 | 2.04 | 20.75 | 8.08 |
| deepseek, outline, no style | 12 | 1176 | 5.39 | 0.06 | 0.31 | 3.36 | 14.71 | 7.54 |
| mistral, outline, no style | 12 | 1171 | 5.42 | 0.00 | 0.24 | 1.37 | 14.52 | 7.54 |
| gemini, outline + style | 12 | 779 | 0.00 | 0.00 | 0.00 | 0.19 | 13.25 | 5.47 |
| deepseek, outline + style | 11 | 947 | 0.12 | 0.11 | 0.10 | 0.69 | 12.92 | 5.95 |
| mistral, outline + style | 12 | 734 | 1.51 | 0.00 | 0.35 | 0.91 | 14.31 | 5.97 |
| claude -p haiku, style in system slot | 12 | 1311 | 0.00 | 0.61 | 0.43 | 2.51 | 11.48 | 6.50 |
| claude -p sonnet, style in system slot | 12 | 1153 | 0.81 | 0.78 | 0.15 | 3.87 | 13.95 | 7.84 |
| claude -p opus, style in system slot | 12 | 1294 | 0.00 | 0.11 | 0.27 | 3.54 | 12.53 | 7.20 |
| claude -p haiku, thinking on | 11 | 1206 | 0.14 | 0.46 | 0.23 | 1.55 | 11.26 | 6.01 |
| **Alex, published** | **147** | **1960** | **3.68** | **0.25** | **0.30** | **2.01** | **17.54** | **9.92** |

## Result 1: the style prompt does the work, not the cheap model

Paired within each model, styled against unstyled from the same outline:

| model | em dashes | colons |
|---|---|---|
| gemini | 10 better / 0 worse, p = 0.002 | 10 / 0, p = 0.002 |
| deepseek | 9 / 0, p = 0.004 | 11 / 0, p = 0.001 |
| mistral | 11 / 1, p = 0.006 | 6 / 4, p = 0.754 |

Unstyled, the cheap models already run at 5.04 to 5.42 em dashes per 1000,
close to Alex's 3.68 and well under the opus control's 8.00. The style prompt
takes them to near zero. So the earlier reading that "cheap models write
cleaner" was wrong: the prompt was doing it, and cheap is only cheap.

## Result 2: the bill arrives in variance and volume

Every model loses about a quarter of its sentence-length variance when given
the style prompt: 8.08 to 5.47, 7.68 to 5.95, 7.18 to 5.63, 7.54 to 5.97. Alex
sits at 9.92. **The unstyled arms are closer to him on variance than the styled
ones.**

Word count falls with it: gemini down 30%, mistral down 37%, delivering 734 to
947 words against Alex's average of 1960.

The cleanest statement of this does not need a correlation. **The style prompt
carried six instructions about counts and one about a distribution.** The six
count instructions all worked. The one distribution instruction, "average
sentence length around 18 words, with real variation between short and long",
failed in both halves: every arm landed between 11.5 and 14.3 words, and
variance went *down* rather than up.

Across the eleven arms, em-dash rate and sentence-length variance correlate at
**r = +0.808**, and the arm closest to Alex's variance is the worst arm on every
tell. Part of that link is mechanical, since an em dash is itself a device for
building a long sentence. The failed instruction is the stronger evidence,
because it was aimed directly at variance and missed.

## Result 3: a forbid list handed to a weak model becomes a vocabulary list

Qwen, metaphor-noun counts across twelve documents:

| | with style prompt | without |
|---|---|---|
| vector | 36 | 2 |
| substrate | 33 | 4 |
| primitive | 32 | 0 |
| bedrock | 29 | 1 |
| scaffolding | 29 | 0 |
| harness | 27 | 0 |
| wedge | 26 | 0 |

Rate per 1000 words: **17.07 with the list, 0.44 without.** Paired 0 of 12,
p = 0.000.

The near-uniform frequency across every banned word is the signature. This is
not technical vocabulary arriving naturally: "wedge" twenty-six times across
twelve posts on binary search and the history of AI is not natural usage of
anything. The model read the prohibition list and used it as a word bank.

This is the measured version of what the workspace already recorded from image
generation, that negative prompts are the weakest instrument available. The
multiplier here is 39x.

## Result 4: the system slot mitigates both costs

`claude -p` with `--system-prompt` **replaces** Claude Code's agentic system
prompt rather than appending to it, and `--setting-sources ""` drops CLAUDE.md,
skills and plugins. The same style text, moved from the user turn into that
slot, behaves differently:

| | OpenRouter styled | claude -p styled |
|---|---|---|
| words | 734 to 947 | 1153 to 1311 |
| variance | 5.47 to 5.97 | 6.50 to 7.84 |
| colons vs Alex's 2.01 | 0.19 to 0.91 | 2.51 to 3.87 |

Volume is preserved, variance recovers most of the way to the unstyled arms,
and mid-sentence colons land near Alex instead of far under him. Sonnet at 7.84
variance is the best of any styled arm.

Cost and latency, measured, thinking disabled:

| model | wall | list cost | words |
|---|---|---|---|
| haiku | 20.8s | $0.0119 | 1316 |
| sonnet | 26.1s | $0.0324 | 1172 |
| opus | 37.3s | $0.0872 | 1343 |

Input runs 1400 to 1700 tokens because the clean room holds no CLAUDE.md, no
skills and no tool schemas. The dollar figures are list-price accounting; the
actual charge falls on the subscription pool.

## Result 5: extended thinking buys nothing here

Haiku, same outline, same style prompt, thinking on against off:

| | thinking on | thinking off |
|---|---|---|
| wall time | 137.7s | 17.5s |
| thinking tokens | 12,527 | 0 |
| output tokens | 13,943 | 1,441 |
| prose words | 1052 | 1105 |

Across the full arms the measured tells are a wash: thinking is marginally
better on colons (1.55 against 2.51) and nouns (0.23 against 0.43), marginally
worse on em dashes, word count and variance.

So a post written from a finished outline spends nine times more thinking than
prose, takes eight times as long, and comes out the same. `MAX_THINKING_TOKENS=0`
is the only real off switch; `--effort low` still produced 133 thinking tokens
on a two-sentence task.

**This applies to aegis.** `_oneshot_argv` in `drivers/claude.py` documents a
64% cut in *input* tokens from `--setting-sources ""` and leaves the output side
untouched. The loop judge and the recap are structured-generation calls at every
turn boundary with nothing to reason about, and they are paying this bill.

## Limits

Twelve prompts, one run per arm, no repeats. Enough to reject a large effect,
not to rank two close arms.

**These are tells, not quality.** No human has read any of these documents. The
arm with the most human-like variance is the arm with the worst tells, and
nothing here says which reads better. That measurement is one blind rating
session and it is the missing instrument in every finding above.

The style prompt was written in English and every arm is English. Nothing here
transfers to Spanish without re-measuring.

## What this changes

For `unslop` and any successor: a forbid list is not merely unconfirmed, as
phase 0 found. It is **actively harmful on two axes nobody was watching**,
volume and variance, and it **inverts on weaker models**. Rules move counts.
Quality lives in the distribution, and no instruction tested here moved a
distribution in the intended direction.

For `rift`: this is the argument for the `delta` and variance metrics in
[reference-corpora-design](https://github.com/apiad/rift/blob/main/docs/reference-corpora-design.md).
A checker that only counts banned phrases would score the gemini styled arm
best and Alex himself worst, since he writes 3.68 em dashes per 1000 and that
arm writes zero. Any slop rule set needs a two-sided target, not a floor.

For the pipeline: `claude -p` with the style in the system slot, thinking off,
is the best-performing configuration measured, at subscription cost and about
20 seconds per post on haiku.
