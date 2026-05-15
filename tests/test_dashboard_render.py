from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import dashboard
from minigpt import dashboard_render


class DashboardRenderSplitTests(unittest.TestCase):
    def test_render_module_renders_dashboard_payload(self) -> None:
        payload = {
            "title": "MiniGPT <dashboard>",
            "run_dir": "runs/demo",
            "summary": {
                "available_artifacts": 1,
                "metrics_records": 3,
                "tokenizer": "char",
                "max_iters": 5,
                "best_val_loss": 1.25,
                "eval_loss": 1.5,
                "perplexity": 4.48,
                "eval_suite_cases": 2,
                "pair_batch_cases": 1,
                "pair_trend_reports": 1,
                "dataset_quality": "pass",
                "git_commit": "abc1234",
                "total_parameters": 123456,
            },
            "artifacts": [
                {
                    "key": "sample",
                    "title": "Sample text",
                    "path": "runs/demo/sample.txt",
                    "kind": "TXT",
                    "description": "sample output",
                    "exists": True,
                    "size_bytes": 12,
                    "href": "sample.txt",
                }
            ],
            "sample_text": "<script>alert(1)</script>",
            "generated_text": "hello",
            "warnings": ["watch <html> escaping"],
        }

        html = dashboard_render.render_dashboard_html(payload)

        self.assertIn("MiniGPT &lt;dashboard&gt;", html)
        self.assertIn("sample.txt", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("watch &lt;html&gt; escaping", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_dashboard_module_keeps_legacy_render_export(self) -> None:
        self.assertIs(dashboard.render_dashboard_html, dashboard_render.render_dashboard_html)

    def test_write_dashboard_uses_render_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "sample.txt").write_text("hello <world>", encoding="utf-8")
            out_path = run_dir / "dashboard.html"

            dashboard.write_dashboard(run_dir, output_path=out_path, title="Demo <dash>")

            html = out_path.read_text(encoding="utf-8")
            self.assertIn("Demo &lt;dash&gt;", html)
            self.assertIn("hello &lt;world&gt;", html)


if __name__ == "__main__":
    unittest.main()
