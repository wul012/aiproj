from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dashboard import build_dashboard_payload, collect_artifacts, render_dashboard_html, write_dashboard


class DashboardTests(unittest.TestCase):
    def test_collect_artifacts_marks_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")

            artifacts = collect_artifacts(run_dir, run_dir)

            checkpoint = next(artifact for artifact in artifacts if artifact.key == "checkpoint")
            self.assertTrue(checkpoint.exists)
            self.assertEqual(checkpoint.href, "checkpoint.pt")

    def test_build_payload_reads_summary_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "train_config.json").write_text(json.dumps({"tokenizer": "char", "max_iters": 2}), encoding="utf-8")
            (run_dir / "history_summary.json").write_text(json.dumps({"best_val_loss": 1.25}), encoding="utf-8")
            (run_dir / "eval_report.json").write_text(json.dumps({"loss": 1.5, "perplexity": 4.48}), encoding="utf-8")
            model_dir = run_dir / "model_report"
            model_dir.mkdir()
            (model_dir / "model_report.json").write_text(
                json.dumps({"total_parameters": 123, "config": {"n_layer": 1}, "owned_parameter_groups": []}),
                encoding="utf-8",
            )

            payload = build_dashboard_payload(run_dir)

            self.assertEqual(payload["summary"]["tokenizer"], "char")
            self.assertEqual(payload["summary"]["best_val_loss"], 1.25)
            self.assertEqual(payload["summary"]["total_parameters"], 123)

    def test_render_dashboard_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "sample.txt").write_text("<script>alert(1)</script>", encoding="utf-8")

            payload = build_dashboard_payload(run_dir, title="<MiniGPT>")
            html = render_dashboard_html(payload)

            self.assertIn("&lt;MiniGPT&gt;", html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertNotIn("<script>alert(1)</script>", html)

    def test_write_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "sample.txt").write_text("hello", encoding="utf-8")
            out_path = run_dir / "dashboard.html"

            payload = write_dashboard(run_dir, output_path=out_path)

            self.assertTrue(out_path.exists())
            self.assertIn("MiniGPT experiment dashboard", out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["output_path"], str(out_path))

    def test_invalid_json_adds_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "eval_report.json").write_text("{broken", encoding="utf-8")

            payload = build_dashboard_payload(run_dir)

            self.assertTrue(payload["warnings"])


if __name__ == "__main__":
    unittest.main()
