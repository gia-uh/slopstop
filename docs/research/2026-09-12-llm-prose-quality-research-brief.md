---
date: 2026-09-12
type: research-brief
status: complete
tags: [writing, llm, evaluation, voice, personalization]
---

# Why models write bad prose, and what actually moves it

Companion to [[2026-09-12-llm-prose-quality-research-plan]] and
[[2026-09-12-slop-profile-phase-0-findings]]. The plan sets up an experiment;
the findings report what one measurement found. This brief is the literature
and the argument: what causes the defect, which interventions exist, where each
one sits in the pipeline, and what the evidence says each one buys.

## The short version

The defect is not a bug in any one model. It is the predictable output of an
optimisation that rewards familiarity, applied a few million times.

Interventions exist at six points in the pipeline. Their power drops sharply
with distance from the weights, and **every lever available from outside a
model provider is at the far end.** The strongest thing reachable from here is
measurement plus revision, which is unglamorous and is also the only arm with
evidence behind it that survives contact with a second instrument.

Author-voice calibration, the part that sounds most promising, has the weakest
evidence of anything in this document. The one large study finds it works for
structured genres and fails on exactly the genre Alex writes.

## Part 1: the causal chain

Six mechanisms. They compose rather than compete, and they run in order from
cause to symptom.

### 1. Annotators prefer the familiar sentence

