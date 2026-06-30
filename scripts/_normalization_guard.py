from __future__ import annotations

import sys
from collections.abc import Iterable

FOCUSED_TEST_MODULES = (
    "tests.test_architecture_boundaries",
    "tests.test_script_import_boundaries",
    "tests.test_public_api_policy",
    "tests.test_foundation_package_reexports",
    "tests.test_evidence_package_reexports",
    "tests.test_engineering_health",
    "tests.test_report_utils",
    "tests.test_report_utils_helpers",
    "tests.test_source_encoding_hygiene",
    "tests.test_ci_workflow",
    "tests.test_test_coverage_report",
    "tests.test_project_configuration",
    "tests.test_repository_hygiene",
    "tests.test_script_bootstrap",
    "tests.test_script_bootstrap_helpers",
    "tests.test_script_surface_registry",
    "tests.test_script_cli_contracts",
    "tests.test_active_cli_coverage",
    "tests.test_active_cli_behavior",
    "tests.test_model_cli_behavior",
    "tests.test_serving_cli_behavior",
    "tests.test_report_cli_behavior",
    "tests.test_governance_cli_behavior",
    "tests.test_governance_extended_cli_behavior",
    "tests.test_project_docs_readability",
)


def build_command(*, python_executable: str = sys.executable) -> list[str]:
    return [python_executable, "-B", "-m", "unittest", *FOCUSED_TEST_MODULES]


def focused_test_paths(*, exclude_modules: Iterable[str] = ()) -> tuple[str, ...]:
    excluded = set(exclude_modules)
    return tuple(
        module.replace(".", "/") + ".py"
        for module in FOCUSED_TEST_MODULES
        if module not in excluded
    )


__all__ = ["FOCUSED_TEST_MODULES", "build_command", "focused_test_paths"]
