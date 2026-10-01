# Track 5: Reusable building blocks and the AI-tell catalogues

Date: 2026-10-01. Scope: open-source code we could reuse for a writing
toolkit, the phrase and pattern catalogues that exist as data, and the
syntactic and discourse-level tells that a phrase list cannot catch.

## Headline

1. The strongest reusable assets are not detectors. They are three pieces of
   measurement infrastructure built by Sam Paech: `not-x-but-y-bench` (a
   spaCy POS plus regex detector for the "not X but Y" construction with a
   measured human baseline of 0.065 per 1,000 characters), `slop-score` (a
   browser analyzer with a 1,648-word slop list and a 25 percent
   not-x-but-y component), and `slop-forensics` (a pipeline that profiles
   over-represented n-grams and builds slop lists from scratch). All three are
   MIT licensed and cover exactly the register our own Phase 0 found is the
   signal: the contracted corrective.

2. The published slop word lists are calibrated on fiction and essays, not on
   blog or technical register. The EQ-Bench list's top entries are fantasy
   names like "aetheria" and "aelara". Using them as-is would repeat the
   Phase 0 mistake of flagging Alex's own vocabulary. They are useful as a
   seed and a format, not as the target.

3. Structural tells (uniform sentence and paragraph length, repeated sentence
   openers) already have a reusable implementation, in the `vale-ai-tells`
   experimental package. It computes coefficient of variation per section with
   published thresholds. The tells it explicitly cannot catch are elegant
   variation, argument restatement, appositive definitions, and awkward
   analogy. Those four require a parser or embeddings, and nobody has shipped
   a packaged detector for them.

