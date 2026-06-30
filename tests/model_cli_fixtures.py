from __future__ import annotations

import json
from pathlib import Path

import torch

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.core.model import GPTConfig, MiniGPT
from minigpt.core.tokenizer import CharTokenizer


def make_tiny_checkpoint(root: Path) -> tuple[Path, Path, Path, Path]:
    text = "abcdefghijklmnopqrstuvwx " * 3
    tokenizer = CharTokenizer.train(text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    config = GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=8,
        n_layer=1,
        n_head=2,
        n_embd=8,
        dropout=0.0,
    )
    model = MiniGPT(config)
    checkpoint_path = root / "checkpoint.pt"
    torch.save(
        {
            "config": config.__dict__,
            "model": model.state_dict(),
            "step": 1,
            "last_loss": 1.0,
            "tokenizer_type": "char",
        },
        checkpoint_path,
    )
    data_path = root / "data.txt"
    data_path.write_text(text, encoding="utf-8")
    suite_path = root / "suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "name": "tiny-suite",
                "version": "1",
                "cases": [
                    {
                        "name": "case-a",
                        "prompt": "abc",
                        "max_new_tokens": 2,
                        "temperature": 1.0,
                        "top_k": 5,
                        "seed": 1,
                        "task_type": "continuation",
                        "difficulty": "easy",
                        "expected_behavior": "continue",
                        "tags": ["tiny"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return checkpoint_path, tokenizer_path, data_path, suite_path


__all__ = ["make_tiny_checkpoint"]
