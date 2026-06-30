from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt import (
    RECEIPT_SCHEMA_V5_REQUIRED_FIELDS,
    check_promoted_training_scale_seed_handoff_embedded_receipt_check,
    load_promoted_training_scale_seed_handoff_report,
    render_promoted_training_scale_seed_handoff_embedded_receipt_check,
    resolve_promoted_training_scale_seed_handoff_report_path,
)
from minigpt.promoted_training_scale_seed_handoff_assurance_render import (
    render_promoted_training_scale_seed_handoff_assurance_check,
)
from minigpt.report_utils import (
    as_dict,
    archived_reference_path,
    positive_int_mapping,
    resolve_archived_reference_path,
    string_list,
)


HANDOFF_ASSURANCE_JSON_FILENAME = "promoted_training_scale_seed_handoff_assurance.json"
HANDOFF_ASSURANCE_TEXT_FILENAME = "promoted_training_scale_seed_handoff_assurance.txt"
EMBEDDED_ASSURANCE_COMPARE_KEYS = (
    "status",
    "decision",
    "exit_code",
    "checker_exit_code",
    "receipt_path",
    "receipt_check_json",
    "receipt_check_text",
    "embedded_status",
    "embedded_decision",
    "expected_status",
    "expected_decision",
    "receipt_schema_version",
    "receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
    "receipt_selected_handoff_batch_maturity_ci_regression_count",
    "receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
    "receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "receipt_handoff_batch_maturity_ci_regression_count",
    "receipt_handoff_batch_maturity_ci_regression_reason_counts",
    "receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "receipt_selected_handoff_batch_maturity_suite_design_regression_count",
    "receipt_selected_handoff_batch_maturity_suite_design_regression_names",
    "receipt_handoff_batch_maturity_suite_design_regression_count",
    "receipt_handoff_batch_maturity_suite_design_regression_names",
    "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
    "receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
    "receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
    "receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
    "receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
    "receipt_comparison_exclusion_reasons",
    "issue_count",
    "issues",
    "sidecar_status",
    "sidecar_issue_count",
    "sidecar_issues",
    "receipt_path_exists",
    "receipt_check_json_exists",
    "receipt_check_text_exists",
)
EMBEDDED_ASSURANCE_JSON_COMPARE_KEYS = EMBEDDED_ASSURANCE_COMPARE_KEYS + ("handoff_report_path",)
EMBEDDED_ASSURANCE_V5_COMPARE_FIELDS = tuple(f"receipt_{field}" for field in RECEIPT_SCHEMA_V5_REQUIRED_FIELDS)


