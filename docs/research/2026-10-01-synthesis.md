---
date: 2026-10-01
type: research-brief
status: complete
tags: [writing, llm, humanization, voice, detection, unslop]
---

# What makes AI-assisted writing read as AI, and what moves it

Follows [[2026-09-12-llm-prose-quality-research-brief]],
[[2026-09-12-slop-profile-phase-0-findings]] and
[[2026-09-13-style-prompt-arms-experiment]]. Those three covered why models
write the way they do and what a style prompt buys. This brief covers what the
September work skipped: what humanizer tools do, how detectors decide, what
human readers notice, and how a specific author's voice gets into generated
text.

Five research tracks and one fact-check pass ran on DeepSeek V4 Pro through
opencode. The raw reports, the shared prompt and the verification table are in
`vault/Efforts/Areas/Writing/voice/research/2026-10-01-humanization/`. Every
number below was checked against its primary source in `06-verification.md`
unless it says otherwise.

## The short version

1. Commercial humanizers are built to fool a classifier, and the readers who
   matter catch their output anyway. Nothing from that market is worth
   reusing.
2. Readers who use LLMs daily detect AI text at 92.7% with 4% false alarms.
   They key on model vocabulary, formulaic structure and vague optimistic
   conclusions. Underneath those cues sits a content defect our instruments
   do not measure: specific facts turn into generic, inflated claims.
3. Editing an LLM draft toward your own style still leaves it closer to the
   LLM than to you. This is the strongest result for choosing between "Claude
   drafts, Alex edits" and "Alex drafts, model polishes".
4. Voice moves through the weights and not through the prompt. Fine-tuning on
   an author's works flipped expert readers from rejecting the imitation to
   preferring it, and detectors stopped flagging it.
5. Telling readers that a text was AI-assisted lowers their ratings of the
   identical text, and better prose cannot remove that penalty. It is a
   separate problem with a separate lever.

## 1. What readers catch

Russell, Karpinska and Iyyer (arXiv:2501.15654, ACL 2025) had annotators label
300 non-fiction articles as human or AI. Annotators who never use LLMs for
writing scored 56.7% true positives and 51.7% false positives, which is chance.
Annotators who use LLMs daily scored 92.7% and 4.0%, and a majority vote of
five of them misclassified one article in 300, including articles that had
been paraphrased and run through humanizers. On the humanized set the open
detectors collapsed (Binoculars 7%, Fast-DetectGPT 23%).

The experts named their cues. The most common was "AI vocabulary" (vibrant,
crucial, significantly), followed by formulaic sentence and document
structure, including "optimistically vague conclusions". The novices chased
fancy words, perfect grammar and a neutral tone, which are wrong cues and
produced their false positives.

That vocabulary list is a moving target. Phase 0 found that uninstructed
Claude in 2026 writes none of the 2023 words, while the corrective "it isn't
X, it's Y" runs at 22 to 52 times Alex's rate. The structure cues are the
durable ones, and the corrective is one of them. EQ-Bench gives the
not-X-but-Y pattern a quarter of its slop score, and blader/humanizer lists it
first among its 26 patterns.

Wikipedia's "Signs of AI writing" names a cause beneath the surface cues: the
model regresses to the mean, replacing a rare specific fact with a generic
positive description that is "simultaneously less specific and more
exaggerated". Pagan et al. (arXiv:2511.04195) found that a BERT classifier
still separates model text from human social-media text at 85% or better after
fine-tuning and persona prompting, and that affective tone is the
discriminator that persists. A survey of university professors (Georgiou,
2026, not independently verified) ranks invented facts and missing sources as
the strongest tells and difficult words as the weakest.

No study isolates "add specific, personal, verifiable detail" as an
intervention and measures detection before and after. The content-side cause
rests on field guides, surveys and the affective-tone result, not on a causal
experiment.

## 2. What humanizers do

Pangram's DAMAGE paper (arXiv:2501.03437) audited 19 humanizers. They fall
into two families. Word spinners swap synonyms one for one, inject typos,
break spacing, and substitute look-alike Unicode characters such as the thin
space U+2009. LLM humanizers are a language model told to paraphrase "in a
conversational tone", and they add and delete claims while doing it.

Both families degrade the text. In DAMAGE's fluency test the best humanizers
were preferred over their own unedited input 26% of the time and the worst
2.67% of the time. Pangram states the tradeoff directly: the more readable a
humanizer's output, the more detectable it is. The tools that evade detection
are the ones that produce garbled prose, and Russell's expert readers catch
the rest.

Everything in this market changes surface statistics to fool a classifier,
none of it makes prose better or more personal, and we will not build it.

## 3. The disclosure penalty

Raj, Berg and Seamans (Journal of Experimental Psychology: General, 2026)
ran 16 preregistered experiments with 27,491 participants. Readers rated the
same text lower when told an AI wrote it, or helped write it. Saying a human
used AI as a tool cost as much as full machine authorship. Perceived
authenticity mediated the effect, not perceived quality.

Once a reader believes a text is AI-assisted, no rewrite of the prose changes
that judgment. The toolkit can make the prose stop triggering the suspicion.
What to say about the process, and when, is a separate decision.

## 4. Post-editing keeps the model's style

"Can You Make It Sound Like You?" (arXiv:2604.24444, n=81) asked writers to
edit LLM drafts toward their own style. The edits did move the text toward
the writer (g = 0.55) and away from the LLM (g = −0.41). But the edited text
stayed significantly closer to the LLM draft than to the same writer's
unassisted writing (p = .0002, g = −1.43).

A second result points the same way. "How LLMs Distort Our Written Language"
(arXiv:2603.18161) found that models asked to make only grammar edits still
change the meaning of the text significantly.

