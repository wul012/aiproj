from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_artifacts import (
    build_promoted_training_scale_seed_handoff_automation_receipt,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_validation import (
    EMBEDDED_RECEIPT_CHECK_COMPARE_KEYS,
    EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS,
    RECEIPT_SCHEMA_V2_REQUIRED_FIELDS,
    RECEIPT_SCHEMA_V3_REQUIRED_FIELDS,
    RECEIPT_SCHEMA_V4_REQUIRED_FIELDS,
    RECEIPT_SCHEMA_V5_REQUIRED_FIELDS,
    RECEIPT_SCHEMA_V5_TEXT_FIELDS,
    normalized_receipt_check_value as _normalized_check_value,
    receipt_check_compare_keys as _receipt_check_compare_keys,
    receipt_int as _int,
    v2_receipt_field_issues as _v2_receipt_field_issues,
    v3_receipt_field_issues as _v3_receipt_field_issues,
    v4_receipt_field_issues as _v4_receipt_field_issues,
    v5_receipt_field_issues as _v5_receipt_field_issues,
)
from minigpt.report_utils import as_dict
from minigpt.report_utils import positive_int_mapping
from minigpt.report_utils import resolve_archived_reference_path
from minigpt.report_utils import string_list


RECEIPT_TYPE = "promoted_training_scale_seed_handoff_automation"
RECEIPT_FILENAME = "promoted_training_scale_seed_handoff_automation_receipt.json"
HANDOFF_REPORT_FILENAME = "promoted_training_scale_seed_handoff.json"
EMBEDDED_RECEIPT_CHECK_JSON_FILENAME = "promoted_training_scale_seed_handoff_embedded_receipt_check.json"
EMBEDDED_RECEIPT_CHECK_TEXT_FILENAME = "promoted_training_scale_seed_handoff_embedded_receipt_check.txt"


def load_promoted_training_scale_seed_handoff_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(resolve_promoted_training_scale_seed_handoff_report_path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted seed handoff report must be a JSON object")
    return dict(payload)


def resolve_promoted_training_scale_seed_handoff_report_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / HANDOFF_REPORT_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def load_promoted_training_scale_seed_handoff_automation_receipt(path: str | Path) -> dict[str, Any]:
    payload = json.loads(resolve_promoted_training_scale_seed_handoff_automation_receipt_path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted seed handoff automation receipt must be a JSON object")
    return dict(payload)


def resolve_promoted_training_scale_seed_handoff_automation_receipt_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / RECEIPT_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def check_promoted_training_scale_seed_handoff_automation_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = as_dict(receipt)
    receipt_type = str(payload.get("receipt_type") or "")
    decision = str(payload.get("automation_decision") or "")
    blocking_source = payload.get("automation_blocking_source")
    failed_requirements = string_list(payload.get("failed_requirements"))
    schema_version = _int(payload.get("schema_version"))
    exit_code = _int(payload.get("automation_exit_code"))
    selected_ci_regressions = _int(payload.get("selected_handoff_batch_maturity_ci_regression_count"))
    selected_ci_reason_counts = positive_int_mapping(
        payload.get("selected_handoff_batch_maturity_ci_regression_reason_counts")
    )
    selected_boundary_plan_regressions = _int(
        payload.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    selected_selected_ci_reason_counts = positive_int_mapping(
        payload.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    selected_selected_boundary_plan_regressions = _int(
        payload.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    handoff_ci_regressions = _int(payload.get("handoff_batch_maturity_ci_regression_count"))
    handoff_ci_reason_counts = positive_int_mapping(payload.get("handoff_batch_maturity_ci_regression_reason_counts"))
    handoff_boundary_plan_regressions = _int(
        payload.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    handoff_selected_ci_reason_counts = positive_int_mapping(
        payload.get("handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    handoff_selected_boundary_plan_regressions = _int(
        payload.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total")
    )
    clean_batch_selected_ci_reason_counts = positive_int_mapping(
        payload.get("clean_batch_review_requirement_selected_ci_regression_reason_counts")
    )
    selected_suite_design_regressions = _int(
        payload.get("selected_handoff_batch_maturity_suite_design_regression_count")
    )
    selected_suite_design_names = string_list(
        payload.get("selected_handoff_batch_maturity_suite_design_regression_names")
    )
    handoff_suite_design_regressions = _int(payload.get("handoff_batch_maturity_suite_design_regression_count"))
    handoff_suite_design_names = string_list(payload.get("handoff_batch_maturity_suite_design_regression_names"))
    ready_suite_design_regressions = _int(
        payload.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count")
    )
    ready_boundary_plan_regressions = _int(
        payload.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count")
    )
    ready_ci_reason_counts = positive_int_mapping(
        payload.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts")
    )
    ready_selected_boundary_plan_regressions = _int(
        payload.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total")
    )
    ready_selected_ci_reason_counts = positive_int_mapping(
        payload.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts")
    )
    ready_suite_design_names = string_list(
        payload.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names")
    )
    comparison_exclusion_reasons = string_list(payload.get("comparison_exclusion_reasons"))
    issues: list[str] = []
    if receipt_type != RECEIPT_TYPE:
        issues.append(f"receipt_type must be {RECEIPT_TYPE}")
    if schema_version < 1:
        issues.append("schema_version must be >= 1")
    if decision not in {"continue", "stop"}:
        issues.append("automation_decision must be continue or stop")
    if decision == "stop" and exit_code == 0:
        issues.append("stop decision must carry a non-zero automation_exit_code")
    if decision == "continue" and exit_code != 0:
        issues.append("continue decision must carry automation_exit_code=0")
    if decision == "stop" and not blocking_source:
        issues.append("stop decision must carry automation_blocking_source")
    if decision == "continue" and blocking_source:
        issues.append("continue decision must not carry automation_blocking_source")
    if blocking_source == "automation_gate" and not failed_requirements:
        issues.append("automation_gate blocking source must include failed_requirements")
    if schema_version >= 2:
        issues.extend(_v2_receipt_field_issues(payload))
    if schema_version >= 3:
        issues.extend(_v3_receipt_field_issues(payload))
    if schema_version >= 4:
        issues.extend(_v4_receipt_field_issues(payload))
    if schema_version >= 5:
        issues.extend(_v5_receipt_field_issues(payload))
    status = "pass" if not issues else "fail"
    checker_exit_code = 0 if status == "pass" and decision == "continue" else 1
    return {
        "schema_version": schema_version,
        "receipt_type": receipt_type,
        "status": status,
        "decision": decision,
        "exit_code": exit_code,
        "checker_exit_code": checker_exit_code,
        "blocking_source": str(blocking_source) if blocking_source is not None else None,
        "failed_requirements": failed_requirements,
        "clean_batch_review_requirement_selected_ci_regression_reason_counts": clean_batch_selected_ci_reason_counts,
        "selected_handoff_batch_maturity_ci_regression_count": selected_ci_regressions,
        "selected_handoff_batch_maturity_ci_regression_reason_counts": selected_ci_reason_counts,
        "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": selected_boundary_plan_regressions,
        "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": selected_selected_ci_reason_counts,
        "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": (
            selected_selected_boundary_plan_regressions
        ),
        "handoff_batch_maturity_ci_regression_count": handoff_ci_regressions,
        "handoff_batch_maturity_ci_regression_reason_counts": handoff_ci_reason_counts,
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": handoff_boundary_plan_regressions,
        "handoff_selected_batch_maturity_ci_regression_reason_counts": handoff_selected_ci_reason_counts,
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": (
            handoff_selected_boundary_plan_regressions
        ),
        "selected_handoff_batch_maturity_suite_design_regression_count": selected_suite_design_regressions,
        "selected_handoff_batch_maturity_suite_design_regression_names": selected_suite_design_names,
        "handoff_batch_maturity_suite_design_regression_count": handoff_suite_design_regressions,
        "handoff_batch_maturity_suite_design_regression_names": handoff_suite_design_names,
        "comparison_ready_handoff_batch_maturity_suite_design_regression_count": ready_suite_design_regressions,
        "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": ready_ci_reason_counts,
        "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": ready_boundary_plan_regressions,
        "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": (
            ready_selected_boundary_plan_regressions
        ),
        "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": ready_selected_ci_reason_counts,
        "comparison_ready_handoff_batch_maturity_suite_design_regression_names": ready_suite_design_names,
        "comparison_exclusion_reasons": comparison_exclusion_reasons,
        "issue_count": len(issues),
        "issues": issues,
    }


def render_promoted_training_scale_seed_handoff_automation_receipt_check(check: dict[str, Any]) -> str:
    rows = [
        ("receipt_check_status", check.get("status")),
        ("receipt_decision", check.get("decision")),
        ("receipt_exit_code", check.get("exit_code")),
        ("receipt_checker_exit_code", check.get("checker_exit_code")),
        ("receipt_blocking_source", check.get("blocking_source")),
        ("receipt_failed_requirements", json.dumps(check.get("failed_requirements"), ensure_ascii=False)),
        (
            "receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
            json.dumps(
                check.get("clean_batch_review_requirement_selected_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_selected_handoff_batch_maturity_ci_regression_count",
            check.get("selected_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("selected_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("selected_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_handoff_batch_maturity_ci_regression_count",
            check.get("handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "receipt_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "receipt_selected_handoff_batch_maturity_suite_design_regression_count",
            check.get("selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "receipt_selected_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("selected_handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "receipt_handoff_batch_maturity_suite_design_regression_count",
            check.get("handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "receipt_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
            check.get("comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(
                check.get("comparison_ready_handoff_batch_maturity_suite_design_regression_names"),
                ensure_ascii=False,
            ),
        ),
        ("receipt_comparison_exclusion_reasons", json.dumps(check.get("comparison_exclusion_reasons"), ensure_ascii=False)),
        ("receipt_issue_count", check.get("issue_count")),
        ("receipt_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
    ]
    if _int(check.get("schema_version")) < 5:
        rows = [row for row in rows if row[0] not in RECEIPT_SCHEMA_V5_TEXT_FIELDS]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs(
    check: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_seed_handoff_automation_receipt_check.json",
        "text": root / "promoted_training_scale_seed_handoff_automation_receipt_check.txt",
    }
    paths["json"].write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_automation_receipt_check(check),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def check_promoted_training_scale_seed_handoff_embedded_receipt_check(
    report: dict[str, Any],
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    payload = as_dict(report)
    embedded = as_dict(payload.get("receipt_check"))
    embedded_outputs = as_dict(payload.get("receipt_check_outputs"))
    expected_receipt = build_promoted_training_scale_seed_handoff_automation_receipt(payload)
    embedded_schema_version = _int(embedded.get("schema_version"))
    if 0 < embedded_schema_version < _int(expected_receipt.get("schema_version")):
        expected_receipt = dict(expected_receipt)
        expected_receipt["schema_version"] = embedded_schema_version
    expected_check = check_promoted_training_scale_seed_handoff_automation_receipt(expected_receipt)
    compare_keys = _receipt_check_compare_keys(_int(expected_check.get("schema_version")))
    issues: list[str] = []
    if not embedded:
        issues.append("receipt_check must be embedded in the promoted seed handoff report")
    if embedded and not embedded.get("receipt_path"):
        issues.append("receipt_check.receipt_path is required for persisted handoff reports")
    if embedded and not embedded_outputs:
        issues.append("receipt_check_outputs must be embedded when receipt_check is embedded")
    if embedded_outputs and not embedded_outputs.get("json"):
        issues.append("receipt_check_outputs.json is required")
    if embedded_outputs and not embedded_outputs.get("text"):
        issues.append("receipt_check_outputs.text is required")
    for key in compare_keys:
        expected_value = _normalized_check_value(key, expected_check.get(key))
        actual_value = _normalized_check_value(key, embedded.get(key))
        if expected_value != actual_value:
            issues.append(f"receipt_check.{key} expected {expected_value!r} but got {actual_value!r}")
    sidecars = _check_embedded_receipt_sidecars(
        embedded,
        embedded_outputs,
        expected_check,
        compare_keys=compare_keys,
        base_dir=Path(base_dir) if base_dir is not None else None,
    )
    issues.extend(string_list(sidecars.get("issues")))
    status = "pass" if not issues else "fail"
    decision = str(expected_check.get("decision") or "")
    checker_exit_code = 0 if status == "pass" and decision == "continue" else 1
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "exit_code": _int(expected_check.get("exit_code")),
        "checker_exit_code": checker_exit_code,
        "receipt_schema_version": expected_check.get("schema_version"),
        "receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts": expected_check.get(
            "clean_batch_review_requirement_selected_ci_regression_reason_counts"
        ),
        "receipt_selected_handoff_batch_maturity_ci_regression_count": expected_check.get(
            "selected_handoff_batch_maturity_ci_regression_count"
        ),
        "receipt_selected_handoff_batch_maturity_ci_regression_reason_counts": expected_check.get(
            "selected_handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected_check.get(
            "selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts": expected_check.get(
            "selected_handoff_selected_batch_maturity_ci_regression_reason_counts"
        ),
        "receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected_check.get(
            "selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "receipt_handoff_batch_maturity_ci_regression_count": expected_check.get(
            "handoff_batch_maturity_ci_regression_count"
        ),
        "receipt_handoff_batch_maturity_ci_regression_reason_counts": expected_check.get(
            "handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected_check.get(
            "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "receipt_handoff_selected_batch_maturity_ci_regression_reason_counts": expected_check.get(
            "handoff_selected_batch_maturity_ci_regression_reason_counts"
        ),
        "receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": expected_check.get(
            "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "receipt_selected_handoff_batch_maturity_suite_design_regression_count": expected_check.get(
            "selected_handoff_batch_maturity_suite_design_regression_count"
        ),
        "receipt_selected_handoff_batch_maturity_suite_design_regression_names": expected_check.get(
            "selected_handoff_batch_maturity_suite_design_regression_names"
        ),
        "receipt_handoff_batch_maturity_suite_design_regression_count": expected_check.get(
            "handoff_batch_maturity_suite_design_regression_count"
        ),
        "receipt_handoff_batch_maturity_suite_design_regression_names": expected_check.get(
            "handoff_batch_maturity_suite_design_regression_names"
        ),
        "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count": expected_check.get(
            "comparison_ready_handoff_batch_maturity_suite_design_regression_count"
        ),
        "receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": expected_check.get(
            "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected_check.get(
            "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": expected_check.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"
        ),
        "receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": expected_check.get(
            "comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names": expected_check.get(
            "comparison_ready_handoff_batch_maturity_suite_design_regression_names"
        ),
        "receipt_comparison_exclusion_reasons": expected_check.get("comparison_exclusion_reasons"),
        "receipt_path": embedded.get("receipt_path"),
        "receipt_check_json": embedded_outputs.get("json"),
        "receipt_check_text": embedded_outputs.get("text"),
        "embedded_status": embedded.get("status"),
        "embedded_decision": embedded.get("decision"),
        "expected_status": expected_check.get("status"),
        "expected_decision": expected_check.get("decision"),
        "issue_count": len(issues),
        "issues": issues,
        "expected_check": expected_check,
        "embedded_check": embedded,
        "embedded_check_outputs": embedded_outputs,
        "sidecar_status": sidecars.get("status"),
        "sidecar_issue_count": sidecars.get("issue_count"),
        "sidecar_issues": sidecars.get("issues"),
        "receipt_path_resolved": sidecars.get("receipt_path_resolved"),
        "receipt_path_exists": sidecars.get("receipt_path_exists"),
        "receipt_check_json_resolved": sidecars.get("receipt_check_json_resolved"),
        "receipt_check_json_exists": sidecars.get("receipt_check_json_exists"),
        "receipt_check_text_resolved": sidecars.get("receipt_check_text_resolved"),
        "receipt_check_text_exists": sidecars.get("receipt_check_text_exists"),
    }


def render_promoted_training_scale_seed_handoff_embedded_receipt_check(check: dict[str, Any]) -> str:
    rows = [
        ("embedded_receipt_check_status", check.get("status")),
        ("embedded_receipt_check_decision", check.get("decision")),
        ("embedded_receipt_check_exit_code", check.get("exit_code")),
        ("embedded_receipt_check_checker_exit_code", check.get("checker_exit_code")),
        ("embedded_receipt_check_receipt_schema_version", check.get("receipt_schema_version")),
        (
            "embedded_receipt_check_receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count",
            check.get("receipt_selected_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_selected_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count",
            check.get("receipt_handoff_batch_maturity_ci_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count",
            check.get("receipt_selected_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("receipt_selected_handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count",
            check.get("receipt_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(check.get("receipt_handoff_batch_maturity_suite_design_regression_names"), ensure_ascii=False),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
            check.get("receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
            check.get("receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
            json.dumps(
                check.get("receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"),
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
            check.get("receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"),
        ),
        (
            "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
            json.dumps(
                check.get("receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names"),
                ensure_ascii=False,
            ),
        ),
        (
            "embedded_receipt_check_receipt_comparison_exclusion_reasons",
            json.dumps(check.get("receipt_comparison_exclusion_reasons"), ensure_ascii=False),
        ),
        ("embedded_receipt_check_receipt_path", check.get("receipt_path")),
        ("embedded_receipt_check_json", check.get("receipt_check_json")),
        ("embedded_receipt_check_text", check.get("receipt_check_text")),
        ("embedded_receipt_check_sidecar_status", check.get("sidecar_status")),
        ("embedded_receipt_check_receipt_path_exists", check.get("receipt_path_exists")),
        ("embedded_receipt_check_json_exists", check.get("receipt_check_json_exists")),
        ("embedded_receipt_check_text_exists", check.get("receipt_check_text_exists")),
        ("embedded_receipt_check_issue_count", check.get("issue_count")),
        ("embedded_receipt_check_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
    ]
    if _int(check.get("receipt_schema_version")) < 5:
        rows = [row for row in rows if row[0] not in EMBEDDED_RECEIPT_SCHEMA_V5_TEXT_FIELDS]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs(
    check: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / EMBEDDED_RECEIPT_CHECK_JSON_FILENAME,
        "text": root / EMBEDDED_RECEIPT_CHECK_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_embedded_receipt_check(check),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _check_embedded_receipt_sidecars(
    embedded: dict[str, Any],
    embedded_outputs: dict[str, Any],
    expected_check: dict[str, Any],
    *,
    compare_keys: tuple[str, ...],
    base_dir: Path | None,
) -> dict[str, Any]:
    issues: list[str] = []
    receipt_path = _resolve_reference_path(embedded.get("receipt_path"), base_dir)
    check_json_path = _resolve_reference_path(embedded_outputs.get("json"), base_dir)
    check_text_path = _resolve_reference_path(embedded_outputs.get("text"), base_dir)
    receipt_exists = _is_file(receipt_path)
    check_json_exists = _is_file(check_json_path)
    check_text_exists = _is_file(check_text_path)
    if embedded.get("receipt_path") and not receipt_exists:
        issues.append(f"receipt_check.receipt_path does not exist: {embedded.get('receipt_path')}")
    if embedded_outputs.get("json") and not check_json_exists:
        issues.append(f"receipt_check_outputs.json does not exist: {embedded_outputs.get('json')}")
    if embedded_outputs.get("text") and not check_text_exists:
        issues.append(f"receipt_check_outputs.text does not exist: {embedded_outputs.get('text')}")
    if receipt_exists and receipt_path is not None:
        issues.extend(_check_receipt_file_matches_expected(receipt_path, expected_check, compare_keys))
    if check_json_exists and check_json_path is not None:
        issues.extend(_check_receipt_check_json_matches_expected(check_json_path, expected_check, embedded, compare_keys))
    if check_text_exists and check_text_path is not None:
        issues.extend(_check_receipt_check_text_matches_expected(check_text_path, expected_check))
    return {
        "status": "pass" if not issues else "fail",
        "issue_count": len(issues),
        "issues": issues,
        "receipt_path_resolved": str(receipt_path) if receipt_path is not None else None,
        "receipt_path_exists": receipt_exists,
        "receipt_check_json_resolved": str(check_json_path) if check_json_path is not None else None,
        "receipt_check_json_exists": check_json_exists,
        "receipt_check_text_resolved": str(check_text_path) if check_text_path is not None else None,
        "receipt_check_text_exists": check_text_exists,
    }


def _check_receipt_file_matches_expected(
    path: Path,
    expected_check: dict[str, Any],
    compare_keys: tuple[str, ...],
) -> list[str]:
    try:
        receipt = load_promoted_training_scale_seed_handoff_automation_receipt(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [f"receipt_check.receipt_path could not be read: {exc}"]
    actual_check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)
    return _compare_check_fields("receipt_check.receipt_path", expected_check, actual_check, compare_keys)


def _check_receipt_check_json_matches_expected(
    path: Path,
    expected_check: dict[str, Any],
    embedded: dict[str, Any],
    compare_keys: tuple[str, ...],
) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"receipt_check_outputs.json could not be read: {exc}"]
    if not isinstance(payload, dict):
        return ["receipt_check_outputs.json must contain a JSON object"]
    issues = _compare_check_fields("receipt_check_outputs.json", expected_check, payload, compare_keys)
    expected_receipt_path = str(embedded.get("receipt_path") or "")
    actual_receipt_path = str(payload.get("receipt_path") or "")
    if expected_receipt_path != actual_receipt_path:
        issues.append(
            "receipt_check_outputs.json.receipt_path "
            f"expected {expected_receipt_path!r} but got {actual_receipt_path!r}"
        )
    return issues


def _check_receipt_check_text_matches_expected(path: Path, expected_check: dict[str, Any]) -> list[str]:
    try:
        actual_text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return [f"receipt_check_outputs.text could not be read: {exc}"]
    expected_text = render_promoted_training_scale_seed_handoff_automation_receipt_check(expected_check)
    if actual_text != expected_text:
        return ["receipt_check_outputs.text content does not match rendered receipt check"]
    return []


def _compare_check_fields(
    prefix: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    compare_keys: tuple[str, ...],
) -> list[str]:
    issues: list[str] = []
    for key in compare_keys:
        expected_value = _normalized_check_value(key, expected.get(key))
        actual_value = _normalized_check_value(key, actual.get(key))
        if expected_value != actual_value:
            issues.append(f"{prefix}.{key} expected {expected_value!r} but got {actual_value!r}")
    return issues


def _resolve_reference_path(value: Any, base_dir: Path | None) -> Path | None:
    return resolve_archived_reference_path(value, base_dir)


def _is_file(path: Path | None) -> bool:
    return bool(path and path.is_file())


__all__ = [
    "EMBEDDED_RECEIPT_CHECK_JSON_FILENAME",
    "EMBEDDED_RECEIPT_CHECK_TEXT_FILENAME",
    "HANDOFF_REPORT_FILENAME",
    "RECEIPT_FILENAME",
    "RECEIPT_TYPE",
    "check_promoted_training_scale_seed_handoff_embedded_receipt_check",
    "check_promoted_training_scale_seed_handoff_automation_receipt",
    "load_promoted_training_scale_seed_handoff_report",
    "load_promoted_training_scale_seed_handoff_automation_receipt",
    "render_promoted_training_scale_seed_handoff_embedded_receipt_check",
    "render_promoted_training_scale_seed_handoff_automation_receipt_check",
    "resolve_promoted_training_scale_seed_handoff_report_path",
    "resolve_promoted_training_scale_seed_handoff_automation_receipt_path",
    "write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs",
    "write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs",
]
