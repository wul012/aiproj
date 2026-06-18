from __future__ import annotations

import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.grok_logit_freq_v1190 import (  # noqa: E402
    decide_alignment,
    fold_frequency,
    frequency_overlap,
    ideal_addition_cube,
    logit_frequency_metrics,
    prompt_grid,
)


def test_prompt_grid_contains_four_token_addition_prompts() -> None:
    grid = prompt_grid(5)
    assert grid.shape == (25, 4)
    assert grid[0].tolist() == [0, 5, 0, 6]
    assert grid[-1].tolist() == [4, 5, 4, 6]


def test_ideal_addition_cube_has_unit_diagonal_fft_fraction() -> None:
    metrics = logit_frequency_metrics(ideal_addition_cube(7), 7, top_k=3)
    assert metrics["diagonal_fraction"] == 1.0
    assert metrics["dominant_freq"] in {1, 2, 3}
    assert len(metrics["top_freqs"]) == 3


def test_random_cube_has_low_diagonal_fft_fraction() -> None:
    torch.manual_seed(0)
    cube = torch.randn(11, 11, 11)
    metrics = logit_frequency_metrics(cube, 11, top_k=3)
    assert metrics["diagonal_fraction"] < 0.25


def test_fold_frequency_maps_negative_pair_to_same_canonical_frequency() -> None:
    assert fold_frequency(3, 97) == 3
    assert fold_frequency(94, 97) == 3


def test_frequency_overlap_counts_top_frequency_alignment() -> None:
    out = frequency_overlap([43, 3, 48, 26, 44], [3, 26, 44, 7, 43])
    assert out == {"count": 4, "fraction": 0.8, "freqs": [3, 26, 43, 44]}


def test_decide_alignment_passes_when_logits_and_embeddings_align() -> None:
    info = decide_alignment(
        table={"heldout_acc": 0.96},
        embedding_metrics={"top_freqs": [43, 3, 48, 26, 44], "dominant_freq": 43},
        shipped_logit={"diagonal_fraction": 0.72, "top_freqs": [43, 3, 48, 26, 44], "dominant_freq": 43},
        random_logit={"diagonal_fraction": 0.01, "top_freqs": [1, 2, 3], "dominant_freq": 1},
        ideal_logit={"diagonal_fraction": 1.0, "top_freqs": [1, 2, 3], "dominant_freq": 1},
    )
    assert info["status"] == "pass"
    assert info["decision"] == "embedding_logit_frequency_alignment_supports_trig_addition"


def test_decide_alignment_reviews_when_top_freqs_do_not_align() -> None:
    info = decide_alignment(
        table={"heldout_acc": 0.96},
        embedding_metrics={"top_freqs": [43, 3, 48, 26, 44], "dominant_freq": 43},
        shipped_logit={"diagonal_fraction": 0.72, "top_freqs": [1, 2, 4, 5, 6], "dominant_freq": 1},
        random_logit={"diagonal_fraction": 0.01, "top_freqs": [1, 2, 3], "dominant_freq": 1},
        ideal_logit={"diagonal_fraction": 1.0, "top_freqs": [1, 2, 3], "dominant_freq": 1},
    )
    assert info["status"] == "review"
    assert "embedding_logit_top_freqs_overlap" in {row["id"] for row in info["failed"]}