This bears directly on our workflows. "Claude drafts, Alex edits" starts from
the model's distribution and does not get out of it by editing. "Alex drafts,
model polishes" starts from his and risks drifting away, by an amount nobody
has measured for this author. Both directions can be measured on his own
topics with the instruments in section 6.

## 5. Voice moves through the weights

Chakrabarty, Ginsburg and Dhillon (arXiv:2510.13939, preregistered) compared
MFA-trained writers with three frontier models imitating 50 award-winning
authors. With in-context prompting, MFA readers rejected the imitation on
stylistic fidelity (odds ratio 0.16) and on quality (0.13). With the model
fine-tuned on each author's complete works, the same readers preferred the AI
on fidelity (8.16) and quality (1.87). Detectors flagged 97% of the prompted
output as AI and 3% of the fine-tuned output. The median fine-tuning cost was
$81 per author.

This contradicts nothing in September. The EMNLP 2025 study and our own arms
tested prompting, and prompting fails. The September brief listed fine-tuning
as rung 2 and called it closed because the Claude API exposes no weights.
That was an API constraint, not a hardware one: smaug carries two RTX 5090
GPUs, which is enough to train a LoRA on a 7B to 14B open model.

The corpus is fiction, and nobody has fine-tuned on a single blogger. The one
author who resisted imitation in that study had the smallest body of work and
the most idiosyncratic voice, which is the hard end. Blog register is the
central untested assumption.

The recipe that fits 288,000 words is inverse paraphrase. A frontier model
rewrites each of Alex's paragraphs into neutral prose, which models do well,
and a local model learns to map the neutral version back to his original,
which is the hard direction. Every training pair is his own text, so the
model learns his style without being taught any content he did not write.
STRAP (EMNLP 2020) introduced the idea. TinyStyler (arXiv:2406.15586, 800M
parameters) reconstructs text from paraphrases conditioned on an authorship
embedding and beats GPT-4 on authorship style transfer. Liu and Koehn
(arXiv:2602.15013) build the neutral side by round-trip translation and beat
few-shot prompting with parameter-efficient fine-tuning.

These systems work near the sentence. Whether a sentence-level restyler keeps
paragraph rhythm, meaning sentence-length variance and paragraph shape, is
open. The style-prompt experiment found variance is where a voice lives.

## 6. Instruments we can reuse

Calibrate every instrument on Alex's own posts before trusting a threshold. He
writes formal technical English as a non-native speaker, which is the
population detectors were least calibrated for (Liang et al. 2023 measured 61%
false positives on non-native essays; a 2026 revisit, arXiv:2602.05769, finds
modern classifiers much less biased, in Czech).

- **Style distance.** LUAR (Apache-2.0) and the Wegmann content-independent
  style embeddings score same-author confidence, and TinyStyler uses them as
  its yardstick. Burrows' delta, already a rift metric, is the explainable
  companion.
- **Syntactic tells.** `sam-paech/not-x-but-y-bench` (MIT) detects the
  corrective with spaCy part-of-speech patterns and has a human baseline of
  0.065 per 1,000 characters from 82 published books. `tbhb/vale-ai-tells`
  (MIT) computes sentence and paragraph length uniformity per section.
  Triplets, unmarked summary sentences and one point restated several ways
  have no packaged detector.
- **Phrase tells.** `slopcheck` already does this against Alex's corpus.
  `sam-paech/slop-forensics` (MIT) is the general pipeline. Published slop
  lists are calibrated on fiction (the top of EQ-Bench's list is fantasy
  names) and would flag Alex's vocabulary.
- **Detector probe.** The top open classifiers on the RAID leaderboard,
  `Oxidane/tmr-ai-text-detector` (MIT, AUROC 0.997) and
  `GeorgeDrayson/modernbert-ai-detection-raid-mage` (Apache-2.0, 0.991), run
  on a CPU. Pangram's API costs $0.05 per 100 words, has a free tier of 2,000
  words a day, and returns human, AI-assisted and AI-generated fractions per
  segment, which no open model does. Use detectors to probe drafts, never as
  a score to optimize: lowering a detector score pushes toward the
  surface-statistics games of section 2.
- **Watermarks.** Anthropic announced on 2026-08-14 that future Claude models
  will watermark text with a version of SynthID-Text, for the EU AI Act. Only
  the provider holds the key, the mark reads nothing about style, and it does
  not change how readers judge prose. Nothing to build around.

## What this changes

- The September instruments are all style-side. The cause readers and field
  guides point at, generic claims standing in for specifics, has no
  instrument here yet.
- The workflow question is measurable. Section 4 predicts that "Alex drafts,
  model polishes" lands closer to his voice than "Claude drafts, Alex edits".
  We have the corpus, the topic set from the arms experiment, and now a
  style-distance instrument to test it.
- Rung 2 of the September ladder is reachable on smaug. Fine-tuning is the
  only intervention in either brief with a strong positive human-reader
  result.
- Rule lists stay what September found them to be: useful for measuring and
  weak, sometimes harmful, as generation instructions.

## Open questions

- Is the corpus clean? Phase 0 noted that the later posts may be LLM-assisted.
  A restyler trained on them learns the habits we are trying to remove, so
  which posts count as Alex's own needs settling before any training.
- Does fine-tuning transfer from literary fiction to blog register?
- Does putting the whole 288,000-word corpus in a 1M-token context beat few-shot
  prompting? No published result exists either way.
- Does any of this work in Spanish? There is no Spanish voice-transfer
  literature and no clean Spanish corpus of Alex's writing.
- Does one noticed tell send a reader hunting for more? No controlled study
  exists.
