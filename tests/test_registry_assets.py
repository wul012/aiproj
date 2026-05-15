from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry import render_registry_html  # noqa: E402
from minigpt.registry_assets import registry_script, registry_style  # noqa: E402


class RegistryAssetsTests(unittest.TestCase):
    def test_registry_style_contains_expected_layout_contracts(self) -> None:
        style = registry_style()

        self.assertTrue(style.startswith("<style>"))
        self.assertTrue(style.endswith("</style>"))
        self.assertIn("--ink:#111827", style)
        self.assertIn(".toolbar", style)
        self.assertIn(".leaderboard", style)
        self.assertIn("@media (max-width:760px)", style)

    def test_registry_script_contains_interaction_contracts(self) -> None:
        script = registry_script()

        self.assertTrue(script.startswith("<script>"))
        self.assertTrue(script.endswith("</script>"))
        self.assertIn('document.getElementById("registry-search")', script)
        self.assertIn('document.getElementById("quality-filter")', script)
        self.assertIn('document.getElementById("sort-key")', script)
        self.assertIn('new Set(["rank", "bestVal", "delta", "params", "artifacts", "rubric", "pair", "readiness", "eval"])', script)
        self.assertIn("URLSearchParams", script)
        self.assertIn("navigator.clipboard.writeText", script)
        self.assertIn("registry-visible-", script)
        self.assertIn("new Blob", script)

    def test_render_registry_html_uses_extracted_assets(self) -> None:
        registry = {
            "run_count": 0,
            "best_by_best_val_loss": None,
            "quality_counts": {},
            "dataset_fingerprints": [],
            "runs": [],
        }

        html = render_registry_html(registry)

        self.assertIn(registry_style(), html)
        self.assertIn(registry_script(), html)


if __name__ == "__main__":
    unittest.main()
