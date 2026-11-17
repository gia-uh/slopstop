.PHONY: test register calibrate rules-doc

# The gate: unit tests, then what the repo already promises.
test:
	uv run pytest -q
	python3 -m compileall -q experiments
	grep -q '^## Disclose your AI use$$' README.md
	grep -q '^## AI use in this repository$$' README.md

CORPUS ?= ../../vault/Efforts/Areas/Writing/voice/corpus/slop

# Regenerates the shipped register from the author's published posts (human) and
# uninstructed model essays on the same topics (for the phrase list). Needs the
# private corpus, so CI never runs it. arm-nostyle-qwen-en is left out: its files
# contain the model's own planning notes, which would enter the phrase list.
register:
	uv run slopstop profile $(CORPUS)/alex-en --name apiad-blog-en \
	  --model $(CORPUS)/control-en --model $(CORPUS)/arm-nostyle-deepseek-en \
	  --model $(CORPUS)/arm-nostyle-gemini-en --model $(CORPUS)/arm-nostyle-mistral-en \
	  --out src/slopstop/registers/apiad-blog-en.json

# Measures the catalog on four sets of texts and regenerates docs/rules.md.
# SETS is a folder with en-human, es-human, en-agent and es-agent subfolders;
# docs/calibration/README.md says what each held. The texts are private, so CI
# never runs it; the JSON it writes holds counts only.
SETS ?= calibration-sets
calibrate:
	for s in en-human es-human en-agent es-agent; do \
	  uv run slopstop calibrate $(SETS)/$$s --name $$s --out docs/calibration/$$s.json > /dev/null || exit 1; \
	done
	$(MAKE) rules-doc

rules-doc:
	uv run slopstop rules --markdown --calibration docs/calibration/en-human.json docs/calibration/en-agent.json \
	  docs/calibration/es-human.json docs/calibration/es-agent.json > docs/rules.md
