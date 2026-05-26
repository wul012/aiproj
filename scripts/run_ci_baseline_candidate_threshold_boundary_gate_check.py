from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]

PLAN_JSON_FILENAME = "ci_baseline_candidate_threshold_boundary_gate_check_plan.json"
PLAN_TEXT_FILENAME = "ci_baseline_candidate_threshold_boundary_gate_check_plan.txt"
GATE_CHECK_JSON_FILENAME = "baseline_candidate_threshold_boundary_gate_check.json"
GATE_CHECK_TEXT_FILENAME = "baseline_candidate_threshold_boundary_gate_check.txt"
GATE_CHECK_MARKDOWN_FILENAME = "baseline_candidate_threshold_boundary_gate_check.md"
GATE_CHECK_HTML_FILENAME = "baseline_candidate_threshold_boundary_gate_check.html"
BOUNDARY_SMOKE_JSON_FILENAME = "baseline_candidate_threshold_boundary_smoke.json"

DEFAULT_SMOKE_SUMMARY = (
    ROOT
    / "d"
    / "438"
    / "解释"
    / "baseline-candidate-threshold-boundary-smoke"
    / "tiny-scorecard-comparison-smoke"
    / "tiny_scorecard_comparison_smoke_summary.json"
)

CI_BOUNDARY_GATE_CONFIG = {
    "thresholds": "0:1:0.5",
    "require_diagnosis_pass": True,
    "expected_exit_code": 2,
    "expected_diagnosis_decision": "candidate_not_accepted",
    "require_pass": True,
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CI baseline-candidate threshold boundary expected-exit gate check.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-threshold-boundary-gate-check-ci")
    parser.add_argument("--smoke-summary", type=Path, default=DEFAULT_SMOKE_SUMMARY)
    parser.add_argument("--thresholds", default=str(CI_BOUNDARY_GATE_CONFIG["thresholds"]))
    parser.add_argument("--expected-exit-code", type=int, default=int(CI_BOUNDARY_GATE_CONFIG["expected_exit_code"]))
    parser.add_argument("--expected-diagnosis-decision", default=str(CI_BOUNDARY_GATE_CONFIG["expected_diagnosis_decision"]))
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory before running the gate check.")
    return parser.parse_args(argv)


def build_ci_boundary_gate_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "check_baseline_candidate_threshold_boundary_gate.py"),
        "--smoke-summary",
        str(args.smoke_summary),
        "--out-dir",
        str(args.out_dir),
        "--thresholds",
        str(args.thresholds),
        "--require-diagnosis-pass",
        "--expected-exit-code",
        str(args.expected_exit_code),
        "--expected-diagnosis-decision",
        str(args.expected_diagnosis_decision),
        "--require-pass",
    ]
    if args.force:
        command.append("--force")
    return command


def build_invocation_plan(args: argparse.Namespace, command: Sequence[str], *, returncode: int | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "wrapper": "run_ci_baseline_candidate_threshold_boundary_gate_check",
        "out_dir": str(args.out_dir),
        "smoke_summary": str(args.smoke_summary),
        "config": {
            "thresholds": str(args.thresholds),
            "require_diagnosis_pass": True,
            "expected_exit_code": int(args.expected_exit_code),
            "expected_diagnosis_decision": str(args.expected_diagnosis_decision),
            "require_pass": True,
        },
        "flags": {"force": bool(args.force)},
        "command": list(command),
        "command_text": " ".join(command),
        "returncode": returncode,
        "gate_check_summary": build_gate_check_summary(args.out_dir),
        "artifact_digest": build_artifact_digest(args.out_dir),
    }


