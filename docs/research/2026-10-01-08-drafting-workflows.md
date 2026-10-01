# Track 8: drafting workflows with AI assistance and no per-author training

## Headline

1. The one lever that reliably preserves voice is to keep the content tokens
   human. Every model-touches-the-draft workflow, even the mildest, drifts
   toward model style. The strongest measured version of this is
   arXiv:2603.18161: models told to make "grammar only" or "minimal" edits
   still raise adjective use 40 to 87 percent, cut pronouns 31 to 56 percent,
   and shift meaning, while a human editor moves under 5 percent on any part of
   speech. So the workflow question is not "which model writes" but "which
   model does the least, bounded by a machine check the model cannot argue
   with."

2. Translation is not a free pass out of the model's style. LLM and NMT output
   both carry translationese, and even a multilingual LLM generating in plain
   English produces translationese (arXiv:2608.17399, Aug 2026). A
   Spanish-draft-then-translate pipeline trades "reads like Claude" for "reads
   translated." It may lower a detector score while still reading non-native to
   a human.

3. Alignment is what makes prose both bad and detectable. Instruction-tuning
   and RLHF widen the uncertainty gap against a model's own base model
   (arXiv:2602.16162), and RLHF makes output longer, more repetitive, and more
   detectable (arXiv:2503.17965). Base, older, non-aligned models are the one
   class that points the right way on both axes, and they run locally, outside
   any watermarking provider.

4. Speech-first drafting is the only workflow where every content token is the
   author's by construction, and it is cheap. The evidence is thin and mostly
   practitioner-level, but it is consistent: dictation changes prose in a human
   direction (looser rhythm, longer natural sentences, more specificity) rather
   than a model direction.

5. Span-level, detector-guided revision has the right idea and no measured win.
   A span-level detector now exists for scientific text (arXiv:2510.00890), but
   detectors explicitly struggle with light rewriting, and Pangram's own demo
   shows removing flagged phrases leaves the prediction at 99.9 percent. Local
   rewriting also re-injects model style at exactly the spans it touches.

## Findings

### 1. L1 drafting plus machine translation

There is no clean measured comparison of "draft in Spanish then translate"
against "draft directly in English" for a bilingual author. The literature
that exists runs in two neighboring lanes, and both are discouraging for the
translate-then-publish idea.

The translationese lane says machine output keeps a fingerprint no matter who
translates. Kong and Macken (arXiv:2506.22050, Jun 2025) built a four-corpus
English to Chinese news set and found that original Chinese text is "nearly
perfectly distinguishable" from both NMT and LLM output. The tell is shorter
sentences and more adversative conjunctions. They also separated LLM from NMT
at roughly 70 percent accuracy, with LLMs showing higher lexical diversity.
Valentini et al. (arXiv:2608.17399, Aug 2026) went further: they measured
translationese indicators in what multilingual LLMs generate directly, with no
translation step at all, in five languages. Their central result is that
LLM-generated text carries translationese in every language, including
English, and it is elevated in non-English languages. They also repeat the
older finding (Toral, 2019) that even machine-translated text a human then
post-edits still shows translationese. Taken together: passing your draft
through a translation model does not leave your voice, it leaves a translated
fingerprint, and a human post-edit does not fully scrub it.

On the question of whether LLM translation rewrites, the evidence says yes in
the specific sense that matters. Translationese is itself a kind of rewrite:
simplification and explicitation, the two universal translation effects, mean
the model drops rare words and adds connectives. The same generic claim that
readers catch in LLM prose reappears as "translated" prose. I did not find a
study measuring whether a "literal, minimal-change" translation prompt bounds
this, or whether sentence-aligned or terminology-locked translation avoids
translationese. Terminology-locked constrained decoding exists
(arXiv:2511.07461 is a recent dual-stage terminology-aware system), but it
targets term accuracy, not naturalness. The null result matters for design: no
published prompt has been shown to make machine translation read like native
human English, so the toolkit should not assume a good translation prompt
exists.

The education lane is about L2 learners using MT, not about this author.
Work such as the Taylor and Francis review (Cogent Education, 2025) describes
how non-native writers lean on MT and what teachers do about it, but it
measures nothing about voice or detectability. One comparison exists between
L2 learner writing and machine-translated text (System, 2021, comparing learner
essays against parallel MT), but that study contrasts learner error against MT
fluency, which is the opposite of what this project needs.

