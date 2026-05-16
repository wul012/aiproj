from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry_rankings import (  # noqa: E402
    annotate_loss_leaderboard,
    annotate_rubric_leaderboard,
    benchmark_rubric_summary,
    collect_pair_delta_rows,
    collect_release_readiness_delta_rows,
    counts,
    pair_delta_leaderboard,
    pair_delta_summary,
    release_readiness_delta_leaderboard,
    release_readiness_delta_summary,
)
from tests.test_registry import make_run  # noqa: E402


class RegistryRankingsTests(unittest.TestCase):
    def test_annotates_loss_and_rubric_leaderboards_in_place(self) -> None:
        rows = [
            {"name": "A", "path": "a", "best_val_loss": 1.2, "benchmark_rubric_avg_score": 94.0},
            {"name": "B", "path": "b", "best_val_loss": 0.9, "benchmark_rubric_avg_score": 76.0},
        ]

        loss = annotate_loss_leaderboard(rows)
        rubric = annotate_rubric_leaderboard(rows)
        summary = benchmark_rubric_summary(rubric)

        self.assertEqual(loss[0]["name"], "B")
        self.assertEqual(rows[1]["best_val_loss_rank"], 1)
        self.assertAlmostEqual(rows[0]["best_val_loss_delta"], 0.3)
        self.assertEqual(rubric[0]["name"], "A")
        self.assertEqual(rows[1]["benchmark_rubric_rank"], 2)
        self.assertAlmostEqual(rows[1]["benchmark_rubric_delta_from_best"], -18.0)
        self.assertEqual(summary["best_run"], "A")
        self.assertEqual(summary["regression_count"], 1)

    def test_counts_pair_and_release_readiness_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_run(root, "a", 1.2, pair_reports=True, pair_generated_delta=4, readiness_trend="improved")
            run_b = make_run(root, "b", 0.9, pair_reports=True, pair_generated_delta=-9, readiness_trend="regressed")

            pair_rows = collect_pair_delta_rows([run_a, run_b], ["A", "B"])
            pair_summary = pair_delta_summary(pair_rows)
            pair_leader = pair_delta_leaderboard(pair_rows)[0]
            readiness_rows = collect_release_readiness_delta_rows([run_a, run_b], ["A", "B"])
            readiness_summary = release_readiness_delta_summary(readiness_rows)
            readiness_leader = release_readiness_delta_leaderboard(readiness_rows)[0]

            self.assertEqual(pair_summary["case_count"], 4)
            self.assertEqual(pair_summary["max_abs_generated_char_delta"], 9)
            self.assertEqual(pair_leader["run_name"], "B")
            self.assertEqual(pair_leader["case"], "b-delta")
            self.assertEqual(readiness_summary["regressed_count"], 1)
            self.assertEqual(readiness_summary["improved_count"], 1)
            self.assertEqual(readiness_leader["run_name"], "B")
            self.assertEqual(readiness_leader["delta_status"], "regressed")
            self.assertEqual(counts(["pass", "warn", "pass"]), {"pass": 2, "warn": 1})


if __name__ == "__main__":
    unittest.main()
