from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry import build_run_registry, discover_run_dirs, render_registry_html, summarize_registered_run, write_registry_outputs


def make_run(root: Path, name: str, loss: float, quality: str = "pass", note: str | None = None, tags: list[str] | None = None) -> Path:
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
            self.assertGreaterEqual(run.artifact_count, 6)

    def test_summarize_registered_run_reads_notes_and_tags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), "one", 1.0, note="baseline for registry", tags=["baseline", "demo"])

            run = summarize_registered_run(run_dir)

            self.assertEqual(run.note, "baseline for registry")
            self.assertEqual(run.tags, ["baseline", "demo"])

    def test_build_registry_picks_best_and_counts_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_run(root, "a", 1.2, quality="pass", tags=["baseline"])
            run_b = make_run(root, "b", 0.9, quality="warn", tags=["baseline", "candidate"])

            registry = build_run_registry([run_a, run_b], names=["A", "B"])

            self.assertEqual(registry["run_count"], 2)
            self.assertEqual(registry["best_by_best_val_loss"]["name"], "B")
            self.assertEqual(registry["quality_counts"], {"pass": 1, "warn": 1})
            self.assertEqual(registry["tag_counts"], {"baseline": 2, "candidate": 1})
            self.assertEqual(registry["loss_leaderboard"][0]["name"], "B")
            self.assertAlmostEqual(registry["loss_leaderboard"][1]["best_val_loss_delta"], 0.3)
            self.assertEqual(registry["runs"][1]["best_val_loss_rank"], 1)
            self.assertTrue(registry["runs"][1]["is_best_val_loss"])
            self.assertEqual(registry["runs"][0]["best_val_loss_rank"], 2)

    def test_write_registry_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run(root, "one", 1.0)
            (run_dir / "experiment_card.html").write_text("<html></html>", encoding="utf-8")
            registry = build_run_registry([run_dir])

            outputs = write_registry_outputs(registry, root / "registry")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("<svg", Path(outputs["svg"]).read_text(encoding="utf-8"))
            self.assertIn("best_val_loss_rank", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("+0", Path(outputs["svg"]).read_text(encoding="utf-8"))
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("MiniGPT run registry", html)
            self.assertIn(">card</a>", html)

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
            self.assertIn("<th>Rank</th>", html)
            self.assertIn("#1", html)
            self.assertIn("Loss Leaderboard", html)
            self.assertIn("<div class=\"label\">Comparable</div>", html)
            self.assertIn('<option value="rank">Rank</option>', html)
            self.assertIn('<option value="delta">Loss Delta</option>', html)
            self.assertIn('<option value="pass">pass</option>', html)
            self.assertIn('<option value="warn">warn</option>', html)
            self.assertIn("addEventListener", html)
            self.assertIn("URLSearchParams", html)
            self.assertIn("navigator.clipboard.writeText", html)
            self.assertIn("registry-visible-", html)
            self.assertIn("new Blob", html)
            self.assertIn("<th>Notes</th>", html)
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
