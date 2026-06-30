from __future__ import annotations

import unittest
from pathlib import Path

from scripts._bootstrap import (
    BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS,
    FOUNDATION_ACTIVE_CLI_ENTRYPOINTS,
    GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS,
    PROJECT_ROOT,
    REPORT_ACTIVE_CLI_ENTRYPOINTS,
)
from scripts._normalization_guard import FOCUSED_TEST_MODULES
from tests._bootstrap import ROOT
from tests.test_script_import_boundaries import (
    FOUNDATION_SCRIPT_IMPORTS,
    GOVERNANCE_SCRIPT_IMPORTS,
    REPORT_SCRIPT_IMPORTS,
)

FOUNDATION_DATA_ACTIVE_CLI_ENTRYPOINTS = (
    "scripts/analyze_generation_quality.py",
    "scripts/compare_runs.py",
    "scripts/inspect_tokenizer.py",
    "scripts/plot_history.py",
    "scripts/prepare_dataset.py",
)

FOUNDATION_MODEL_ACTIVE_CLI_ENTRYPOINTS = (
    "scripts/chat.py",
    "scripts/eval_suite.py",
    "scripts/evaluate.py",
    "scripts/generate.py",
    "scripts/inspect_attention.py",
    "scripts/inspect_predictions.py",
    "scripts/train.py",
)

FOUNDATION_SERVING_ACTIVE_CLI_ENTRYPOINTS = (
    "scripts/serve_playground.py",
)

ACTIVE_CLI_BEHAVIOR_COVERAGE = {
    "tests.test_active_cli_behavior": FOUNDATION_DATA_ACTIVE_CLI_ENTRYPOINTS,
    "tests.test_model_cli_behavior": FOUNDATION_MODEL_ACTIVE_CLI_ENTRYPOINTS,
    "tests.test_serving_cli_behavior": FOUNDATION_SERVING_ACTIVE_CLI_ENTRYPOINTS,
    "tests.test_report_cli_behavior": REPORT_ACTIVE_CLI_ENTRYPOINTS,
    "tests.test_governance_cli_behavior": (
        "scripts/build_release_bundle.py",
        "scripts/build_release_readiness.py",
        "scripts/check_release_gate.py",
        "scripts/register_runs.py",
    ),
    "tests.test_governance_extended_cli_behavior": (
        "scripts/build_maturity_narrative.py",
        "scripts/build_maturity_summary.py",
        "scripts/check_release_readiness_drift_contract.py",
        "scripts/compare_release_gate_profiles.py",
        "scripts/compare_release_readiness.py",
    ),
}


class ActiveCliCoverageTests(unittest.TestCase):
    def test_active_cli_entrypoints_cover_import_boundary_scripts(self) -> None:
        boundary_scripts = (
            set(REPORT_SCRIPT_IMPORTS)
            | set(FOUNDATION_SCRIPT_IMPORTS)
            | set(GOVERNANCE_SCRIPT_IMPORTS)
        )

        self.assertEqual(PROJECT_ROOT, ROOT)
        self.assertEqual(boundary_scripts, set(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS))

    def test_active_cli_entrypoint_groups_are_partitioned(self) -> None:
        groups = (
            set(FOUNDATION_ACTIVE_CLI_ENTRYPOINTS),
            set(REPORT_ACTIVE_CLI_ENTRYPOINTS),
            set(GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS),
        )

        self.assertFalse(groups[0] & groups[1])
        self.assertFalse(groups[0] & groups[2])
        self.assertFalse(groups[1] & groups[2])
        self.assertEqual(set(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS), set().union(*groups))
        self.assertEqual(
            BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS,
            FOUNDATION_ACTIVE_CLI_ENTRYPOINTS
            + REPORT_ACTIVE_CLI_ENTRYPOINTS
            + GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS,
        )
        self.assertIn("scripts/train.py", FOUNDATION_ACTIVE_CLI_ENTRYPOINTS)
        self.assertIn("scripts/inspect_model.py", REPORT_ACTIVE_CLI_ENTRYPOINTS)
        self.assertIn("scripts/check_release_gate.py", GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS)

    def test_active_cli_entrypoints_have_behavior_coverage_assignment(self) -> None:
        assigned: list[str] = []
        for module, entrypoints in ACTIVE_CLI_BEHAVIOR_COVERAGE.items():
            with self.subTest(module=module):
                self.assertIn(module, FOCUSED_TEST_MODULES)
                self.assertEqual(len(entrypoints), len(set(entrypoints)))
                self.assertTrue((PROJECT_ROOT / (module.replace(".", "/") + ".py")).is_file())
            assigned.extend(entrypoints)

        self.assertEqual(set(BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS), set(assigned))
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertEqual(
            set(GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS),
            set(ACTIVE_CLI_BEHAVIOR_COVERAGE["tests.test_governance_cli_behavior"])
            | set(ACTIVE_CLI_BEHAVIOR_COVERAGE["tests.test_governance_extended_cli_behavior"]),
        )
        self.assertEqual(
            set(FOUNDATION_ACTIVE_CLI_ENTRYPOINTS),
            set(ACTIVE_CLI_BEHAVIOR_COVERAGE["tests.test_active_cli_behavior"])
            | set(ACTIVE_CLI_BEHAVIOR_COVERAGE["tests.test_model_cli_behavior"])
            | set(ACTIVE_CLI_BEHAVIOR_COVERAGE["tests.test_serving_cli_behavior"]),
        )

        for module, entrypoints in ACTIVE_CLI_BEHAVIOR_COVERAGE.items():
            text = (PROJECT_ROOT / (module.replace(".", "/") + ".py")).read_text(encoding="utf-8")
            for relative in entrypoints:
                with self.subTest(module=module, relative=relative):
                    self.assertIn(Path(relative).stem, text)


if __name__ == "__main__":
    unittest.main()
