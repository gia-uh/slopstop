.PHONY: test

# Until the tool code lands, the gate checks what the repo already promises:
# the experiment code compiles, and the README keeps its disclosure sections,
# because the project's first rule is that AI use is always disclosed.
test:
	python3 -m compileall -q experiments
	grep -q '^## Disclose your AI use$$' README.md
	grep -q '^## AI use in this repository$$' README.md
