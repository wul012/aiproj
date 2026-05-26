from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import as_dict, write_json_payload  # noqa: E402
from scripts.run_ci_baseline_candidate_threshold_boundary_gate_check import (  # noqa: E402
    CI_BOUNDARY_GATE_CONFIG,
    PLAN_JSON_FILENAME,
)

CHECK_JSON_FILENAME = "ci_baseline_candidate_threshold_boundary_gate_check_plan_check.json"
CHECK_TEXT_FILENAME = "ci_baseline_candidate_threshold_boundary_gate_check_plan_check.txt"
REQUIRED_ARTIFACTS = (
    "gate_check_json",
    "gate_check_text",
    "gate_check_markdown",
    "gate_check_html",
    "boundary_smoke_json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check CI baseline-candidate threshold boundary gate wrapper plan digests.")
    parser.add_argument(
        "plan",
        type=Path,
        nargs="?",
        default=ROOT / "runs" / "baseline-candidate-threshold-boundary-gate-check-ci",
        help="Path to ci_baseline_candidate_threshold_boundary_gate_check_plan.json or its output directory.",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "ci-baseline-candidate-boundary-gate-plan-check")
    parser.add_argument("--no-fail", action="store_true", help="Write check outputs but do not exit non-zero on fail.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan_path = resolve_plan_path(args.plan)
    plan = load_plan(plan_path)
    report = check_plan(plan, plan_path=plan_path)
    outputs = write_check_outputs(report, args.out_dir)
    print(render_check(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["status"] == "fail" and not args.no_fail:
        raise SystemExit(1)


def resolve_plan_path(path: Path) -> Path:
    if path.is_file():
        return path
    candidate = path / PLAN_JSON_FILENAME
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"CI baseline-candidate boundary gate plan not found: {path}")


def load_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"plan JSON must contain an object: {path}")
    return dict(payload)


def check_plan(plan: dict[str, Any], *, plan_path: Path | None = None) -> dict[str, Any]:
    artifact_digest = as_dict(plan.get("artifact_digest"))
    artifacts = as_dict(artifact_digest.get("artifacts"))
    gate_summary = as_dict(plan.get("gate_check_summary"))
    config = as_dict(plan.get("config"))
    issues: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    for name in REQUIRED_ARTIFACTS:
        expected = as_dict(artifacts.get(name))
        actual = _actual_digest(Path(str(expected.get("path", "")))) if expected.get("path") else _missing_actual()
        row = {
            "name": name,
            "path": expected.get("path", ""),
            "expected_exists": bool(expected.get("exists")),
            "actual_exists": bool(actual.get("exists")),
            "expected_size_bytes": _int_or_zero(expected.get("size_bytes")),
            "actual_size_bytes": _int_or_zero(actual.get("size_bytes")),
            "expected_sha256": str(expected.get("sha256", "")),
            "actual_sha256": str(actual.get("sha256", "")),
        }
        row["status"] = "pass" if _row_matches(row) else "fail"
        rows.append(row)
        if row["status"] != "pass":
            issues.append(_issue("artifact_digest_mismatch", name, f"{name} digest does not match recorded plan values"))

    if not artifact_digest:
        issues.append(_issue("artifact_digest_missing", "artifact_digest", "plan has no artifact_digest object"))
    if not artifacts:
        issues.append(_issue("artifact_digest_artifacts_missing", "artifact_digest.artifacts", "plan has no artifact digest map"))
    if plan.get("wrapper") != "run_ci_baseline_candidate_threshold_boundary_gate_check":
        issues.append(_issue("wrapper_mismatch", "wrapper", f"unexpected wrapper {plan.get('wrapper')!r}"))
    if plan.get("returncode") != 0:
        issues.append(_issue("returncode_not_zero", "returncode", f"plan returncode is {plan.get('returncode')!r}"))
    issues.extend(_config_issues(config))
    issues.extend(_gate_summary_issues(gate_summary))

    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "continue" if status == "pass" else "fix-ci-boundary-gate-plan",
        "plan_path": "" if plan_path is None else str(plan_path),
        "wrapper": plan.get("wrapper"),
        "returncode": plan.get("returncode"),
        "artifact_count": len(rows),
        "artifact_failure_count": sum(1 for row in rows if row.get("status") != "pass"),
        "artifacts": rows,
        "gate_check": gate_summary,
        "issue_count": len(issues),
        "issues": issues,
    }


