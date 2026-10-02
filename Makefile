.PHONY: test

# The gate: unit tests, then what the repo already promises.
test:
	uv run pytest -q
	python3 -m compileall -q experiments
	grep -q '^## Disclose your AI use$$' README.md
	grep -q '^## AI use in this repository$$' README.md