4. Style distance and detector score both have strong reusable code (LUAR,
   Burrows' Delta, Binoculars, Fast-DetectGPT) but both need to be pointed at
   Alex's corpus to be useful. None of them measures "is this in Alex's
   voice" out of the box. That calibration is ours to build.

5. The most-cited phrase catalogue with model-specific tells, Wikipedia's
   "Signs of AI writing", is a hand-written editorial field guide, not a
   measured baseline. Its value is breadth and provenance (it links to the
   measured studies), not the numbers. The one measured model-specific source
   I found is a July 2026 Substack study over 300,000 words.

## Findings

### 1. Inventory of reusable code

Read from each repository's README and GitHub metadata. License, last commit
date, language, and what it does.

| project | lang | license | last commit | what it does |
|---|---|---|---|---|
| sam-paech/antislop-sampler | Python | Apache-2.0 | 2026-03-05 | backtracking sampler; phrase + regex bans at decode time; OpenAI-compatible API |
| sam-paech/slop-forensics | Python/NB | MIT | 2025-11-01 | generate outputs, profile over-represented n-grams, build slop lists, phylogeny |
| sam-paech/slop-score | JS/HTML | MIT + wordfreq (Apache/CC-BY-SA) | 2025-11-22 | in-browser slop analyzer; word/trigram/not-x-but-y score; leaderboard scripts |
| sam-paech/not-x-but-y-bench | Python | MIT | 2025-11-16 | spaCy POS + regex detector for "not X but Y"; measured human baseline |
| sam-paech/auto-antislop | Python | no license | 2026-07-29 | FTPO fine-tuning pipeline that removes slop from a model |
| ahans30/Binoculars | Python | BSD-3-Clause | 2024-05-14 | zero-shot detector; perplexity ratio between two models |
| baoguangsheng/fast-detect-gpt | Python | MIT | 2026-02-07 | detector via conditional probability curvature |
| llnl/LUAR | Python | Apache-2.0 | 2024-08-12 | universal authorship representations (style embeddings) |
| vale-cli/vale | Go | MIT | 2026-09-28 | extensible prose linter engine; hosts vale-ai-tells |
| tbhb/vale-ai-tells | YAML/Shell | MIT | 2026-09-29 | ~100 Vale rules for AI tells plus experimental structural rules |
| amperser/proselint | Python | BSD-3-Clause | 2026-09-04 | prose linter: clichés, hedging, weasel words, redundancy, jargon |
| btford/write-good | JS | MIT | 2025-03-10 | naive linter: passive voice, weasel words, "very", adverbs, repeated words |
| get-alex/alex | JS | MIT | 2024-11-27 | flags insensitive/inconsiderate writing, not AI tells |
| textstat/textstat | Python | MIT | 2026-02-18 | readability scores: Flesch, FK grade, Gunning Fog, SMOG, ARI, Coleman-Liau, LIX, Dale-Chall |
| fastdatascience/faststylometry | Python/NB | MIT | 2025-07-21 | Burrows' Delta authorship distance |
| computationalstylistics/stylo | R | no LICENSE file | 2026-06-19 | R stylometry suite (stylo, opposition, rolling classify) |
| evllabs/JGAAP | Java | no LICENSE file | 2026-03-18 | GUI authorship attribution, hundreds of features |

Notes on each that matter for a toolkit decision.

**antislop-sampler** needs logit access, so it only runs on local or
open-weight models. Its regex-bans mode is what catches "not X but Y", and
its README says regex bans disable streaming because the sampler may have to
backtrack an unpredictable distance. The bundled slop list is
`slop_phrase_prob_adjustments_full_list.json`, 50,046 entries, which the
README calls "mostly auto-generated ... not well optimised or curated". A
curated subset (`slop_phrases_2025-04-07.json`, 2,500 entries) and a word
list (`slop_words_2025-04-07.json`, 2,000 entries) are separate. There is also
`slop_regexes.txt` with three patterns: "not [^.!?]{3,60} but", "each ... a",
"every ... a". The sampler was merged into koboldcpp v1.76 and works through
Open WebUI.

**slop-forensics** is the most reusable single piece. It is the pipeline that
turns "generate a model's output" into "here is the canonical list of what
this model overuses", with word, bigram, and trigram counts, a repetition
score, and a phylogenetic clustering step (PHYLIP parsimony) that groups
models by slop profile. This is the exact corpus-driven method our own brief
recommends for Spanish, and it already exists with a permissive license.

**slop-score** is a browser analyzer, not a library, but its data directory
is the cleanest published phrase list: `slop_list.json` (1,648 words),
`slop_list_bigrams.json` (200), `slop_list_trigrams.json` (430), and
`human_writing_profile.json` (frequency counts of n-grams in a human-authored
corpus). The composite score is weighted 60 percent slop words, 25 percent
not-x-but-y, 15 percent slop trigrams. The not-x-but-y detector is a two-stage
regex pipeline over a wink-pos-tagger stream. The list is generated from 150
creative-writing and 150 essay outputs per model, matched against a human
baseline, which means it is measured, but measured on fiction and essay
register. The top of the word list is fantasy names ("aetheria", "aelara",
"aeldrin"), a clear signal that this list would misfire on a technical blog.

**not-x-but-y-bench** is the smallest and most on-target repository. It runs a
model over 300 creative-writing prompts and scores the rate of the corrective
construction per 1,000 characters, using 10 surface regexes plus 35 POS-tagged
regexes over spaCy (`en_core_web_sm`). Its human baseline is 0.065 per 1,000
characters, computed from 82 published books (about 53 million characters).
This is the only packaged detector I found that measures a syntactic tell
against a human baseline with a real number. It is effectively the
syntactic-template detector that item 3 of my brief asked whether anyone had
built, specialized to one construction.

**auto-antislop** is the FTPO trainer from the Antislop paper
(arXiv:2510.15061). It has no license file, which blocks reuse in anything
serious, and it requires a GPU and vLLM. It is the "rewrite at the weights"
option and out of reach for an API-only workflow, but the README documents
early-stopping thresholds and LoRA ranks that are otherwise hard-won
parameters.

**Binoculars** (ICML 2024) and **Fast-DetectGPT** (ICLR 2024) are the two
strongest zero-shot detector scores with code. Binoculars computes a
perplexity ratio between an observer and a performer model (default Falcon-7B
and Falcon-7B-instruct) and ships a fixed global threshold; its README warns
it is English-oriented and academic. Fast-DetectGPT samples and scores with
two models to estimate probability curvature, with a 340x speedup over
DetectGPT and, in a January 2026 update, a note that Llama-3-8B scoring models
beat Falcon-7B especially on reasoning-model output. Both measure
"AI-generated or not", not "reads like Alex", so they are calibration targets
rather than direct components.

**LUAR** (EMNLP 2021) is the canonical style-embedding package: a sentence
transformer (paraphrase-MiniLM-L6-v2) fine-tuned to produce an embedding per
author such that same-author texts are near each other and different-author
texts are far. It was built for authorship attribution and verification, not
for AI detection, which is exactly the right instrument for measuring distance
from Alex's voice. Weights are on Hugging Face. It has not been updated since
August 2024 but the method is stable.

**Prose linters.** Vale is the engine worth reusing: it is markup-aware, fast,
extensible, and the `vale-ai-tells` package already targets AI tells
specifically (more in section 2). proselint and write-good are classic prose
linters whose checks (hedging, weasel words, passive voice, repeated words,
lexical illusions) overlap heavily with slop detection but were not designed
for it. alex is about insensitive language, not AI tells; it belongs in a
different pipeline. textstat gives readability scores in one call. Burrows'
Delta (faststylometry) is the classic style-distance number and pairs with
LUAR as a cheap, explainable alternative to an embedding. stylo and JGAAP
both have no LICENSE file, which is a concrete reason to prefer the Python
MIT options.

No dedicated "spaCy syntactic feature extractor" package surfaced. The
reusable substrate is spaCy's `en_core_web_sm` (used directly by
not-x-but-y-bench), and the Shaib et al. template extractor (section 3) uses a
dependency parser rather than shipping as a library.