def render_invocation_plan(plan: dict[str, Any]) -> str:
    config = _as_dict(plan.get("config"))
    gate = _as_dict(plan.get("gate_check_summary"))
    rows = [
        ("schema_version", plan.get("schema_version")),
        ("wrapper", plan.get("wrapper")),
        ("out_dir", plan.get("out_dir")),
        ("smoke_summary", plan.get("smoke_summary")),
        ("thresholds", config.get("thresholds")),
        ("require_diagnosis_pass", config.get("require_diagnosis_pass")),
        ("expected_exit_code", config.get("expected_exit_code")),
        ("expected_diagnosis_decision", config.get("expected_diagnosis_decision")),
        ("require_pass", config.get("require_pass")),
        ("force", _as_dict(plan.get("flags")).get("force")),
        ("returncode", plan.get("returncode")),
        ("gate_check_available", gate.get("available")),
        ("gate_check_status", gate.get("status")),
        ("gate_check_decision", gate.get("decision")),
        ("gate_check_failed_count", gate.get("failed_count")),
        ("gate_check_actual_exit_code", gate.get("actual_exit_code")),
        ("gate_check_expected_exit_code", gate.get("expected_exit_code")),
        ("gate_check_diagnosis_decision", gate.get("diagnosis_decision")),
        ("gate_check_json_sha256", _digest_value(plan, "gate_check_json", "sha256")),
        ("gate_check_text_sha256", _digest_value(plan, "gate_check_text", "sha256")),
        ("gate_check_markdown_sha256", _digest_value(plan, "gate_check_markdown", "sha256")),
        ("gate_check_html_sha256", _digest_value(plan, "gate_check_html", "sha256")),
        ("boundary_smoke_json_sha256", _digest_value(plan, "boundary_smoke_json", "sha256")),
        ("command_text", plan.get("command_text")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def build_gate_check_summary(out_dir: Path) -> dict[str, Any]:
    path = out_dir / "gate-check" / GATE_CHECK_JSON_FILENAME
    if not path.is_file():
        return {"available": False, "parse_status": "missing", "path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": False, "parse_status": "invalid_json", "path": str(path), "error": str(exc)}
    if not isinstance(payload, dict):
        return {"available": False, "parse_status": "invalid_payload", "path": str(path)}
    return {
        "available": True,
        "parse_status": "pass",
        "path": str(path),
        "status": payload.get("status"),
        "decision": payload.get("decision"),
        "failed_count": payload.get("failed_count"),
        "actual_exit_code": payload.get("actual_exit_code"),
        "expected_exit_code": payload.get("expected_exit_code"),
        "diagnosis_decision": payload.get("diagnosis_decision"),
        "boundary_decision": payload.get("boundary_decision"),
    }


def build_artifact_digest(out_dir: Path) -> dict[str, Any]:
    gate_dir = out_dir / "gate-check"
    boundary_dir = out_dir / "threshold-boundary-smoke" / "live-boundary-summary"
    return {
        "artifacts": {
            "gate_check_json": _file_digest(gate_dir / GATE_CHECK_JSON_FILENAME),
            "gate_check_text": _file_digest(gate_dir / GATE_CHECK_TEXT_FILENAME),
            "gate_check_markdown": _file_digest(gate_dir / GATE_CHECK_MARKDOWN_FILENAME),
            "gate_check_html": _file_digest(gate_dir / GATE_CHECK_HTML_FILENAME),
            "boundary_smoke_json": _file_digest(boundary_dir / BOUNDARY_SMOKE_JSON_FILENAME),
        }
    }


def write_invocation_plan(plan: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / PLAN_JSON_FILENAME,
        "text": out_dir / PLAN_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["text"].write_text(render_invocation_plan(plan), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _file_digest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False, "size_bytes": 0, "sha256": ""}
    data = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _digest_value(plan: dict[str, Any], name: str, key: str) -> Any:
    artifact_digest = _as_dict(plan.get("artifact_digest"))
    artifacts = _as_dict(artifact_digest.get("artifacts"))
    return _as_dict(artifacts.get(name)).get(key)


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    command = build_ci_boundary_gate_command(args)
    completed = subprocess.run(command, check=False)
    plan = build_invocation_plan(args, command, returncode=completed.returncode)
    outputs = write_invocation_plan(plan, args.out_dir)
    print(f"ci_boundary_gate_plan_json={outputs['json']}")
    print(f"ci_boundary_gate_plan_text={outputs['text']}")
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
