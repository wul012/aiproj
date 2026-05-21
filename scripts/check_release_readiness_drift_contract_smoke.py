from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]

COMPARISON_JSON_FILENAME = "release_readiness_comparison.json"
SMOKE_SUMMARY_JSON_FILENAME = "release_readiness_drift_contract_smoke_summary.json"
SMOKE_SUMMARY_TEXT_FILENAME = "release_readiness_drift_contract_smoke_summary.txt"
CHECK_JSON_FILENAME = "release_readiness_drift_contract_check.json"
CHECK_TEXT_FILENAME = "release_readiness_drift_contract_check.txt"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a CI-sized release readiness drift contract smoke check.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "release-readiness-drift-contract-smoke")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    comparison_dir = out_dir / "comparison"
    check_dir = out_dir / "check"
    stdout_path = out_dir / "checker_stdout.txt"
    stderr_path = out_dir / "checker_stderr.txt"
    comparison_path = write_smoke_comparison(comparison_dir)
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "check_release_readiness_drift_contract.py"),
        str(comparison_dir),
        "--out-dir",
        str(check_dir),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    check_path = check_dir / CHECK_JSON_FILENAME
    check = _read_check(check_path)
    issues = _smoke_issues(completed.returncode, comparison_path, check_dir, check)
    summary = build_smoke_summary(
        out_dir=out_dir,
        comparison_path=comparison_path,
        check_dir=check_dir,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        command=command,
        returncode=completed.returncode,
        check=check,
        issues=issues,
    )
    outputs = write_smoke_summary_outputs(summary, out_dir)
    print_smoke_summary(summary, outputs)
    if issues:
        raise SystemExit(1)


