"""Reject deterministic training input errors before output mutation."""

from __future__ import annotations

import math
from argparse import Namespace


def _minimum(args: Namespace, bounds: tuple[tuple[str, int], ...]) -> None:
    for name, lower in bounds:
        if getattr(args, name) < lower:
            raise ValueError(f"--{name.replace('_', '-')} must be at least {lower}")


def _finite(name: str, value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"--{name.replace('_', '-')} must be finite")
    return value


def validate_options(args: Namespace) -> None:
    """Validate parsed, active options without I/O or random-state changes."""
    _minimum(args, (("batch_size", 1), ("max_iters", 1), ("eval_interval", 1), ("eval_iters", 1)))
    if _finite("learning_rate", args.learning_rate) < 0:
        raise ValueError("--learning-rate must be nonnegative")
    if not 0 < _finite("train_ratio", args.train_ratio) < 1:
        raise ValueError("--train-ratio must be between 0 and 1")
    if not 0 <= args.seed <= 2**32 - 1:
        raise ValueError("--seed must be between 0 and 4294967295")

    if args.resume is None:
        _minimum(args, (("block_size", 1), ("n_layer", 0), ("n_head", 1), ("n_embd", 1)))
        if args.n_layer > 0 and args.n_embd % args.n_head != 0:
            raise ValueError("--n-embd must be divisible by --n-head")
        if not 0 <= _finite("dropout", args.dropout) <= 1:
            raise ValueError("--dropout must be between 0 and 1 inclusive")
        if args.tokenizer == "bpe":
            _minimum(args, (("bpe_vocab_size", 2), ("bpe_min_frequency", 1)))

    if not args.no_sample:
        _minimum(args, (("sample_tokens", 0),))
        if _finite("sample_temperature", args.sample_temperature) <= 0:
            raise ValueError("--sample-temperature must be greater than 0")
        if args.sample_tokens > 0:
            _minimum(args, (("sample_top_k", 1),))
            if not args.sample_prompt:
                raise ValueError("--sample-prompt must not be empty when generating tokens")


def validate_splits(train_size: int, val_size: int, block_size: int) -> None:
    """Mirror get_batch's current minimum, using the effective checkpoint config."""
    if block_size < 1:
        raise ValueError("Effective block_size must be at least 1")
    for name, size in (("train", train_size), ("validation", val_size)):
        if size <= block_size + 1:
            raise ValueError(
                f"{name} split has {size} tokens; block_size={block_size} needs at least {block_size + 2}. "
                "Use more text or a compatible block size/train ratio."
            )
