from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.playground import render_playground_html  # noqa: E402
from minigpt.playground_assets import playground_script, playground_style  # noqa: E402


class PlaygroundAssetsTests(unittest.TestCase):
    def test_playground_style_contains_layout_contracts(self) -> None:
        style = playground_style()

        self.assertTrue(style.startswith("<style>"))
        self.assertTrue(style.endswith("</style>"))
        self.assertIn("--ink: #172033", style)
        self.assertIn(".builder", style)
        self.assertIn(".pair-grid", style)
        self.assertIn(".status-pill.timeout", style)
        self.assertIn("@media (max-width: 760px)", style)

    def test_playground_script_contains_interaction_contracts(self) -> None:
        page_data = {
            "runDir": "runs/demo",
            "defaults": {"prompt": "abc", "max_new_tokens": 4, "temperature": 0.8, "top_k": 30, "seed": 7},
            "commands": {},
            "checkpoints": [],
            "checkpointComparison": [],
            "requestHistory": [],
            "requestHistoryDetail": None,
            "requestHistoryFilters": {"status": "", "endpoint": "", "checkpoint": "", "limit": 12},
            "streamController": None,
        }

        script = playground_script(page_data)

        self.assertTrue(script.startswith("<script>"))
        self.assertTrue(script.endswith("</script>"))
        self.assertIn('const MiniGPTPlayground = {"runDir": "runs/demo"', script)
        self.assertIn("/api/checkpoints", script)
        self.assertIn("/api/generate-stream", script)
        self.assertIn("AbortController", script)
        self.assertIn("requestHistoryQuery", script)
        self.assertIn("/api/request-history-detail", script)
        self.assertIn("/api/checkpoint-compare", script)
        self.assertIn("/api/generate-pair-artifact", script)
        self.assertIn("window.addEventListener('DOMContentLoaded'", script)

    def test_render_playground_html_uses_extracted_assets(self) -> None:
        payload = {
            "title": "Asset Split",
            "run_dir": "runs/demo",
            "summary": {
                "available_artifacts": 0,
                "playground_links": 0,
                "metrics_records": 0,
                "tokenizer": "char",
                "best_val_loss": None,
                "sampling_cases": 0,
            },
            "defaults": {"prompt": "abc", "max_new_tokens": 4, "temperature": 0.8, "top_k": 30, "seed": 7},
            "commands": {},
            "links": [],
            "sampling_report": None,
            "warnings": [],
        }

        html = render_playground_html(payload)

        self.assertIn(playground_style(), html)
        self.assertIn("MiniGPTPlayground", html)
        self.assertIn("runs/demo", html)
        self.assertIn("Stream Generate", html)


if __name__ == "__main__":
    unittest.main()