### 2. AI-tell phrase and pattern catalogues as data

I separated these by whether they are measured against a human baseline or
hand-written.

Measured against a human baseline:

- **EQ-Bench slop lists** (`slop_list.json` and the bigram/trigram siblings)
  are computed as over-representation of words and trigrams in model output
  versus a human-authored corpus. The README states this directly. They are
  measured, but on fiction plus essay register, so the vocabulary is the
  wrong population for a technical blog. Date: repo last touched 2025-11-22.

- **antislop banned lists** are auto-generated by the same over-representation
  method against a "large LLM-generated story dataset". The author's own
  disclaimer says they are "not well optimised or curated". Measured but
  noisy. 50,046 full-list entries, or the 2,500-phrase curated subset.

- **not-x-but-y-bench human baseline**, 0.065 per 1,000 characters from 82
  published books, is the cleanest single measured number in this whole
  survey. It is the one place a syntactic tell is put on a human scale.

- **The July 2026 Substack study** ("I prompted ChatGPT, Claude, and Gemini to
  generate over 300,000 words", Karen Spinner, wonderingaboutai) is the only
  measured model-specific tell source I found. It ran Claude Opus 4.8, Gemini
  3.5 Flash, and GPT-5.2 through fifteen prompts (opinion essays, workplace
  messages, fiction), ten runs each, 450 samples and about 310,000 words, and
  measured 44 quantitative metrics per sample plus word choices compared
  across models with no seed list. Findings: Claude is cautious and reluctant
  to stake a claim; Gemini is formal with a taste for extreme adjectives; and
  ChatGPT uses negative parallelism more than the other two and narrates
  fiction through somatic cues. The author also ran a prior study over 16,000
  Substack articles to establish that "it's not this, it's that" is
  pervasive. Directional, self-reported, but it is real measurement with a
  disclosed method.

Hand-written (human-curated, not corpus-measured):

- **Wikipedia:Signs of AI writing** is the widest catalogue. It is an advice
  page from WikiProject AI Cleanup, explicitly descriptive not prescriptive.
  Its phrase lists (words to watch) are hand-compiled by editors, but it cites
  the measured literature underneath: Russell 2025 (heavy LLM users detect AI
  about 90 percent of the time), Kriss 2025, an Economist study of July 2026,
  and Reinhart et al. PNAS 2025. Its value is coverage and its "Historical
  indicators" section, which lists tells that have gone stale (didactic
  disclaimers, "In conclusion" summaries, prompt refusal, elegant variation
  from the repetition-penalty era). That section is the closest thing I found
  to a record of which tells are version-dependent.

