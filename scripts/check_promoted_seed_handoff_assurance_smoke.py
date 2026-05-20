from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    (out_dir / "execute_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (out_dir / "execute_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise SystemExit(completed.returncode)
    report_path = handoff_dir / "promoted_training_scale_seed_handoff.json"
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
    _require(checks["handoff_assurance_status"] == "pass", "handoff assurance status must pass")
    _require(checks["handoff_assurance_decision"] == "continue", "handoff assurance decision must continue")
    _require(
        checks["handoff_assurance_embedded_receipt_check_status"] == "pass",
        "embedded receipt-check status must pass",
    )
    _require(
        checks["handoff_assurance_embedded_receipt_check_sidecar_status"] == "pass",
        "embedded receipt-check sidecar status must pass",
    )
    _require(checks["handoff_assurance_output_json_exists"] is True, "assurance JSON sidecar must exist")
    _require(checks["handoff_assurance_output_text_exists"] is True, "assurance text sidecar must exist")
    _require(
        _is_file_reference(checks["handoff_assurance_output_json"], ROOT),
        "assurance JSON output path must be a file",
    )
    _require(
        _is_file_reference(checks["handoff_assurance_output_text"], ROOT),
        "assurance text output path must be a file",
    )
    print("status=pass")
    print("decision=continue")
    print(f"seed={seed}")
    print(f"handoff_report={report_path}")
    print("command=" + " ".join(command))
    for key, value in checks.items():
        print(f"{key}={value}")


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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


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
