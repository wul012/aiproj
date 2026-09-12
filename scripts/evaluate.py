from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.core.dataset import load_text  # noqa: E402
from minigpt.core.model import GPTConfig, MiniGPT  # noqa: E402
from minigpt.core.tokenizer import Tokenizer, load_tokenizer  # noqa: E402
from minigpt.evaluation.windows import make_plan, score_windows, select_split  # noqa: E402
from minigpt.evaluation.paired import pair_results, render_pair  # noqa: E402
from minigpt.evaluation.prediction import perplexity_from_loss  # noqa: E402
from minigpt.training.tokenizer_binding import tokenizer_digest, validate_tokenizer_binding  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a MiniGPT checkpoint on local text data.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "sample_zh.txt")
    parser.add_argument("--split", choices=["train", "val", "all"], default="val")
    parser.add_argument("--train-ratio", type=float, default=0.9)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--compare-with", type=Path, help="Candidate checkpoint scored on the same windows")
    parser.add_argument("--candidate-tokenizer", type=Path, default=None)
    parser.add_argument("--context-size", type=int, default=None, help="Default: smallest supported model context")
    parser.add_argument("--windows", type=int, default=None, help="Unique windows; default eval-iters * batch-size")
    return parser.parse_args(argv)


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


def estimate_loss(
    model: MiniGPT,
    data: torch.Tensor,
    block_size: int,
    batch_size: int,
    eval_iters: int,
    device: torch.device,
    seed: int = 1337,
) -> float:
    plan = make_plan(len(data), block_size, batch_size * eval_iters, seed)
    return sum(score_windows(model, data, plan, batch_size, device)) / len(plan.starts)


def _load_model(path: Path, tokenizer_path: Path, device: torch.device) -> tuple[MiniGPT, Tokenizer, str]:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        stream.seek(0)
        checkpoint = torch.load(stream, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    validate_tokenizer_binding(checkpoint, tokenizer)
    config = GPTConfig(**checkpoint["config"])
    if config.vocab_size != tokenizer.vocab_size:
        raise ValueError("Checkpoint and tokenizer vocabularies differ")
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    return model, tokenizer, digest


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    if args.batch_size < 1 or (args.windows is None and args.eval_iters < 1):
        raise ValueError("Positive batch size and evaluation window count required")
    model, tokenizer, digest = _load_model(args.checkpoint, tokenizer_path, device)
    candidate = None
    candidate_path = args.candidate_tokenizer
    if args.compare_with is not None:
        candidate_path = candidate_path or args.compare_with.parent / "tokenizer.json"
        candidate, other, other_digest = _load_model(args.compare_with, candidate_path, device)
        if tokenizer_digest(tokenizer) != tokenizer_digest(other):
            raise ValueError("Paired token losses require identical tokenizer semantics")
    context = (
        args.context_size
        if args.context_size is not None
        else min(
            model.config.block_size, candidate.config.block_size if candidate is not None else model.config.block_size
        )
    )
    if context > model.config.block_size or (candidate is not None and context > candidate.config.block_size):
        raise ValueError("Context size exceeds a compared model's supported context")
    text = load_text(args.data)
    token_ids = tokenizer.encode(text)
    data, offset = select_split(token_ids, args.split, args.train_ratio)
    count = args.windows if args.windows is not None else args.eval_iters * args.batch_size
    plan = make_plan(len(data), context, count, args.seed)
    losses = score_windows(model, data, plan, args.batch_size, device)
    loss = statistics.fmean(losses)
    perplexity = perplexity_from_loss(loss)
    report: dict[str, Any] = {
        "checkpoint": str(args.checkpoint),
        "checkpoint_sha256": digest,
        "data": str(args.data),
        "split": args.split,
        "train_ratio": args.train_ratio if args.split != "all" else None,
        "tokenizer": getattr(tokenizer, "name", "unknown"),
        "tokens": len(token_ids),
        "vocab_size": tokenizer.vocab_size,
        "block_size": context,
        "model_context_limit": model.config.block_size,
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "loss": round(loss, 8),
        "perplexity": round(perplexity, 8) if math.isfinite(perplexity) else None,
        "sampling": asdict(plan) | {"protocol": "fixed_windows_v1", "replacement": False},
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "tokenizer_sha256": tokenizer_digest(tokenizer),
        "split_offset": offset,
        "split_tokens": len(data),
        "evaluated_tokens": len(plan.starts) * context,
        "unknown_tokens": int((data == tokenizer.stoi[tokenizer.unk_token]).sum()),
        "interpretation": "Sampled teacher-forced NLL only. Overlapping windows are correlated; holdout provenance and statistical significance are not verified. Different protocols/tokenizers are not comparable.",
    }
    if candidate is not None:
        other_losses = score_windows(candidate, data, plan, args.batch_size, device)
        report["candidate_checkpoint"] = str(args.compare_with)
        report["candidate_sha256"] = other_digest
        report["candidate_context_limit"] = candidate.config.block_size
        report["comparison"] = pair_results(losses, other_losses, plan, data, tokenizer, offset)
    out_path = args.out or args.checkpoint.parent / (
        "eval_comparison.json" if candidate is not None else "eval_report.json"
    )
    outputs = [out_path, out_path.with_suffix(".md")] if candidate is not None else [out_path]
    inputs = [p.resolve() for p in (args.data, args.checkpoint, tokenizer_path, args.compare_with, candidate_path) if p]
    if len({p.resolve() for p in outputs}) != len(outputs) or any(p.resolve() in inputs for p in outputs):
        raise ValueError("Evaluation outputs must be distinct from each other and all inputs")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    if candidate is not None:
        markdown = render_pair(report)
        out_path.with_suffix(".md").write_text(markdown, encoding="utf-8")
        print(markdown)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"saved={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
