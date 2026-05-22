from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]

PLAN_JSON_FILENAME = "ci_tiny_scorecard_smoke_plan.json"
PLAN_TEXT_FILENAME = "ci_tiny_scorecard_smoke_plan.txt"
SUMMARY_JSON_FILENAME = "tiny_scorecard_comparison_smoke_summary.json"
SUMMARY_TEXT_FILENAME = "tiny_scorecard_comparison_smoke_summary.txt"
CHECK_JSON_FILENAME = "tiny_scorecard_comparison_smoke_check.json"
CHECK_TEXT_FILENAME = "tiny_scorecard_comparison_smoke_check.txt"
BENCHMARK_HISTORY_JSON_FILENAME = "benchmark_history.json"
BENCHMARK_HISTORY_CSV_FILENAME = "benchmark_history.csv"
BENCHMARK_HISTORY_MARKDOWN_FILENAME = "benchmark_history.md"
BENCHMARK_HISTORY_HTML_FILENAME = "benchmark_history.html"

CI_TINY_SCORECARD_CONFIG = {
    "suite_name": "standard-zh",
    "case_token_cap": 3,
    "max_iters": 1,
    "baseline_max_iters": 1,
    "candidate_max_iters": 2,
    "decision_min_rubric_score": 60.0,
    "eval_iters": 1,
    "batch_size": 2,
    "block_size": 8,
    "n_embd": 8,
    "baseline_seed": 1337,
    "candidate_seed": 2026,
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the CI-sized tiny scorecard comparison smoke with inline summary-check sidecars."
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "tiny-scorecard-comparison-smoke-ci")
    parser.add_argument(
        "--summary-check-out-dir",
        type=Path,
        default=ROOT / "runs" / "tiny-scorecard-comparison-smoke-check-ci",
    )
    parser.add_argument(
        "--summary-check-allow-gate-stop",
        action="store_true",
        help="Let the inline summary checker accept an expected strict remediation gate stop.",
    )
    parser.add_argument(
        "--summary-check-no-fail",
        action="store_true",
        help="Write inline summary-check outputs without failing the smoke on summary-check failures.",
    )
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def build_ci_smoke_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_tiny_scorecard_comparison_smoke.py"),
        "--out-dir",
        str(args.out_dir),
        "--suite-name",
        str(CI_TINY_SCORECARD_CONFIG["suite_name"]),
        "--case-token-cap",
        str(CI_TINY_SCORECARD_CONFIG["case_token_cap"]),
        "--max-iters",
        str(CI_TINY_SCORECARD_CONFIG["max_iters"]),
        "--baseline-max-iters",
        str(CI_TINY_SCORECARD_CONFIG["baseline_max_iters"]),
        "--candidate-max-iters",
        str(CI_TINY_SCORECARD_CONFIG["candidate_max_iters"]),
        "--decision-min-rubric-score",
        str(CI_TINY_SCORECARD_CONFIG["decision_min_rubric_score"]),
        "--eval-iters",
        str(CI_TINY_SCORECARD_CONFIG["eval_iters"]),
        "--batch-size",
        str(CI_TINY_SCORECARD_CONFIG["batch_size"]),
        "--block-size",
        str(CI_TINY_SCORECARD_CONFIG["block_size"]),
        "--n-embd",
        str(CI_TINY_SCORECARD_CONFIG["n_embd"]),
        "--baseline-seed",
        str(CI_TINY_SCORECARD_CONFIG["baseline_seed"]),
        "--candidate-seed",
        str(CI_TINY_SCORECARD_CONFIG["candidate_seed"]),
        "--summary-check-out-dir",
        str(args.summary_check_out_dir),
    ]
    if args.summary_check_allow_gate_stop:
        command.append("--summary-check-allow-gate-stop")
    if args.summary_check_no_fail:
        command.append("--summary-check-no-fail")
    if args.force:
        command.append("--force")
    return command


