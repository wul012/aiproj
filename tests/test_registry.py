from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry import REGISTRY_ARTIFACT_PATHS, build_run_registry, discover_run_dirs, render_registry_html, summarize_registered_run, write_registry_outputs


def make_run(
    root: Path,
    name: str,
    loss: float,
    quality: str = "pass",
    note: str | None = None,
    tags: list[str] | None = None,
    pair_reports: bool = False,
    pair_generated_delta: int = 5,
    rubric_score: float | None = 92.0,
    rubric_status: str = "pass",
) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "checkpoint.pt").write_bytes(b"fake")
    (run_dir / "train_config.json").write_text(json.dumps({"tokenizer": "char", "max_iters": 2}), encoding="utf-8")
    (run_dir / "history_summary.json").write_text(
        json.dumps({"best_val_loss": loss, "last_val_loss": loss + 0.1}),
        encoding="utf-8",
    )
    (run_dir / "dataset_quality.json").write_text(
        json.dumps({"status": quality, "short_fingerprint": f"{name}12345678", "warning_count": 0}),
        encoding="utf-8",
    )
    if note is not None or tags is not None:
        (run_dir / "run_notes.json").write_text(
            json.dumps({"note": note, "tags": tags or []}, ensure_ascii=False),
            encoding="utf-8",
        )
    eval_dir = run_dir / "eval_suite"
    eval_dir.mkdir()
    (run_dir / "dashboard.html").write_text("<html></html>", encoding="utf-8")
    (eval_dir / "eval_suite.json").write_text(
        json.dumps({"case_count": 3, "avg_unique_chars": 8.5, "results": []}),
        encoding="utf-8",
    )
    quality_dir = run_dir / "generation-quality"
    quality_dir.mkdir()
    (quality_dir / "generation_quality.json").write_text(
        json.dumps(
            {
                "summary": {
                    "overall_status": "pass",
                    "case_count": 3,
                    "pass_count": 3,
                    "warn_count": 0,
                    "fail_count": 0,
                    "avg_unique_ratio": 0.72,
                }
            }
        ),
        encoding="utf-8",
    )
    (quality_dir / "generation_quality.html").write_text("<html></html>", encoding="utf-8")
    if rubric_score is not None:
        scorecard_dir = run_dir / "benchmark-scorecard"
        scorecard_dir.mkdir()
        (scorecard_dir / "benchmark_scorecard.json").write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "summary": {
                        "overall_status": "pass" if rubric_score >= 80 else "warn" if rubric_score >= 60 else "fail",
                        "overall_score": rubric_score,
                        "rubric_status": rubric_status,
                        "rubric_avg_score": rubric_score,
                        "rubric_pass_count": 2 if rubric_status == "pass" else 1,
                        "rubric_warn_count": 0 if rubric_status == "pass" else 1,
                        "rubric_fail_count": 0,
                        "weakest_rubric_case": f"{name}-rubric-weak",
                        "weakest_rubric_score": max(0.0, rubric_score - 18),
                    },
                    "rubric_scores": {
                        "summary": {
                            "case_count": 2,
                            "avg_score": rubric_score,
                            "overall_status": rubric_status,
                            "weakest_case": f"{name}-rubric-weak",
                            "weakest_score": max(0.0, rubric_score - 18),
                        },
                        "cases": [],
                    },
                }
            ),
            encoding="utf-8",
        )
        (scorecard_dir / "benchmark_scorecard.html").write_text("<html></html>", encoding="utf-8")
        (scorecard_dir / "benchmark_scorecard_rubric.csv").write_text("name,score\n", encoding="utf-8")
    if pair_reports:
        pair_batch_dir = run_dir / "pair_batch"
        pair_batch_dir.mkdir()
        (pair_batch_dir / "pair_generation_batch.json").write_text(
            json.dumps(
                {
                    "suite": {"name": "registry-pair-suite", "version": "1"},
                    "left": {"checkpoint_id": "base"},
                    "right": {"checkpoint_id": "wide"},
                    "case_count": 2,
                    "generated_difference_count": 1,
                    "results": [
                        {
                            "name": f"{name}-delta",
                            "task_type": "qa",
                            "difficulty": "medium",
                            "comparison": {
                                "generated_equal": False,
                                "continuation_equal": False,
                                "generated_char_delta": pair_generated_delta,
                                "continuation_char_delta": pair_generated_delta - 1,
                            },
                        },
                        {
                            "name": f"{name}-stable",
                            "task_type": "continuation",
                            "difficulty": "easy",
                            "comparison": {
                                "generated_equal": True,
                                "continuation_equal": True,
                                "generated_char_delta": 0,
                                "continuation_char_delta": 0,
                            },
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        (pair_batch_dir / "pair_generation_batch.html").write_text("<html></html>", encoding="utf-8")
        pair_trend_dir = run_dir / "pair_batch_trend"
        pair_trend_dir.mkdir()
        (pair_trend_dir / "pair_batch_trend.json").write_text(
            json.dumps({"report_count": 2, "changed_generated_equal_cases": 1, "case_trends": []}),
            encoding="utf-8",
        )
        (pair_trend_dir / "pair_batch_trend.html").write_text("<html></html>", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "git": {"short_commit": "abc1234", "dirty": False},
                "training": {"tokenizer": "char", "args": {"max_iters": 2}},
                "data": {
                    "source": {"kind": "data"},
                    "dataset_quality": {"status": quality, "short_fingerprint": f"{name}12345678"},
                },
                "model": {"parameter_count": 1234},
                "results": {"history_summary": {"best_val_loss": loss}},
                "artifacts": [{"key": "checkpoint", "exists": True}, {"key": "metrics", "exists": False}],
            }
        ),
        encoding="utf-8",
    )
    return run_dir


class RegistryTests(unittest.TestCase):
    def test_discover_run_dirs_finds_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = make_run(root, "one", 1.0)
            make_run(root / "nested", "two", 2.0)

            runs = discover_run_dirs(root)

            self.assertIn(one, runs)
            self.assertEqual(len(runs), 2)

    def test_summarize_registered_run_reads_manifest_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), "one", 1.0, quality="warn")

            run = summarize_registered_run(run_dir, name="demo")

            self.assertEqual(run.name, "demo")
            self.assertEqual(run.git_commit, "abc1234")
            self.assertEqual(run.best_val_loss, 1.0)
            self.assertEqual(run.dataset_quality, "warn")
            self.assertEqual(run.eval_suite_cases, 3)
            self.assertEqual(run.generation_quality_status, "pass")
            self.assertEqual(run.generation_quality_cases, 3)
            self.assertEqual(run.benchmark_scorecard_status, "pass")
            self.assertEqual(run.benchmark_scorecard_score, 92.0)
            self.assertEqual(run.benchmark_rubric_status, "pass")
            self.assertEqual(run.benchmark_rubric_avg_score, 92.0)
            self.assertEqual(run.benchmark_weakest_rubric_case, "one-rubric-weak")
            self.assertTrue(run.benchmark_scorecard_html_exists)
            self.assertGreaterEqual(run.artifact_count, 6)
            self.assertIn("dataset_version.json", REGISTRY_ARTIFACT_PATHS)
            self.assertIn("pair_batch/pair_generation_batch.html", REGISTRY_ARTIFACT_PATHS)
            self.assertIn("pair_batch_trend/pair_batch_trend.html", REGISTRY_ARTIFACT_PATHS)
            self.assertIn("benchmark-scorecard/benchmark_scorecard.html", REGISTRY_ARTIFACT_PATHS)

    def test_summarize_registered_run_reads_pair_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), "one", 1.0, pair_reports=True)

            run = summarize_registered_run(run_dir)

            self.assertEqual(run.pair_batch_cases, 2)
            self.assertEqual(run.pair_batch_generated_differences, 1)
            self.assertTrue(run.pair_batch_html_exists)
            self.assertEqual(run.pair_trend_reports, 2)
            self.assertEqual(run.pair_trend_changed_cases, 1)
            self.assertTrue(run.pair_trend_html_exists)

    def test_summarize_registered_run_reads_notes_and_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), "one", 1.0, note="baseline for registry", tags=["baseline", "demo"])

            run = summarize_registered_run(run_dir)

            self.assertEqual(run.note, "baseline for registry")
            self.assertEqual(run.tags, ["baseline", "demo"])

    def test_build_registry_picks_best_and_counts_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_run(root, "a", 1.2, quality="pass", tags=["baseline"], pair_reports=True, rubric_score=94.0)
            run_b = make_run(root, "b", 0.9, quality="warn", tags=["baseline", "candidate"], rubric_score=76.0, rubric_status="warn")

            registry = build_run_registry([run_a, run_b], names=["A", "B"])

            self.assertEqual(registry["run_count"], 2)
            self.assertEqual(registry["best_by_best_val_loss"]["name"], "B")
            self.assertEqual(registry["quality_counts"], {"pass": 1, "warn": 1})
            self.assertEqual(registry["generation_quality_counts"], {"pass": 2})
            self.assertEqual(registry["benchmark_rubric_counts"], {"pass": 1, "warn": 1})
            self.assertEqual(registry["benchmark_rubric_summary"]["best_run"], "A")
            self.assertEqual(registry["benchmark_rubric_summary"]["weakest_run"], "B")
            self.assertEqual(registry["benchmark_rubric_summary"]["regression_count"], 1)
            self.assertEqual(registry["benchmark_rubric_leaderboard"][0]["name"], "A")
            self.assertEqual(registry["runs"][0]["benchmark_rubric_rank"], 1)
            self.assertEqual(registry["runs"][1]["benchmark_rubric_rank"], 2)
            self.assertAlmostEqual(registry["runs"][1]["benchmark_rubric_delta_from_best"], -18.0)
            self.assertEqual(registry["pair_report_counts"], {"pair_batch": 1, "pair_trend": 1})
            self.assertEqual(registry["tag_counts"], {"baseline": 2, "candidate": 1})
            self.assertEqual(registry["pair_delta_summary"]["case_count"], 2)
            self.assertEqual(registry["pair_delta_summary"]["max_abs_generated_char_delta"], 5)
            self.assertEqual(registry["pair_delta_leaderboard"][0]["case"], "a-delta")
            self.assertEqual(registry["loss_leaderboard"][0]["name"], "B")
            self.assertAlmostEqual(registry["loss_leaderboard"][1]["best_val_loss_delta"], 0.3)
            self.assertEqual(registry["runs"][1]["best_val_loss_rank"], 1)
            self.assertTrue(registry["runs"][1]["is_best_val_loss"])
            self.assertEqual(registry["runs"][0]["best_val_loss_rank"], 2)

    def test_pair_delta_leaderboard_aggregates_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_run(root, "a", 1.2, pair_reports=True, pair_generated_delta=4)
            run_b = make_run(root, "b", 0.9, pair_reports=True, pair_generated_delta=-9)

            registry = build_run_registry([run_a, run_b], names=["A", "B"])

            self.assertEqual(registry["pair_delta_summary"]["case_count"], 4)
            self.assertEqual(registry["pair_delta_summary"]["run_count"], 2)
            self.assertEqual(registry["pair_delta_summary"]["max_abs_generated_char_delta"], 9)
            self.assertEqual(registry["pair_delta_summary"]["max_abs_continuation_char_delta"], 10)
            leader = registry["pair_delta_leaderboard"][0]
            self.assertEqual(leader["run_name"], "B")
            self.assertEqual(leader["case"], "b-delta")
            self.assertEqual(leader["generated_char_delta"], -9)
            self.assertEqual(leader["abs_generated_char_delta"], 9)
            self.assertEqual(leader["left_checkpoint_id"], "base")
            self.assertEqual(leader["right_checkpoint_id"], "wide")

    def test_write_registry_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run(root, "one", 1.0, pair_reports=True)
            (run_dir / "experiment_card.html").write_text("<html></html>", encoding="utf-8")
            registry = build_run_registry([run_dir])

            outputs = write_registry_outputs(registry, root / "registry")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("<svg", Path(outputs["svg"]).read_text(encoding="utf-8"))
            self.assertIn("best_val_loss_rank", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("generation_quality_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("benchmark_rubric_avg_score", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("pair_batch_cases", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("+0", Path(outputs["svg"]).read_text(encoding="utf-8"))
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("MiniGPT run registry", html)
            self.assertIn(">card</a>", html)
            self.assertIn(">gen quality</a>", html)
            self.assertIn(">scorecard</a>", html)
            self.assertIn(">pair batch</a>", html)
            self.assertIn(">pair trend</a>", html)
            self.assertIn("Pair Reports", html)
            self.assertIn("Rubric Leaderboard", html)
            self.assertIn("score=92", html)
            self.assertIn("one-rubric-weak", html)
            self.assertIn("batch cases=2 diff=1", html)
            self.assertIn("trend reports=2 changed=1", html)
            self.assertIn("Pair Delta Leaders", html)
            self.assertIn("Abs Gen Delta", html)
            self.assertIn("one-delta", html)
            self.assertIn("<div class=\"label\">Pair deltas</div>", html)
            self.assertIn("../one/pair_batch/pair_generation_batch.json", html)

    def test_render_registry_html_has_interactive_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_run(root, "alpha", 1.2, quality="pass", note="stable baseline", tags=["baseline"])
            run_b = make_run(root, "beta", 0.9, quality="warn", note="needs review", tags=["candidate"])
            registry = build_run_registry([run_a, run_b])

            html = render_registry_html(registry)

            self.assertIn('id="registry-search"', html)
            self.assertIn('id="quality-filter"', html)
            self.assertIn('id="sort-key"', html)
            self.assertIn('id="sort-direction"', html)
            self.assertIn('id="registry-count"', html)
            self.assertIn('id="share-view"', html)
            self.assertIn('id="export-visible-csv"', html)
            self.assertIn('id="registry-status"', html)
            self.assertIn("data-run-row", html)
            self.assertIn("data-rank", html)
            self.assertIn("data-best-val", html)
            self.assertIn("data-delta", html)
            self.assertIn("data-pair", html)
            self.assertIn("<th>Rank</th>", html)
            self.assertIn("#1", html)
            self.assertIn("Loss Leaderboard", html)
            self.assertIn("Pair Delta Leaders", html)
            self.assertIn("<div class=\"label\">Comparable</div>", html)
            self.assertIn('<option value="rank">Rank</option>', html)
            self.assertIn('<option value="delta">Loss Delta</option>', html)
            self.assertIn('<option value="pair">Pair Reports</option>', html)
            self.assertIn('<option value="pass">pass</option>', html)
            self.assertIn('<option value="warn">warn</option>', html)
            self.assertIn("addEventListener", html)
            self.assertIn("URLSearchParams", html)
            self.assertIn("navigator.clipboard.writeText", html)
            self.assertIn("registry-visible-", html)
            self.assertIn("new Blob", html)
            self.assertIn("<th>Notes</th>", html)
            self.assertIn("<th>Gen Quality</th>", html)
            self.assertIn("<th>Rubric</th>", html)
            self.assertIn("<th>Pair Reports</th>", html)
            self.assertIn('<option value="rubric">Rubric</option>', html)
            self.assertIn('class="tag">baseline</span>', html)
            self.assertIn("stable baseline", html)
            self.assertIn("<div class=\"label\">Tags</div>", html)

    def test_render_registry_html_escapes_run_text(self) -> None:
        registry = {
            "run_count": 1,
            "best_by_best_val_loss": {"name": "<best>", "best_val_loss": 1.0},
            "quality_counts": {"pass": 1},
            "dataset_fingerprints": ["abc"],
            "runs": [
                {
                    "name": "<script>",
                    "path": "runs/demo",
                    "best_val_loss": 1.0,
                    "total_parameters": 123,
                    "dataset_quality": "pass",
                    "artifact_count": 3,
                    "note": "<b>note</b>",
                    "tags": ["<tag>"],
                }
            ],
        }

        html = render_registry_html(registry)

        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;note&lt;/b&gt;", html)
        self.assertIn("&lt;tag&gt;", html)
        self.assertIn("<script>", html)
        self.assertNotIn("<strong><script>", html)
        self.assertNotIn('data-search="<script>', html)


if __name__ == "__main__":
    unittest.main()
