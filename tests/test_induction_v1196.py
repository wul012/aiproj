"""Tests for v1196 in-context induction (depth requirement).

Task/metric logic is tested directly; the verdict is a deterministic function of cached accuracies,
so the decide() ladder runs on synthetic caches. A tiny real Phase-A smoke exercises the pipeline.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import torch  # noqa: E402

from minigpt.induction_v1196 import (  # noqa: E402
    IGNORE, InductionConfig, build_report, decide, make_batch, run_phase_a, summarize, unigram_acc,
)
from minigpt.induction_v1196_decision import decide_induction  # noqa: E402
from minigpt.induction_v1196_report import build_induction_report  # noqa: E402

SEEDS = (1, 2, 3, 4, 5)
WIDTHS = (8, 16, 24, 32, 48, 64, 96, 128)


# --------------------------------------------------------------------------- task generation
class Task(unittest.TestCase):
    def test_clean_target_is_most_recent_successor_first_masked(self):
        cfg = InductionConfig(K=6, T=24)
        g = torch.Generator().manual_seed(0)
        x, t = make_batch(cfg, 8, g, torch.device("cpu"), mode="clean")
        for b in range(8):
            last = {}
            for i in range(cfg.T - 1):
                c = int(x[b, i])
                if int(t[b, i]) != IGNORE:
                    self.assertIn(c, last)                                   # inductable => seen before
                    self.assertEqual(int(t[b, i]), int(x[b, last[c] + 1]))   # most-recent successor
                else:
                    self.assertNotIn(c, last)                                # masked => first occurrence
                last[c] = i

    def test_fixed_offset_masks_first_copy(self):
        cfg = InductionConfig(K=8, T=20)
        g = torch.Generator().manual_seed(1)
        x, t = make_batch(cfg, 4, g, torch.device("cpu"), mode="fixed_offset")
        L = cfg.T // 2
        self.assertTrue(bool((t[:, : L - 1] == IGNORE).all()))
        self.assertTrue(bool((x[:, :L] == x[:, L:]).all()))                  # it is a repeat
        self.assertTrue(bool((t[:, L:] == x[:, L + 1:]).all()))             # second-copy target = next

    def test_unigram_acc_in_range(self):
        cfg = InductionConfig(K=10, T=40)
        g = torch.Generator().manual_seed(2)
        x, t = make_batch(cfg, 16, g, torch.device("cpu"), mode="clean")
        ua, mm = unigram_acc(cfg, x, t)
        self.assertTrue(0.0 <= ua <= 1.0)
        self.assertGreater(mm, 1.0 / cfg.K)        # leading in-context token beats uniform


# --------------------------------------------------------------------------- synthetic caches
def _arm(acc, *, swap=0.95, succ=0.5, prev=0.4, seeds=SEEDS):
    jit = [-0.01, -0.005, 0.0, 0.005, 0.01]
    return {s: {"acc": min(1.0, max(0.0, acc + jit[i % len(jit)])), "swap_follow": swap,
                "best_layer_succ_mass": succ, "succ_mass_by_layer": [succ], "layer0_prev_token": prev,
                "traj": [0.05, acc]} for i, s in enumerate(seeds)}


def synth_cache(acc1, acc2, *, shortcut_acc=0.95, attn2_acc=0.95, attn1_acc=0.2, unigram=0.14,
                random_init=0.06, swap2=0.95, K=20, T=64, widths=WIDTHS,
                shortcut_widths=(16, 32, 64), attn_only_widths=(24, 48, 96)):
    """acc1/acc2: dict width->mean clean accuracy for depth 1 / depth 2."""
    S = 0.6 * (1.0 - 1.0 / K)
    clean = {}
    for w in widths:
        # a genuinely inducting cell (acc >= S) follows swaps; a failing one does not
        clean[f"d1w{w}"] = _arm(acc1[w], swap=(0.95 if acc1[w] >= S else 0.2), succ=0.05, prev=0.1)
        clean[f"d2w{w}"] = _arm(acc2[w], swap=(swap2 if acc2[w] >= S else 0.2), succ=0.5, prev=0.45)
    shortcut = {f"w{w}": _arm(shortcut_acc) for w in shortcut_widths}
    attn_only = {}
    for w in attn_only_widths:
        attn_only[f"d1w{w}"] = _arm(attn1_acc)
        attn_only[f"d2w{w}"] = _arm(attn2_acc)
    return {
        "config": {"K": K, "T": T, "widths": list(widths), "depths": [1, 2],
                   "shortcut_widths": list(shortcut_widths), "attn_only_widths": list(attn_only_widths),
                   "steps": 1500, "seeds": list(SEEDS), "n_head": 4},
        "chance": 1.0 / K, "ceiling": 1.0 - 1.0 / K, "S": 0.6 * (1.0 - 1.0 / K),
        "unigram_acc": unigram, "max_marginal": 0.2, "random_init_acc": random_init,
        "clean": clean, "shortcut": shortcut, "attn_only": attn_only,
    }


# 1-layer fails everywhere (~unigram), 2-layer succeeds from width 24 -> requires_depth
ACC1_FAIL = {w: 0.18 for w in WIDTHS}
ACC2_GOOD = {8: 0.30, 16: 0.45, 24: 0.99, 32: 1.0, 48: 1.0, 64: 1.0, 96: 1.0, 128: 1.0}


class DecideLadder(unittest.TestCase):
    def test_extracted_decision_matches_public_facade(self):
        cfg = self.cfg()
        result = summarize(synth_cache(ACC1_FAIL, ACC2_GOOD), cfg)
        self.assertEqual(decide(result, cfg), decide_induction(result, cfg))

    def cfg(self):
        return InductionConfig(seeds=SEEDS)

    def test_requires_depth(self):
        info = decide(summarize(synth_cache(ACC1_FAIL, ACC2_GOOD), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "induction_requires_depth")
        f = info["flags"]
        self.assertIsNone(f["wstar_1L"])              # 1L never crosses
        self.assertIsNotNone(f["wstar_2L"])
        self.assertTrue(f["in_context_ok"] and f["shortcut_control_ok"] and f["random_init_ok"])

    def test_depth_lowers_threshold(self):
        # both cross, 2L earlier, still ahead at the widest width (not caught up)
        acc1 = {8: 0.18, 16: 0.18, 24: 0.2, 32: 0.3, 48: 0.45, 64: 0.6, 96: 0.62, 128: 0.64}
        acc2 = {8: 0.3, 16: 0.5, 24: 0.99, 32: 1.0, 48: 1.0, 64: 1.0, 96: 1.0, 128: 1.0}
        info = decide(summarize(synth_cache(acc1, acc2), self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "depth_lowers_capacity_threshold")

    def test_independent_of_depth(self):
        # both cross at similar widths and 1L catches up at the widest
        acc = {8: 0.3, 16: 0.6, 24: 0.99, 32: 1.0, 48: 1.0, 64: 1.0, 96: 1.0, 128: 1.0}
        info = decide(summarize(synth_cache(acc, dict(acc)), self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "induction_independent_of_depth")

    def test_review_task_not_learnable(self):
        info = decide(summarize(synth_cache(ACC1_FAIL, {w: 0.2 for w in WIDTHS}), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "task_not_learnable")

    def test_review_not_in_context_low_swap(self):
        # 2L "succeeds" on accuracy but the swap probe does NOT follow -> not genuine induction
        info = decide(summarize(synth_cache(ACC1_FAIL, ACC2_GOOD, swap2=0.1), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "not_in_context")

    def test_review_not_in_context_unigram(self):
        # succeeding 2L cells barely beat a high unigram floor -> not past frequency
        info = decide(summarize(synth_cache(ACC1_FAIL, {w: 0.6 for w in WIDTHS}, unigram=0.55), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "not_in_context")

    def test_review_shortcut_control_failed(self):
        info = decide(summarize(synth_cache(ACC1_FAIL, ACC2_GOOD, shortcut_acc=0.2), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "shortcut_control_failed")

    def test_review_random_init(self):
        info = decide(summarize(synth_cache(ACC1_FAIL, ACC2_GOOD, random_init=0.5), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "random_init_not_null")

    def test_attn_only_flags(self):
        # 2L attn-only inducts (>= S); recorded in flags
        info = decide(summarize(synth_cache(ACC1_FAIL, ACC2_GOOD, attn2_acc=0.95), self.cfg()), self.cfg())
        self.assertTrue(info["flags"]["attn_only_2L_inducts"])
        info2 = decide(summarize(synth_cache(ACC1_FAIL, ACC2_GOOD, attn2_acc=0.2), self.cfg()), self.cfg())
        self.assertFalse(info2["flags"]["attn_only_2L_inducts"])


class ReportShape(unittest.TestCase):
    def test_build_report(self):
        r = summarize(synth_cache(ACC1_FAIL, ACC2_GOOD), InductionConfig(seeds=SEEDS))
        info = decide(r, InductionConfig(seeds=SEEDS))
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        for fld in report["csv_fieldnames"]:
            self.assertIn(fld, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertIn("acc_curve", report)
        self.assertEqual(report["summary"]["verdict"], "induction_requires_depth")

    def test_extracted_report_matches_public_facade(self):
        result = summarize(synth_cache(ACC1_FAIL, ACC2_GOOD), InductionConfig(seeds=SEEDS))
        info = decide(result, InductionConfig(seeds=SEEDS))
        expected = build_report(result, info, "synthetic", generated_at="2026-01-01T00:00:00Z")
        actual = build_induction_report(
            result,
            info,
            "synthetic",
            generated_at="2026-01-01T00:00:00Z",
            unigram_margin=InductionConfig().unigram_margin,
        )
        self.assertEqual(actual, expected)


class PhaseASmoke(unittest.TestCase):
    def test_tiny_run_phase_a(self):
        cfg = InductionConfig(K=8, T=24, widths=(8, 16), depths=(1, 2), shortcut_widths=(16,),
                              attn_only_widths=(16,), steps=60, batch=64, eval_every=30, eval_batch=64,
                              eval_n_batches=2, mech_batch=16, seeds=(1, 2))
        cache = run_phase_a(cfg, torch.device("cpu"))
        self.assertIn("d2w16", cache["clean"])
        self.assertIn("w16", cache["shortcut"])
        self.assertIn("d1w16", cache["attn_only"])
        rec = cache["clean"]["d2w16"][1]
        self.assertIn("acc", rec)
        self.assertIn("swap_follow", rec)
        self.assertIn("best_layer_succ_mass", rec)
        info = decide(summarize(cache, cfg), cfg)
        self.assertIn(info["status"], ("pass", "review"))


if __name__ == "__main__":
    unittest.main()