Zhang et al. formalise **typicality bias** in preference data: human annotators
systematically favour text that feels familiar, a well-established finding in
cognitive psychology. They verify the bias on real preference datasets and show
it drives mode collapse ([arXiv:2510.01171](https://arxiv.org/abs/2510.01171),
Stanford and Northeastern, Manning as co-author).

This is the origin. Nobody wrote "prefer clichés" into a reward model. Enough
annotators picked the familiar option over the strange one, and the gradient
did the rest. Which means the defect is not an accident of any lab's process;
it is what you get from honest preference collection.

### 2. Alignment suppresses uncertainty, and uncertainty is where the writing is

Sui quantifies an information-theoretic gap between human-authored stories and
model continuations across 28 LLMs
([arXiv:2602.16162](https://arxiv.org/abs/2602.16162), Feb 2026). Human writing
carries measurably higher token-level uncertainty. Alignment steers models away
from uncertain outputs to control hallucination. Instruction-tuned and
reasoning variants widen the gap against their own base models, the gap is
larger in creative writing than in functional domains, and it correlates with
writing quality.

This is the most mechanistic account available of "trite and cliché-ridden",
and it names a genuine tradeoff rather than an oversight: the training that
stops the model inventing facts also stops it reaching for the surprising word.
Literary theory has held for a century that ambiguity is a precondition of
literary effect; the paper makes that measurable and shows alignment removes it.

It also predicts something falsifiable on open weights: a reasoning model should
write worse prose than its own base model.

### 3. The narrowing is baked into the weights, not imposed at generation

Karouzos, Tan and Aletras traced output diversity through three parallel
post-training lineages of Olmo 3 across 15 tasks and four diversity metrics
([arXiv:2604.16027](https://arxiv.org/abs/2604.16027), Apr 2026). Where the
collapse happens co-varies with training data composition: chain-of-thought
distillation loses most semantic diversity at supervised fine-tuning, while DPO
does more damage in the broad instruction-tuned lineage. Suppressing
chain-of-thought at inference leaves answer-level diversity unchanged.

Their conclusion is the sentence that bounds everything in Part 2: diversity
collapse "cannot be addressed at inference time alone."

### 4. The symptom is countable

Paech, Roush, Goldfeder and Shwartz-Ziv measured phrase frequency in model
output against human baselines and found patterns appearing **over 1,000 times
more often** than in human text
([arXiv:2510.15061](https://arxiv.org/abs/2510.15061), MIT-licensed code).

So the defect has a surface that a counter can see. That matters more than it
sounds, because it means the evaluation problem in Part 3 has at least one
instrument that is not itself a language model.

### 5. The judge shares the defect

Self-preference bias in LLM judges tracks perplexity: judges score low-perplexity
text higher than human annotators do, whether or not the judge wrote it
([arXiv:2410.21819](https://arxiv.org/abs/2410.21819)). A NeurIPS 2024 result
shows evaluators recognise and favour their own generations at quality levels
human annotators call equal.

Low perplexity means familiar. So an LLM judge prefers exactly the property
that causes the defect. Every LLM-judged writing benchmark inherits this, which
is why `claude-opus-5` can hold first place on
[EQ-Bench longform](https://eqbench.com/creative_writing_longform.html) at 86.3
with the field's lowest slop score of 5.6 while a careful reader finds its prose
bad. Both readings are correct; they are measuring different things.

### 6. Co-writing propagates the narrowing into the human

Padmakumar and He ran a controlled experiment on argumentative essays and found
that writing with a feedback-tuned model reduces content diversity across users,
not only within one output
([arXiv:2309.05196](https://arxiv.org/abs/2309.05196)). A 2025 empirical
comparison reports the same homogenising effect on creative diversity
([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S294988212500091X)).

This one applies to any months-long collaboration, which is the shape of both
the encyclopedia and `books-tsoc`.

## Part 2: the intervention ladder

Ordered by where it acts. The ordering is the argument: power falls off with
distance from the weights, and everything reachable without being a model
provider sits at the bottom three rungs.

### Rung 1, the data. Fix the preference signal

The only intervention that addresses cause rather than symptom, and the only one
requiring a training run from someone who owns the model. Diversity-aware
objectives exist (group-relative RL variants, planning-branch RL for writing),
but the honest summary is that nobody has shown a preference pipeline that keeps
instruction-following while preserving the tail. Out of reach and worth knowing
about only to understand why the rest of the ladder is weak.

### Rung 2, the weights. Targeted fine-tuning

**FTPO** (Final Token Preference Optimization) from the Antislop paper operates
on individual tokens, adjusting logits wherever a banned pattern appeared in an
inference trace. It achieves **90% slop reduction while holding or improving
GSM8K, MMLU and creative-writing scores**. DPO, on the same task, suppressed
less and degraded writing quality and lexical diversity.

That contrast is the useful part. A surgical, token-level objective beat a
general preference objective at a style task, and the general one did collateral
damage. Available on open weights only.

### Rung 3, the activations. Steering vectors

The seductive option: find a direction in hidden states corresponding to a
style, add it at inference, keep the weights. It works for some concepts.

The evidence says do not build on it for this. Braun et al.,
[arXiv:2505.22637](https://arxiv.org/html/2505.22637v1) (ICLR 2025), conclude
that vector steering "is unreliable when the target behavior is not represented
by a coherent direction", and the companion writeup reports that steering
vectors **tend to degrade model performance, often significantly**. "An author's
voice" is close to the worst case for the coherent-direction assumption: it is a
bundle of dozens of weakly-correlated habits, not one axis.

Also needs hidden-state access, so it is open-weights only regardless.

### Rung 4, the decoding. Sampling

The one rung with a clean positive result. **min-p sampling**
([arXiv:2407.01082](https://arxiv.org/abs/2407.01082), ICLR) improves both
quality and diversity across model families, particularly at high temperature,
confirmed by human evaluation. Shwartz-Ziv is a co-author on both this and
Antislop, which is not a coincidence: both attack the tail of the distribution
rather than the instruction.

**The Antislop sampler** belongs here too: backtracking suppression that handles
8,000+ patterns where plain token banning becomes unusable at 2,000. The
backtracking is what makes the difference, because banning a token mid-phrase
strands the model in a sentence it can no longer finish.

Both need logit access. The Claude API exposes none, so this rung is closed
from here despite being the most promising available-in-principle one.

### Rung 5, the prompt. Instructions, rules, styles, exemplars

Everything reachable today, and the evidence is discouraging.

**Claude Code output styles** replace the default instructions and are sent with
every request, with the system also reminding the model of the style during the
conversation. Stronger delivery than a skill read once at session start. They do
not reach subagents, and a custom style silently removes the built-in
engineering instructions unless `keep-coding-instructions: true`.

**Verbalized sampling** is the interesting outlier: asking the model for k
responses with their probabilities rather than one response raises creative
diversity **1.6 to 2.1x**, training-free, with larger gains on more capable
models ([arXiv:2510.01171](https://arxiv.org/abs/2510.01171)). It works by
routing around the collapsed mode rather than instructing against it, which is
why it does something a rule list cannot.

**Rule lists and exemplar anchoring** are what everyone reaches for and what
Pangram tested: presets "all still sound like Claude, no different than asking
the assistant for a concise answer"; custom styles built from real writing
"still clearly identifiable as AI writing", and substituting the source posts
for the generated examples made it "not particularly" better.

Their mechanism finding is worth keeping. When you give claude.ai your writing
to build a style, an LLM produces **about three sentences of instructions**, and
the example section is itself **generated**, not your paragraphs. So the
feature named after your samples does not put your samples in context.

### Rung 6, after generation. Measure, then revise

Where the defect is finally visible with an instrument that does not share it.

**Critique-and-revise** is established (Self-Refine, and a 2025 critique-refine
framework for personalization,
[arXiv:2510.24469](https://arxiv.org/abs/2510.24469)). The catch is Part 1's
mechanism 5: if the critic is a language model, it prefers low perplexity, which
is the defect. A critique loop with an LLM critic optimises toward the problem.

**Mechanical measurement** escapes that, and it is the one thing this workspace
has actually built and verified. `bin/slopcheck` counts phrase frequency against
a 288k-word corpus of Alex's own published writing plus 5.2M words of general
English, requires overrepresentation against both before ranking a phrase, and
is mutation-tested on three paths.

## Part 3: calibrating against the author's voice

The part that sounds most promising and has the weakest evidence.

### The one large study says it fails on exactly this genre

"Catch Me If You Can? Not Yet"
([arXiv:2509.14543](https://arxiv.org/abs/2509.14543), EMNLP 2025 Findings)
evaluated in-context style imitation with an ensemble of metrics (authorship
attribution, authorship verification, style matching, AI detection) over
**40,000+ generations per model across 400+ real authors**.

The result: models approximate style in **structured formats like news and
email**, and **struggle with nuanced, informal writing in blogs and forums**.
Varying the number of demonstrations did not rescue it.

Blogs is the category. Alex's corpus is 146 blog posts.

### Why generation fails where measurement succeeds

Worth separating, because the two get conflated.

A voice is a joint distribution over dozens of weak signals: sentence-length
variance, function-word ratios, punctuation habits, how often a paragraph opens
with a subordinate clause, which of two synonyms wins. **Recognising** that
distribution is easy, because the signals are individually weak but jointly
distinctive, which is why authorship attribution has worked since the 1960s and
why `slopcheck` finds a 51x ratio on a contracted phrase.

**Producing** it requires the model to hold all of them simultaneously while
also solving the actual writing task, through a channel (the prompt) that can
only carry a description. A three-sentence description of a joint distribution
over forty variables is not a specification of it. That is the gap the EMNLP
study measured, and it explains why the failure is worse in informal genres:
formal genres have conventions doing most of the work, so the model can hit the
target without representing the author at all.

### What voice-calibration does buy

**A baseline that is the author instead of the internet.** The reason Phase 0
found what a generic slop list could not is that it measured against Alex rather
than against "human writing". Generic lists flagged sixteen words he uses freely
and missed the habit running at 51x. Any measurement of "is this in my voice"
needs his corpus; the generation question is separate and harder.

**The corpus already exists and nobody had used it.** 146 posts, 288,150 words,
sitting as an unopened Substack export zip inside `vault/Sources/`. The 20 posts
previously pulled as individual sources were not enough to measure anything: at
43k words almost every candidate phrase had a human count of zero, which means
"did not come up", not "he never writes this".

**A second baseline is required.** One corpus cannot separate an overused phrase
from a topic the other corpus never covered. Phase 0's first two runs ranked
"hopper week" and "government data integration" at the top. The fix that finally
worked was generating the model corpus **on the author's own topics**, which is
the design constraint for any future comparison.

### What it cannot buy, on the evidence

Making the model write like him from a prompt. Three independent results point
the same way: the EMNLP study's direct negative on blogs, Pangram's finding that
substituting real source posts for generated examples changed little, and the
Olmo 3 result that the narrowing lives in the weights.

## Part 4: what this implies for someone in Alex's position

Constraints: Claude API (no logits, no hidden states, no fine-tuning), a 288k-word
English corpus, no Spanish corpus of matching register, two working languages,
and prose that matters in three genres (blog, book, technical report).

Rungs 1 to 4 are closed by the API. Rung 5 has the discouraging evidence above,
with verbalized sampling as the one untried exception. Rung 6 is open, built,
and verified.

That yields a short ranked list.

**First, verbalized sampling, because it is untried, free, and the only prompt-level
method with a mechanism rather than an exhortation.** One session's work to test
on real drafting tasks.

**Second, keep the mechanical evaluator and stop paying for rules that nothing
confirms.** Phase 0 already deleted sixteen banned words that the model does not
write and that Alex uses himself. The same audit should run against every other
rule the pipeline carries, including `/draft`'s voice rubrics and `/revise`'s
catalog, neither of which has been measured.

**Third, treat the Spanish gap as the available contribution rather than a gap.**
Every slop list, every benchmark and all 8,000 Antislop patterns are English.
Spanish slop exists, is not a translation of English slop, and the profiling
method that would find it is corpus-driven and language-agnostic. The blocker is
one corpus of Alex-written Spanish in a consistent register, which does not exist
yet: the encyclopedia chapters are Claude drafts he revised, so both hands are
mixed inside every file.

**Fourth, and only if a local model ever becomes acceptable for drafting: FTPO.**
It is the single intervention with a strong published result on this exact
problem, 90% reduction with no collateral damage on reasoning benchmarks. It
requires open weights, which changes which model writes, which is a larger
decision than a writing tweak.

## What would change my mind

**On the uncertainty gap being the real mechanism.** Measure per-token negative
log likelihood on Alex's corpus against Claude prose using one open model held
fixed, and check whether the gap correlates with his own blind quality ratings.
A null result would mean the defect he reads is not the one the paper measures,
and Part 1 would need reordering.

**On prompt-level methods being weak.** Verbalized sampling reporting 1.6 to 2.1x
diversity has not been tested against a stylometric baseline on this corpus. If
it moves the Phase 0 metric on Alex's own topics, Rung 5 is worth more than this
brief credits.

**On voice calibration being hopeless for generation.** The EMNLP study used
in-context learning with a handful of samples. Nobody has tested it with 288k
words of the same author in a 1M-token context, which is a regime that did not
exist when that evaluation was designed. That is a cheap experiment and it is
the one I would run first if the goal is generation rather than measurement.

## Sources

- [Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity](https://arxiv.org/abs/2510.01171), Zhang et al., v4 Jul 2026.
- [Where does output diversity collapse in post-training?](https://arxiv.org/abs/2604.16027), Karouzos, Tan, Aletras, Apr 2026.
- [LLMs Exhibit Significantly Lower Uncertainty in Creative Writing Than Professional Writers](https://arxiv.org/abs/2602.16162), Sui, Feb 2026.
- [Antislop: A Comprehensive Framework for Identifying and Eliminating Repetitive Patterns in Language Models](https://arxiv.org/abs/2510.15061), Paech et al., Oct 2025.
- [Catch Me If You Can? Not Yet: LLMs Still Struggle to Imitate the Implicit Writing Styles of Everyday Authors](https://arxiv.org/abs/2509.14543), EMNLP 2025 Findings.
- [Understanding (Un)Reliability of Steering Vectors in Language Models](https://arxiv.org/html/2505.22637v1), Braun et al., ICLR 2025, and [A Sober Look at Steering Vectors for LLMs](https://www.lesswrong.com/posts/QQP4nq7TXg89CJGBh/a-sober-look-at-steering-vectors-for-llms).
- [Turning Up the Heat: Min-p Sampling for Creative and Coherent LLM Outputs](https://arxiv.org/abs/2407.01082), ICLR.
- [Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819).
- [Does Writing with Language Models Reduce Content Diversity?](https://arxiv.org/abs/2309.05196), Padmakumar and He.
- [Iterative Critique-Refine Framework for Enhancing LLM Personalization](https://arxiv.org/abs/2510.24469).
- [Homogenizing effect of LLMs on creative diversity](https://www.sciencedirect.com/science/article/pii/S294988212500091X), 2025.
- [Output styles](https://code.claude.com/docs/en/output-styles), Claude Code docs.
- [Can AI detection catch Claude writing styles?](https://www.pangram.com/blog/claude-writing-styles), Pangram.
- [EQ-Bench longform creative writing leaderboard](https://eqbench.com/creative_writing_longform.html), Paech.
