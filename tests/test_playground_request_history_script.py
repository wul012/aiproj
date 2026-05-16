from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.playground_request_history_script import playground_request_history_script  # noqa: E402


class PlaygroundRequestHistoryScriptTests(unittest.TestCase):
    def test_request_history_script_contains_endpoint_contracts(self) -> None:
        script = playground_request_history_script()

        self.assertIn("function requestHistoryQuery", script)
        self.assertIn("/api/request-history?", script)
        self.assertIn("/api/request-history-detail?log_index=", script)
        self.assertIn("request_history_${logIndex}.json", script)
        self.assertIn("renderRequestHistory", script)
        self.assertIn("showRequestHistoryDetail", script)

    def test_request_history_script_is_plain_javascript_fragment(self) -> None:
        script = playground_request_history_script()

        self.assertNotIn("{{", script)
        self.assertNotIn("}}", script)
        self.assertNotIn("<script>", script)
        self.assertNotIn("</script>", script)
        self.assertTrue(script.lstrip().startswith("function requestCheckpointLabel"))
        self.assertTrue(script.rstrip().endswith("}"))


if __name__ == "__main__":
    unittest.main()
