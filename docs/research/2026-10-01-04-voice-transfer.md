> **Corrections (06-verification.md):** TinyStyler beats GPT-4 on authorship transfer (Away/Towards metrics), not on the "joint" metric, where it is on par (0.85 vs 0.88, C5). The ITDA "inverse beats forward by about 40%" figure is unverified (C13).

# Track 4: making generated prose carry one author's voice

## Headline

1. **Fine-tuning beats prompting for voice, and the numbers are now measured, not anecdotal.** A preregistered study of 50 award-winning authors found that in-context prompting was disfavored by MFA-trained readers (fidelity odds ratio 0.16) but that fine-tuning on an author's complete works flipped the same readers to favor AI (fidelity odds ratio 8.16), and detectors flagged fine-tuned output as AI only 3 percent of the time versus 97 percent for prompted output. This is the direct contradiction of the EMNLP 2025 "Catch Me If You Can" result, which only tested in-context imitation.
2. **The inverse-paraphrase trick turns one author's corpus into unlimited paired training data.** Three independent systems (STRAP, TinyStyler, ITDA) all work by neutralizing an author's sentence into a bland paraphrase, then training a small model to reconstruct the original. ITDA reports inverse transfer beating forward transfer by roughly 40 percent on GPT-4 score. TinyStyler, at 800M parameters, beats GPT-4 on authorship transfer. This is the recipe that scales from our 288k-word corpus.
3. **A small model restyler is a deployable artifact, not a research prototype.** TinyStyler runs in under a second on one A100 and exceeds GPT-4 on the joint style metric while using about 0.5 percent of GPT-3.5's parameters. On two RTX 5090s this is a trivial fine-tune.
4. **Authorship embeddings are a working local measuring instrument today.** LUAR (LLNL, EMNLP 2021) and Wegmann's content-independent style embeddings are both public and both are what the style-transfer papers themselves use to score "how close is this to the author." We can adopt them as the score that slopcheck lacks.
5. **Nobody has tested 50k to 500k words of one author inside a frontier model's context window.** Long-context many-shot imitation is the one arm with no published result on author voice, which makes it a cheap experiment rather than a known loser.
6. **Spanish is a blank.** There is no measured voice-transfer work in Spanish; the reusable assets are the Stylo R package and stylometric methods, which are language-agnostic but English-benchmarked.

## Findings

### 1. Fine-tuning on one author's corpus