def build_invocation_plan(
    args: argparse.Namespace,
    command: Sequence[str],
    *,
    returncode: int | None = None,
    summary_digest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "wrapper": "run_ci_tiny_scorecard_comparison_smoke",
        "out_dir": str(args.out_dir),
        "summary_check_out_dir": str(args.summary_check_out_dir),
        "config": dict(CI_TINY_SCORECARD_CONFIG),
        "flags": {
            "summary_check_allow_gate_stop": bool(args.summary_check_allow_gate_stop),
            "summary_check_no_fail": bool(args.summary_check_no_fail),
            "force": bool(args.force),
        },
        "command": list(command),
        "command_text": " ".join(command),
        "returncode": returncode,
        "summary_digest": summary_digest or build_summary_digest(args.out_dir, args.summary_check_out_dir),
        "benchmark_history_summary": build_benchmark_history_summary(args.out_dir),
    }


def render_invocation_plan(plan: dict[str, Any]) -> str:
    config = plan["config"]
    flags = plan["flags"]
    digest = plan.get("summary_digest", {})
    rows = [
        ("schema_version", plan["schema_version"]),
        ("wrapper", plan["wrapper"]),
        ("out_dir", plan["out_dir"]),
        ("summary_check_out_dir", plan["summary_check_out_dir"]),
        ("suite_name", config["suite_name"]),
        ("case_token_cap", config["case_token_cap"]),
        ("baseline_max_iters", config["baseline_max_iters"]),
        ("candidate_max_iters", config["candidate_max_iters"]),
        ("decision_min_rubric_score", config["decision_min_rubric_score"]),
        ("eval_iters", config["eval_iters"]),
        ("batch_size", config["batch_size"]),
        ("block_size", config["block_size"]),
        ("n_embd", config["n_embd"]),
        ("baseline_seed", config["baseline_seed"]),
        ("candidate_seed", config["candidate_seed"]),
        ("summary_check_allow_gate_stop", flags["summary_check_allow_gate_stop"]),
        ("summary_check_no_fail", flags["summary_check_no_fail"]),
        ("force", flags["force"]),
        ("returncode", plan.get("returncode")),
        ("summary_json_sha256", _artifact_digest_value(digest, "summary_json", "sha256")),
        ("summary_text_sha256", _artifact_digest_value(digest, "summary_text", "sha256")),
        ("check_json_sha256", _artifact_digest_value(digest, "summary_check_json", "sha256")),
        ("check_text_sha256", _artifact_digest_value(digest, "summary_check_text", "sha256")),
        ("benchmark_history_json_sha256", _artifact_digest_value(digest, "benchmark_history_json", "sha256")),
        ("benchmark_history_csv_sha256", _artifact_digest_value(digest, "benchmark_history_csv", "sha256")),
        ("benchmark_history_markdown_sha256", _artifact_digest_value(digest, "benchmark_history_markdown", "sha256")),
        ("benchmark_history_html_sha256", _artifact_digest_value(digest, "benchmark_history_html", "sha256")),
        ("benchmark_history_available", _benchmark_history_value(plan, "available")),
        ("benchmark_history_parse_status", _benchmark_history_value(plan, "parse_status")),
        ("benchmark_history_evidence_kind", _benchmark_history_value(plan, "evidence_kind")),
        ("benchmark_history_entry_count", _benchmark_history_value(plan, "entry_count")),
        ("benchmark_history_ready_count", _benchmark_history_value(plan, "ready_count")),
        ("benchmark_history_model_quality_claim", _benchmark_history_value(plan, "model_quality_claim")),
        ("benchmark_history_readiness_requirement_status", _benchmark_history_value(plan, "readiness_requirement_status")),
        ("benchmark_history_readiness_requirement_decision", _benchmark_history_value(plan, "readiness_requirement_decision")),
        ("benchmark_history_readiness_requirement_exit_code", _benchmark_history_value(plan, "readiness_requirement_exit_code")),
        (
            "benchmark_history_readiness_requirement_failed_reasons",
            ",".join(_string_list(_benchmark_history_value(plan, "readiness_requirement_failed_reasons"))),
        ),
        ("benchmark_history_latest_boundary", _benchmark_history_value(plan, "latest_boundary")),
        ("command_text", plan["command_text"]),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def build_summary_digest(out_dir: Path, summary_check_out_dir: Path) -> dict[str, Any]:
    return {
        "artifacts": {
            "summary_json": _file_digest(out_dir / SUMMARY_JSON_FILENAME),
            "summary_text": _file_digest(out_dir / SUMMARY_TEXT_FILENAME),
            "summary_check_json": _file_digest(summary_check_out_dir / CHECK_JSON_FILENAME),
            "summary_check_text": _file_digest(summary_check_out_dir / CHECK_TEXT_FILENAME),
            "benchmark_history_json": _file_digest(out_dir / "benchmark-history" / BENCHMARK_HISTORY_JSON_FILENAME),
            "benchmark_history_csv": _file_digest(out_dir / "benchmark-history" / BENCHMARK_HISTORY_CSV_FILENAME),
            "benchmark_history_markdown": _file_digest(out_dir / "benchmark-history" / BENCHMARK_HISTORY_MARKDOWN_FILENAME),
            "benchmark_history_html": _file_digest(out_dir / "benchmark-history" / BENCHMARK_HISTORY_HTML_FILENAME),
        }
    }


def build_benchmark_history_summary(out_dir: Path) -> dict[str, Any]:
    path = out_dir / "benchmark-history" / BENCHMARK_HISTORY_JSON_FILENAME
    if not path.is_file():
        return {
            "available": False,
            "parse_status": "missing",
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "available": False,
            "parse_status": "invalid_json",
            "path": str(path),
            "error": str(exc),
        }
    if not isinstance(payload, dict):
        return {
            "available": False,
            "parse_status": "invalid_payload",
            "path": str(path),
        }
    summary = _as_dict(payload.get("summary"))
    requirement = _as_dict(payload.get("readiness_requirement"))
    entries = [dict(item) for item in payload.get("entries", []) if isinstance(item, dict)] if isinstance(payload.get("entries"), list) else []
    return {
        "available": True,
        "parse_status": "pass",
        "path": str(path),
        "evidence_kind": payload.get("evidence_kind"),
        "entry_count": summary.get("entry_count"),
        "ready_count": summary.get("ready_count"),
        "model_quality_claim": summary.get("model_quality_claim"),
        "readiness_requirement_status": requirement.get("status"),
        "readiness_requirement_decision": requirement.get("decision"),
        "readiness_requirement_exit_code": requirement.get("exit_code"),
        "readiness_requirement_failed_reasons": _string_list(requirement.get("failed_reasons")),
        "latest_boundary": entries[-1].get("boundary") if entries else None,
        "boundary_values": sorted({str(item.get("boundary")) for item in entries if item.get("boundary")}),
    }


def _file_digest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": 0,
            "sha256": "",
        }
    data = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _artifact_digest_value(digest: dict[str, Any], name: str, key: str) -> Any:
    artifacts = digest.get("artifacts", {})
    artifact = artifacts.get(name, {})
    return artifact.get(key)


def _benchmark_history_value(plan: dict[str, Any], key: str) -> Any:
    return _as_dict(plan.get("benchmark_history_summary")).get(key)


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item) != ""]


def write_invocation_plan(plan: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / PLAN_JSON_FILENAME,
        "text": out_dir / PLAN_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["text"].write_text(render_invocation_plan(plan), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    command = build_ci_smoke_command(args)
    completed = subprocess.run(command, check=False)
    digest = build_summary_digest(args.out_dir, args.summary_check_out_dir)
    plan = build_invocation_plan(args, command, returncode=completed.returncode, summary_digest=digest)
    outputs = write_invocation_plan(plan, args.out_dir)
    print(f"ci_plan_json={outputs['json']}")
    print(f"ci_plan_text={outputs['text']}")
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
