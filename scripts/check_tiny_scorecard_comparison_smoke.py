from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import as_dict, list_of_dicts, write_json_payload  # noqa: E402


SUMMARY_JSON_FILENAME = "tiny_scorecard_comparison_smoke_summary.json"
CHECK_JSON_FILENAME = "tiny_scorecard_comparison_smoke_check.json"
CHECK_TEXT_FILENAME = "tiny_scorecard_comparison_smoke_check.txt"

REQUIRED_ARTIFACT_FLAGS = [
    "baseline_smoke_summary_exists",
    "baseline_scorecard_exists",
    "candidate_smoke_summary_exists",
    "candidate_scorecard_exists",
    "comparison_json_exists",
    "comparison_html_exists",
    "decision_json_exists",
    "decision_remediation_csv_exists",
    "decision_html_exists",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a MiniGPT tiny scorecard comparison smoke summary without rerunning training."
    )
    parser.add_argument(
        "summary",
        type=Path,
        nargs="?",
        default=ROOT / "runs" / "tiny-scorecard-comparison-smoke",
        help="Path to the smoke output directory or tiny_scorecard_comparison_smoke_summary.json.",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "tiny-scorecard-comparison-smoke-check")
    parser.add_argument(
        "--allow-gate-stop",
        action="store_true",
        help="Treat a strict remediation gate stop as an expected, structurally valid outcome.",
    )
    parser.add_argument("--no-fail", action="store_true", help="Write check outputs but do not exit non-zero on fail.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary_path = resolve_summary_path(args.summary)
    summary = load_summary(summary_path)
    report = check_summary(summary, summary_path=summary_path, allow_gate_stop=args.allow_gate_stop)
    outputs = write_check_outputs(report, args.out_dir)
    print(render_check(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["status"] == "fail" and not args.no_fail:
        raise SystemExit(1)


def resolve_summary_path(path: Path) -> Path:
    if path.is_file():
        return path
    candidate = path / SUMMARY_JSON_FILENAME
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"tiny scorecard comparison smoke summary not found: {path}")


def load_summary(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"summary JSON must contain an object: {path}")
    return dict(payload)


def check_summary(
    summary: dict[str, Any],
    *,
    summary_path: Path | None = None,
    allow_gate_stop: bool = False,
) -> dict[str, Any]:
    remediation_gate = as_dict(summary.get("remediation_gate"))
    remediation_gate_issues = list_of_dicts(remediation_gate.get("issues"))
    first_remediation_gate_issue = remediation_gate_issues[0] if remediation_gate_issues else {}
    interpretation = as_dict(summary.get("interpretation"))
    artifacts = as_dict(summary.get("artifacts"))
    commands = list_of_dicts(summary.get("commands"))
    command_failures = [command for command in commands if command.get("status") != "pass"]
    artifact_failures = [flag for flag in REQUIRED_ARTIFACT_FLAGS if artifacts.get(flag) is not True]

    smoke_status = _string_or_empty(summary.get("status"))
    smoke_decision = _string_or_empty(summary.get("decision"))
    remediation_gate_status = _string_or_empty(remediation_gate.get("status"))
    remediation_gate_decision = _string_or_empty(remediation_gate.get("decision"))
    allowed_gate_stop = bool(
        allow_gate_stop
        and smoke_status == "fail"
        and remediation_gate_status == "fail"
        and remediation_gate_decision == "stop"
        and not command_failures
    )

    issues: list[dict[str, Any]] = []
    if smoke_status != "pass" and not allowed_gate_stop:
        issues.append(_issue("smoke_status_not_pass", "smoke", f"summary status is {smoke_status!r}"))
    if command_failures:
        issues.append(
            _issue(
                "command_status_not_pass",
                "commands",
                "one or more smoke commands failed",
                count=len(command_failures),
            )
        )
    if not commands:
        issues.append(_issue("commands_missing", "commands", "summary does not expose command statuses"))
    if not remediation_gate:
        issues.append(_issue("remediation_gate_missing", "remediation_gate", "summary has no remediation gate object"))
    elif remediation_gate_status != "pass" and not allowed_gate_stop:
        issues.append(
            _issue(
                "remediation_gate_not_pass",
                "remediation_gate",
                f"remediation gate status is {remediation_gate_status!r}",
            )
        )
    if interpretation.get("model_quality_claim") != "not_claimed":
        issues.append(
            _issue(
                "model_quality_claim_not_guarded",
                "interpretation",
                "tiny comparison smoke must not claim real model quality improvement",
            )
        )
    if artifact_failures:
        issues.append(
            _issue(
                "required_artifact_missing",
                "artifacts",
                "one or more required smoke artifacts are missing",
                count=len(artifact_failures),
            )
        )

    status = "pass" if not issues else "fail"
    decision = "fix-smoke-summary"
    if status == "pass":
        decision = "allowed-gate-stop" if allowed_gate_stop else "continue"
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "summary_path": "" if summary_path is None else str(summary_path),
        "allow_gate_stop": allow_gate_stop,
        "allowed_gate_stop": allowed_gate_stop,
        "smoke_status": smoke_status,
        "smoke_decision": smoke_decision,
        "command_count": len(commands),
        "command_failure_count": len(command_failures),
        "command_failures": [command.get("name") for command in command_failures],
        "remediation_gate_status": remediation_gate_status,
        "remediation_gate_decision": remediation_gate_decision,
        "remediation_gate_issue_count": _int_or_zero(remediation_gate.get("issue_count")),
        "remediation_gate_first_issue_code": first_remediation_gate_issue.get("code"),
        "remediation_gate_first_issue_severity": first_remediation_gate_issue.get("severity"),
        "remediation_gate_first_issue_category": first_remediation_gate_issue.get("category"),
        "remediation_gate_first_issue_action_code": first_remediation_gate_issue.get("action_code"),
        "remediation_gate_first_issue_owner_scope": first_remediation_gate_issue.get("owner_scope"),
        "model_quality_claim": interpretation.get("model_quality_claim"),
        "required_artifact_count": len(REQUIRED_ARTIFACT_FLAGS),
        "required_artifact_failure_count": len(artifact_failures),
        "required_artifact_failures": artifact_failures,
        "decision_remediation_csv_exists": artifacts.get("decision_remediation_csv_exists"),
        "issue_count": len(issues),
        "issues": issues,
    }


def render_check(report: dict[str, Any]) -> str:
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("summary_path", report.get("summary_path")),
        ("allow_gate_stop", report.get("allow_gate_stop")),
        ("allowed_gate_stop", report.get("allowed_gate_stop")),
        ("smoke_status", report.get("smoke_status")),
        ("smoke_decision", report.get("smoke_decision")),
        ("command_count", report.get("command_count")),
        ("command_failure_count", report.get("command_failure_count")),
        ("remediation_gate_status", report.get("remediation_gate_status")),
        ("remediation_gate_decision", report.get("remediation_gate_decision")),
        ("remediation_gate_issue_count", report.get("remediation_gate_issue_count")),
        ("remediation_gate_first_issue_code", report.get("remediation_gate_first_issue_code")),
        ("remediation_gate_first_issue_severity", report.get("remediation_gate_first_issue_severity")),
        ("remediation_gate_first_issue_category", report.get("remediation_gate_first_issue_category")),
        ("remediation_gate_first_issue_action_code", report.get("remediation_gate_first_issue_action_code")),
        ("remediation_gate_first_issue_owner_scope", report.get("remediation_gate_first_issue_owner_scope")),
        ("model_quality_claim", report.get("model_quality_claim")),
        ("required_artifact_count", report.get("required_artifact_count")),
        ("required_artifact_failure_count", report.get("required_artifact_failure_count")),
        ("decision_remediation_csv_exists", report.get("decision_remediation_csv_exists")),
        ("issue_count", report.get("issue_count")),
    ]
    for index, issue in enumerate(list_of_dicts(report.get("issues")), start=1):
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


def _issue(code: str, target: str, detail: str, *, severity: str = "blocker", count: int = 1) -> dict[str, Any]:
    return {"code": code, "severity": severity, "target": target, "detail": detail, "count": count}


def _string_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def _int_or_zero(value: Any) -> int:
    if isinstance(value, bool) or value is None or value == "":
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    main()