def render_check(report: dict[str, Any]) -> str:
    gate = as_dict(report.get("gate_check"))
    rows: list[tuple[str, Any]] = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("plan_path", report.get("plan_path")),
        ("wrapper", report.get("wrapper")),
        ("returncode", report.get("returncode")),
        ("artifact_count", report.get("artifact_count")),
        ("artifact_failure_count", report.get("artifact_failure_count")),
        ("issue_count", report.get("issue_count")),
        ("gate_check_available", gate.get("available")),
        ("gate_check_parse_status", gate.get("parse_status")),
        ("gate_check_status", gate.get("status")),
        ("gate_check_decision", gate.get("decision")),
        ("gate_check_failed_count", gate.get("failed_count")),
        ("gate_check_actual_exit_code", gate.get("actual_exit_code")),
        ("gate_check_expected_exit_code", gate.get("expected_exit_code")),
        ("gate_check_diagnosis_decision", gate.get("diagnosis_decision")),
    ]
    for artifact in report.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        name = artifact.get("name")
        rows.append((f"{name}_status", artifact.get("status")))
        rows.append((f"{name}_expected_sha256", artifact.get("expected_sha256")))
        rows.append((f"{name}_actual_sha256", artifact.get("actual_sha256")))
    for index, issue in enumerate(report.get("issues", []), start=1):
        if not isinstance(issue, dict):
            continue
        rows.append((f"issue_{index}_code", issue.get("code")))
        rows.append((f"issue_{index}_target", issue.get("target")))
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_check_outputs(report: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / CHECK_JSON_FILENAME,
        "text": out_dir / CHECK_TEXT_FILENAME,
    }
    write_json_payload(report, paths["json"])
    paths["text"].write_text(render_check(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _config_issues(config: dict[str, Any]) -> list[dict[str, Any]]:
    expected = dict(CI_BOUNDARY_GATE_CONFIG)
    issues: list[dict[str, Any]] = []
    for key in ["thresholds", "require_diagnosis_pass", "expected_exit_code", "expected_diagnosis_decision", "require_pass"]:
        if config.get(key) != expected.get(key):
            issues.append(_issue("config_mismatch", f"config.{key}", f"expected {expected.get(key)!r}, got {config.get(key)!r}"))
    return issues


def _gate_summary_issues(summary: dict[str, Any]) -> list[dict[str, Any]]:
    expectations = {
        "available": True,
        "parse_status": "pass",
        "status": "pass",
        "decision": "expected_exit_verified",
        "failed_count": 0,
        "actual_exit_code": 2,
        "expected_exit_code": 2,
        "diagnosis_decision": "candidate_not_accepted",
    }
    issues: list[dict[str, Any]] = []
    for key, expected in expectations.items():
        if summary.get(key) != expected:
            issues.append(_issue("gate_summary_mismatch", f"gate_check_summary.{key}", f"expected {expected!r}, got {summary.get(key)!r}"))
    return issues


def _actual_digest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "size_bytes": 0, "sha256": ""}
    data = path.read_bytes()
    return {"exists": True, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _missing_actual() -> dict[str, Any]:
    return {"exists": False, "size_bytes": 0, "sha256": ""}


def _row_matches(row: dict[str, Any]) -> bool:
    return (
        row["expected_exists"] == row["actual_exists"]
        and row["expected_size_bytes"] == row["actual_size_bytes"]
        and row["expected_sha256"] == row["actual_sha256"]
    )


def _issue(code: str, target: str, detail: str, *, severity: str = "blocker") -> dict[str, Any]:
    return {"code": code, "severity": severity, "target": target, "detail": detail}


def _int_or_zero(value: Any) -> int:
    if isinstance(value, bool) or value is None or value == "":
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    main()
