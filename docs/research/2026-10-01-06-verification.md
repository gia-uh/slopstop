# Verification of research-track claims

Fact-check of 13 claims against primary sources. All arXiv and vendor pages were fetched directly. PubMed was blocked by reCAPTCHA and skipped; the APA PsycNet record was used instead for C4.

| # | Verdict | Claim (short) |
|---|---------|---------------|
| C1 | VERIFIED | arXiv:2510.13939 — fidelity OR 0.16 (prompted) vs 8.16 (fine-tuned), quality 1.87, detectors 3% vs 97%, $81/author |
| C2 | VERIFIED | Anthropic SynthID-Text watermark announcement, 14 Aug 2026, EU AI Act |
| C3 | VERIFIED | arXiv:2501.15654 — 56.7/51.7 vs 92.7/4.0 TPR/FPR, 1 of 300, "AI vocabulary" |
| C4 | VERIFIED | Raj et al. disclosure penalty — 16 experiments, 27,491, authenticity mediates |
| C5 | PARTLY | TinyStyler — 800M + training objective correct; "joint metric" is misattributed |
| C6 | VERIFIED | arXiv:2604.24444 — post-edited text stays closer to LLM than to self |
| C7 | VERIFIED | arXiv:2603.18161 + arXiv:2605.03202 — grammar edits shift meaning; hedging/emphasis words |
| C8 | VERIFIED | Pangram — $0.05/100 words, 2,000 words/day free, fraction_* + windows |
| C9 | VERIFIED | RAID — Oxidane 0.997, GeorgeDrayson 0.991, both exist, MIT/Apache-2.0 |
| C10 | VERIFIED | gemma-3-27b-it-antislop EQ-Bench slop 20.8 vs 69.5 base, human 10.4 |
| C11 | PARTLY | blader/humanizer — 53k stars + v3.1.0 correct; 26 patterns, not ~35 |
| C12 | VERIFIED | arXiv:2511.04195 — BERT ≥85%, affective tone persists after calibration |
| C13 | PARTLY | arXiv:2602.15013 — Liu & Koehn, PEFT + round-trip correct; ITDA/Shao/40% GPT-4 not in paper |

---

## C1 — VERIFIED

Read `https://arxiv.org/abs/2510.13939` (abstract). The abstract states: "AI text from in-context prompting was strongly disfavored by MFA readers for stylistic fidelity (OR=0.16) and quality (OR=0.13)". Fine-tuning reverses it: "MFA readers favored AI for fidelity (OR=8.16) and quality (OR=1.87)". Detectors: "Fine-tuned outputs were rarely flagged as AI-generated (3% vs. 97% for prompting)". Cost: "the median fine-tuning cost of $81 per author". Authors are Chakrabarty, Ginsburg, Dhillon. Every number in the claim matches the abstract exactly.

## C2 — VERIFIED

Read `https://www.anthropic.com/news/claude-text-watermark` via Firecrawl. The page is dated "Aug 14, 2026", opens "Future Claude models will generate text that contains a watermark", and states "we, along with several other major AI providers, are implementing this change to comply with the EU AI Act". The SynthID link is explicit: "Claude's text watermark is a version of the SynthID-Text approach published by Google DeepMind in a Nature paper in 2024."

## C3 — VERIFIED

Read `https://arxiv.org/abs/2501.15654` abstract plus full text at `https://arxiv.org/html/2501.15654`. Table 1 gives "Metric Nonexperts Experts / Avg. TPR 56.7 92.7 / Avg. FPR 51.7 4.0". The abstract says "the majority vote among five such 'expert' annotators misclassifies only 1 of 300 articles". The full text lists the tells: "usage of 'AI vocabulary' (e.g., vibrant, crucial, significantly) form the most common giveaways. Close behind are formulaic sentence and document structures (e.g., optimistically vague conclusions)". The claim maps "nonexpert" to non-LLM-user and "expert" to frequent-LLM-user, which is how the paper defines the groups.

## C4 — VERIFIED

Read `https://psycnet.apa.org/record/2027-12675-001` (PubMed was reCAPTCHA-blocked). The citation is "Raj, M., Berg, J. M., & Seamans, R. (2026). The artificial intelligence disclosure penalty: Humans persistently devalue AI-generated creative writing. Journal of Experimental Psychology: General, 155(4), 896–915. https://doi.org/10.1037/xge0001889". Abstract: "In a series of 16 preregistered experiments (N = 27,491)"; "decrease when they believe writing samples were written by an AI model—or with the help of one—rather than a human author alone, and this effect is mediated by perceived authenticity". The "penalized as much as full AI" claim is supported by Study 5ba in the Method section: "Compare disclosure of AI-only versus human-only versus human–AI collaboration | Penalty persisted and was the same for AI-only and human–AI collaboration."

## C5 — PARTLY

