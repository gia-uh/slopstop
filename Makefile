.PHONY: test calibrate rules-doc

# The gate: unit tests, then what the repo already promises.
test:
	uv run pytest -q
	python3 -m compileall -q experiments
	grep -q '^## Not for hiding$$' README.md
	grep -q '^## AI use in this repository$$' README.md

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