def write_smoke_comparison(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / COMPARISON_JSON_FILENAME
    path.write_text(json.dumps(build_smoke_comparison(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_smoke_comparison() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "title": "MiniGPT release readiness drift contract smoke",
        "summary": {
            "benchmark_history_readiness_requirement_failed_reason_added_count": 1,
            "benchmark_history_readiness_requirement_failed_reason_removed_count": 1,
            "benchmark_history_readiness_requirement_failed_reason_added": ["tiny_smoke_only"],
            "benchmark_history_readiness_requirement_failed_reason_removed": ["legacy_fixture_gap"],
            "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": 0,
            "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": 1,
            "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": {"mixed": 1},
        },
        "deltas": [
            {
                "baseline_release": "baseline-smoke",
                "compared_release": "candidate-smoke",
                "baseline_benchmark_history_readiness_requirement_failed_reasons": [
                    "insufficient_ready_entries",
                    "legacy_fixture_gap",
                ],
                "compared_benchmark_history_readiness_requirement_failed_reasons": [
                    "insufficient_ready_entries",
                    "tiny_smoke_only",
                ],
                "benchmark_history_readiness_requirement_failed_reason_added_count": 1,
                "benchmark_history_readiness_requirement_failed_reason_removed_count": 1,
                "benchmark_history_readiness_requirement_failed_reason_added": ["tiny_smoke_only"],
                "benchmark_history_readiness_requirement_failed_reason_removed": ["legacy_fixture_gap"],
                "benchmark_history_readiness_requirement_failed_reason_drift_status": "mixed",
            }
        ],
    }


def build_smoke_summary(
    *,
    out_dir: Path,
    comparison_path: Path,
    check_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
    command: Sequence[str],
    returncode: int,
    check: dict[str, Any],
    issues: list[str],
) -> dict[str, Any]:
    status = "pass" if not issues else "fail"
    summary_paths = _summary_output_paths(out_dir)
    check_outputs = {
        "json": str(check_dir / CHECK_JSON_FILENAME),
        "text": str(check_dir / CHECK_TEXT_FILENAME),
    }
    return {
        "schema_version": 1,
        "status": status,
        "decision": "continue" if status == "pass" else "fix-release-readiness-drift-contract-smoke",
        "issue_count": len(issues),
        "issues": issues,
        "comparison_path": str(comparison_path),
        "comparison_exists": comparison_path.is_file(),
        "check_status": check.get("status"),
        "check_decision": check.get("decision"),
        "check_issue_count": check.get("issue_count"),
        "check_delta_count": check.get("delta_count"),
        "check_delta_fail_count": check.get("delta_fail_count"),
        "check_expected_mixed_delta_count": _nested(check, "expected_summary", "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"),
        "check_actual_mixed_delta_count": _nested(check, "actual_summary", "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"),
        "check_expected_drift_status_counts": _nested(check, "expected_summary", "benchmark_history_readiness_requirement_failed_reason_drift_status_counts"),
        "check_actual_drift_status_counts": _nested(check, "actual_summary", "benchmark_history_readiness_requirement_failed_reason_drift_status_counts"),
        "checker_returncode": returncode,
        "command": list(command),
        "command_text": " ".join(command),
        "logs": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "stdout_exists": stdout_path.is_file(),
            "stderr_exists": stderr_path.is_file(),
        },
        "outputs": {
            "summary_json": str(summary_paths["json"]),
            "summary_text": str(summary_paths["text"]),
            "check_json": check_outputs["json"],
            "check_text": check_outputs["text"],
        },
    }


def write_smoke_summary_outputs(summary: dict[str, Any], out_dir: Path) -> dict[str, str]:
    paths = _summary_output_paths(out_dir)
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_smoke_summary(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_smoke_summary(summary: dict[str, Any]) -> str:
    rows = [
        ("status", summary.get("status")),
        ("decision", summary.get("decision")),
        ("comparison_path", summary.get("comparison_path")),
        ("comparison_exists", summary.get("comparison_exists")),
        ("checker_returncode", summary.get("checker_returncode")),
        ("check_status", summary.get("check_status")),
        ("check_decision", summary.get("check_decision")),
        ("check_issue_count", summary.get("check_issue_count")),
        ("check_delta_count", summary.get("check_delta_count")),
        ("check_delta_fail_count", summary.get("check_delta_fail_count")),
        ("check_expected_mixed_delta_count", summary.get("check_expected_mixed_delta_count")),
        ("check_actual_mixed_delta_count", summary.get("check_actual_mixed_delta_count")),
        ("check_expected_drift_status_counts", json.dumps(summary.get("check_expected_drift_status_counts") or {}, sort_keys=True)),
        ("check_actual_drift_status_counts", json.dumps(summary.get("check_actual_drift_status_counts") or {}, sort_keys=True)),
        ("issue_count", summary.get("issue_count")),
        ("issues", json.dumps(summary.get("issues"), ensure_ascii=False)),
        ("command_text", summary.get("command_text")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def print_smoke_summary(summary: dict[str, Any], outputs: dict[str, str]) -> None:
    print(f"status={summary.get('status')}")
    print(f"decision={summary.get('decision')}")
    print(f"comparison_path={summary.get('comparison_path')}")
    print(f"checker_returncode={summary.get('checker_returncode')}")
    print(f"check_status={summary.get('check_status')}")
    print(f"check_delta_count={summary.get('check_delta_count')}")
    print(f"check_delta_fail_count={summary.get('check_delta_fail_count')}")
    print(f"check_expected_mixed_delta_count={summary.get('check_expected_mixed_delta_count')}")
    print(f"check_actual_mixed_delta_count={summary.get('check_actual_mixed_delta_count')}")
    print(f"summary_json={outputs['json']}")
    print(f"summary_text={outputs['text']}")


def _smoke_issues(returncode: int, comparison_path: Path, check_dir: Path, check: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    _check(returncode == 0, f"drift contract checker returned {returncode}", issues)
    _check(comparison_path.is_file(), "smoke comparison JSON must exist", issues)
    _check((check_dir / CHECK_JSON_FILENAME).is_file(), "checker JSON output must exist", issues)
    _check((check_dir / CHECK_TEXT_FILENAME).is_file(), "checker text output must exist", issues)
    _check(check.get("status") == "pass", "checker status must pass", issues)
    _check(check.get("decision") == "continue", "checker decision must continue", issues)
    _check(check.get("delta_count") == 1, "smoke fixture must contain one delta", issues)
    _check(check.get("delta_fail_count") == 0, "smoke delta must pass contract checks", issues)
    _check(
        _nested(check, "expected_summary", "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") == 1,
        "checker must recompute mixed delta count",
        issues,
    )
    _check(
        _nested(check, "actual_summary", "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") == 1,
        "checker must read actual mixed delta count",
        issues,
    )
    return issues


def _read_check(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def _summary_output_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "json": out_dir / SMOKE_SUMMARY_JSON_FILENAME,
        "text": out_dir / SMOKE_SUMMARY_TEXT_FILENAME,
    }


def _nested(payload: dict[str, Any], outer: str, inner: str) -> Any:
    value = payload.get(outer)
    if not isinstance(value, dict):
        return None
    return value.get(inner)


def _check(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


if __name__ == "__main__":
    main()
