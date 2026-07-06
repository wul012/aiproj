from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.ci_workflow_hygiene import build_ci_workflow_hygiene_report, write_ci_workflow_hygiene_outputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MiniGPT CI workflow hygiene.")
    parser.add_argument("--workflow", type=Path, default=ROOT / ".github" / "workflows" / "ci.yml")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "ci-workflow-hygiene")
    parser.add_argument("--title", type=str, default="MiniGPT CI workflow hygiene")
    parser.add_argument("--no-fail", action="store_true", help="Write the report without returning a non-zero status.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_ci_workflow_hygiene_report(args.workflow, project_root=ROOT, title=args.title)
    outputs = write_ci_workflow_hygiene_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={summary['status']}")
    print(f"decision={summary['decision']}")
    print(f"check_count={summary['check_count']}")
    print(f"passed_check_count={summary['passed_check_count']}")
    print(f"failed_check_count={summary['failed_check_count']}")
    print(f"action_count={summary['action_count']}")
    print(f"node24_native_action_count={summary['node24_native_action_count']}")
    print(f"forbidden_env_count={summary['forbidden_env_count']}")
    print(f"missing_step_count={summary['missing_step_count']}")
    print(f"required_order_count={summary['required_order_count']}")
    print(f"order_violation_count={summary['order_violation_count']}")
    print(f"release_readiness_drift_contract_smoke_present={summary['release_readiness_drift_contract_smoke_present']}")
    print(
        f"release_readiness_drift_contract_smoke_order_ready={summary['release_readiness_drift_contract_smoke_order_ready']}"
    )
    print(f"release_readiness_drift_contract_smoke_ready={summary['release_readiness_drift_contract_smoke_ready']}")
    print(
        f"baseline_candidate_threshold_boundary_gate_check_present={summary['baseline_candidate_threshold_boundary_gate_check_present']}"
    )
    print(
        f"baseline_candidate_threshold_boundary_gate_check_order_ready={summary['baseline_candidate_threshold_boundary_gate_check_order_ready']}"
    )
    print(
        f"baseline_candidate_threshold_boundary_gate_check_ready={summary['baseline_candidate_threshold_boundary_gate_check_ready']}"
    )
    print(
        f"baseline_candidate_threshold_boundary_gate_plan_check_present={summary['baseline_candidate_threshold_boundary_gate_plan_check_present']}"
    )
    print(
        f"baseline_candidate_threshold_boundary_gate_plan_check_order_ready={summary['baseline_candidate_threshold_boundary_gate_plan_check_order_ready']}"
    )
    print(
        f"baseline_candidate_threshold_boundary_gate_plan_check_ready={summary['baseline_candidate_threshold_boundary_gate_plan_check_ready']}"
    )
    print(f"archived_path_portability_check_present={summary['archived_path_portability_check_present']}")
    print(f"archived_path_portability_check_order_ready={summary['archived_path_portability_check_order_ready']}")
    print(f"archived_path_portability_check_ready={summary['archived_path_portability_check_ready']}")
    print(
        f"promoted_seed_receipt_contract_failure_smoke_present={summary['promoted_seed_receipt_contract_failure_smoke_present']}"
    )
    print(
        f"promoted_seed_receipt_contract_failure_smoke_order_ready={summary['promoted_seed_receipt_contract_failure_smoke_order_ready']}"
    )
    print(
        f"promoted_seed_receipt_contract_failure_smoke_ready={summary['promoted_seed_receipt_contract_failure_smoke_ready']}"
    )
    print(
        f"promoted_seed_receipt_contract_failure_smoke_plan_check_present={summary['promoted_seed_receipt_contract_failure_smoke_plan_check_present']}"
    )
    print(
        f"promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready={summary['promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready']}"
    )
    print(
        f"promoted_seed_receipt_contract_failure_smoke_plan_check_ready={summary['promoted_seed_receipt_contract_failure_smoke_plan_check_ready']}"
    )
    print(f"project_docs_readability_present={summary['project_docs_readability_present']}")
    print(f"project_docs_readability_order_ready={summary['project_docs_readability_order_ready']}")
    print(f"project_docs_readability_ready={summary['project_docs_readability_ready']}")
    print(f"static_analysis_present={summary['static_analysis_present']}")
    print(f"static_analysis_order_ready={summary['static_analysis_order_ready']}")
    print(f"static_analysis_ready={summary['static_analysis_ready']}")
    print(f"normalization_guard_present={summary['normalization_guard_present']}")
    print(f"normalization_guard_order_ready={summary['normalization_guard_order_ready']}")
    print(f"normalization_guard_ready={summary['normalization_guard_ready']}")
    print(f"python_version={summary['python_version']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if summary["status"] != "pass" and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
