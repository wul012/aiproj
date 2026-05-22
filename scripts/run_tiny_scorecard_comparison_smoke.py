from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import as_dict, list_of_dicts  # noqa: E402
from minigpt.benchmark_history import build_benchmark_history, write_benchmark_history_outputs  # noqa: E402
from scripts.check_tiny_scorecard_comparison_smoke import (  # noqa: E402
    check_summary as check_smoke_summary,
    write_check_outputs as write_smoke_check_outputs,
)


SUMMARY_JSON_FILENAME = "tiny_scorecard_comparison_smoke_summary.json"
SUMMARY_TEXT_FILENAME = "tiny_scorecard_comparison_smoke_summary.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run two CPU tiny standard benchmark smokes, compare their scorecards, and build a promotion decision."
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "tiny-scorecard-comparison-smoke")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=12)
    parser.add_argument("--max-iters", type=int, default=1)
    parser.add_argument(
        "--baseline-max-iters",
        type=int,
        default=None,
        help="Override --max-iters for the baseline tiny training run.",
    )
    parser.add_argument(
        "--candidate-max-iters",
        type=int,
        default=None,
        help="Override --max-iters for the candidate tiny training run.",
    )
    parser.add_argument(
        "--decision-min-rubric-score",
        type=float,
        default=80.0,
        help="Minimum rubric average score passed to the scorecard promotion decision.",
    )
    parser.add_argument(
        "--require-clean-remediation",
        action="store_true",
        help="Fail the smoke when the decision report contains remediation rows.",
    )
    parser.add_argument(
        "--summary-check-out-dir",
        type=Path,
        default=None,
        help="Optionally validate the generated smoke summary and write check JSON/text sidecars.",
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
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--baseline-seed", type=int, default=1337)
    parser.add_argument("--candidate-seed", type=int, default=2026)
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.case_token_cap < 1:
        raise ValueError("--case-token-cap must be at least 1")
    if args.max_iters < 1:
        raise ValueError("--max-iters must be at least 1")
    run_config = build_run_config(args)
    if int(run_config["baseline_max_iters"]) < 1:
        raise ValueError("--baseline-max-iters must be at least 1")
    if int(run_config["candidate_max_iters"]) < 1:
        raise ValueError("--candidate-max-iters must be at least 1")
    out_dir = args.out_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        if not args.force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    baseline_dir = out_dir / "baseline"
    candidate_dir = out_dir / "candidate"
    comparison_dir = out_dir / "scorecard-comparison"
    decision_dir = out_dir / "scorecard-decision"
    history_dir = out_dir / "benchmark-history"
    commands = [
        ("baseline_smoke", tiny_smoke_command(args, baseline_dir, args.baseline_seed, int(run_config["baseline_max_iters"]))),
        ("candidate_smoke", tiny_smoke_command(args, candidate_dir, args.candidate_seed, int(run_config["candidate_max_iters"]))),
        (
            "scorecard_comparison",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "compare_benchmark_scorecards.py"),
                str(baseline_dir / "run"),
                str(candidate_dir / "run"),
                "--name",
                "tiny-baseline",
                "--name",
                "tiny-candidate",
                "--baseline",
                "tiny-baseline",
                "--out-dir",
                str(comparison_dir),
                "--title",
                "MiniGPT tiny scorecard comparison smoke",
            ],
        ),
        (
            "scorecard_decision",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "build_benchmark_scorecard_decision.py"),
                str(comparison_dir),
                "--out-dir",
                str(decision_dir),
                "--min-rubric-score",
                str(run_config["decision_min_rubric_score"]),
                "--title",
                "MiniGPT tiny scorecard decision smoke",
            ],
        ),
    ]

    command_results = []
    for name, command in commands:
        result = run_command(name, command, logs_dir)
        command_results.append(result)
        if result["returncode"] != 0:
            summary = build_summary(
                out_dir=out_dir,
                baseline_dir=baseline_dir,
                candidate_dir=candidate_dir,
                comparison_dir=comparison_dir,
                decision_dir=decision_dir,
                history_dir=history_dir,
                run_config=run_config,
                command_results=command_results,
                issues=[f"{name} command returned {result['returncode']}"],
            )
            outputs = write_summary_and_optional_check(
                summary,
                out_dir,
                summary_check_out_dir=args.summary_check_out_dir,
                summary_check_allow_gate_stop=args.summary_check_allow_gate_stop,
            )
            print_summary(summary, outputs)
            raise SystemExit(int(result["returncode"] or 1))

    summary = build_summary(
        out_dir=out_dir,
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        comparison_dir=comparison_dir,
        decision_dir=decision_dir,
        history_dir=history_dir,
        run_config=run_config,
        command_results=command_results,
        issues=[],
    )
    outputs = write_summary_and_optional_check(
        summary,
        out_dir,
        summary_check_out_dir=args.summary_check_out_dir,
        summary_check_allow_gate_stop=args.summary_check_allow_gate_stop,
    )
    print_summary(summary, outputs)
    summary_check = as_dict(summary.get("summary_check"))
    if summary_check.get("status") == "fail" and not args.summary_check_no_fail:
        raise SystemExit(1)
    if summary["status"] != "pass":
        raise SystemExit(1)


