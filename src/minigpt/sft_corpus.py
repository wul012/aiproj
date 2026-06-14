"""A synthetic instruction-tuning (SFT) dataset of deterministic string ops.

Each example is an instruction the model must *follow*::

    R a b c = c b a \n          ("reverse abc" -> "cba")

* a single op-marker char (``C`` copy, ``R`` reverse, ``S`` sort) is the
  instruction;
* a random input string over :data:`INPUT_ALPHABET`;
* the ``=`` separator ends the prompt;
* the deterministic output plus an ``\n`` end marker is the completion.

The held-out split uses *unseen input strings* for each op, so held-out
exact-match measures whether the model learned to APPLY the op to new inputs
(instruction-following / generalization), not whether it memorized pairs. This is
the dataset for v1164's supervised fine-tuning, where the key SFT mechanic is
computing loss only over the completion tokens (see ``minigpt.sft_training``).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

INPUT_ALPHABET = "abcde"
SEP = "="
EOS = "\n"
PAD = "#"  # padding only; never appears in a real example

# op marker -> transform
OPS = {
    "C": lambda s: s,                       # copy
    "R": lambda s: s[::-1],                 # reverse
    "S": lambda s: "".join(sorted(s)),      # sort
}
ALPHABET = INPUT_ALPHABET + "".join(OPS) + SEP + EOS + PAD


@dataclass
class SftExample:
    op: str
    prompt: str       # e.g. "Rabc="
    completion: str    # e.g. "cba\n"

    @property
    def text(self) -> str:
        return self.prompt + self.completion

    @property
    def expected_output(self) -> str:
        return self.completion[: -len(EOS)] if self.completion.endswith(EOS) else self.completion


@dataclass
class SftCorpus:
    train: list[SftExample] = field(default_factory=list)
    heldout: list[SftExample] = field(default_factory=list)
    ops: tuple[str, ...] = ()
    lengths: tuple[int, ...] = ()
    seed: int = 0

    @property
    def alphabet(self) -> str:
        return ALPHABET

    @property
    def max_text_len(self) -> int:
        return max((len(e.text) for e in self.train + self.heldout), default=0)

    def stats(self) -> dict[str, object]:
        return {
            "train_example_count": len(self.train),
            "heldout_example_count": len(self.heldout),
            "ops": ",".join(self.ops),
            "lengths": ",".join(str(length) for length in self.lengths),
            "max_text_len": self.max_text_len,
            "vocab_char_count": len(set(ALPHABET)),
        }


def _distinct_inputs(rng: random.Random, length: int, count: int) -> list[str]:
    seen: set[str] = set()
    cap = len(INPUT_ALPHABET) ** length
    target = min(count, cap)
    while len(seen) < target:
        seen.add("".join(rng.choice(INPUT_ALPHABET) for _ in range(length)))
    return list(seen)


def build_sft_corpus(
    *,
    seed: int = 1337,
    ops: tuple[str, ...] = ("C", "R", "S"),
    lengths: tuple[int, ...] = (3, 4, 5),
    inputs_per_op_length: int = 240,
    heldout_ratio: float = 0.25,
) -> SftCorpus:
    """Build a deterministic SFT corpus. For each op and length we draw distinct
    inputs and split them into train/held-out, so held-out inputs are unseen."""
    for op in ops:
        if op not in OPS:
            raise ValueError(f"unknown op {op!r}; choose from {sorted(OPS)}")
    if not 0.0 < heldout_ratio < 1.0:
        raise ValueError("heldout_ratio must be between 0 and 1")

    rng = random.Random(seed)
    train: list[SftExample] = []
    heldout: list[SftExample] = []
    for op in ops:
        transform = OPS[op]
        for length in lengths:
            inputs = _distinct_inputs(rng, length, inputs_per_op_length)
            rng.shuffle(inputs)
            n_heldout = max(1, int(len(inputs) * heldout_ratio))
            for split, bucket in ((inputs[:n_heldout], heldout), (inputs[n_heldout:], train)):
                for text in split:
                    bucket.append(SftExample(op=op, prompt=op + text + SEP, completion=transform(text) + EOS))
    rng.shuffle(train)
    rng.shuffle(heldout)
    return SftCorpus(train=train, heldout=heldout, ops=tuple(ops), lengths=tuple(lengths), seed=seed)


__all__ = ["SftExample", "SftCorpus", "build_sft_corpus", "OPS", "INPUT_ALPHABET", "SEP", "EOS", "PAD", "ALPHABET"]