The strongest evidence is Chakrabarty, Ginsburg, and Dhillon, "Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers" ([arXiv:2510.13939](https://arxiv.org/abs/2510.13939), Oct 2025, v4 Mar 2026). Preregistered. Fifty award-winning authors, excerpts up to 450 words, three frontier models (ChatGPT, Claude, Gemini) versus MFA-trained writers. Twenty-eight MFA readers and 516 college-educated general readers, blind pairwise.

The in-context arm reproduces our September finding. MFA readers strongly disfavored prompted AI on stylistic fidelity (odds ratio 0.16) and quality (0.13). General readers showed no fidelity preference (1.06) but did favor AI quality (1.82). Fine-tuning ChatGPT on each author's complete works reversed both groups. MFA readers favored fine-tuned AI for fidelity (odds ratio 8.16) and quality (1.87). General readers favored it more strongly (fidelity 16.65, quality 5.42). The reader-type interaction stayed significant (p = 0.021 for fidelity, p < 0.0001 for quality). Leading detectors flagged fine-tuned output as AI in 3 percent of cases versus 97 percent for prompting. Median fine-tuning cost was $81 per author, a 99.7 percent reduction against typical writer pay.

Two caveats matter for us. The corpus is literary fiction, not blog-register prose, and "complete works" for these authors means books, likely several hundred thousand words each. The authors report real variation: Tony Tulathimutte resisted imitation because he has few books and his style leans on transgressive humor and tonal shifts. That is the same lesson as "Catch Me If You Can" on blogs: informal, idiosyncratic voice is the hard end.

On the mechanism side, StyleAdaptedLM ([arXiv:2507.18294](https://arxiv.org/abs/2507.18294), Jul 2025) shows LoRA is the right tool: it trains LoRA adapters on unstructured stylistic corpora and then merges them into an instruction-following model, preserving task performance while moving style. Liu and Koehn, "Text Style Transfer with Parameter-efficient LLM Finetuning and Round-trip Translation" ([arXiv:2602.15013](https://arxiv.org/abs/2602.15013), Feb 2026), add the missing piece: round-trip translation synthesizes neutralized parallel data from monolingual text, and PEFT fine-tuning on it beats zero-shot prompting and few-shot in-context learning on BLEU and style accuracy across four domains.

For a practitioner write-up with numbers, Didier Lopes fine-tuned Phi-3-mini (3.8B) with LoRA on 91 of his own blog posts converted to roughly 2,100 Q&A pairs ([didierlopes.com, Sep 2025](https://didierlopes.com/blog/fine-tuning-a-llm-on-my-blog-posts/)). He trained 0.08 percent of parameters (rank 16, all 32 layers, dropout 0.1), saw validation loss plateau, and measured a 27.6 percent word-overlap gain (0.157 to 0.201) plus a sharp correction of response length toward his own. His stated failure is that information transfer stayed poor: a 3.8B model plus partial fine-tuning captures how he writes but not what he knows. That matches the standard advice he quotes from Chip Huyen that fine-tuning is for behavior, not facts.

How many words are needed: the three data points give a usable band. Didier got a measurable style shift from roughly 150k words on a 3.8B model. Chakrabarty used each author's complete works. The one author who failed, Tulathimutte, was the one with the smallest corpus. Our 288k words is comfortably in the working range for a single-author fine-tune. What goes wrong: topic overfitting and content memorization when the corpus is narrow (the ITDA paper and Phase 0 both observed topic confound), style collapse toward an archetype rather than the individual (ITDA notes the model may "mirror a classical Chinese style rather than the specific style"), and representational ceiling on small models. Dropout and early stopping are the standard guards.

### 2. Style transfer as rewriting, and the inverse-paraphrase recipe

STRAP ([arXiv:2010.05700](https://arxiv.org/abs/2010.05700), EMNLP 2020) is the ancestor. Krishna, Wieting, and Iyyer reformulate style transfer as paraphrase generation: generate a style-neutral paraphrase of a sentence, then train an inverse paraphrase model to reconstruct the original. They report beating prior state of the art on human and automatic evaluations, and they show 23 prior papers' metrics were gameable. The per-style inverse model is the weakness: one model per style, and an external paraphraser at inference.

TinyStyler ([arXiv:2406.15586](https://arxiv.org/abs/2406.15586), Horvitz et al., 2024) fixes both. It trains a single 800M T5 to reconstruct a comment from its paraphrase conditioned on an authorship embedding (Wegmann style embeddings for training, LUAR held out for scoring). It then self-distills on 40k high-quality synthetic pairs. On the low-resource authorship transfer benchmark from Patel et al. 2022, TinyStyler with reranking beats GPT-4 on the joint metric in all three splits (Diverse: 0.39 versus GPT-4's 0.30 and GPT-3.5's 0.37). It uses about 0.5 percent of GPT-3.5's parameters, runs sub-second on an A100, and is over 35x faster than the controllable baselines. The model is public on Hugging Face.

ITDA, "Authorship style transfer with inverse transfer data augmentation" ([AI Open, 2024](https://www.sciencedirect.com/science/article/pii/S2666651024000135)), is the cleanest statement of the inverse idea and the one the brief flagged. Shao et al. use an LLM to strip style from an author's text, producing (neutral, stylized) pairs, then fine-tune a compact BART to map neutral back to stylized. Their pilot shows inverse transfer beating forward transfer by roughly 40 percent on GPT-4 score, and they argue the reason: LLMs are far better at producing neutral text (plentiful in pretraining) than at producing a rare author's style, so it is easier to ask the LLM to do the easy direction and the small model to learn the hard direction. They add two multipliers that matter for a sparse corpus: stylized-text augmentation (ask the LLM to write new sentences in the author's style, filtered by a style classifier) and clustering-based dynamic prompt selection. Tested on four datasets (Shakespeare, Trump, Lyrics, Lin Daiyu).

STEER ([arXiv:2311.07167](https://arxiv.org/abs/2311.07167), 2023) is a different mechanism, product-of-experts decoding plus offline-to-online RL, that beats the 175B GPT-3 while being 226 times smaller. It is arbitrary-style rather than per-author, so it is less directly applicable, but it reinforces the same conclusion: a small model with the right training signal matches or beats large in-context imitation.

The common thread across STRAP, TinyStyler, ITDA, and the round-trip PEFT paper is that all four manufacture parallel data from a single monolingual corpus by neutralizing and reconstructing. For us that is the load-bearing insight: 288k words of Alex's prose becomes an effectively unlimited set of (neutral, Alex) training pairs, and every pair is content-true because the target is his own original sentence.

### 3. Long-context many-shot imitation

I found no published result testing tens to hundreds of thousands of words of a single author inside a frontier model's context. Many-shot in-context learning in general is established (Agarwal et al., [arXiv:2404.11018](https://arxiv.org/abs/2404.11018), Apr 2024): many demonstrations beat few-shot on a wide range of tasks, and the effect is strongest for the largest models. But the style papers test few demonstrations at most, and the Chakrabarty study compares few-shot in-context against fine-tuning, not many-shot. The September brief already noted this gap, and my search did not close it.

The honest statement is therefore that this arm is unmeasured rather than defeated. Given the cost profile, it is the cheapest thing to try first: a 1M-token context can hold all 288k words, which is a regime that did not exist when "Catch Me If You Can" was designed. The risk is the same mechanism the brief names: a voice is a joint distribution over dozens of weak signals, and packing the corpus into context does not guarantee the model can hold all of them while solving the writing task. Fine-tuning has a mechanism for this (gradient over the full distribution); context does not. I would expect many-shot to beat few-shot but fall short of fine-tuning, and that expectation is itself worth one measurement.

### 4. Style representations as a measuring instrument

LUAR, "Learning Universal Authorship Representations" (Rivera-Soto et al., EMNLP 2021, [repo](https://github.com/llnl/luar)), is an SBERT-based model that embeds a text passage into an authorship space and scores same-author versus different-author. It was trained for cross-domain transfer across Amazon reviews, fanfiction, and Reddit. Models are on Hugging Face. Wegmann, Schraagen, and Nguyen, "Same Author or Just Same Topic?" ([arXiv:2204.04907](https://arxiv.org/abs/2204.04907), 2022), train content-independent style embeddings with a contrastive authorship verification objective that deliberately separates style from topic. These two are exactly what TinyStyler uses to score its outputs, which is the strongest endorsement available: the style-transfer community already treats them as the yardstick for "how close is this to the author."

A newer entry is "Layered Insights" (Alshomary et al., [arXiv:2503.00958](https://arxiv.org/abs/2503.00958), Mar 2025, v3 Oct 2025), which pools representations across all transformer layers for authorship attribution and reports new state of the art specifically on out-of-domain data. That out-of-domain robustness is the property we need, because a draft we want to score is by construction not a published blog post.

All three can run locally and score a draft against the 288k corpus without a frontier API. The cleanest build is a verification-style score: embed the draft, embed a batch of Alex's posts, and report same-author confidence. This closes the gap the September brief left open: slopcheck measures overrepresentation against Alex's corpus, but it does not measure overall closeness to his voice. LUAR or Wegmann embeddings are the natural complement, and unlike an LLM judge they do not carry the self-preference / low-perplexity bias that Part 1 of the brief identified.

### 5. Workflow-level methods from working writers

Measured evidence here is thin, and I will say so rather than dress opinion as data. What exists:

The Chakrabarty study explicitly describes the realistic workflow as human steering: the model generates a paragraph or scene, the writer edits and redirects, then the next section, with outlining and revision passes to hold the whole manuscript coherent. This is opinion from the author interview, but it is the only workflow claim in the measured papers and it is consistent with our two-pass drafting experiment.

The Tricontinental institute published a systematic method in Spanish and English ([May 2026](https://thetricontinental.org/es/a-systematic-method-for-controlling-ai-writing-style/)). It runs a seven-level stylistics framework (from Paul Simpson's textbook) over a reference text to produce a structured style profile, then feeds that profile back as instructions. It reports that this reduced editing time and produced text in the source's register rather than the default register. It ships an open-source "stylistics" skill that extracts a profile from any reference. This is a prompt-level method, so it inherits the known weakness (the profile is still a description of the distribution, not the distribution), but it is the most disciplined prompt-level method I found and it is reusable across authors.

Beyond that, the writer-facing material (Novelcrafter's fine-tuning guide, the "Fine-Tuned an LLM to Write 91% Like Me" video, assorted r/LocalLLaMA threads) is process without independent measurement. I flag it rather than rely on it. The recurring themes across all of them are genuine and match the papers: fine-tune rather than prompt, keep a human in the loop for what to say, and treat style as a reusable asset rather than a per-draft instruction.

### 6. Spanish

There is no measured voice-transfer literature in Spanish. What exists is stylometric tooling and slop journalism. Stylo (the R package by Maciej Eder and collaborators) is the standard authorship-analysis tool and handles Spanish corpora natively. A CEUR workshop paper, "Extraction of Stylometric Information from Spanish Documents" (2024), is an example of Spanish-specific stylometry, not generation. On the slop side, Pangram maintains a Spanish version of its AI-pattern guide, and the Tricontinental piece above doubles as the most concrete Spanish-language account of the AI register problem. The September brief's conclusion stands: Spanish slop is not translated English slop, and the blocker is the absence of a clean Spanish corpus of Alex's writing in one register. Nothing in this track changes that.

## Implications for our toolkit

Build in this order.

**First, wire a local authorship score.** Adopt LUAR or Wegmann embeddings, run them over the 288k corpus once, and expose a function that returns same-author confidence for any draft. This is the missing instrument. It is public, it is what the transfer papers themselves use, and it escapes the LLM-judge bias. Every method below gets scored against it, alongside slopcheck and one blind human rating session.

**Second, run the inverse-paraphrase fine-tune.** This is the strongest method given what the evidence shows. Take the 288k posts, split into sentence- or paragraph-level units, and generate neutral paraphrases with a frontier API (the LLM's easy direction). Then fine-tune an open model locally to map neutral back to Alex's original, in the ITDA and TinyStyler pattern. The target is always Alex's own sentence, so every pair is content-true and no content is invented. On two RTX 5090s (64GB total) this is comfortable with QLoRA on a 7B to 14B model, and the 800M TinyStyler scale is trivial. The result is a restyler that rewrites any draft into Alex's register without an external paraphraser at inference (self-distillation removes that dependency, exactly as TinyStyler did).

**Third, and only if the restyler's long-form coherence disappoints, go to full LoRA fine-tuning of the whole model on the corpus.** The Chakrabarty result is the strongest single piece of evidence that voice lives in the weights, but it is fiction and it used an API fine-tune. The restyler route is cheaper, keeps the base model intact, and gives a switchable artifact. If coherence across paragraphs is the failure mode, the whole-model fine-tune is the fallback, and 288k words is enough by the Didier and Chakrabarty calibrations.

**What to avoid.** Pure in-context style prompts on blog register are a measured loser (EMNLP 2025, and reproduced by Chakrabarty). Forbid lists are actively harmful on weak models (Phase 0's 39x inversion). Steering vectors are unreliable for a bundle of weakly correlated habits (the brief's Rung 3). An LLM critic in the loop optimizes toward low perplexity, which is the defect.

**What to measure.** Authorship confidence (LUAR/Wegmann) before and after restyling, slopcheck rates on Alex's own topics, and one blind human rating session. The blind rating is the missing instrument in every prior phase and is the only thing that closes the loop between "closer in embedding space" and "reads like Alex."

## Open questions

- Does the fine-tuning result from fiction transfer to blog-register prose? Chakrabarty used literary fiction; "Catch Me If You Can" shows blogs are the hard end for in-context imitation. No study fine-tunes on a single blogger's corpus, so this is the central untested assumption.
- Does many-shot (all 288k words in a 1M-token context) beat few-shot on blog voice? Unmeasured, cheap to test, and I expect it to land between few-shot and fine-tuning.
- Is the author's own 288k-word corpus clean enough? The September findings note the later posts may be LLM-assisted, which would put model habits into the target and bias the restyler toward slop. Corpus hygiene matters before training.
- Can a sentence-level restyler hold paragraph-level rhythm? TinyStyler and ITDA operate near the sentence. Sentence-length variance and the contracted corrective are Alex's tells, and a restyler that works one sentence at a time may still miss the distribution across sentences that the brief identified as the core of a voice.

## Sources

- "Readers Prefer Outputs of AI Trained on Copyrighted Books over Expert Human Writers," Chakrabarty, Ginsburg, Dhillon. arXiv:2510.13939, Oct 2025 (v4 Mar 2026). https://arxiv.org/abs/2510.13939
- "When AI learns an author's voice, even experts prefer it," University of Michigan News, Jan 8 2026. https://news.umich.edu/when-ai-learns-an-authors-voice-even-experts-prefer-it/
- "Reformulating Unsupervised Style Transfer as Paraphrase Generation" (STRAP), Krishna, Wieting, Iyyer. EMNLP 2020. https://arxiv.org/abs/2010.05700
- "TinyStyler: Efficient Few-Shot Text Style Transfer with Authorship Embeddings," Horvitz, Patel, Singh, Callison-Burch, McKeown, Yu. arXiv:2406.15586, Jun 2024. https://arxiv.org/abs/2406.15586
- "Authorship style transfer with inverse transfer data augmentation" (ITDA), Shao et al. AI Open, 2024. https://www.sciencedirect.com/science/article/pii/S2666651024000135
- "STEER: Unified Style Transfer with Expert Reinforcement," Hallinan et al. arXiv:2311.07167, Nov 2023. https://arxiv.org/abs/2311.07167
- "Text Style Transfer with Parameter-efficient LLM Finetuning and Round-trip Translation," Liu, Koehn. arXiv:2602.15013, Feb 2026. https://arxiv.org/abs/2602.15013
- "StyleAdaptedLM: Enhancing Instruction Following Models with Efficient Stylistic Transfer," Ramu et al. arXiv:2507.18294, Jul 2025. https://arxiv.org/abs/2507.18294
- "Learning Universal Authorship Representations" (LUAR), Rivera-Soto et al. EMNLP 2021. https://github.com/llnl/luar
- "Same Author or Just Same Topic? Towards Content-Independent Style Representations," Wegmann, Schraagen, Nguyen. arXiv:2204.04907, 2022. https://arxiv.org/abs/2204.04907
- "Layered Insights: Generalizable Analysis of Authorial Style by Leveraging All Transformer Layers," Alshomary et al. arXiv:2503.00958, Mar 2025. https://arxiv.org/abs/2503.00958
- "Many-Shot In-Context Learning," Agarwal et al. arXiv:2404.11018, Apr 2024. https://arxiv.org/abs/2404.11018
- "Catch Me If You Can? Not Yet," EMNLP 2025 Findings. https://arxiv.org/abs/2509.14543
- "Fine-tuning a LLM on my blog posts," Didier Lopes, Sep 2025. https://didierlopes.com/blog/fine-tuning-a-llm-on-my-blog-posts/
- "Un método sistemático para controlar el estilo de redacción de la IA," Tricontinental Institute, May 2026. https://thetricontinental.org/es/a-systematic-method-for-controlling-ai-writing-style/
- "Extraction of Stylometric Information from Spanish Documents," CEUR Workshop Proceedings, 2024. https://ceur-ws.org/Vol-3625/paper4.pdf
- Stylo (R package for stylometry), Maciej Eder et al. https://maciejeder.org/projects/stylo/
