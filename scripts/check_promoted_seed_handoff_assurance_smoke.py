from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SMOKE_SUMMARY_JSON_FILENAME = "promoted_seed_handoff_assurance_smoke_summary.json"
SMOKE_SUMMARY_TEXT_FILENAME = "promoted_seed_handoff_assurance_smoke_summary.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a MiniGPT promoted seed handoff inline assurance smoke check.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "promoted-seed-handoff-assurance-smoke")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    seed = _write_seed_tree(out_dir / "seed-source")
    handoff_dir = out_dir / "handoff"
    receipt_check_dir = out_dir / "receipt-check"
    embedded_check_dir = out_dir / "embedded-receipt-check"
    assurance_dir = out_dir / "assurance"
    stdout_path = out_dir / "execute_stdout.txt"
    stderr_path = out_dir / "execute_stderr.txt"
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
        str(seed),
        "--out-dir",
        str(handoff_dir),
        "--execute",
        "--require-clean-evidence",
        "--receipt-check-out-dir",
        str(receipt_check_dir),
        "--embedded-receipt-check-out-dir",
        str(embedded_check_dir),
        "--assurance-out-dir",
        str(assurance_dir),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    report_path = handoff_dir / "promoted_training_scale_seed_handoff.json"
    if completed.returncode:
        summary = _build_smoke_summary(
            out_dir=out_dir,
            seed=seed,
            handoff_dir=handoff_dir,
            receipt_check_dir=receipt_check_dir,
            embedded_check_dir=embedded_check_dir,
            assurance_dir=assurance_dir,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            report_path=report_path,
            command=command,
            returncode=completed.returncode,
            checks={},
            issues=[f"handoff execution command returned {completed.returncode}"],
        )
        summary_outputs = write_smoke_summary_outputs(summary, out_dir)
        _print_smoke_summary(summary, summary_outputs)
        raise SystemExit(completed.returncode)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assurance = _dict(report.get("handoff_assurance"))
    assurance_outputs = _dict(report.get("handoff_assurance_outputs"))
    checks = {
        "handoff_assurance_status": assurance.get("status"),
        "handoff_assurance_decision": assurance.get("decision"),
        "handoff_assurance_embedded_receipt_check_status": assurance.get("embedded_receipt_check_status"),
        "handoff_assurance_embedded_receipt_check_sidecar_status": assurance.get("embedded_receipt_check_sidecar_status"),
        "handoff_assurance_output_json_exists": assurance.get("embedded_receipt_check_output_json_exists"),
        "handoff_assurance_output_text_exists": assurance.get("embedded_receipt_check_output_text_exists"),
        "handoff_assurance_output_json": assurance_outputs.get("json"),
        "handoff_assurance_output_text": assurance_outputs.get("text"),
    }
    issues: list[str] = []
    _check(checks["handoff_assurance_status"] == "pass", "handoff assurance status must pass", issues)
    _check(checks["handoff_assurance_decision"] == "continue", "handoff assurance decision must continue", issues)
    _check(
        checks["handoff_assurance_embedded_receipt_check_status"] == "pass",
        "embedded receipt-check status must pass",
        issues,
    )
    _check(
        checks["handoff_assurance_embedded_receipt_check_sidecar_status"] == "pass",
        "embedded receipt-check sidecar status must pass",
        issues,
    )
    _check(checks["handoff_assurance_output_json_exists"] is True, "assurance JSON sidecar must exist", issues)
    _check(checks["handoff_assurance_output_text_exists"] is True, "assurance text sidecar must exist", issues)
    _check(
        _is_file_reference(checks["handoff_assurance_output_json"], ROOT),
        "assurance JSON output path must be a file",
        issues,
    )
    _check(
        _is_file_reference(checks["handoff_assurance_output_text"], ROOT),
        "assurance text output path must be a file",
        issues,
    )
    summary = _build_smoke_summary(
        out_dir=out_dir,
        seed=seed,
        handoff_dir=handoff_dir,
        receipt_check_dir=receipt_check_dir,
        embedded_check_dir=embedded_check_dir,
        assurance_dir=assurance_dir,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        report_path=report_path,
        command=command,
        returncode=completed.returncode,
        checks=checks,
        issues=issues,
    )
    summary_outputs = write_smoke_summary_outputs(summary, out_dir)
    _print_smoke_summary(summary, summary_outputs)
    if issues:
        raise SystemExit(1)