def build_run_config(args: argparse.Namespace) -> dict[str, Any]:
    baseline_max_iters = int(args.baseline_max_iters if args.baseline_max_iters is not None else args.max_iters)
    candidate_max_iters = int(args.candidate_max_iters if args.candidate_max_iters is not None else args.max_iters)
    decision_min_rubric_score = float(args.decision_min_rubric_score)
    if not 0.0 <= decision_min_rubric_score <= 100.0:
        raise ValueError("--decision-min-rubric-score must be between 0 and 100")
    max_iters_delta = candidate_max_iters - baseline_max_iters
    if max_iters_delta > 0:
        budget_mode = "candidate_more_iters"
    elif max_iters_delta < 0:
        budget_mode = "candidate_fewer_iters"
    else:
        budget_mode = "matched_iters"
    return {
        "suite_name": args.suite_name,
        "case_token_cap": args.case_token_cap,
        "baseline_max_iters": baseline_max_iters,
        "candidate_max_iters": candidate_max_iters,
        "max_iters_delta": max_iters_delta,
        "budget_mode": budget_mode,
        "decision_min_rubric_score": decision_min_rubric_score,
        "require_clean_remediation": bool(args.require_clean_remediation),
        "summary_check_requested": getattr(args, "summary_check_out_dir", None) is not None,
        "summary_check_allow_gate_stop": bool(getattr(args, "summary_check_allow_gate_stop", False)),
        "summary_check_no_fail": bool(getattr(args, "summary_check_no_fail", False)),
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "block_size": args.block_size,
        "n_layer": args.n_layer,
        "n_head": args.n_head,
        "n_embd": args.n_embd,
        "baseline_seed": args.baseline_seed,
        "candidate_seed": args.candidate_seed,
    }


def tiny_smoke_command(args: argparse.Namespace, out_dir: Path, seed: int, max_iters: int) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_tiny_standard_benchmark_smoke.py"),
        "--out-dir",
        str(out_dir),
        "--suite-name",
        str(args.suite_name),
        "--case-token-cap",
        str(args.case_token_cap),
        "--max-iters",
        str(max_iters),
        "--eval-iters",
        str(args.eval_iters),
        "--batch-size",
        str(args.batch_size),
        "--block-size",
        str(args.block_size),
        "--n-layer",
        str(args.n_layer),
        "--n-head",
        str(args.n_head),
        "--n-embd",
        str(args.n_embd),
        "--seed",
        str(seed),
        "--force",
    ]


def run_command(name: str, command: list[str], logs_dir: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / f"{name}_stdout.txt"
    stderr_path = logs_dir / f"{name}_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return {
        "name": name,
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "command": command,
        "command_text": " ".join(command),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }


def build_summary(
    *,
    out_dir: Path,
    baseline_dir: Path,
    candidate_dir: Path,
    comparison_dir: Path,
    decision_dir: Path,
    history_dir: Path,
    run_config: dict[str, Any],
    command_results: list[dict[str, Any]],
    issues: list[str],
) -> dict[str, Any]:
    history_report, history_outputs = build_tiny_benchmark_history(comparison_dir, decision_dir, history_dir)
    artifacts = artifact_status(baseline_dir, candidate_dir, comparison_dir, decision_dir, history_dir)
    issue_list = list(issues)
    for key, value in artifacts.items():
        if key.endswith("_exists") and not value:
            issue_list.append(f"missing artifact: {key}")
    status = "pass" if not issue_list else "fail"
    baseline_smoke = read_json(baseline_dir / "tiny_standard_benchmark_smoke_summary.json")
    candidate_smoke = read_json(candidate_dir / "tiny_standard_benchmark_smoke_summary.json")
    comparison = read_json(comparison_dir / "benchmark_scorecard_comparison.json")
    decision = read_json(decision_dir / "benchmark_scorecard_decision.json")
    decision_view = decision_summary(decision)
    remediation_gate = remediation_gate_status(run_config, decision_view)
    if remediation_gate["decision"] == "stop":
        issue_list.append("remediation gate blocked: decision contains remediation rows")
    status = "pass" if not issue_list else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "comparison-evidence-ready" if status == "pass" else "fix-comparison-smoke-chain",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "out_dir": str(out_dir),
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "comparison_dir": str(comparison_dir),
        "decision_dir": str(decision_dir),
        "benchmark_history_dir": str(history_dir),
        "run_config": run_config,
        "commands": command_results,
        "artifacts": artifacts,
        "baseline_smoke": smoke_summary(baseline_smoke),
        "candidate_smoke": smoke_summary(candidate_smoke),
        "scorecard_comparison": comparison_summary(comparison),
        "scorecard_decision": decision_view,
        "benchmark_history": history_summary(history_report, history_outputs),
        "remediation_gate": remediation_gate,
        "interpretation": {
            "comparison_is_smoke_only": True,
            "model_quality_claim": "not_claimed",
            "reason": "Tiny CPU scorecard deltas and decisions verify benchmark plumbing and configuration routing, not robust model improvement.",
        },
        "outputs": {
            "summary_json": str(out_dir / SUMMARY_JSON_FILENAME),
            "summary_text": str(out_dir / SUMMARY_TEXT_FILENAME),
        },
    }