Read `https://arxiv.org/abs/2406.15586` abstract plus full text at `https://arxiv.org/html/2406.15586`. Two of three sub-claims are exact: "a small language model (800M params)" and "trained in an unsupervised fashion ... to reconstruct texts from paraphrases by conditioning on an authorship embedding of the original text". The third is misstated. The authorship-style-transfer evaluation uses "Away and Towards metrics", not a "joint metric". "Joint" is the metric name for the separate formality task, where the paper says "Gpt-4 and Gpt-3.5 are most performant on Joint, Sim, and Fluency metrics" and "on informal transfer, TinyStyler performs on par with Gpt-4 on the Joint metric (0.85 vs 0.88)". So on the joint metric TinyStyler does not beat GPT-4; the "beats GPT-4" finding is confined to authorship style transfer (abstract: "outperforms strong approaches such as GPT-4").

## C6 — VERIFIED

Read `https://arxiv.org/abs/2604.24444` abstract plus full text at `https://arxiv.org/html/2604.24444`. Title: "Can You Make It Sound Like You? Post-Editing LLM-Generated Text for Personal Style". The claim's paraphrase is accurate. Numbers: n=81; H1c — "participants' post-edited text remained significantly more stylistically similar to LLM-generated text than to their unassisted control text (H1c, p = .0002, g = −1.43, 95% CI: [−1.55, −1.32])". Post-editing moves toward the writer's own style (H1a, g = 0.55) and away from LLM text (H1b, g = −0.41), but the residual is still closer to the LLM than to the writer.

## C7 — VERIFIED

C7a `https://arxiv.org/abs/2603.18161`, "How LLMs Distort Our Written Language": the abstract states "even when LLMs are prompted with expert feedback and asked to only make grammar edits, they still change the text in a way that significantly alters its semantic meaning". C7b `https://arxiv.org/abs/2605.03202`, "Stop Automating Peer Review Without Rigorous Evaluation": the hedging/emphasis finding is in the paper-laundering section — "Laundering disproportionately makes stylistic modifications, with increased hedging words ('may,' 'typically,' 'suggests', …) and emphasis words ('strong,' 'robust,' 'consistent', …)". Note this finding is specifically about adversarially "laundered" (LLM-rewritten) papers, not all LLM rewriting.

## C8 — VERIFIED

Read `https://www.pangram.com/pricing` (free tier: "Scan up to 2,000 words per day") and `https://www.pangram.com/solutions/api` ("Pangram 4: $0.05 = 100 words"; "Window fields show the label, score, and character range for each analyzed section"; the response field list includes "fraction_ai, fraction_ai_assisted, fraction_human" and "windows[].label"). All four sub-claims check out.

## C9 — VERIFIED

Both checkpoints exist on Hugging Face: `Oxidane/tmr-ai-text-detector` (license: MIT) and `GeorgeDrayson/modernbert-ai-detection-raid-mage` (license: Apache-2.0), confirmed via the HF API. The RAID leaderboard at `https://raid-bench.xyz/leaderboard` (columns "AUROC | TPR@FPR=5% | TPR@FPR=1%") lists TMR at AUROC 0.997 and ModernBERT AI Detection at AUROC 0.991, exactly matching the claim.

## C10 — VERIFIED

Read `https://eqbench.com/slop-score.html`. It lists `google/gemma-3-27b-it` at 69.5, `sam-paech/gemma-3-27b-it-antislop` at 20.8, and `human-baseline` at 10.4. The model also exists on Hugging Face. All three numbers match.

## C11 — PARTLY

Read `https://github.com/blader/humanizer` (GitHub API + README). Stars: 53,208 (≈53k, correct). Latest release tag: v3.1.0 (correct). The pattern count is wrong: the README states "Humanizer checks for 26 patterns in all" under the section "The 26 patterns". It is built on Wikipedia's "Signs of AI writing", but there is no "about 35 patterns" anywhere; the correct figure is 26.

## C12 — VERIFIED

Read `https://arxiv.org/abs/2511.04195` abstract plus full text at `https://arxiv.org/html/2511.04195`. Title matches; authors are Pagan, Törnberg, Bail, Hannák, Barrie. "The BERT classifier achieves consistently high accuracy across all models and datasets, never falling below 85%." On calibration: "Some sophisticated strategies, such as fine-tuning and persona descriptions, fail to improve realism or even make text more detectable" and "deeper emotional and affective cues persist as reliable discriminators", with "LLM outputs remain clearly distinguishable ... particularly in affective tone and emotional expression."

## C13 — PARTLY

Read `https://arxiv.org/abs/2602.15013` abstract plus full text at `https://arxiv.org/html/2602.15013`. The first half is correct: authors Ruoxi Liu and Philipp Koehn (Johns Hopkins), title "Text Style Transfer with Parameter-efficient LLM Finetuning and Round-trip Translation", method PEFT + roundtrip translation. The ITDA part is not in this paper: the full text contains no mention of "ITDA", "Shao", "inverse transfer", "forward transfer", or "GPT-4", and its evaluation uses BLEU and BERT-based style-accuracy scores (compared against zero-shot prompting, few-shot ICL, and APE), not a GPT-4 score. The "ITDA ... inverse transfer beats forward by about 40% on GPT-4 score" is either from a different paper or hallucinated.
