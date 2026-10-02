import random
from pathlib import Path

import pytest

WORDS = ("alpha beta gamma delta river stone light window table garden "
         "music paper engine market winter summer teacher student city road").split()


def human_text(seed: int, paras: int = 8) -> str:
    """Deterministic English-ish prose: short paragraphs, no slop tells."""
    rng = random.Random(seed)
    out = []
    for _ in range(paras):
        sents = []
        for _ in range(rng.randint(2, 4)):
            n = rng.randint(8, 20)
            body = " ".join(rng.choice(WORDS) for _ in range(n))
            sents.append(f"The {body} is in the house.")
        out.append(" ".join(sents))
    return "\n\n".join(out) + "\n"


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    d = tmp_path / "corpus"
    d.mkdir()
    for i in range(40):
        (d / f"post-{i:02d}.md").write_text(human_text(i))
    return d