def build_tiny_benchmark_history(
    comparison_dir: Path,
    decision_dir: Path,
    history_dir: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    comparison_json = comparison_dir / "benchmark_scorecard_comparison.json"
    decision_json = decision_dir / "benchmark_scorecard_decision.json"
    if not comparison_json.is_file() or not decision_json.is_file():
        return {}, {}
    report = build_benchmark_history(
        [comparison_json],
        decision_paths=[decision_json],
        names=["tiny-scorecard-smoke"],
        evidence_kind="tiny-smoke",
        title="MiniGPT tiny scorecard smoke benchmark history",
    )
    outputs = write_benchmark_history_outputs(report, history_dir)
    return report, outputs


def artifact_status(
    baseline_dir: Path,
    candidate_dir: Path,
    comparison_dir: Path,
    decision_dir: Path,
    history_dir: Path,
) -> dict[str, Any]:
    paths = {
        "baseline_smoke_summary": baseline_dir / "tiny_standard_benchmark_smoke_summary.json",
        "baseline_scorecard": baseline_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json",
        "baseline_pair_batch": baseline_dir / "run" / "pair_batch" / "pair_generation_batch.json",
        "candidate_smoke_summary": candidate_dir / "tiny_standard_benchmark_smoke_summary.json",
        "candidate_scorecard": candidate_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json",
        "candidate_pair_batch": candidate_dir / "run" / "pair_batch" / "pair_generation_batch.json",
        "comparison_json": comparison_dir / "benchmark_scorecard_comparison.json",
        "comparison_csv": comparison_dir / "benchmark_scorecard_comparison.csv",
        "comparison_case_delta_csv": comparison_dir / "benchmark_scorecard_case_deltas.csv",
        "comparison_markdown": comparison_dir / "benchmark_scorecard_comparison.md",
        "comparison_html": comparison_dir / "benchmark_scorecard_comparison.html",
        "decision_json": decision_dir / "benchmark_scorecard_decision.json",
        "decision_csv": decision_dir / "benchmark_scorecard_decision.csv",
        "decision_remediation_csv": decision_dir / "benchmark_scorecard_decision_remediation.csv",
        "decision_markdown": decision_dir / "benchmark_scorecard_decision.md",
        "decision_html": decision_dir / "benchmark_scorecard_decision.html",
        "benchmark_history_json": history_dir / "benchmark_history.json",
        "benchmark_history_csv": history_dir / "benchmark_history.csv",
        "benchmark_history_markdown": history_dir / "benchmark_history.md",
        "benchmark_history_html": history_dir / "benchmark_history.html",
    }
    return {f"{key}_path": str(path) for key, path in paths.items()} | {
        f"{key}_exists": path.is_file() for key, path in paths.items()
    }


def smoke_summary(payload: dict[str, Any]) -> dict[str, Any]:
    scorecard = as_dict(payload.get("benchmark_scorecard"))
    pair_batch = as_dict(payload.get("pair_batch"))
    eval_suite = as_dict(payload.get("eval_suite"))
    return {
        "available": bool(payload),
        "status": payload.get("status"),
        "decision": payload.get("decision"),
        "eval_suite_case_count": eval_suite.get("case_count"),
        "scorecard_overall_status": scorecard.get("overall_status"),
        "scorecard_overall_score": scorecard.get("overall_score"),
        "pair_same_checkpoint_baseline": pair_batch.get("same_checkpoint_baseline"),
        "pair_generated_difference_count": pair_batch.get("generated_difference_count"),
    }


def comparison_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(payload.get("summary"))
    baseline = as_dict(payload.get("baseline"))
    best_overall = as_dict(payload.get("best_by_overall_score"))
    best_rubric = as_dict(payload.get("best_by_rubric_avg_score"))
    return {
        "available": bool(payload),
        "scorecard_count": payload.get("scorecard_count"),
        "baseline_name": baseline.get("name"),
        "best_by_overall_score": best_overall.get("name"),
        "best_by_rubric_avg_score": best_rubric.get("name"),
        "improved_overall_count": summary.get("improved_overall_count"),
        "regressed_overall_count": summary.get("regressed_overall_count"),
        "improved_rubric_count": summary.get("improved_rubric_count"),
        "regressed_rubric_count": summary.get("regressed_rubric_count"),
        "case_delta_count": summary.get("case_delta_count"),
        "case_regression_count": summary.get("case_regression_count"),
        "generation_quality_flag_improvement_count": summary.get("generation_quality_flag_improvement_count"),
        "generation_quality_flag_regression_count": summary.get("generation_quality_flag_regression_count"),
        "non_comparison_ready_count": summary.get("non_comparison_ready_count"),
        "recommendation_count": len(payload.get("recommendations")) if isinstance(payload.get("recommendations"), list) else 0,
    }


def history_summary(report: dict[str, Any], outputs: dict[str, str]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    requirement = as_dict(report.get("readiness_requirement"))
    return {
        "available": bool(report),
        "entry_count": summary.get("entry_count"),
        "ready_count": summary.get("ready_count"),
        "review_count": summary.get("review_count"),
        "blocked_count": summary.get("blocked_count"),
        "best_candidate_name": summary.get("best_candidate_name"),
        "model_quality_claim": summary.get("model_quality_claim"),
        "readiness_requirement_status": requirement.get("status"),
        "readiness_requirement_decision": requirement.get("decision"),
        "readiness_requirement_exit_code": requirement.get("exit_code"),
        "readiness_requirement_failed_reasons": requirement.get("failed_reasons", []),
        "outputs": outputs,
    }


def decision_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(payload.get("summary"))
    selected = as_dict(payload.get("selected_run"))
    evaluations = list_of_dicts(payload.get("candidate_evaluations"))
    nonbaseline = [item for item in evaluations if not item.get("is_baseline")]
    blocked = [item for item in nonbaseline if item.get("blockers")]
    review = [item for item in nonbaseline if item.get("review_items") and not item.get("blockers")]
    threshold_profile = threshold_block_profile(blocked, payload.get("min_rubric_score"), summary)
    threshold_block = first_threshold_block(blocked, payload.get("min_rubric_score"), summary)
    raw_recommendations = payload.get("recommendations")
    recommendations = [str(item) for item in raw_recommendations if isinstance(item, str)] if isinstance(raw_recommendations, list) else []
    remediation_plan = list_of_dicts(payload.get("remediation_plan"))
    first_remediation = remediation_plan[0] if remediation_plan else {}
    return {
        "available": bool(payload),
        "decision_status": payload.get("decision_status"),
        "recommended_action": payload.get("recommended_action"),
        "selected_name": selected.get("name"),
        "selected_relation": selected.get("decision_relation"),
        "candidate_evaluation_count": len(evaluations),
        "candidate_count": summary.get("candidate_count"),
        "clean_candidate_count": summary.get("clean_candidate_count"),
        "review_candidate_count": summary.get("review_candidate_count"),
        "blocked_candidate_count": summary.get("blocked_candidate_count"),
        "non_comparison_ready_candidate_count": summary.get("non_comparison_ready_candidate_count"),
        "blocker_category_counts": as_dict(summary.get("blocker_category_counts")),
        "dominant_blocker_category": summary.get("dominant_blocker_category"),
        "review_category_counts": as_dict(summary.get("review_category_counts")),
        "dominant_review_category": summary.get("dominant_review_category"),
        "remediation_plan_count": summary.get("remediation_plan_count"),
        "remediation_blocker_count": summary.get("remediation_blocker_count"),
        "remediation_review_count": summary.get("remediation_review_count"),
        "dominant_remediation_kind": summary.get("dominant_remediation_kind"),
        "dominant_remediation_category": summary.get("dominant_remediation_category"),
        "dominant_remediation_action": summary.get("dominant_remediation_action"),
        "blocked_candidate_names": [str(item.get("name")) for item in blocked if item.get("name") is not None],
        "review_candidate_names": [str(item.get("name")) for item in review if item.get("name") is not None],
        "first_blocked_candidate": first_name(blocked),
        "first_blocker": first_list_item(blocked, "blockers"),
        "first_threshold_blocked_candidate": threshold_block.get("name"),
        "first_threshold_blocker": threshold_block.get("blocker"),
        "first_threshold_rubric_score": threshold_block.get("rubric_avg_score"),
        "first_threshold_min_rubric_score": threshold_block.get("min_rubric_score"),
        "first_threshold_margin": threshold_block.get("margin"),
        "threshold_blocked_candidate_count": threshold_profile.get("blocked_candidate_count"),
        "threshold_blocked_candidate_names": threshold_profile.get("blocked_candidate_names"),
        "threshold_closest_candidate": threshold_profile.get("closest_candidate"),
        "threshold_closest_margin": threshold_profile.get("closest_margin"),
        "threshold_largest_gap_candidate": threshold_profile.get("largest_gap_candidate"),
        "threshold_largest_gap_margin": threshold_profile.get("largest_gap_margin"),
        "first_review_candidate": first_name(review),
        "first_review_item": first_list_item(review, "review_items"),
        "remediation_count": len(remediation_plan),
        "first_remediation_category": first_remediation.get("category"),
        "first_remediation_action_code": first_remediation.get("action_code"),
        "first_remediation_severity": first_remediation.get("severity"),
        "first_remediation_owner_scope": first_remediation.get("owner_scope"),
        "first_remediation_action": first_remediation.get("action"),
        "recommendation_count": len(recommendations),
        "first_recommendation": recommendations[0] if recommendations else None,
    }


def remediation_gate_status(run_config: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    required = bool(run_config.get("require_clean_remediation"))
    remediation_count = int(decision.get("remediation_count") or 0)
    failed = required and remediation_count > 0
    issues = []
    if failed:
        issues.append(
            {
                "code": "remediation_rows_present",
                "severity": decision.get("first_remediation_severity") or "blocker",
                "category": decision.get("first_remediation_category"),
                "action_code": decision.get("first_remediation_action_code"),
                "owner_scope": decision.get("first_remediation_owner_scope"),
                "count": remediation_count,
            }
        )
    return {
        "required": required,
        "status": "fail" if failed else "pass",
        "decision": "stop" if failed else "continue",
        "remediation_count": remediation_count,
        "issue_count": len(issues),
        "issues": issues,
        "first_category": decision.get("first_remediation_category"),
        "first_action_code": decision.get("first_remediation_action_code"),
        "first_severity": decision.get("first_remediation_severity"),
        "first_owner_scope": decision.get("first_remediation_owner_scope"),
        "reason": "remediation rows must be cleared before strict smoke promotion" if failed else "clean remediation is not required or no remediation rows were found",
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def render_summary(summary: dict[str, Any]) -> str:
    baseline = as_dict(summary.get("baseline_smoke"))
    candidate = as_dict(summary.get("candidate_smoke"))
    comparison = as_dict(summary.get("scorecard_comparison"))
    decision = as_dict(summary.get("scorecard_decision"))
    history = as_dict(summary.get("benchmark_history"))
    remediation_gate = as_dict(summary.get("remediation_gate"))
    remediation_gate_issues = list_of_dicts(remediation_gate.get("issues"))
    first_remediation_gate_issue = remediation_gate_issues[0] if remediation_gate_issues else {}
    run_config = as_dict(summary.get("run_config"))
    interpretation = as_dict(summary.get("interpretation"))
    rows = [
        ("status", summary.get("status")),
        ("decision", summary.get("decision")),
        ("issue_count", summary.get("issue_count")),
        ("config_suite_name", run_config.get("suite_name")),
        ("config_case_token_cap", run_config.get("case_token_cap")),
        ("config_baseline_max_iters", run_config.get("baseline_max_iters")),
        ("config_candidate_max_iters", run_config.get("candidate_max_iters")),
        ("config_max_iters_delta", run_config.get("max_iters_delta")),
        ("config_budget_mode", run_config.get("budget_mode")),
        ("config_decision_min_rubric_score", run_config.get("decision_min_rubric_score")),
        ("config_require_clean_remediation", run_config.get("require_clean_remediation")),
        ("config_summary_check_requested", run_config.get("summary_check_requested")),
        ("config_summary_check_allow_gate_stop", run_config.get("summary_check_allow_gate_stop")),
        ("config_summary_check_no_fail", run_config.get("summary_check_no_fail")),
        ("baseline_scorecard_status", baseline.get("scorecard_overall_status")),
        ("baseline_scorecard_score", baseline.get("scorecard_overall_score")),
        ("candidate_scorecard_status", candidate.get("scorecard_overall_status")),
        ("candidate_scorecard_score", candidate.get("scorecard_overall_score")),
        ("baseline_pair_same_checkpoint", baseline.get("pair_same_checkpoint_baseline")),
        ("candidate_pair_same_checkpoint", candidate.get("pair_same_checkpoint_baseline")),
        ("comparison_scorecard_count", comparison.get("scorecard_count")),
        ("comparison_baseline", comparison.get("baseline_name")),
        ("comparison_best_overall", comparison.get("best_by_overall_score")),
        ("comparison_improved_overall_count", comparison.get("improved_overall_count")),
        ("comparison_regressed_overall_count", comparison.get("regressed_overall_count")),
        ("comparison_case_delta_count", comparison.get("case_delta_count")),
        ("comparison_non_ready_count", comparison.get("non_comparison_ready_count")),
        ("history_entry_count", history.get("entry_count")),
        ("history_ready_count", history.get("ready_count")),
        ("history_model_quality_claim", history.get("model_quality_claim")),
        ("history_readiness_requirement_status", history.get("readiness_requirement_status")),
        ("history_readiness_requirement_decision", history.get("readiness_requirement_decision")),
        ("history_readiness_requirement_exit_code", history.get("readiness_requirement_exit_code")),
        (
            "history_readiness_requirement_failed_reasons",
            ",".join(str(item) for item in history.get("readiness_requirement_failed_reasons", [])),
        ),
        ("history_json", as_dict(history.get("outputs")).get("json")),
        ("decision_status", decision.get("decision_status")),
        ("decision_action", decision.get("recommended_action")),
        ("decision_selected_name", decision.get("selected_name")),
        ("decision_candidate_evaluation_count", decision.get("candidate_evaluation_count")),
        ("decision_blocked_candidate_count", decision.get("blocked_candidate_count")),
        ("decision_blocked_candidates", ",".join(str(item) for item in decision.get("blocked_candidate_names", []))),
        ("decision_dominant_blocker_category", decision.get("dominant_blocker_category")),
        ("decision_dominant_review_category", decision.get("dominant_review_category")),
        ("decision_remediation_plan_count", decision.get("remediation_plan_count")),
        ("decision_remediation_blocker_count", decision.get("remediation_blocker_count")),
        ("decision_remediation_review_count", decision.get("remediation_review_count")),
        ("decision_dominant_remediation_kind", decision.get("dominant_remediation_kind")),
        ("decision_dominant_remediation_category", decision.get("dominant_remediation_category")),
        ("decision_dominant_remediation_action", decision.get("dominant_remediation_action")),
        ("decision_blocker_category_counts", format_counts(decision.get("blocker_category_counts"))),
        ("decision_review_category_counts", format_counts(decision.get("review_category_counts"))),
        ("decision_first_blocker", decision.get("first_blocker")),
        ("decision_first_threshold_candidate", decision.get("first_threshold_blocked_candidate")),
        ("decision_first_threshold_score", decision.get("first_threshold_rubric_score")),
        ("decision_first_threshold_min", decision.get("first_threshold_min_rubric_score")),
        ("decision_first_threshold_margin", decision.get("first_threshold_margin")),
        ("decision_threshold_blocked_count", decision.get("threshold_blocked_candidate_count")),
        ("decision_threshold_blocked_candidates", ",".join(str(item) for item in decision.get("threshold_blocked_candidate_names", []))),
        ("decision_threshold_closest_candidate", decision.get("threshold_closest_candidate")),
        ("decision_threshold_closest_margin", decision.get("threshold_closest_margin")),
        ("decision_threshold_largest_gap_candidate", decision.get("threshold_largest_gap_candidate")),
        ("decision_threshold_largest_gap_margin", decision.get("threshold_largest_gap_margin")),
        ("decision_review_candidates", ",".join(str(item) for item in decision.get("review_candidate_names", []))),
        ("decision_first_review_item", decision.get("first_review_item")),
        ("decision_remediation_count", decision.get("remediation_count")),
        ("decision_first_remediation_category", decision.get("first_remediation_category")),
        ("decision_first_remediation_action_code", decision.get("first_remediation_action_code")),
        ("decision_first_remediation_severity", decision.get("first_remediation_severity")),
        ("decision_first_remediation_owner_scope", decision.get("first_remediation_owner_scope")),
        ("decision_first_remediation_action", decision.get("first_remediation_action")),
        ("remediation_gate_required", remediation_gate.get("required")),
        ("remediation_gate_status", remediation_gate.get("status")),
        ("remediation_gate_decision", remediation_gate.get("decision")),
        ("remediation_gate_count", remediation_gate.get("remediation_count")),
        ("remediation_gate_issue_count", remediation_gate.get("issue_count")),
        ("remediation_gate_first_issue_code", first_remediation_gate_issue.get("code")),
        ("remediation_gate_first_issue_severity", first_remediation_gate_issue.get("severity")),
        ("remediation_gate_first_issue_category", first_remediation_gate_issue.get("category")),
        ("remediation_gate_first_issue_action_code", first_remediation_gate_issue.get("action_code")),
        ("remediation_gate_first_issue_owner_scope", first_remediation_gate_issue.get("owner_scope")),
        ("remediation_gate_first_category", remediation_gate.get("first_category")),
        ("remediation_gate_first_action_code", remediation_gate.get("first_action_code")),
        ("remediation_gate_first_severity", remediation_gate.get("first_severity")),
        ("remediation_gate_first_owner_scope", remediation_gate.get("first_owner_scope")),
        ("decision_first_recommendation", decision.get("first_recommendation")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
    ]
    summary_check = as_dict(summary.get("summary_check"))
    summary_check_outputs = as_dict(summary.get("summary_check_outputs"))
    summary_check_issues = list_of_dicts(summary_check.get("issues"))
    first_summary_check_issue = summary_check_issues[0] if summary_check_issues else {}
    rows.extend(
        [
            ("summary_check_status", summary_check.get("status")),
            ("summary_check_decision", summary_check.get("decision")),
            ("summary_check_issue_count", summary_check.get("issue_count")),
            ("summary_check_allowed_gate_stop", summary_check.get("allowed_gate_stop")),
            ("summary_check_first_issue_code", first_summary_check_issue.get("code")),
            ("summary_check_json", summary_check_outputs.get("json")),
            ("summary_check_text", summary_check_outputs.get("text")),
        ]
    )
    rows.extend((f"command_{item['name']}", item["status"]) for item in list_of_dicts(summary.get("commands")))
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_summary_outputs(summary: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / SUMMARY_JSON_FILENAME,
        "text": out_dir / SUMMARY_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_summary(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def write_summary_and_optional_check(
    summary: dict[str, Any],
    out_dir: Path,
    *,
    summary_check_out_dir: Path | None = None,
    summary_check_allow_gate_stop: bool = False,
) -> dict[str, str]:
    outputs = write_summary_outputs(summary, out_dir)
    if summary_check_out_dir is None:
        return outputs
    summary_check = check_smoke_summary(
        summary,
        summary_path=Path(outputs["json"]),
        allow_gate_stop=summary_check_allow_gate_stop,
    )
    summary_check_outputs = write_smoke_check_outputs(summary_check, summary_check_out_dir)
    summary["summary_check"] = summary_check
    summary["summary_check_outputs"] = summary_check_outputs
    return write_summary_outputs(summary, out_dir)


def print_summary(summary: dict[str, Any], outputs: dict[str, str]) -> None:
    print(render_summary(summary), end="")
    print(f"summary_json={outputs['json']}")
    print(f"summary_text={outputs['text']}")


def first_name(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    value = rows[0].get("name")
    return None if value is None else str(value)


def first_list_item(rows: list[dict[str, Any]], key: str) -> str | None:
    for row in rows:
        values = row.get(key)
        if isinstance(values, list):
            for item in values:
                if item is not None:
                    return str(item)
    return None


def format_counts(value: Any) -> str:
    counts = as_dict(value)
    return ",".join(f"{key}:{counts[key]}" for key in sorted(counts))


def first_threshold_block(rows: list[dict[str, Any]], min_rubric_score: Any, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = as_dict(summary)
    if summary.get("first_threshold_blocked_candidate") is not None:
        return {
            "name": summary.get("first_threshold_blocked_candidate"),
            "blocker": summary.get("first_threshold_blocker"),
            "rubric_avg_score": summary.get("first_threshold_rubric_score"),
            "min_rubric_score": summary.get("first_threshold_min_rubric_score"),
            "margin": summary.get("first_threshold_margin"),
        }
    blocks = threshold_blocks(rows, min_rubric_score)
    return blocks[0] if blocks else {}


def threshold_block_profile(rows: list[dict[str, Any]], min_rubric_score: Any, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = as_dict(summary)
    if summary.get("threshold_blocked_candidate_count") is not None:
        return {
            "blocked_candidate_count": summary.get("threshold_blocked_candidate_count"),
            "blocked_candidate_names": summary.get("threshold_blocked_candidate_names"),
            "closest_candidate": summary.get("threshold_closest_candidate"),
            "closest_margin": summary.get("threshold_closest_margin"),
            "largest_gap_candidate": summary.get("threshold_largest_gap_candidate"),
            "largest_gap_margin": summary.get("threshold_largest_gap_margin"),
        }
    blocks = threshold_blocks(rows, min_rubric_score)
    if not blocks:
        return {
            "blocked_candidate_count": 0,
            "blocked_candidate_names": [],
            "closest_candidate": None,
            "closest_margin": None,
            "largest_gap_candidate": None,
            "largest_gap_margin": None,
        }
    with_margin = [item for item in blocks if item.get("margin") is not None]
    closest = max(with_margin, key=lambda item: float(item.get("margin") or 0.0)) if with_margin else {}
    largest_gap = min(with_margin, key=lambda item: float(item.get("margin") or 0.0)) if with_margin else {}
    return {
        "blocked_candidate_count": len(blocks),
        "blocked_candidate_names": [str(item.get("name")) for item in blocks if item.get("name") is not None],
        "closest_candidate": closest.get("name"),
        "closest_margin": closest.get("margin"),
        "largest_gap_candidate": largest_gap.get("name"),
        "largest_gap_margin": largest_gap.get("margin"),
    }


def threshold_blocks(rows: list[dict[str, Any]], min_rubric_score: Any) -> list[dict[str, Any]]:
    threshold = float_or_none(min_rubric_score)
    blocks = []
    for row in rows:
        blocker = first_matching_list_item(row, "blockers", "rubric_avg_score below")
        if blocker is None:
            continue
        rubric_score = float_or_none(row.get("rubric_avg_score"))
        margin = None if rubric_score is None or threshold is None else round(rubric_score - threshold, 4)
        blocks.append(
            {
                "name": None if row.get("name") is None else str(row.get("name")),
                "blocker": blocker,
                "rubric_avg_score": rubric_score,
                "min_rubric_score": threshold,
                "margin": margin,
            }
        )
    return blocks


def first_matching_list_item(row: dict[str, Any], key: str, prefix: str) -> str | None:
    values = row.get(key)
    if not isinstance(values, list):
        return None
    for item in values:
        text = str(item)
        if text.startswith(prefix):
            return text
    return None


def float_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


if __name__ == "__main__":
    main()
