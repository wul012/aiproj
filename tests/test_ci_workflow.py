from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class CIWorkflowTests(unittest.TestCase):
    def test_ci_opts_into_node24_action_runtime(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24", workflow)
        self.assertIn('FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"', workflow)
        self.assertIn("actions/checkout@v4", workflow)
        self.assertIn("actions/setup-python@v5", workflow)


if __name__ == "__main__":
    unittest.main()
