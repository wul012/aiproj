from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry import build_run_registry as facade_build_run_registry
from minigpt.registry import render_registry_html as facade_render_registry_html
from minigpt.registry_data import build_run_registry, discover_run_dirs, summarize_registered_run
from minigpt.registry_render import render_registry_html, write_registry_outputs
from tests.test_registry import make_run


class RegistrySplitTests(unittest.TestCase):
    def test_data_module_builds_registry_without_render_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_run(root, "alpha", 1.2, tags=["baseline"], pair_reports=True)
            run_b = make_run(root, "beta", 0.8, tags=["candidate"], readiness_trend="improved")

            registry = build_run_registry([run_a, run_b], names=["A", "B"])

            self.assertEqual(registry["run_count"], 2)
            self.assertEqual(registry["best_by_best_val_loss"]["name"], "B")
            self.assertEqual(registry["pair_report_counts"], {"pair_batch": 1, "pair_trend": 1})
            self.assertEqual(registry["release_readiness_comparison_counts"], {"improved": 1, "missing": 1})
            self.assertEqual(discover_run_dirs(root), [run_a, run_b])
            self.assertEqual(summarize_registered_run(run_a).name, "alpha")

    def test_render_module_writes_outputs_from_data_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run(root, "alpha", 1.0, tags=["baseline"], pair_reports=True)
            registry = build_run_registry([run_dir])

            outputs = write_registry_outputs(registry, root / "registry")
            html = render_registry_html(registry, base_dir=root / "registry")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["svg"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("MiniGPT run registry", html)
            self.assertIn("Pair Delta Leaders", html)

    def test_registry_facade_keeps_public_api_identity(self) -> None:
        self.assertIs(facade_build_run_registry, build_run_registry)
        self.assertIs(facade_render_registry_html, render_registry_html)


if __name__ == "__main__":
    unittest.main()
