from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

REPORT_SCRIPT_IMPORTS = {
    "scripts/build_dashboard.py": "minigpt.reports.dashboard",
    "scripts/build_dataset_card.py": "minigpt.reports.cards",
    "scripts/build_experiment_card.py": "minigpt.reports.cards",
    "scripts/build_model_card.py": "minigpt.reports.cards",
    "scripts/inspect_model.py": "minigpt.reports.model",
    "scripts/train.py": "minigpt.reports.manifest",
}

FOUNDATION_SCRIPT_IMPORTS = {
    "scripts/prepare_dataset.py": {"minigpt.training.data_prep"},
    "scripts/eval_suite.py": {"minigpt.core.model", "minigpt.core.tokenizer", "minigpt.evaluation.suite"},
    "scripts/evaluate.py": {"minigpt.core.dataset", "minigpt.core.model", "minigpt.core.tokenizer", "minigpt.evaluation.prediction"},
    "scripts/compare_runs.py": {"minigpt.evaluation.comparison"},
    "scripts/analyze_generation_quality.py": {"minigpt.evaluation.generation_quality"},
    "scripts/generate.py": {"minigpt.serving.contracts", "minigpt.serving.generator", "minigpt.serving.profiles"},
    "scripts/chat.py": {"minigpt.core.model", "minigpt.core.tokenizer", "minigpt.serving.chat"},
    "scripts/serve_playground.py": {"minigpt.serving", "minigpt.serving.server"},
    "scripts/inspect_tokenizer.py": {"minigpt.core.dataset", "minigpt.core.tokenizer"},
    "scripts/inspect_model.py": {"minigpt.core.model", "minigpt.core.tokenizer", "minigpt.reports.model"},
    "scripts/inspect_attention.py": {"minigpt.core.model", "minigpt.core.tokenizer"},
    "scripts/inspect_predictions.py": {"minigpt.core.model", "minigpt.core.tokenizer", "minigpt.evaluation.prediction"},
    "scripts/plot_history.py": {"minigpt.core.history"},
    "scripts/train.py": {
        "minigpt.core.dataset",
        "minigpt.core.model",
        "minigpt.core.tokenizer",
        "minigpt.training.data_prep",
        "minigpt.training.data_quality",
        "minigpt.training.history",
        "minigpt.reports.manifest",
    },
}

GOVERNANCE_SCRIPT_IMPORTS = {
    "scripts/build_release_bundle.py": "minigpt.governance.release",
    "scripts/build_release_readiness.py": "minigpt.governance.release",
    "scripts/check_release_gate.py": "minigpt.governance.release",
    "scripts/compare_release_gate_profiles.py": "minigpt.governance.release",
    "scripts/compare_release_readiness.py": "minigpt.governance.release",
    "scripts/check_release_readiness_drift_contract.py": "minigpt.governance.release",
    "scripts/build_maturity_summary.py": "minigpt.governance.maturity",
    "scripts/build_maturity_narrative.py": "minigpt.governance.maturity",
    "scripts/register_runs.py": "minigpt.governance.registry",
}

PROHIBITED_ROOT_FACADE_IMPORTS = {
    "minigpt",
}

PROHIBITED_FLAT_MODULES = {
    "minigpt.artifact_map",
    "minigpt.chat",
    "minigpt.dashboard",
    "minigpt.comparison",
    "minigpt.data_prep",
    "minigpt.data_quality",
    "minigpt.dataset",
    "minigpt.dataset_card",
    "minigpt.eval_suite",
    "minigpt.eval_suites",
    "minigpt.experiment_card",
    "minigpt.generation_quality",
    "minigpt.generation_profiles",
    "minigpt.history",
    "minigpt.lm_training",
    "minigpt.manifest",
    "minigpt.maturity",
    "minigpt.maturity_narrative",
    "minigpt.model",
    "minigpt.model_card",
    "minigpt.model_report",
    "minigpt.prediction",
    "minigpt.registry",
    "minigpt.release_bundle",
    "minigpt.release_gate",
    "minigpt.release_gate_comparison",
    "minigpt.release_readiness",
    "minigpt.release_readiness_comparison",
    "minigpt.release_readiness_drift_contract",
    "minigpt.server",
    "minigpt.server_contracts",
    "minigpt.server_generator",
    "minigpt.tokenizer",
}


def imports_for(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.append(node.module)
    return imports


def prohibited_import_messages(relative: str, imports: list[str]) -> list[str]:
    messages = []
    for module in imports:
        if module in PROHIBITED_ROOT_FACADE_IMPORTS:
            messages.append(f"{relative} still imports root facade {module}")
        if module in PROHIBITED_FLAT_MODULES:
            messages.append(f"{relative} still imports flat module {module}")
    return messages


class ScriptImportBoundaryTests(unittest.TestCase):
    def test_active_report_scripts_use_reports_owner_package(self) -> None:
        violations = []
        for relative, expected in REPORT_SCRIPT_IMPORTS.items():
            imports = imports_for(ROOT / relative)
            if expected not in imports:
                violations.append(f"{relative} does not import {expected}")
            violations.extend(prohibited_import_messages(relative, imports))

        self.assertEqual([], violations)

    def test_active_foundation_scripts_use_owner_packages(self) -> None:
        violations = []
        for relative, expected_modules in FOUNDATION_SCRIPT_IMPORTS.items():
            imports = imports_for(ROOT / relative)
            for expected in expected_modules:
                if expected not in imports:
                    violations.append(f"{relative} does not import {expected}")
            violations.extend(prohibited_import_messages(relative, imports))

        self.assertEqual([], violations)

    def test_active_governance_scripts_use_governance_owner_package(self) -> None:
        violations = []
        for relative, expected in GOVERNANCE_SCRIPT_IMPORTS.items():
            imports = imports_for(ROOT / relative)
            if expected not in imports:
                violations.append(f"{relative} does not import {expected}")
            violations.extend(prohibited_import_messages(relative, imports))

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