def check_promoted_training_scale_seed_handoff_assurance(path: str | Path) -> dict[str, Any]:
    report_path = resolve_promoted_training_scale_seed_handoff_report_path(path)
    report = load_promoted_training_scale_seed_handoff_report(report_path)
    expected = check_promoted_training_scale_seed_handoff_embedded_receipt_check(
        report,
        base_dir=report_path.parent,
    )
    expected["handoff_report_path"] = str(report_path)
    compare_keys = _embedded_assurance_compare_keys(_int(expected.get("receipt_schema_version")))
    json_compare_keys = compare_keys + ("handoff_report_path",)
    embedded = as_dict(report.get("embedded_receipt_check"))
    embedded_outputs = as_dict(report.get("embedded_receipt_check_outputs"))
    issues: list[str] = []
    if expected.get("status") != "pass":
        issues.append("embedded receipt-check recomputation must pass")
        issues.extend(f"embedded_receipt_check.{issue}" for issue in string_list(expected.get("issues")))
    if not embedded:
        issues.append("embedded_receipt_check must be embedded in the main handoff report")
    if not embedded_outputs:
        issues.append("embedded_receipt_check_outputs must be embedded in the main handoff report")
    if embedded:
        issues.extend(_compare_embedded_check("embedded_receipt_check", expected, embedded, compare_keys))
    nested_outputs = as_dict(embedded.get("embedded_receipt_check_outputs")) if embedded else {}
    if nested_outputs and embedded_outputs:
        issues.extend(_compare_outputs("embedded_receipt_check.embedded_receipt_check_outputs", embedded_outputs, nested_outputs))
    json_path = _resolve_reference_path(embedded_outputs.get("json"), report_path.parent)
    text_path = _resolve_reference_path(embedded_outputs.get("text"), report_path.parent)
    json_exists = _is_file(json_path)
    text_exists = _is_file(text_path)
    if embedded_outputs and not embedded_outputs.get("json"):
        issues.append("embedded_receipt_check_outputs.json is required")
    if embedded_outputs and not embedded_outputs.get("text"):
        issues.append("embedded_receipt_check_outputs.text is required")
    if embedded_outputs.get("json") and not json_exists:
        issues.append(f"embedded_receipt_check_outputs.json does not exist: {embedded_outputs.get('json')}")
    if embedded_outputs.get("text") and not text_exists:
        issues.append(f"embedded_receipt_check_outputs.text does not exist: {embedded_outputs.get('text')}")
    if json_exists and json_path is not None:
        issues.extend(_check_embedded_assurance_json_matches_expected(json_path, expected, json_compare_keys))
    if text_exists and text_path is not None:
        issues.extend(_check_embedded_assurance_text_matches_expected(text_path, expected))
    status = "pass" if not issues else "fail"
    decision = str(expected.get("decision") or "")
    checker_exit_code = 0 if status == "pass" and decision == "continue" else 1
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "exit_code": _int(expected.get("exit_code")),
        "checker_exit_code": checker_exit_code,
        "handoff_report_path": str(report_path),
        "embedded_receipt_check_status": expected.get("status"),
        "embedded_receipt_check_sidecar_status": expected.get("sidecar_status"),
        "embedded_receipt_check_issue_count": expected.get("issue_count"),
        "embedded_receipt_check_receipt_schema_version": expected.get("receipt_schema_version"),
        "embedded_receipt_check_receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts": expected.get(
            "receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count": expected.get(
            "receipt_selected_handoff_batch_maturity_ci_regression_count"
        ),
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_reason_counts": expected.get(
            "receipt_selected_handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected.get(
            "receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts": expected.get(
            "receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected.get(
            "receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count": expected.get(
            "receipt_handoff_batch_maturity_ci_regression_count"
        ),
        "embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_reason_counts": expected.get(
            "receipt_handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected.get(
            "receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_regression_reason_counts": expected.get(
            "receipt_handoff_selected_batch_maturity_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": expected.get(
            "receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_count": expected.get(
            "receipt_selected_handoff_batch_maturity_suite_design_regression_count"
        ),
        "embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names": expected.get(
            "receipt_selected_handoff_batch_maturity_suite_design_regression_names"
        ),
        "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count": expected.get(
            "receipt_handoff_batch_maturity_suite_design_regression_count"
        ),
        "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names": expected.get(
            "receipt_handoff_batch_maturity_suite_design_regression_names"
        ),
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count": expected.get(
            "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
        ),
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": expected.get(
            "receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": expected.get(
            "receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"
        ),
        "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": expected.get(
            "receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"
        ),
        "embedded_receipt_check_receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total": expected.get(
            "receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"
        ),
        "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names": expected.get(
            "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names"
        ),
        "embedded_receipt_check_receipt_comparison_exclusion_reasons": expected.get(
            "receipt_comparison_exclusion_reasons"
        ),
        "main_embedded_receipt_check_status": embedded.get("status"),
        "embedded_receipt_check_output_json": embedded_outputs.get("json"),
        "embedded_receipt_check_output_json_resolved": str(json_path) if json_path is not None else None,
        "embedded_receipt_check_output_json_exists": json_exists,
        "embedded_receipt_check_output_text": embedded_outputs.get("text"),
        "embedded_receipt_check_output_text_resolved": str(text_path) if text_path is not None else None,
        "embedded_receipt_check_output_text_exists": text_exists,
        "issue_count": len(issues),
        "issues": issues,
        "expected_embedded_receipt_check": expected,
        "main_embedded_receipt_check": embedded,
        "main_embedded_receipt_check_outputs": embedded_outputs,
    }

def write_promoted_training_scale_seed_handoff_assurance_check_outputs(
    check: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / HANDOFF_ASSURANCE_JSON_FILENAME,
        "text": root / HANDOFF_ASSURANCE_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_promoted_training_scale_seed_handoff_assurance_check(check), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _compare_embedded_check(
    prefix: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
    keys: tuple[str, ...],
) -> list[str]:
    issues: list[str] = []
    for key in keys:
        expected_value = _normalized_assurance_value(key, expected.get(key))
        actual_value = _normalized_assurance_value(key, actual.get(key))
        if expected_value != actual_value:
            issues.append(f"{prefix}.{key} expected {expected_value!r} but got {actual_value!r}")
    return issues


def _compare_outputs(prefix: str, expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in ("json", "text"):
        expected_value = str(expected.get(key) or "")
        actual_value = str(actual.get(key) or "")
        if expected_value != actual_value:
            issues.append(f"{prefix}.{key} expected {expected_value!r} but got {actual_value!r}")
    return issues


def _check_embedded_assurance_json_matches_expected(
    path: Path,
    expected: dict[str, Any],
    compare_keys: tuple[str, ...],
) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"embedded_receipt_check_outputs.json could not be read: {exc}"]
    if not isinstance(payload, dict):
        return ["embedded_receipt_check_outputs.json must contain a JSON object"]
    return _compare_embedded_check("embedded_receipt_check_outputs.json", expected, payload, compare_keys)


def _embedded_assurance_compare_keys(schema_version: int) -> tuple[str, ...]:
    if schema_version >= 5:
        return EMBEDDED_ASSURANCE_COMPARE_KEYS
    return tuple(key for key in EMBEDDED_ASSURANCE_COMPARE_KEYS if key not in EMBEDDED_ASSURANCE_V5_COMPARE_FIELDS)


def _check_embedded_assurance_text_matches_expected(path: Path, expected: dict[str, Any]) -> list[str]:
    try:
        actual_text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return [f"embedded_receipt_check_outputs.text could not be read: {exc}"]
    expected_text = render_promoted_training_scale_seed_handoff_embedded_receipt_check(expected)
    if actual_text != expected_text:
        return ["embedded_receipt_check_outputs.text content does not match rendered embedded receipt check"]
    return []


def _resolve_reference_path(value: Any, base_dir: Path | None) -> Path | None:
    return resolve_archived_reference_path(value, base_dir)


def _is_file(path: Path | None) -> bool:
    return bool(path and path.is_file())


def _normalized_assurance_value(key: str, value: Any) -> Any:
    if key in {
        "exit_code",
        "checker_exit_code",
        "issue_count",
        "sidecar_issue_count",
        "receipt_schema_version",
        "receipt_selected_handoff_batch_maturity_ci_regression_count",
        "receipt_selected_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "receipt_selected_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "receipt_handoff_batch_maturity_ci_regression_count",
        "receipt_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "receipt_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
        "receipt_selected_handoff_batch_maturity_suite_design_regression_count",
        "receipt_handoff_batch_maturity_suite_design_regression_count",
        "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count",
        "receipt_comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count",
        "receipt_comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total",
    }:
        return _int(value)
    if key in {
        "issues",
        "sidecar_issues",
        "receipt_selected_handoff_batch_maturity_suite_design_regression_names",
        "receipt_handoff_batch_maturity_suite_design_regression_names",
        "receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names",
        "receipt_comparison_exclusion_reasons",
    }:
        return string_list(value)
    if key in {
        "receipt_clean_batch_review_requirement_selected_ci_regression_reason_counts",
        "receipt_selected_handoff_batch_maturity_ci_regression_reason_counts",
        "receipt_selected_handoff_selected_batch_maturity_ci_regression_reason_counts",
        "receipt_handoff_batch_maturity_ci_regression_reason_counts",
        "receipt_handoff_selected_batch_maturity_ci_regression_reason_counts",
        "receipt_comparison_ready_handoff_batch_maturity_ci_regression_reason_counts",
        "receipt_comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts",
    }:
        return positive_int_mapping(value)
    if key in {"receipt_path_exists", "receipt_check_json_exists", "receipt_check_text_exists"}:
        return bool(value)
    if key in {"handoff_report_path", "receipt_path", "receipt_check_json", "receipt_check_text"}:
        return str(archived_reference_path(value)) if value else ""
    return str(value or "")


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "HANDOFF_ASSURANCE_JSON_FILENAME",
    "HANDOFF_ASSURANCE_TEXT_FILENAME",
    "check_promoted_training_scale_seed_handoff_assurance",
    "render_promoted_training_scale_seed_handoff_assurance_check",
    "write_promoted_training_scale_seed_handoff_assurance_check_outputs",
]
