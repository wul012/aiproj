"""Contract tests for the preregistered v1275 Fourier-ticket experiment."""

from __future__ import annotations

import json

import torch

from minigpt.fourier_ticket_v1275 import (
    TicketConfig,
    arm_p_result,
    build_report,
    decide,
    make_mask,
    mask_sparsity,
    prune_targets,
    run_arm_p,
)
from minigpt.grok_checkpoint_v1185 import CheckpointMeta, train_to_grok
from minigpt.grok_v1179 import GrokConfig, make_grok_model
from minigpt.script_runtime import seed_everything


def _cfg() -> TicketConfig:
    return TicketConfig(
        sparsities=(0.5, 0.7),
        random_seeds=(11, 12),
        train_seeds=(1, 2, 3),
        requested_levels=(0.5, 0.75, 0.875),
        run_levels=(0.5,),
        expected_sha256="PINNED",
        known_freqs=(1, 2, 3),
        overlap_min=2,
    )


def _p_rows(*, margin: float = 0.10, acc: float = 0.95) -> list[dict]:
    rows = []
    for mode in ("per_tensor", "global"):
        for sparsity in (0.5, 0.7):
            rows.append(
                {
                    "mode": mode,
                    "sparsity": sparsity,
                    "actual_sparsity": sparsity,
                    "heldout_acc": acc,
                    "known_share": 0.30,
                    "top5_share": 0.30,
                    "top_freqs": [1, 2, 3],
                    "known_overlap": 3,
                    "random_acc_mean": 0.20,
                    "random_acc_std": 0.01,
                    "random_share_mean": 0.30 - margin,
                    "random_share_std": 0.01,
                    "share_margin": margin,
                    "random_trials": 2,
                }
            )
    return rows


def _l_row(seed: int, arm: str, *, grokked: bool, aligned: bool = True) -> dict:
    dense = arm == "dense"
    return {
        "seed": seed,
        "arm": arm,
        "sparsity": 0.0 if dense else 0.5,
        "t_gen": 100 if grokked else None,
        "steps_run": 100,
        "step_cap": 150,
        "heldout_acc": 0.96 if grokked else 0.20,
        "grokked": grokked,
        "known_share": 0.30,
        "top5_share": 0.31,
        "top_freqs": [1, 2, 3],
        "known_overlap": 3,
        "share_gap": 0.0,
        "circuit_aligned": aligned,
    }


def _cache(*, margin: float = 0.10, ticket=True, aligned=True, random=False, reinit=False) -> dict:
    rows = []
    for seed in (1, 2, 3):
        rows.extend(
            [
                _l_row(seed, "dense", grokked=True),
                _l_row(seed, "ticket", grokked=ticket, aligned=aligned),
                _l_row(seed, "random", grokked=random),
                _l_row(seed, "reinit", grokked=reinit),
            ]
        )
    return {
        "checkpoint": "checkpoint.pt",
        "checkpoint_sha_before": "PINNED",
        "checkpoint_sha_after": "PINNED",
        "arm_p": {
            "full": {"heldout_acc": 0.96, "known_share": 0.30, "top5_share": 0.31,
                     "top_freqs": [1, 2, 3], "known_overlap": 3},
            "rows": _p_rows(margin=margin),
        },
        "arm_l": {
            "rows": rows,
            "requested_levels": [0.5, 0.75, 0.875],
            "run_levels": [0.5],
            "descoped_levels": [0.75, 0.875],
            "actual_runs": 12,
            "max_runs": 15,
        },
    }


def test_masks_are_exact_and_unique():
    model = make_grok_model(13, GrokConfig(p=11, n_embd=16))
    targets = prune_targets(model)
    assert set(targets) == {
        "token_embedding.weight",
        "blocks.0.mlp.net.0.weight",
        "blocks.0.mlp.net.2.weight",
    }
    for mode in ("per_tensor", "global"):
        masks = make_mask(model, 0.7, mode)
        total = sum(mask.numel() for mask in masks.values())
        kept = sum(int(mask.sum()) for mask in masks.values())
        expected = sum(round(mask.numel() * 0.3) for mask in masks.values()) if mode == "per_tensor" else round(total * 0.3)
        assert kept == expected
        assert mask_sparsity(masks) == round(1.0 - kept / total, 6)


def test_random_masks_are_reproducible():
    model = make_grok_model(13, GrokConfig(p=11, n_embd=16))
    first = make_mask(model, 0.5, "global", random_seed=7)
    again = make_mask(model, 0.5, "global", random_seed=7)
    other = make_mask(model, 0.5, "global", random_seed=8)
    assert all(torch.equal(first[name], again[name]) for name in first)
    assert any(not torch.equal(first[name], other[name]) for name in first)


