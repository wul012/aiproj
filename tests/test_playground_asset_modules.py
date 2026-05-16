from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import playground_assets  # noqa: E402
from minigpt.playground_request_history_script import playground_request_history_script  # noqa: E402
from minigpt.playground_script import playground_script  # noqa: E402
from minigpt.playground_style import playground_style  # noqa: E402


class PlaygroundAssetModuleSplitTests(unittest.TestCase):
    def test_legacy_asset_module_reexports_split_functions(self) -> None:
        self.assertIs(playground_assets.playground_style, playground_style)
        self.assertIs(playground_assets.playground_script, playground_script)
        self.assertEqual(playground_assets.__all__, ["playground_script", "playground_style"])

    def test_style_module_keeps_static_layout_contract(self) -> None:
        style = playground_style()

        self.assertTrue(style.startswith("<style>"))
        self.assertTrue(style.endswith("</style>"))
        self.assertIn(".builder", style)
        self.assertIn(".pair-grid", style)
        self.assertIn("@media (max-width: 760px)", style)

    def test_script_module_serializes_page_data_and_live_endpoints(self) -> None:
        page_data = {
            "runDir": "runs/demo",
            "defaults": {"prompt": "中文 prompt", "max_new_tokens": 4, "temperature": 0.8, "top_k": 30, "seed": 7},
            "commands": {},
            "checkpoints": [{"id": "ckpt-a", "path": "runs/demo/checkpoint.pt", "exists": True}],
            "checkpointComparison": [],
            "requestHistory": [],
            "requestHistoryDetail": None,
            "requestHistoryFilters": {"status": "", "endpoint": "", "checkpoint": "", "limit": 12},
            "streamController": None,
        }

        script = playground_script(page_data)

        self.assertTrue(script.startswith("<script>"))
        self.assertTrue(script.endswith("</script>"))
        self.assertIn('"prompt": "中文 prompt"', script)
        self.assertIn("/api/generate-stream", script)
        self.assertIn("/api/request-history-detail", script)
        self.assertIn("/api/generate-pair-artifact", script)
        self.assertIn(playground_request_history_script(), script)


if __name__ == "__main__":
    unittest.main()