- **vale-ai-tells** (tbhb/vale-ai-tells) is a Vale package of about 100 rules
  targeting AI tells, plus a commit-message style and an experimental
  structural style. It is explicitly for technical documentation. The README
  states each rule was human-validated against test documents containing
  known patterns, so it is hand-written and spot-checked rather than
  corpus-measured. Rule names read like a taxonomy: ContrastiveNegation,
  CoordinatedReveal, ConclusionMarkers, DefensiveHedges, EmDashUsage, and a
  long Figurative* family (FigurativeCarries, FigurativeSurfaces, and so on)
  that targets inanimate subjects given human verbs, which is our own
  rule 26 territory.

Model-specific tells as a category:

- Wikipedia's "Differences between LLMs" section asserts each model has an
  idiolect and gives one contrast (ChatGPT and Grok emphasize broader context
  more than Gemini and Claude; Gemini and Claude are more concise).
- The "Y rather than X" reversed corrective is flagged as particularly common
  in Grok output, also present in ChatGPT and Claude.
- The July 2026 Economist study (cited from Wikipedia, dated July 2026) found
  that among contemporary models only Claude used em dashes more than
  professional writers, while ChatGPT used them less after GPT-5.1 began
  suppressing them. This is the kind of model-specific, time-stamped tell we
  should expect to keep moving.

Bottom line for our toolkit: the measured lists are all English and all
calibrated to fiction or essay register. The hand-written lists have better
breadth and structure but no numbers behind their entries. Nothing exists for
blog or technical register, and nothing exists for Spanish. Our Phase 0
finding, that generic lists flag Alex's own words, is predicted by this: the
lists measure "over-represented in fiction-writing models", not "foreign to a
specific human author".

### 3. Syntactic and discourse tells, and who has built detectors

The reference paper is **Shaib, Elazar, Li, and Wallace, "Detection and
Measurement of Syntactic Templates in Generated Text"**, EMNLP 2024,
arXiv:2407.00211 (CC-BY 4.0). The method defines a syntactic template as a
recurring dependency-parse structure, and shows models produce templated text
at a higher rate than human references; 76 percent of model templates are
traceable to pre-training data versus 35 percent of human templates, and RLHF
does not overwrite them. Templates also differentiate models, tasks, and
domains. There is a project page (cshaib.github.io/syntactic_templates) but
no packaged library, so it is a method to reimplement, not a dependency.

The honest answer to "has anyone built a detector for these with a parser or a
small model" is: for one construction, yes, and for the rest, partially, and
for four of them, no.

Built and reusable:

