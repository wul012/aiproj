from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    build_promoted_training_scale_seed_handoff_automation_receipt,
    build_promoted_training_scale_seed_handoff,
    write_promoted_training_scale_seed_handoff_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_assurance import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_assurance,
    render_promoted_training_scale_seed_handoff_assurance_check,
    write_promoted_training_scale_seed_handoff_assurance_check_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_receipt import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_embedded_receipt_check,
    check_promoted_training_scale_seed_handoff_automation_receipt,
    load_promoted_training_scale_seed_handoff_automation_receipt,
    load_promoted_training_scale_seed_handoff_report,
    render_promoted_training_scale_seed_handoff_embedded_receipt_check,
    render_promoted_training_scale_seed_handoff_automation_receipt_check,
    write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs,
    write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or execute a MiniGPT promoted training scale seed plan command.")
    parser.add_argument("seed", type=Path, help="promoted_training_scale_seed.json file or seed directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <seed>/handoff")
    parser.add_argument("--execute", action="store_true", help="Run the generated next-cycle plan command. Default only validates it.")
    parser.add_argument("--no-allow-review", action="store_true", help="Block review-status seeds instead of allowing their plan command.")
    parser.add_argument(
        "--require-clean-evidence",
        action="store_true",
        help="Exit non-zero unless the seed handoff clean-evidence readiness is true.",
    )
    parser.add_argument(
        "--require-clean-batch-review",
        action="store_true",
        help="Exit non-zero unless selected clean-required handoff batch-review evidence is clean.",
    )
    parser.add_argument(
        "--receipt-check-out-dir",
        type=Path,
        default=None,
        help="Optional directory for validating the generated automation receipt and writing check JSON/text outputs.",
    )
    parser.add_argument(
        "--embedded-receipt-check-out-dir",
        type=Path,
        default=None,
        help=(
            "Optional directory for validating embedded receipt-check fields and referenced receipt/check sidecars. "
            "Requires --receipt-check-out-dir."
        ),
    )
    parser.add_argument(
        "--assurance-out-dir",
        type=Path,
        default=None,
        help=(
            "Optional directory for validating the final handoff report, embedded receipt-check fields, "
            "and embedded receipt-check sidecars. Requires --embedded-receipt-check-out-dir."
        ),
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--title", type=str, default="MiniGPT promoted training scale seed handoff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_path = Path(args.seed)
    out_dir = args.out_dir or _default_out_dir(seed_path)
    report = build_promoted_training_scale_seed_handoff(
        seed_path,
        execute=args.execute,
        allow_review=not args.no_allow_review,
        require_clean_evidence=args.require_clean_evidence,
        require_clean_batch_review=args.require_clean_batch_review,
        timeout_seconds=args.timeout_seconds,
        title=args.title,
    )
    summary = report["summary"]
    clean_evidence_requirement = report["clean_evidence_requirement"]
    clean_batch_review_requirement = report["clean_batch_review_requirement"]
    automation_gate = report["automation_gate"]
    automation_summary = report["automation_summary"]
    receipt_check = _attach_receipt_check(report, args.receipt_check_out_dir)
    outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
    if args.receipt_check_out_dir is not None:
        report["receipt_check_outputs"] = _write_receipt_check_outputs(report, args.receipt_check_out_dir, outputs)
        outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
    embedded_receipt_check = _write_embedded_receipt_check_outputs(
        out_dir,
        args.embedded_receipt_check_out_dir,
        receipt_check_out_dir=args.receipt_check_out_dir,
    )
    if embedded_receipt_check is not None:
        report["embedded_receipt_check"] = embedded_receipt_check
        embedded_outputs = embedded_receipt_check.get("embedded_receipt_check_outputs")
        if isinstance(embedded_outputs, dict):
            report["embedded_receipt_check_outputs"] = embedded_outputs
        outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
    handoff_assurance = _write_handoff_assurance_outputs(
        out_dir,
        args.assurance_out_dir,
        embedded_receipt_check_out_dir=args.embedded_receipt_check_out_dir,
    )
    if handoff_assurance is not None:
        report["handoff_assurance"] = handoff_assurance
        assurance_outputs = handoff_assurance.get("handoff_assurance_outputs")
        if isinstance(assurance_outputs, dict):
            report["handoff_assurance_outputs"] = assurance_outputs
        outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
    execution = report["execution"]
    print(f"handoff_status={summary.get('handoff_status')}")
    print(f"seed_status={report.get('seed_status')}")
    print(f"decision_status={summary.get('decision_status')}")
    print(f"execute={report.get('execute')}")
    print(f"returncode={execution.get('returncode')}")
    print(f"available_artifacts={summary.get('available_artifact_count')}/{summary.get('artifact_count')}")
    print(f"plan_status={summary.get('plan_status')}")
    print(f"seed_suite_path={summary.get('seed_suite_path')}")
    print(f"selected_handoff_suite_consistency={summary.get('selected_handoff_suite_consistency')}")
    print(f"selected_handoff_suite_mismatch_count={summary.get('selected_handoff_suite_mismatch_count')}")
    print(f"selected_handoff_require_clean_batch_review={summary.get('selected_handoff_require_clean_batch_review')}")
    print(f"selected_handoff_clean_batch_review_status={summary.get('selected_handoff_clean_batch_review_status')}")
    print(
        "selected_handoff_batch_maturity_ci_regression_count="
        f"{summary.get('selected_handoff_batch_maturity_ci_regression_count')}"
    )
    print(
        "selected_handoff_batch_maturity_ci_regression_names="
        + json.dumps(summary.get("selected_handoff_batch_maturity_ci_regression_names"), ensure_ascii=False)
    )
    print(
        "selected_handoff_batch_maturity_ci_regression_reason_counts="
        + json.dumps(summary.get("selected_handoff_batch_maturity_ci_regression_reason_counts"), ensure_ascii=False)
    )
    print(
        "selected_handoff_batch_maturity_suite_design_regression_count="
        f"{summary.get('selected_handoff_batch_maturity_suite_design_regression_count')}"
    )
    print(
        "selected_handoff_batch_maturity_suite_design_regression_names="
        + json.dumps(
            summary.get("selected_handoff_batch_maturity_suite_design_regression_names"),
            ensure_ascii=False,
        )
    )
    print(
        "selected_handoff_selected_batch_maturity_ci_regression_count="
        f"{summary.get('selected_handoff_selected_batch_maturity_ci_regression_count')}"
    )
    print(
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts="
        + json.dumps(
            summary.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts"),
            ensure_ascii=False,
        )
    )
    print(
        "selected_handoff_selected_batch_maturity_suite_design_regression_count="
        f"{summary.get('selected_handoff_selected_batch_maturity_suite_design_regression_count')}"
    )
    print(
        "selected_handoff_selected_batch_maturity_suite_design_regression_names="
        + json.dumps(
            summary.get("selected_handoff_selected_batch_maturity_suite_design_regression_names"),
            ensure_ascii=False,
        )
    )
    print(
        "selected_comparison_exclusion_reasons="
        + json.dumps(summary.get("selected_comparison_exclusion_reasons"), ensure_ascii=False)
    )
    print(f"handoff_require_clean_batch_review_count={summary.get('handoff_require_clean_batch_review_count')}")
    print(f"handoff_clean_batch_review_count={summary.get('handoff_clean_batch_review_count')}")
    print(f"handoff_unclean_batch_review_count={summary.get('handoff_unclean_batch_review_count')}")
    print(f"handoff_batch_maturity_ci_regression_count={summary.get('handoff_batch_maturity_ci_regression_count')}")
    print(
        "handoff_selected_batch_maturity_ci_regression_total="
        f"{summary.get('handoff_selected_batch_maturity_ci_regression_total')}"
    )
    print(
        "handoff_batch_maturity_ci_regression_names="
        + json.dumps(summary.get("handoff_batch_maturity_ci_regression_names"), ensure_ascii=False)
    )
    print(
        "handoff_batch_maturity_ci_regression_reason_counts="
        + json.dumps(summary.get("handoff_batch_maturity_ci_regression_reason_counts"), ensure_ascii=False)
    )
    print(
        "handoff_selected_batch_maturity_ci_regression_reason_counts="
        + json.dumps(summary.get("handoff_selected_batch_maturity_ci_regression_reason_counts"), ensure_ascii=False)
    )
    print(
        "handoff_batch_maturity_suite_design_regression_count="
        f"{summary.get('handoff_batch_maturity_suite_design_regression_count')}"
    )
    print(
        "handoff_selected_batch_maturity_suite_design_regression_total="
        f"{summary.get('handoff_selected_batch_maturity_suite_design_regression_total')}"
    )
    print(
        "handoff_batch_maturity_suite_design_regression_names="
        + json.dumps(summary.get("handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False)
    )
    print(
        "handoff_selected_batch_maturity_suite_design_regression_names="
        + json.dumps(summary.get("handoff_selected_batch_maturity_suite_design_regression_names"), ensure_ascii=False)
    )
    print(
        "comparison_exclusion_reasons="
        + json.dumps(summary.get("comparison_exclusion_reasons"), ensure_ascii=False)
    )
    print(
        "comparison_ready_handoff_require_clean_batch_review_count="
        f"{summary.get('comparison_ready_handoff_require_clean_batch_review_count')}"
    )
    print(
        "comparison_ready_handoff_clean_batch_review_count="
        f"{summary.get('comparison_ready_handoff_clean_batch_review_count')}"
    )
    print(
        "comparison_ready_handoff_unclean_batch_review_count="
        f"{summary.get('comparison_ready_handoff_unclean_batch_review_count')}"
    )
    print(
        "comparison_ready_handoff_batch_maturity_ci_regression_count="
        f"{summary.get('comparison_ready_handoff_batch_maturity_ci_regression_count')}"
    )
    print(
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_total="
        f"{summary.get('comparison_ready_handoff_selected_batch_maturity_ci_regression_total')}"
    )
    print(
        "comparison_ready_handoff_batch_maturity_ci_regression_names="
        + json.dumps(summary.get("comparison_ready_handoff_batch_maturity_ci_regression_names"), ensure_ascii=False)
    )
    print(
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts="
        + json.dumps(
            summary.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"),
            ensure_ascii=False,
        )
    )
    print(
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts="
        + json.dumps(
            summary.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"),
            ensure_ascii=False,
        )
    )
    print(
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count="
        f"{summary.get('comparison_ready_handoff_batch_maturity_suite_design_regression_count')}"
    )
    print(
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total="
        f"{summary.get('comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total')}"
    )
    print(
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names="
        + json.dumps(
            summary.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"),
            ensure_ascii=False,
        )
    )
    print(
        "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names="
        + json.dumps(
            summary.get("comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names"),
            ensure_ascii=False,
        )
    )
    print(f"selected_handoff_selected_batch_review_status={summary.get('selected_handoff_selected_batch_review_status')}")
    print(
        "selected_handoff_selected_batch_comparison_review_action_count="
        f"{summary.get('selected_handoff_selected_batch_comparison_review_action_count')}"
    )
    print(
        "selected_handoff_selected_batch_comparison_blocker_action_count="
        f"{summary.get('selected_handoff_selected_batch_comparison_blocker_action_count')}"
    )
    print(
        "comparison_ready_handoff_selected_batch_review_count="
        f"{summary.get('comparison_ready_handoff_selected_batch_review_count')}"
    )
    print(
        "comparison_ready_handoff_selected_batch_blocker_count="
        f"{summary.get('comparison_ready_handoff_selected_batch_blocker_count')}"
    )
    print(
        "comparison_ready_handoff_batch_comparison_blocker_reasons="
        + json.dumps(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"), ensure_ascii=False)
    )
    print(f"handoff_suite_mismatch_total={summary.get('handoff_suite_mismatch_total')}")
    print(f"plan_suite_path={summary.get('plan_suite_path')}")
    print(f"seed_handoff_suite_alignment_status={summary.get('seed_handoff_suite_alignment_status')}")
    print(f"seed_handoff_suite_alignment_mismatch_count={summary.get('seed_handoff_suite_alignment_mismatch_count')}")
    print(f"seed_handoff_clean_evidence_status={summary.get('seed_handoff_clean_evidence_status')}")
    print(f"seed_handoff_clean_evidence_ready={summary.get('seed_handoff_clean_evidence_ready')}")
    print(f"seed_handoff_clean_evidence_status_domain={summary.get('seed_handoff_clean_evidence_status_domain')}")
    print(f"next_batch_command_available={summary.get('next_batch_command_available')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print(f"command={report.get('command_text')}")
    print(f"next_batch_command={report.get('next_batch_command_text')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    print(f"automation_receipt_json={outputs.get('automation_receipt_json')}")
    print(f"automation_receipt_text={outputs.get('automation_receipt_text')}")
    _print_receipt_check(report)
    _print_embedded_receipt_check(embedded_receipt_check)
    _print_handoff_assurance(handoff_assurance)
    print(f"automation_summary_decision={automation_summary.get('decision')}")
    print(f"automation_summary_exit_code={automation_summary.get('exit_code')}")
    print(f"automation_summary_blocking_source={automation_summary.get('blocking_source')}")
    print(f"automation_summary_gate_decision={automation_summary.get('gate_decision')}")
    print(
        "automation_summary_failed_requirements="
        + json.dumps(automation_summary.get("failed_requirements"), ensure_ascii=False)
    )
    print(f"automation_summary_detail={automation_summary.get('detail')}")
    if args.require_clean_evidence:
        print(f"clean_evidence_required_status={clean_evidence_requirement.get('readiness_status')}")
        print(f"clean_evidence_required_ready={clean_evidence_requirement.get('ready')}")
        print(f"clean_evidence_required_detail={clean_evidence_requirement.get('detail')}")
        print(f"clean_evidence_required={clean_evidence_requirement.get('status')}")
    if args.require_clean_batch_review:
        print(f"clean_batch_review_required_selected_status={clean_batch_review_requirement.get('selected_status')}")
        print(
            "clean_batch_review_required_selected_ci_regression_count="
            f"{clean_batch_review_requirement.get('selected_ci_regression_count')}"
        )
        print(
            "clean_batch_review_required_selected_ci_regression_reason_counts="
            + json.dumps(clean_batch_review_requirement.get("selected_ci_regression_reason_counts"), ensure_ascii=False)
        )
        print(
            "clean_batch_review_required_selected_suite_design_regression_count="
            f"{clean_batch_review_requirement.get('selected_suite_design_regression_count')}"
        )
        print(
            "clean_batch_review_required_selected_suite_design_regression_names="
            + json.dumps(
                clean_batch_review_requirement.get("selected_suite_design_regression_names"),
                ensure_ascii=False,
            )
        )
        print(f"clean_batch_review_required_clean={clean_batch_review_requirement.get('clean')}")
        print(f"clean_batch_review_required_detail={clean_batch_review_requirement.get('detail')}")
        print(f"clean_batch_review_required={clean_batch_review_requirement.get('status')}")
    if args.require_clean_evidence or args.require_clean_batch_review:
        print(f"automation_gate_required={automation_gate.get('required')}")
        print(f"automation_gate_status={automation_gate.get('status')}")
        print(f"automation_gate_decision={automation_gate.get('decision')}")
        print(f"automation_gate_exit_code={automation_gate.get('exit_code')}")
        print(f"automation_gate_required_requirement_count={automation_gate.get('required_requirement_count')}")
        print(f"automation_gate_passed_requirement_count={automation_gate.get('passed_requirement_count')}")
        print(f"automation_gate_failed_requirement_count={automation_gate.get('failed_requirement_count')}")
        print(f"automation_gate_blocking_requirement_count={automation_gate.get('blocking_requirement_count')}")
        print("automation_gate_failed_requirements=" + json.dumps(automation_gate.get("failed_requirements"), ensure_ascii=False))
        print("automation_gate_passed_requirements=" + json.dumps(automation_gate.get("passed_requirements"), ensure_ascii=False))
        print(f"automation_gate_detail={automation_gate.get('detail')}")
    if automation_summary.get("decision") == "stop":
        raise SystemExit(int(automation_summary.get("exit_code") or 1))
    if receipt_check is not None and receipt_check.get("status") != "pass":
        raise SystemExit(1)
    if embedded_receipt_check is not None and embedded_receipt_check.get("status") != "pass":
        raise SystemExit(1)
    if handoff_assurance is not None and handoff_assurance.get("status") != "pass":
        raise SystemExit(1)


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path / "handoff"
    return path.parent / "handoff"


def _attach_receipt_check(report: dict[str, object], out_dir: Path | None) -> dict[str, object] | None:
    if out_dir is None:
        return None
    receipt = build_promoted_training_scale_seed_handoff_automation_receipt(report)
    check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)
    report["receipt_check"] = check
    return check


def _write_receipt_check_outputs(
    report: dict[str, object],
    out_dir: Path,
    outputs: dict[str, str],
) -> dict[str, str]:
    receipt_path = outputs.get("automation_receipt_json")
    if not receipt_path:
        raise ValueError("automation receipt JSON output is missing")
    receipt = load_promoted_training_scale_seed_handoff_automation_receipt(receipt_path)
    check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)
    check["receipt_path"] = str(receipt_path)
    report["receipt_check"] = check
    check_outputs = write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs(check, out_dir)
    return check_outputs


def _write_embedded_receipt_check_outputs(
    handoff_out_dir: Path,
    out_dir: Path | None,
    *,
    receipt_check_out_dir: Path | None,
) -> dict[str, object] | None:
    if out_dir is None:
        return None
    if receipt_check_out_dir is None:
        raise ValueError("--embedded-receipt-check-out-dir requires --receipt-check-out-dir")
    report_path = handoff_out_dir / "promoted_training_scale_seed_handoff.json"
    report = load_promoted_training_scale_seed_handoff_report(report_path)
    check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(report, base_dir=report_path.parent)
    check["handoff_report_path"] = str(report_path)
    check_outputs = write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs(check, out_dir)
    check["embedded_receipt_check_outputs"] = check_outputs
    return check


def _write_handoff_assurance_outputs(
    handoff_out_dir: Path,
    out_dir: Path | None,
    *,
    embedded_receipt_check_out_dir: Path | None,
) -> dict[str, object] | None:
    if out_dir is None:
        return None
    if embedded_receipt_check_out_dir is None:
        raise ValueError("--assurance-out-dir requires --embedded-receipt-check-out-dir")
    check = check_promoted_training_scale_seed_handoff_assurance(handoff_out_dir)
    check_outputs = write_promoted_training_scale_seed_handoff_assurance_check_outputs(check, out_dir)
    check["handoff_assurance_outputs"] = check_outputs
    return check


def _print_receipt_check(report: dict[str, object]) -> None:
    check = report.get("receipt_check")
    if not isinstance(check, dict):
        return
    check_outputs = report.get("receipt_check_outputs")
    print(render_promoted_training_scale_seed_handoff_automation_receipt_check(check), end="")
    print(f"receipt_path={check.get('receipt_path')}")
    if isinstance(check_outputs, dict):
        print("receipt_check_outputs=" + json.dumps(check_outputs, ensure_ascii=False))
        print(f"receipt_check_json={check_outputs.get('json')}")
        print(f"receipt_check_text={check_outputs.get('text')}")


def _print_embedded_receipt_check(check: dict[str, object] | None) -> None:
    if not isinstance(check, dict):
        return
    print(render_promoted_training_scale_seed_handoff_embedded_receipt_check(check), end="")
    print(f"handoff_report_path={check.get('handoff_report_path')}")
    check_outputs = check.get("embedded_receipt_check_outputs")
    if isinstance(check_outputs, dict):
        print("embedded_receipt_check_outputs=" + json.dumps(check_outputs, ensure_ascii=False))
        print(f"embedded_receipt_check_output_json={check_outputs.get('json')}")
        print(f"embedded_receipt_check_output_text={check_outputs.get('text')}")


def _print_handoff_assurance(check: dict[str, object] | None) -> None:
    if not isinstance(check, dict):
        return
    print(render_promoted_training_scale_seed_handoff_assurance_check(check), end="")
    check_outputs = check.get("handoff_assurance_outputs")
    if isinstance(check_outputs, dict):
        print("handoff_assurance_outputs=" + json.dumps(check_outputs, ensure_ascii=False))
        print(f"handoff_assurance_output_json={check_outputs.get('json')}")
        print(f"handoff_assurance_output_text={check_outputs.get('text')}")


if __name__ == "__main__":
    main()
