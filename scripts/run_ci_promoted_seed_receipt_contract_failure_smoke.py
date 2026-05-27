from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]

PLAN_JSON_FILENAME = "ci_promoted_seed_receipt_contract_failure_smoke_plan.json"
PLAN_TEXT_FILENAME = "ci_promoted_seed_receipt_contract_failure_smoke_plan.txt"
CONTRACT_SUMMARY_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
FAILURE_SMOKE_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.json"
FAILURE_SMOKE_CSV_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.csv"
FAILURE_SMOKE_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.html"

DEFAULT_SOURCE_HANDOFF = Path("d") / "448" / "解释" / "promoted-handoff"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CI promoted seed receipt contract failure-smoke wrapper.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "promoted-seed-receipt-contract-failure-smoke-ci")
    parser.add_argument("--source-handoff", type=Path, default=DEFAULT_SOURCE_HANDOFF)
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory before running.")
    return parser.parse_args(argv)


def build_summary_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt_contract.py"),
        str(args.source_handoff),
        "--out-dir",
        str(summary_out_dir(args.out_dir)),
        "--allow-stop",
    ]


def build_failure_smoke_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py"),
        str(summary_out_dir(args.out_dir)),
        "--out-dir",
        str(failure_smoke_out_dir(args.out_dir)),
        "--force",
    ]


def build_invocation_plan(
    args: argparse.Namespace,
    summary_command: Sequence[str],
    failure_smoke_command: Sequence[str],
    *,
    summary_returncode: int | None,
    failure_smoke_returncode: int | None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "wrapper": "run_ci_promoted_seed_receipt_contract_failure_smoke",
        "status": "pass" if summary_returncode == 0 and failure_smoke_returncode == 0 else "fail",
        "decision": (
            "receipt_contract_failure_smoke_verified"
            if summary_returncode == 0 and failure_smoke_returncode == 0
            else "fix_receipt_contract_failure_smoke_ci_wrapper"
        ),
        "out_dir": str(args.out_dir),
        "source_handoff": str(args.source_handoff),
        "summary_out_dir": str(summary_out_dir(args.out_dir)),
        "failure_smoke_out_dir": str(failure_smoke_out_dir(args.out_dir)),
        "flags": {"force": bool(args.force)},
        "commands": [
            {
                "name": "receipt_contract_summary",
                "command": list(summary_command),
                "command_text": " ".join(summary_command),
                "returncode": summary_returncode,
            },
            {
                "name": "receipt_contract_failure_smoke",
                "command": list(failure_smoke_command),
                "command_text": " ".join(failure_smoke_command),
                "returncode": failure_smoke_returncode,
            },
        ],
        "failure_smoke_summary": build_failure_smoke_summary(failure_smoke_out_dir(args.out_dir)),
        "artifact_digest": build_artifact_digest(args.out_dir),
    }


def build_failure_smoke_summary(out_dir: Path) -> dict[str, Any]:
    path = out_dir / FAILURE_SMOKE_JSON_FILENAME
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
        "scenario_count": payload.get("scenario_count"),
        "verified_scenario_count": payload.get("verified_scenario_count"),
        "failed_verification_count": payload.get("failed_verification_count"),
        "issue_count": payload.get("issue_count"),
    }


def build_artifact_digest(out_dir: Path) -> dict[str, Any]:
    summary_dir = summary_out_dir(out_dir)
    smoke_dir = failure_smoke_out_dir(out_dir)
    return {
        "artifacts": {
            "contract_summary_json": file_digest(summary_dir / CONTRACT_SUMMARY_JSON_FILENAME),
            "failure_smoke_json": file_digest(smoke_dir / FAILURE_SMOKE_JSON_FILENAME),
            "failure_smoke_csv": file_digest(smoke_dir / FAILURE_SMOKE_CSV_FILENAME),
            "failure_smoke_html": file_digest(smoke_dir / FAILURE_SMOKE_HTML_FILENAME),
        }
    }


def render_invocation_plan(plan: dict[str, Any]) -> str:
    smoke = as_dict(plan.get("failure_smoke_summary"))
    rows = [
        ("schema_version", plan.get("schema_version")),
        ("wrapper", plan.get("wrapper")),
        ("status", plan.get("status")),
        ("decision", plan.get("decision")),
        ("out_dir", plan.get("out_dir")),
        ("source_handoff", plan.get("source_handoff")),
        ("summary_out_dir", plan.get("summary_out_dir")),
        ("failure_smoke_out_dir", plan.get("failure_smoke_out_dir")),
        ("force", as_dict(plan.get("flags")).get("force")),
        ("summary_returncode", command_returncode(plan, "receipt_contract_summary")),
        ("failure_smoke_returncode", command_returncode(plan, "receipt_contract_failure_smoke")),
        ("failure_smoke_available", smoke.get("available")),
        ("failure_smoke_status", smoke.get("status")),
        ("failure_smoke_decision", smoke.get("decision")),
        ("failure_smoke_scenario_count", smoke.get("scenario_count")),
        ("failure_smoke_verified_scenario_count", smoke.get("verified_scenario_count")),
        ("failure_smoke_failed_verification_count", smoke.get("failed_verification_count")),
        ("contract_summary_json_sha256", digest_value(plan, "contract_summary_json", "sha256")),
        ("failure_smoke_json_sha256", digest_value(plan, "failure_smoke_json", "sha256")),
        ("failure_smoke_csv_sha256", digest_value(plan, "failure_smoke_csv", "sha256")),
        ("failure_smoke_html_sha256", digest_value(plan, "failure_smoke_html", "sha256")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_invocation_plan(plan: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / PLAN_JSON_FILENAME,
        "text": out_dir / PLAN_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["text"].write_text(render_invocation_plan(plan), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def summary_out_dir(out_dir: Path) -> Path:
    return out_dir / "receipt-contract-summary"


def failure_smoke_out_dir(out_dir: Path) -> Path:
    return out_dir / "receipt-contract-failure-smoke"


def file_digest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False, "size_bytes": 0, "sha256": ""}
    data = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def command_returncode(plan: dict[str, Any], name: str) -> int | None:
    for command in plan.get("commands", []):
        if isinstance(command, dict) and command.get("name") == name:
            value = command.get("returncode")
            return int(value) if value is not None else None
    return None


def digest_value(plan: dict[str, Any], name: str, key: str) -> Any:
    artifact_digest = as_dict(plan.get("artifact_digest"))
    artifacts = as_dict(artifact_digest.get("artifacts"))
    return as_dict(artifacts.get(name)).get(key)


def as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        if not args.force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {args.out_dir}")
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_command = build_summary_command(args)
    summary_completed = subprocess.run(summary_command, check=False)
    failure_smoke_returncode: int | None = None
    if summary_completed.returncode == 0:
        failure_smoke_command = build_failure_smoke_command(args)
        failure_smoke_completed = subprocess.run(failure_smoke_command, check=False)
        failure_smoke_returncode = failure_smoke_completed.returncode
    else:
        failure_smoke_command = build_failure_smoke_command(args)
    plan = build_invocation_plan(
        args,
        summary_command,
        failure_smoke_command,
        summary_returncode=summary_completed.returncode,
        failure_smoke_returncode=failure_smoke_returncode,
    )
    outputs = write_invocation_plan(plan, args.out_dir)
    print(f"ci_promoted_receipt_failure_smoke_plan_json={outputs['json']}")
    print(f"ci_promoted_receipt_failure_smoke_plan_text={outputs['text']}")
    raise SystemExit(0 if plan["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