- The "not X but Y" corrective has two working detectors: `not-x-but-y-bench`
  (spaCy POS plus 45 regexes, with a human baseline) and the embedded detector
  in `slop-score` (wink-pos-tagger plus the same regex family). This is our
  strongest tell (Phase 0 measured 22 to 52 times Alex's rate) and it already
  has an instrument.

- Uniform sentence length, uniform paragraph length, and repeated sentence
  openers are implemented in `vale-ai-tells-experimental` as Tengo scripts
  that compute coefficient of variation per markdown section. Sentence CV
  below 0.30 and paragraph CV below 0.25 fire; the README cites human prose
  at CV above 0.40 and AI text clustering at 0.15 to 0.25. These catch three
  of the tells in my brief (uniform paragraph length, topic-sentence-first
  monotony, signposting via repeated openers) with no parser and no model.

Not built, by the same package's own admission (its "Future work" section):

- **Elegant variation** (synonym cycling instead of reusing a name) needs
  coreference resolution.
- **One-point dilution** (one argument restated many ways) needs sentence
  embeddings to detect semantic repetition.
- **Unnecessary inline definitions** (appositive "X, a definition, does Y")
  needs syntactic parsing to find the appositive.
- **Awkward analogies** need semantic judgment.

The triplet (rule of three) is named by Wikipedia as a tell (WP:RO3) and is
trivially detectable with a POS tagger, but I found no packaged detector for
it specifically. Paragraph-final summary sentences are covered as a historical
indicator ("In summary / In conclusion / Overall") by Wikipedia and by a
vale-ai-tells ConclusionMarkers rule, but those catch the lexical marker, not
the unmarked restatement. Topic-sentence-first structure is approximated by
sentence-opener repetition but not directly measured. No 2025 or 2026
follow-up paper or package generalizes Shaib's parser-based template extractor
into a usable detector; the field's energy went into detector scores
(Binoculars, Fast-DetectGPT) and into Paech's regex-plus-POS approach, not
into general syntactic-template detection.

The practical reading: phrase lists catch the corrective and the vocabulary;
coefficient-of-variation scripts catch the uniformity tells; and the remaining
discourse tells (triplets, unmarked summaries, topic-sentence-first, elegant
variation, restatement) require either a dependency parser or embeddings, and
that is ours to build.

## Implications for our toolkit

Reuse the Paech infrastructure wholesale for phrase-level and corrective
measurement. `slop-forensics` is the pipeline to clone and point at Alex's
corpus and at a model corpus generated on his topics, which is the exact
method Phase 0 converged on. `not-x-but-y-bench` and the `slop-score` data
give us a format, a baseline, and a detector for our strongest tell.

Do not import the published word lists as targets. They are fiction-calibrated
and would re-flag Alex's vocabulary. Import them as seeds to be re-ranked by
over-representation against Alex's corpus plus a general English baseline,
which `slopcheck` already does.

Adopt `vale-ai-tells-experimental` for the uniformity tells today. Sentence
CV, paragraph CV, and sentence-opener repetition are implemented, licensed
MIT, and catch the structural monotony a word list cannot. This closes part of
the gap between what our rules catch and what readers notice.

Build the parser and embedding layer, not the phrase layer. The four
uncaught tells (elegant variation, restatement, appositives, analogy) and the
triplet need spaCy dependency parses and sentence embeddings. That is the
differentiating work, and no packaged tool does it.

For style distance, reuse LUAR and Burrows' Delta, but the target corpus is
Alex's, which no package has. For detector score, Binoculars and
Fast-DetectGPT are usable external instruments, but they measure AI-ness, not
Alex-likeness; treat them as calibration targets, not as the objective.

Avoid antislop-sampler and auto-antislop for now. The sampler needs logit
access the Claude API does not expose; auto-antislop has no license and needs
a GPU. Both become relevant only if we move to a local model, at which point
the sampler's regex-bans and FTPO are the strongest rewrite options published.

## Open questions

I could not confirm a license for `stylo` and `JGAAP` (no LICENSE file via the
GitHub API); both may be GPL in reality and need checking before any reuse.

I did not find a measured model-specific tell list that separates Claude,
GPT, Gemini, and DeepSeek in blog register. The Substack study covers three
models in three genres and is self-reported. DeepSeek tells in particular are
under-documented beyond the Wikipedia note on its markup artifacts
(lenticular brackets, dagger symbols).

I could not settle whether Shaib's template extractor has a runnable
release; the project page exists but no pip package or maintained repo
surfaced, so reimplementation cost is unknown.

Nothing here transfers to Spanish. Every list, baseline, and detector is
English, which matches the brief's conclusion that the Spanish gap is the
available contribution rather than a gap to be filled by translating lists.

## Sources

- sam-paech/antislop-sampler, https://github.com/sam-paech/antislop-sampler (README, 2026-03-05)
- sam-paech/slop-forensics, https://github.com/sam-paech/slop-forensics (README, 2025-11-01)
- sam-paech/slop-score, https://github.com/sam-paech/slop-score (README, 2025-11-22)
- sam-paech/not-x-but-y-bench, https://github.com/sam-paech/not-x-but-y-bench (README, 2025-11-16)
- sam-paech/auto-antislop, https://github.com/sam-paech/auto-antislop (README, 2026-07-29)
- ahans30/Binoculars, https://github.com/ahans30/Binoculars (README, 2024-05-14); paper arXiv:2401.12070
- baoguangsheng/fast-detect-gpt, https://github.com/baoguangsheng/fast-detect-gpt (README, 2026-02-07); paper arXiv:2310.05130
- llnl/LUAR, https://github.com/llnl/LUAR (README, 2024-08-12); paper aclanthology.org/2021.emnlp-main.70
- tbhb/vale-ai-tells, https://github.com/tbhb/vale-ai-tells (README and EXPERIMENTAL.md, 2026-09-29)
- vale-cli/vale, https://github.com/vale-cli/vale (2026-09-28)
- amperser/proselint, https://github.com/amperser/proselint (2026-09-04)
- btford/write-good, https://github.com/btford/write-good (2025-03-10)
- get-alex/alex, https://github.com/get-alex/alex (2024-11-27)
- textstat/textstat, https://github.com/textstat/textstat (2026-02-18)
- fastdatascience/faststylometry, https://github.com/fastdatascience/faststylometry (2025-07-21)
- computationalstylistics/stylo, https://github.com/computationalstylistics/stylo (2026-06-19)
- evllabs/JGAAP, https://github.com/evllabs/JGAAP (2026-03-18)
- Shaib et al., "Detection and Measurement of Syntactic Templates in Generated Text", EMNLP 2024, arXiv:2407.00211
- Wikipedia:Signs of AI writing, https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing (accessed 2026-10-01)
- Karen Spinner, "I prompted ChatGPT, Claude, and Gemini to generate over 300,000 words", https://wonderingaboutai.substack.com/p/i-prompted-chatgpt-claude-and-gemini (2026-07-02)

## Build-versus-reuse table

| capability | best existing component | build or reuse | one-line reason |
|---|---|---|---|
| phrase-level tells | EQ-Bench slop lists + vale-ai-tells rules as seeds | reuse the format, build the target | published lists are fiction-calibrated and would flag Alex's own words, so re-rank them against his corpus |
| syntactic templates (not-X-but-Y, corrective) | sam-paech/not-x-but-y-bench, slop-score detector | reuse | MIT, spaCy plus regex, human baseline of 0.065/1k already measured |
| distribution metrics (sentence/paragraph length, lexical diversity) | vale-ai-tells-experimental, textstat, MATTR in slop-score | reuse | CV thresholds are published and these are our uniformity tells |
| style distance | LUAR embeddings + faststylometry Burrows' Delta | reuse the code, build the target | the instrument exists; the target corpus is Alex's and no package has it |
| detector score (AI-ness) | Binoculars, Fast-DetectGPT | reuse as external instrument, do not build | mature zero-shot detectors, but they measure AI-ness not Alex-likeness |
| rewrite (unslopping) | antislop-sampler (regex bans) / auto-antislop FTPO | build for now | sampler needs logit access and auto-antislop has no license and needs a GPU; both wait on a local model |
| triplet, unmarked summaries, appositives, elegant variation | none found | build | need a dependency parser or embeddings, and no packaged detector exists |
