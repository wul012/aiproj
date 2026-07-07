from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

LOCAL_ONLY_ENGINEERING_ENTRYPOINTS = ("scripts/check_engineering_health.py",)

HEALTH_ENGINEERING_ENTRYPOINTS = (
    "scripts/check_source_encoding.py",
    "scripts/check_project_docs_readability.py",
    "scripts/check_ci_workflow_hygiene.py",
    "scripts/check_static_analysis.py",
    "scripts/check_type_analysis.py",
    "scripts/check_normalization_guard.py",
)

CI_ENGINEERING_ENTRYPOINTS = HEALTH_ENGINEERING_ENTRYPOINTS + ("scripts/run_test_coverage.py",)

BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS = LOCAL_ONLY_ENGINEERING_ENTRYPOINTS + CI_ENGINEERING_ENTRYPOINTS

FOUNDATION_ACTIVE_CLI_ENTRYPOINTS = (
    "scripts/analyze_generation_quality.py",
    "scripts/chat.py",
    "scripts/compare_runs.py",
    "scripts/eval_suite.py",
    "scripts/evaluate.py",
    "scripts/generate.py",
    "scripts/inspect_attention.py",
    "scripts/inspect_predictions.py",
    "scripts/inspect_tokenizer.py",
    "scripts/plot_history.py",
    "scripts/prepare_dataset.py",
    "scripts/serve_playground.py",
    "scripts/train.py",
)

REPORT_ACTIVE_CLI_ENTRYPOINTS = (
    "scripts/build_dashboard.py",
    "scripts/build_dataset_card.py",
    "scripts/build_experiment_card.py",
    "scripts/build_model_card.py",
    "scripts/inspect_model.py",
)

GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS = (
    "scripts/build_maturity_narrative.py",
    "scripts/build_maturity_summary.py",
    "scripts/build_release_bundle.py",
    "scripts/build_release_readiness.py",
    "scripts/check_release_gate.py",
    "scripts/check_release_readiness_drift_contract.py",
    "scripts/compare_release_gate_profiles.py",
    "scripts/compare_release_readiness.py",
    "scripts/register_runs.py",
)

BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS = (
    FOUNDATION_ACTIVE_CLI_ENTRYPOINTS + REPORT_ACTIVE_CLI_ENTRYPOINTS + GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS
)

CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS = BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS + BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS

SCRIPT_ENTRYPOINT_SURFACES = {
    "LOCAL_ONLY_ENGINEERING_ENTRYPOINTS": LOCAL_ONLY_ENGINEERING_ENTRYPOINTS,
    "HEALTH_ENGINEERING_ENTRYPOINTS": HEALTH_ENGINEERING_ENTRYPOINTS,
    "CI_ENGINEERING_ENTRYPOINTS": CI_ENGINEERING_ENTRYPOINTS,
    "BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS": BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS,
    "FOUNDATION_ACTIVE_CLI_ENTRYPOINTS": FOUNDATION_ACTIVE_CLI_ENTRYPOINTS,
    "REPORT_ACTIVE_CLI_ENTRYPOINTS": REPORT_ACTIVE_CLI_ENTRYPOINTS,
    "GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS": GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS,
    "BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS": BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS,
    "CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS": CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS,
}

SCRIPT_SUPPORT_MODULES = (
    "scripts._bootstrap",
    "scripts._normalization_guard",
    "scripts._engineering_health",
)


def ensure_src_path() -> Path:
    src_path = str(SRC_ROOT)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    return SRC_ROOT


__all__ = [
    "BOOTSTRAPPED_ACTIVE_CLI_ENTRYPOINTS",
    "BOOTSTRAPPED_ENGINEERING_ENTRYPOINTS",
    "CI_ENGINEERING_ENTRYPOINTS",
    "CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS",
    "FOUNDATION_ACTIVE_CLI_ENTRYPOINTS",
    "GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS",
    "HEALTH_ENGINEERING_ENTRYPOINTS",
    "LOCAL_ONLY_ENGINEERING_ENTRYPOINTS",
    "PROJECT_ROOT",
    "REPORT_ACTIVE_CLI_ENTRYPOINTS",
    "SCRIPT_ENTRYPOINT_SURFACES",
    "SCRIPT_SUPPORT_MODULES",
    "SRC_ROOT",
    "ensure_src_path",
]