def _write_seed_tree(root: Path) -> Path:
    source = root / "corpus.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("MiniGPT assurance smoke corpus.\n" * 180, encoding="utf-8")
    plan_out = root / "next-plan"
    batch_out = root / "batch"
    suite = {"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh", "source": "inherited"}
    command = [
        sys.executable,
        "scripts/plan_training_scale.py",
        str(source),
        "--project-root",
        str(ROOT),
        "--out-dir",
        str(plan_out),
        "--batch-out-root",
        str(batch_out),
        "--dataset-name",
        "assurance-smoke",
        "--dataset-version-prefix",
        "v292-smoke",
        "--suite-name",
        "standard-zh",
        "--max-variants",
        "1",
    ]
    seed = {
        "schema_version": 1,
        "title": "promoted seed handoff assurance smoke",
        "generated_at": "2026-05-20T00:00:00Z",
        "seed_status": "ready",
        "baseline_seed": {
            "selected_name": "beta",
            "decision_status": "accepted",
            "gate_status": "pass",
            "batch_status": "completed",
            "readiness_score": 107,
            "training_scale_run_path": str(root / "beta" / "training_scale_run.json"),
            "training_scale_run_exists": True,
            "suite": suite,
            "suite_path": suite["path"],
            "handoff_suite_guard": {
                "selected_handoff_require_suite_consistency": True,
                "selected_handoff_suite_consistency": "consistent",
                "selected_handoff_suite_mismatch_count": 0,
                "selected_handoff_selected_suite_path": "builtin:standard-zh",
                "handoff_require_suite_consistency_count": 1,
                "handoff_suite_consistent_count": 1,
                "handoff_suite_mismatch_total": 0,
                "comparison_ready_handoff_suite_mismatch_total": 0,
            },
        },
        "next_plan": {
            "project_root": str(ROOT),
            "dataset_name": "assurance-smoke",
            "dataset_version_prefix": "v292-smoke",
            "suite": suite,
            "suite_path": suite["path"],
            "suite_source": suite["source"],
            "plan_out_dir": str(plan_out),
            "batch_out_root": str(batch_out),
            "sources": [
                {
                    "path": str(source),
                    "resolved_path": str(source.resolve()),
                    "exists": True,
                    "kind": "file",
                }
            ],
            "command": command,
            "command_text": " ".join(command),
            "command_available": True,
            "execution_ready": True,
        },
        "summary": {
            "seed_status": "ready",
            "selected_name": "beta",
            "command_available": True,
        },
    }
    seed_path = root / "promoted-seed" / "promoted_training_scale_seed.json"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return seed_path


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _check(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def _build_smoke_summary(
    *,
    out_dir: Path,
    seed: Path,
    handoff_dir: Path,
    receipt_check_dir: Path,
    embedded_check_dir: Path,
    assurance_dir: Path,
    stdout_path: Path,
    stderr_path: Path,
    report_path: Path,
    command: list[str],
    returncode: int,
    checks: dict[str, object],
    issues: list[str],
) -> dict[str, Any]:
    status = "pass" if not issues else "fail"
    decision = "continue" if status == "pass" else "stop"
    summary_outputs = _smoke_summary_output_paths(out_dir)
    return {
        "schema_version": 1,
        "status": status,
        "decision": decision,
        "issue_count": len(issues),
        "issues": issues,
        "execute_returncode": returncode,
        "seed": str(seed),
        "handoff_report": str(report_path),
        "handoff_report_exists": report_path.is_file(),
        "command": command,
        "command_text": " ".join(command),
        "directories": {
            "out_dir": str(out_dir),
            "handoff": str(handoff_dir),
            "receipt_check": str(receipt_check_dir),
            "embedded_receipt_check": str(embedded_check_dir),
            "assurance": str(assurance_dir),
        },
        "logs": {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "stdout_exists": stdout_path.is_file(),
            "stderr_exists": stderr_path.is_file(),
        },
        "checks": checks,
        "outputs": {
            "summary_json": str(summary_outputs["json"]),
            "summary_text": str(summary_outputs["text"]),
            "handoff_assurance_json": str(checks.get("handoff_assurance_output_json") or ""),
            "handoff_assurance_text": str(checks.get("handoff_assurance_output_text") or ""),
        },
    }


def _render_smoke_summary(summary: dict[str, Any]) -> str:
    checks = _dict(summary.get("checks"))
    rows = [
        ("smoke_status", summary.get("status")),
        ("smoke_decision", summary.get("decision")),
        ("smoke_execute_returncode", summary.get("execute_returncode")),
        ("smoke_seed", summary.get("seed")),
        ("smoke_handoff_report", summary.get("handoff_report")),
        ("smoke_handoff_report_exists", summary.get("handoff_report_exists")),
        ("smoke_issue_count", summary.get("issue_count")),
        ("smoke_issues", json.dumps(summary.get("issues"), ensure_ascii=False)),
    ]
    rows.extend((key, value) for key, value in checks.items())
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def _smoke_summary_output_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "json": out_dir / SMOKE_SUMMARY_JSON_FILENAME,
        "text": out_dir / SMOKE_SUMMARY_TEXT_FILENAME,
    }


def write_smoke_summary_outputs(summary: dict[str, Any], out_dir: Path) -> dict[str, str]:
    paths = _smoke_summary_output_paths(out_dir)
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(_render_smoke_summary(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _print_smoke_summary(summary: dict[str, Any], outputs: dict[str, str]) -> None:
    checks = _dict(summary.get("checks"))
    print(f"status={summary.get('status')}")
    print(f"decision={summary.get('decision')}")
    print(f"seed={summary.get('seed')}")
    print(f"handoff_report={summary.get('handoff_report')}")
    print(f"command={summary.get('command_text')}")
    print(f"summary_json={outputs['json']}")
    print(f"summary_text={outputs['text']}")
    for key, value in checks.items():
        print(f"{key}={value}")


def _is_file_reference(value: object, base_dir: Path) -> bool:
    if not value:
        return False
    candidate = Path(str(value))
    if candidate.is_file():
        return True
    if candidate.is_absolute():
        return False
    return (base_dir / candidate).is_file()


if __name__ == "__main__":
    main()
