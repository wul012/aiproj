"""Shared single-corpus setup for the capability-pivot script entrypoints.

The v1164+ ``scripts/run_*`` CLIs all open with the same five statements:
build one SFT corpus, train a char tokenizer over its text + alphabet, read the
PAD/EOS ids, and floor the block size at 16. This module is the single home for
that block (extracted in the v1171 maintenance pass, the v1159/v1163/v1167
cadence: add one helper, migrate only the current active drivers, leave legacy
and the dual-corpus v1165 transfer script untouched).

Contract-preserving by construction — :func:`setup_single_corpus` reproduces the
inline sequence verbatim and touches no global RNG (``build_sft_corpus`` owns its
own ``random.Random(seed)`` and ``CharTokenizer.train`` is a pure
``sorted(set(text))``), so model-init seeds drawn later by each script are
unchanged. Callers keep their own per-experiment encodings (``base_train`` vs
``pref_train_triples`` vs the reward-model pairs), ``corpus_stats``, and the
final report/print logic — only the common opening collapses to one call.

Deliberately single-corpus / single-seed: it does NOT do v1165's dual-corpus
join, ``build_confusable_preferences`` (v1166/v1168/v1169), or the v1169 OOD
corruption — those stay in their scripts.
"""

from __future__ import annotations

from minigpt.sft_corpus import EOS, PAD, SftCorpus, build_sft_corpus
from minigpt.tokenizer import CharTokenizer


def setup_single_corpus(
    *,
    seed: int,
    ops: tuple[str, ...],
    lengths: tuple[int, ...],
    inputs_per_op_length: int,
    heldout_ratio: float,
) -> tuple[SftCorpus, CharTokenizer, int, int, int]:
    """Build the single-corpus SFT setup shared by the v1164+ script entrypoints.

    Returns ``(corpus, tokenizer, pad_id, eos_id, block_size)``. Reproduces, byte
    for byte, the inline sequence used by ``run_sft_instruction_v1164`` /
    ``run_dpo_preference_v1166`` / ``run_dpo_sft_aux_v1168`` /
    ``run_reward_model_v1169`` / ``run_spec_decode_v1170``::

        corpus = build_sft_corpus(...)
        tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id = tokenizer.encode(PAD)[0]
        eos_id = tokenizer.encode(EOS)[0]
        block_size = max(16, corpus.max_text_len)
    """
    corpus = build_sft_corpus(
        seed=seed, ops=ops, lengths=lengths,
        inputs_per_op_length=inputs_per_op_length, heldout_ratio=heldout_ratio,
    )
    tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    pad_id = tokenizer.encode(PAD)[0]
    eos_id = tokenizer.encode(EOS)[0]
    block_size = max(16, corpus.max_text_len)
    return corpus, tokenizer, pad_id, eos_id, block_size


__all__ = ["setup_single_corpus"]
