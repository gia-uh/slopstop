# Shared brief for the humanization research tracks

## The project

Alex (CS professor, AI PhD, writes a technical/ideas blog at blog.apiad.net in
English and books in English and Spanish) co-writes with LLMs. Readers judge his
writing negatively because it reads as AI-made. We are researching how
"humanization" and "unslopping" of AI-assisted prose actually work, so we can
design our own toolkit: tools that make AI-assisted writing read as Alex's own
voice and as good human prose to human readers. Automated detectors matter as
measuring instruments and as a proxy for what readers notice.

## What already exists (read before you search, don't re-research it)

- `vault/Atlas/Architecture/2026-09-12-llm-prose-quality-research-brief.md`
  covers the causes of model prose defects (typicality bias, uncertainty gap,
  diversity collapse in post-training), Antislop/FTPO, min-p, steering vectors,
  verbalized sampling, the EMNLP 2025 "Catch Me If You Can" style-imitation
  study, and the Pangram test of Claude writing styles.
- `vault/Atlas/Architecture/2026-09-12-slop-profile-phase-0-findings.md` and
  `vault/Atlas/Architecture/2026-09-13-style-prompt-arms-experiment.md` report
  our own measurements: forbid lists invert on weak models (39x), style prompts
  cut sentence-length variance, the contracted corrective "it isn't X, it's Y"
  is Claude's strongest tell at 22-52x the author's rate.

Paths are relative to `/home/apiad/Workspace`. Skim those three files first
(10 minutes at most) so your track adds to them instead of repeating them.

## How to research

- Never answer from training memory. Search, then read the primary source.
- Firecrawl is the search engine. Key: `KEY=$(tr -d '\n' < /home/apiad/Workspace/.claude/firecrawl.token)`.
  Search: `curl -s -X POST https://api.firecrawl.dev/v2/search -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"query":"...","limit":8}'`
  Scrape: `curl -s -X POST https://api.firecrawl.dev/v2/scrape -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"url":"...","formats":["markdown"],"onlyMainContent":true}'`
  The account is on a free tier shared by five parallel researchers. Budget
  about 15 searches and 25 scrapes for your track. Pipe scrape output through
  `jq -r .data.markdown | head -c 40000` so you don't flood your context.
- For a known URL (an arXiv abstract, a GitHub README) you may use your own
  web fetch tool instead of Firecrawl.
- Prefer papers, benchmark tables, repo READMEs and vendor docs over listicles.
  Vendor marketing claims ("99% undetectable") are claims, not evidence: label
  them as such and look for an independent test.
- Record numbers. "Detector X drops from 95% to 30% TPR under DIPPER
  paraphrase at 1% FPR" beats "paraphrasing fools detectors".
- Today is 2026-10-01. Note the date of every source. Prefer 2025-2026 work and
  flag anything older that may be stale.

## Output

Write your report as Markdown to the path your task names, inside
`/home/apiad/Workspace/.playground/humanize-research/`. Structure:

1. **Headline**: the 3-6 findings that would change how we build a toolkit.
2. **Findings**: one section per sub-question, each claim followed by its
   source link and date, with the numbers.
3. **Implications for our toolkit**: what to build, what to avoid, what to
   measure. Be concrete.
4. **Open questions**: what you could not settle.
5. **Sources**: full list, title, URL, date.

Write plain English: whole sentences, no em dashes, no hype. 2,000-4,000 words.
Do not modify any file outside `.playground/humanize-research/`. Do not commit.

Your final message must be: the report path, then the headline findings in
under 200 words.