def test_training_keeps_pruned_weights_zero():
    cfg = GrokConfig(p=5, train_frac=0.4, n_embd=8, seeds=(7,), wds=(1.0,), max_steps=3, eval_every=1)
    seed_everything(7)
    initial = make_grok_model(7, cfg).state_dict()
    shape = initial["token_embedding.weight"].shape
    model, _, _ = train_to_grok(
        cfg,
        torch.device("cpu"),
        init_state=initial,
        masks={"token_embedding.weight": torch.zeros(shape, dtype=torch.bool)},
    )
    assert torch.count_nonzero(model.token_embedding.weight) == 0
    assert model.lm_head.weight is model.token_embedding.weight


def test_arm_p_runs_real_forward_controls():
    cfg = TicketConfig(
        sparsities=(0.5,), modes=("per_tensor", "global"), random_seeds=(1, 2),
        known_freqs=(1, 2, 3), train_seeds=(1, 2, 3), expected_sha256="x",
    )
    model = make_grok_model(13, GrokConfig(p=11, train_frac=0.4, n_embd=16))
    meta = CheckpointMeta(
        p=11, train_frac=0.4, seed=0, weight_decay=1.0, vocab_size=13,
        n_layer=1, n_head=4, n_embd=16, block_size=5, t_mem=None, t_gen=None,
        final_train_acc=0.0, final_val_acc=0.0, steps_run=0,
    )
    result = run_arm_p(model, meta, cfg)
    assert len(result["rows"]) == 2
    assert all(row["random_trials"] == 2 for row in result["rows"])
    assert all(0.0 <= row["heldout_acc"] <= 1.0 for row in result["rows"])


def test_arm_p_selects_highest_safe_level():
    info = arm_p_result(_cache()["arm_p"], _cfg())
    assert info["probe_ok"] is True
    assert info["p_pass"] is True
    assert info["selected"]["global"]["sparsity"] == 0.7


def test_verdict_matches_fourier_circuit():
    info = decide(_cache(), _cfg())
    assert info["status"] == "pass"
    assert info["verdict"] == "ticket_matches_fourier_circuit"


def test_verdict_trains_but_unaligned():
    info = decide(_cache(aligned=False), _cfg())
    assert info["verdict"] == "ticket_trains_but_unaligned"


def test_verdict_needs_dense_start():
    assert decide(_cache(ticket=False), _cfg())["verdict"] == "ticket_needs_dense_start"
    tied = decide(_cache(random=True), _cfg())
    assert tied["gates"]["control_tie"] is True
    assert tied["verdict"] == "ticket_needs_dense_start"


def test_verdict_pruning_breaks_circuit():
    info = decide(_cache(margin=0.01), _cfg())
    assert info["status"] == "pass"
    assert info["verdict"] == "pruning_breaks_circuit"


def test_missing_grid_is_review():
    cache = _cache()
    cache["arm_l"]["rows"].pop()
    assert decide(cache, _cfg())["status"] == "review"


def test_probe_failure_is_valid_stop():
    cfg = _cfg()
    cache = _cache()
    for row in cache["arm_p"]["rows"]:
        if row["sparsity"] == 0.5:
            row["heldout_acc"] = 0.20
    cache["arm_l"].update(rows=[], actual_runs=0, run_levels=[], descoped_levels=[0.5, 0.75, 0.875],
                          skipped_reason="arm_p_probe_failed")
    info = decide(cache, cfg)
    assert info["status"] == "pass"
    assert info["verdict"] == "pruning_breaks_circuit"


def test_cache_verdict_is_byte_stable():
    cache = _cache()
    first = json.dumps(decide(cache, _cfg()), sort_keys=True, separators=(",", ":"))
    second = json.dumps(decide(cache, _cfg()), sort_keys=True, separators=(",", ":"))
    assert first == second


def test_report_shape_carries_budget_boundary():
    cache = _cache()
    report = build_report(cache, decide(cache, _cfg()), generated_at="fixed")
    assert report["status"] == "pass"
    assert report["summary"]["scope"] == "toy_scale_own_substrate"
    assert report["summary"]["actual_training_runs"] == 12
    assert report["summary"]["descoped_levels"] == [0.75, 0.875]
    assert all(set(report["csv_fieldnames"]) == set(row) for row in report["rows"])