The honest summary is that "draft in L1, translate, publish" is under-evidenced
as a quality play and over-evidenced as a translationese risk. It has one real
upside worth keeping: composing in the native language usually gives higher
idea density and richer specific detail, because the author is not spending
cognitive budget on English syntax. That upside is about the drafting step,
not the translation step, and a workflow can capture it without letting a
translation model write the English.

### 2. Dictation and speech-first drafting

The strongest source here is a practitioner, not a paper. Clive Thompson, a
working journalist who writes for the New York Times Magazine and Wired,
published "The Literary Style of Voice Dictation" (Medium, Sep 2022). His
account of the mechanism is specific: typing is iterative, full of backspace
and mid-sentence revision, while dictation forces him to think the sentence
through first and then say it whole. He reports the resulting prose is looser,
more conversational, and longer-sentenced. That is exactly the axis where
Phase 0 and the arms experiment found model prose fails: sentence-length
variance. Alex's published writing runs a sentence-length standard deviation of
9.92 against every model arm between 5.47 and 9.51.

The academic side is mostly a register claim, not a voice claim. There is a
long linguistics literature that spoken and written language differ
systematically, and recent work applies it to transcription (NLP4DH 2024, "Text
vs. Transcription"). What this means for the toolkit is that dictation changes
the author's register toward speech. For a technical blog that is an acceptable
trade, arguably a benefit, because spoken register is further from model prose
than formal written register is. But it is a real change, and no study I found
measures whether dictating preserves the author's written voice, specificity,
or idea density. That is an open question.

Tools exist for the cleanup step the workflow needs: taking a rambling
transcript and turning it into prose with only disfluency removal. The
well-known ones (Whisper for transcription, then a constrained edit pass) are
plenty. The design rule the evidence supports is that the cleanup must be
disfluency-only and must not be a free paraphrase. The distort paper below is
the reason: any model asked to "clean up" prose will also smooth it.

### 3. Minimal-edit and constrained-edit methods

This is the best-evidenced question in the track, and the result is blunt.
Abdulhai et al., "How LLMs Distort Our Written Language" (arXiv:2603.18161,
Mar 2026), ran 86 pre-LLM student essays through three frontier models under
five edit instructions, including "grammar: revise for grammar" and "minimal:
rewrite and keep a similar word count," with and without expert human feedback.

The numbers. On lexical change, humans sit at a Jensen-Shannon divergence of
0.2 to 0.3 from their own draft, while claude-haiku, the least-distorting
model, sits at a mean of 0.476, and gpt-5-mini reaches nearly triple the human
baseline with many essays above 0.7. On part of speech, humans move under 5
percent on any category. The models raise adjective use 57 to 90 percent and
coordinating conjunctions 13 to 90 percent, and cut pronouns 40 to 60 percent.
The "minimal edits" instruction still raises adjectives 40 to 87 percent and
cuts pronouns 31 to 56 percent. On meaning, even the grammar-only and
minimal-edit conditions shift the essay's conclusion, often to neutral or
pro-support on the self-driving-cars topic. On emotion, models roughly double
both positive and negative sentiment (positive up 37 to 54 percent, trust up 17
to 53 percent, negative up 24 to 38 percent) while humans move under 5 percent.

Two things follow directly. First, a prompt cannot bound drift: "only fix
grammar" is not enforced by the model, and the model changes meaning anyway.
Second, the bound must come from outside the model, as a mechanical check. An
edit-distance budget, a diff review where the human accepts each change, or a
rule that the model returns a unified diff rather than a rewritten paragraph
are all enforcement, and none of them are prompts. The diff-accept pattern is
the strongest: it lets the human see and veto every token the model would
change, which is the only way the 40 to 87 percent adjective inflation gets
caught before it lands.

This pairs with the earlier finding the synthesis brief already carried: in
"Can You Make It Sound Like You?" (arXiv:2604.24444) writers who edited an LLM
draft toward their own style still ended closer to the LLM than to themselves
(p = .0002). Editing does not escape the model's distribution from either
direction. The only position that keeps the author's distribution is the one
where the author supplies the text.

### 4. Model choice for prose

The uncertainty-gap result (arXiv:2602.16162, Feb 2026) is the mechanism: human
writing carries higher token-level uncertainty than model continuation, and
instruction-tuned and reasoning variants widen that gap against their own base
models. Its direct prediction is that a base model writes more varied prose
than its aligned descendant. Xu and Zubiaga (arXiv:2503.17965, Mar 2025) add
the detectability half: RLHF makes output longer, more repetitive, less
syntactically and semantically diverse, and more detectable. So the class of
models most likely to both write better and read less like AI is the base,
older, less-aligned one, and those are exactly the models that run on open
weights, outside a watermarking provider.

The workflow evidence for base models is early and tool-shaped rather than
measured. Loom (generative.ink, Feb 2021, with code at
github.com/socketteer/loom) is the canonical example: the human writes a
prefix, a base GPT-3 continues it, and the interface branches every
continuation into a tree the user walks and merges. The author's text is the
root, every generation is a continuation from his actual words, and the user
selects branches by reading them. This is "loom-style branching" exactly, and
it is 2021 GPT-3 technology, so it works with small open models today. Its
weakness is control: a base model is hard to steer to a specific point, so this
workflow produces candidate prose for the author to pick and rewrite, not a
finished paragraph on demand.

Multi-model ensembles for prose have no direct measured result I found. The
closest evidence is the general homogenization finding that different model
families converge to the same style anyway (cited throughout the distort
paper), which weakens the hope that mixing models adds diversity. An ensemble
averages toward the common mode, and the common mode is the defect. Model
mixing is better framed as a sampling play: generate candidates from a base
model and pick, which is what Loom already does, rather than averaging logits.

### 5. Span-level, detector-guided revision

The detector half exists. Sci-SpanDet (arXiv:2510.00890, Oct 2025) localizes
AI-generated spans in scientific text with Span-F1 of 74.36 and AUROC of 92.63,
so a tool could flag exactly which sentences read AI-made. Two caveats in the
same paper blunt the workflow. It is built for IMRaD scientific text, not blog
register. And the paper states plainly that finer-grained detection methods
"struggle with light rewriting," which is the condition this workflow creates
by definition.

The revision half has no measured win, and two reasons to expect a loss.
Pangram's writeup (2026, vendor) shows that removing its highlighted AI phrases
from a GPT essay leaves the prediction at 99.9 percent, because the detector
keys on higher-order structure, not the flagged words. So the flagged spans are
post-hoc callouts, not the levers that move the score, and editing them does
not change the verdict. And from the distort paper, any span the model rewrites
gets model style injected at exactly that spot. Local rewrite trades a detector
signal for a style drift signal. No study I found compares span-level rewriting
against whole-document rewriting on either detector score or voice
preservation, so this remains unproven in both directions.

### 6. Verbalized sampling applied to rewriting

Verbalized sampling (arXiv:2510.01171, v4 Jul 2026) raises creative diversity
1.6 to 2.1x by asking for k candidate responses with their probabilities rather
than one, with larger gains on more capable models. It is measured for
generation, not for rewriting. The rewriting analog is straightforward to
state: for each sentence or paragraph that needs changing, ask for k
alternative local rewrites, then pick the one that minimizes edit distance to
the original or maximizes style match against the author's corpus. Whether
that preserves voice better than a single rewrite is untested. The mechanism
is the same as generation (route around the collapsed mode by generating k and
selecting), so the prediction is that it should help, but no number exists.
This is the cheapest experiment in the list to run and the least supported by
prior work.

## Implications for our toolkit

Build the workflow around a one-way rule: the model may not originate the
content tokens, only transform them under a mechanical budget. Concretely:

1. The default is speech-first or hand-typed author draft, in English, with a
   constrained cleanup pass that returns a diff and is bounded by edit
   distance. Reject any cleanup whose diff changes more than a set fraction of
   tokens, and show the author every change for accept or reject.

2. If the author wants to compose in Spanish, keep the translation as a
   reading aid and an idea-density aid, not a publish step. Translation is
   treated as an intermediate the author rewrites from, because translationese
   does not clean off.

3. Move the non-watermarking prose to open weights. The base-model and
   Loom-style branching work depends on a local model, which smaug has. A small
   base model continuing from the author's own prefix is the one workflow the
   uncertainty-gap and RLHF papers jointly predict will be both more varied and
   less detectable.

4. Use detectors and span detectors as probes, never as an objective to lower.
   The brief already says this, and the Pangram demo is the concrete reason: a
   score you lower by editing flags is a score that was never about the flags.

5. Enforce the bound mechanically, the way this workspace already does with
   slopcheck. An edit-distance gate and a diff-accept UI are the enforcement;
   "only fix grammar" is not.

6. Measure on Alex's own corpus, holding topic fixed, per the arms experiment's
   own lesson. The instruments are sentence-length variance, tell rates (em
   dash, the corrective, metaphor nouns), style distance (LUAR or Burrows
   delta), edit distance from the author's draft, and a detector probe, plus
   one blind reader session, which the arms experiment flagged as the missing
   instrument.

## Ranked candidate workflows

Ranked for this author: Spanish-native CS professor, writes well in Spanish,
publishes in English, refuses fine-tuning, will not let a watermarking model
write the final tokens.

### 1. Speech-first draft plus bounded cleanup

Steps. He dictates the post (in English), Whisper transcribes it, and a model
is asked only to remove disfluencies and false starts, returning a diff. A
mechanical gate caps the fraction of tokens the model may change, and the
author accepts or rejects each diff. Final tokens are his.

Models touching final text. A transcription model and a small editor model,
bounded to a small token fraction. The author writes all content.

Strengths. Every content token is the author's by construction, so voice,
specificity, and sentence-length variance are preserved for free. Spoken
register is further from model prose than written register. No watermarking
provider touches the output. Cheap and fast.

Risks. Spoken register differs from his written voice, so the posts may read
looser than his published blog. Transcription errors need his review. The
"dictation preserves voice" claim itself is under-evidenced.

Measure. Sentence-length variance against his 9.92 baseline, tell rates,
style distance to his corpus, edit distance between transcript and final text,
and a blind reader rating.

### 2. Hand-typed author draft plus diff-based constrained edits

Steps. He types the English draft. A model proposes local grammar and spelling
edits as a diff, never a rewrite. He accepts each change. The same
edit-distance gate runs. Optionally pair with a detector probe after editing.

Models touching final text. A small editor model, bounded to a small token
fraction, with the author as the final arbiter of every change.

Strengths. This is the arm the earlier brief predicted lands closest to his
voice ("Alex drafts, model polishes"). The diff pattern is the only tested
guard against the 40 to 87 percent adjective inflation the distort paper
measured.

Risks. Even accepted small edits accumulate model vocabulary. If he accepts
without reading, it becomes Claude-polished by default. No fully local
grammar-only model is guaranteed clean.

Measure. Edit distance from his draft, tell rates before and after, style
distance to his corpus, and a comparison against the speech-first arm on the
same topics.

### 3. Base-model continuation with Loom-style branching

Steps. On smaug, run a small open base model. He writes the opening of each
section or paragraph, the model continues from his text, and a branching
interface offers several continuations he selects and edits. The selected
branch is human-edited into the draft.

Models touching final text. A non-watermarking open base model, with the
author selecting and editing every continuation.

Strengths. Base models write more varied prose (uncertainty gap) and are less
detectable (RLHF result). Continuation from his actual words anchors the
output in his content. No provider watermark. This is the only workflow where
the model writes substantial new prose and there is a mechanistic argument
for it being acceptable.

Risks. Base models are hard to steer and produce nonsense as often as good
branches. Selection burden is on him. No measured result that the output
reads as his voice or as good prose.

Measure. Uncertainty or diversity of the candidate set, tell rates of selected
branches, style distance to his corpus, blind reader rating, and detector
probe on the final merged text.

### 4. Spanish L1 draft plus translation as an intermediate, then rewrite

Steps. He drafts in Spanish for idea density. A translation model produces an
English version, which he treats as a draft to rewrite from, not a draft to
publish. He rewrites the English himself, optionally with the bounded cleanup
from workflow 2.

Models touching final text. A translation model touches only the intermediate;
the final English tokens are his.

Strengths. Captures the real upside of L1 drafting, higher idea density and
specific detail, without letting the translation model write the publishable
English.

Risks. Translationese does not clean off, so if he skips the rewrite step the
text reads translated. He has to do real rewriting work, which is what he was
trying to save. Detector scores may be misleadingly low on translated text,
inviting over-trust.

Measure. Compare idea density and specific-fact count against a directly
drafted English post, and run a translationese probe if one is available; at
minimum, blind reader judgment on whether it reads translated.

### 5. Span-level detector-guided local rewrite

Steps. Run a span detector (Sci-SpanDet or a Pangram-style segment score),
flag the offending sentences, and rewrite only those, bounded by edit distance
and author acceptance.

Models touching final text. A detector plus a small rewrite model, bounded to
the flagged spans.

Strengths. Minimal intervention in principle, and a span detector now exists.

Risks. Detectors struggle with light rewriting, flagged phrases are not the
levers that move the score (Pangram demo: 99.9 percent after removal), and
each rewritten span re-injects model style. No measured win either way.

Measure. Detector score before and after, style distance to his corpus, and a
direct comparison against whole-document cleanup on the same text.

### 6. Verbalized sampling on local rewrites

Steps. For each sentence or paragraph that needs changing, ask for k
alternative rewrites, then select the one closest to the original by edit
distance or best matched to his corpus by style distance.

Models touching final text. One rewrite model, but the author or a mechanical
selector picks among k candidates.

Strengths. Cheapest experiment on the list. The mechanism is the same as
generation, where it measurably helps (1.6 to 2.1x diversity).

Risks. No result exists for the rewriting setting, so it may do nothing. Still
a prompt-level method on an instruct model, so the diversity collapse the
brief documented still applies.

Measure. Diversity across the k candidates, edit distance of the chosen
candidate, tell rates and style distance of the final text against the single
rewrite baseline.

## Open questions

- No measured comparison exists of "draft in L1 then translate" against
  "draft in L2" for a fluent bilingual author, on voice, idea density, or
  detectability. This is the largest literature gap and it is exactly the
  comparison this author would need.
- Does dictation actually preserve an author's written voice, specificity, and
  sentence-length variance, or does it simply swap written voice for spoken
  voice? No study isolates this.
- Does a "literal, minimal-change" or terminology-locked translation prompt
  reduce translationese in a measurable way? No published result either way.
- Does span-level rewriting beat whole-document cleanup on any metric? No
  study compares them.
- Does verbalized sampling help when applied to rewriting rather than
  generation? Untested.
- Does a translated English text score lower on AI detectors precisely
  because it is translated and not generated, and does that score mislead the
  author into trusting prose a reader would still flag as non-native?

## Sources

- Abdulhai, White, Wan, Qureshi, Leibo, Kleiman-Weiner, Jaques, "How LLMs
  Distort Our Written Language," arXiv:2603.18161, Mar 2026.
  https://arxiv.org/abs/2603.18161
- Kong and Macken, "Decoding Machine Translationese in English-Chinese News:
  LLMs vs. NMTs," arXiv:2506.22050, Jun 2025.
  https://arxiv.org/abs/2506.22050
- Valentini, Wright, Granados, Colunga, von der Wense, "An Investigation of
  Translationese in the Generations of Multilingual Large Language Models,"
  arXiv:2608.17399, Aug 2026. https://arxiv.org/abs/2608.17399
- Xu and Zubiaga, "Understanding the Effects of RLHF on the Quality and
  Detectability of LLM-Generated Texts," arXiv:2503.17965, Mar 2025.
  https://arxiv.org/abs/2503.17965
- Yin and Wang, "Span-level Detection of AI-generated Scientific Text via
  Contrastive Learning and Structural Calibration," arXiv:2510.00890, Oct 2025.
  https://arxiv.org/abs/2510.00890
- Sui, "LLMs Exhibit Significantly Lower Uncertainty in Creative Writing Than
  Professional Writers," arXiv:2602.16162, Feb 2026.
  https://arxiv.org/abs/2602.16162
- Zhang et al., "Verbalized Sampling: How to Mitigate Mode Collapse and Unlock
  LLM Diversity," arXiv:2510.01171, v4 Jul 2026.
  https://arxiv.org/abs/2510.01171
- "Can You Make It Sound Like You?" arXiv:2604.24444, cited from the synthesis
  brief. https://arxiv.org/abs/2604.24444
- Thompson, "The Literary Style of Voice Dictation," Medium, Sep 2022.
  https://clivethompson.medium.com/the-literary-style-of-voice-dictation-6968cf2209c9
- "Loom: interface to the multiverse," generative.ink, Feb 2021, code at
  github.com/socketteer/loom.
  https://generative.ink/posts/loom-interface-to-the-multiverse/
- "Can you avoid AI detection through editing?" Pangram, 2026.
  https://www.pangram.com/blog/can-you-avoid-ai-detection-through-editing
- "Text vs. Transcription," NLP4DH 2024.
  https://aclanthology.org/2024.nlp4dh-1.35.pdf
