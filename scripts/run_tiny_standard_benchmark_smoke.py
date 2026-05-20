from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.eval_suite import load_builtin_prompt_suite  # noqa: E402
from minigpt.report_utils import as_dict, list_of_dicts  # noqa: E402


SUMMARY_JSON_FILENAME = "tiny_standard_benchmark_smoke_summary.json"
SUMMARY_TEXT_FILENAME = "tiny_standard_benchmark_smoke_summary.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a CPU tiny MiniGPT train -> eval suite -> generation quality -> pair baseline -> scorecard smoke."
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "tiny-standard-benchmark-smoke")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=24)
    parser.add_argument("--max-iters", type=int, default=2)
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=16)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.case_token_cap < 1:
        raise ValueError("--case-token-cap must be at least 1")
    if args.max_iters < 1:
        raise ValueError("--max-iters must be at least 1")
    out_dir = args.out_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        if not args.force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    suite_payload = build_capped_prompt_suite_payload(args.suite_name, args.case_token_cap)
    suite_path = out_dir / f"{args.suite_name}-capped-suite.json"
    suite_path.write_text(json.dumps(suite_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    corpus_path = out_dir / "tiny_corpus.txt"
    corpus_path.write_text(build_tiny_corpus(suite_payload), encoding="utf-8")

    run_dir = out_dir / "run"
    commands = [
        (
            "train",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "train.py"),
                "--data",
                str(corpus_path),
                "--out-dir",
                str(run_dir),
                "--device",
                "cpu",
                "--tokenizer",
                "char",
                "--max-iters",
                str(args.max_iters),
                "--eval-interval",
                "1",
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
                str(args.seed),
                "--sample-prompt",
                str(suite_payload["cases"][0]["prompt"]),
                "--sample-tokens",
                str(min(12, args.case_token_cap)),
            ],
        ),
        (
            "eval_suite",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "eval_suite.py"),
                "--checkpoint",
                str(run_dir / "checkpoint.pt"),
                "--suite",
                str(suite_path),
                "--out-dir",
                str(run_dir / "eval_suite"),
                "--device",
                "cpu",
            ],
        ),
        (
            "generation_quality",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "analyze_generation_quality.py"),
                "--input",
                str(run_dir / "eval_suite" / "eval_suite.json"),
                "--out-dir",
                str(run_dir / "generation-quality"),
                "--min-continuation-chars",
                "1",
            ],
        ),
        (
            "pair_batch",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "pair_batch.py"),
                "--left-checkpoint",
                str(run_dir / "checkpoint.pt"),
                "--right-checkpoint",
                str(run_dir / "checkpoint.pt"),
                "--left-id",
                "tiny-baseline",
                "--right-id",
                "tiny-repeat",
                "--suite",
                str(suite_path),
                "--out-dir",
                str(run_dir / "pair_batch"),
                "--device",
                "cpu",
            ],
        ),
        (
            "benchmark_scorecard",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "build_benchmark_scorecard.py"),
                "--run-dir",
                str(run_dir),
                "--out-dir",
                str(run_dir / "benchmark-scorecard"),
                "--title",
                "MiniGPT tiny standard benchmark smoke scorecard",
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
                run_dir=run_dir,
                suite_path=suite_path,
                corpus_path=corpus_path,
                command_results=command_results,
                issues=[f"{name} command returned {result['returncode']}"],
            )
            outputs = write_summary_outputs(summary, out_dir)
            print_summary(summary, outputs)
            raise SystemExit(int(result["returncode"] or 1))

    summary = build_summary(
        out_dir=out_dir,
        run_dir=run_dir,
        suite_path=suite_path,
        corpus_path=corpus_path,
        command_results=command_results,
        issues=[],
    )
    outputs = write_summary_outputs(summary, out_dir)
    print_summary(summary, outputs)
    if summary["status"] != "pass":
        raise SystemExit(1)


def build_capped_prompt_suite_payload(suite_name: str, case_token_cap: int) -> dict[str, Any]:
    suite = load_builtin_prompt_suite(suite_name)
    cases = []
    for case in suite.cases:
        payload = case.to_dict()
        payload["max_new_tokens"] = min(int(payload["max_new_tokens"]), case_token_cap)
        cases.append(payload)
    return {
        "suite_name": suite.name,
        "suite_version": f"{suite.version}-cap{case_token_cap}",
        "description": f"{suite.description} Token-capped for CPU smoke verification.",
        "language": suite.language,
        "cases": cases,
    }


def build_tiny_corpus(suite_payload: dict[str, Any]) -> str:
    lines = [
        "MiniGPT tiny benchmark smoke corpus.",
        "This corpus intentionally includes the benchmark prompts so the char tokenizer can encode them.",
    ]
    for case in list_of_dicts(suite_payload.get("cases")):
        lines.append(str(case.get("prompt") or ""))
        lines.append(str(case.get("expected_behavior") or ""))
        lines.append("Evidence chain: train, eval suite, generation quality, pair baseline, benchmark scorecard.")
    return ("\n".join(lines) + "\n") * 6


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
    run_dir: Path,
    suite_path: Path,
    corpus_path: Path,
    command_results: list[dict[str, Any]],
    issues: list[str],
) -> dict[str, Any]:
    artifacts = artifact_status(run_dir, suite_path, corpus_path)
    issue_list = list(issues)
    for key, value in artifacts.items():
        if key.endswith("_exists") and not value:
            issue_list.append(f"missing artifact: {key}")
    status = "pass" if not issue_list else "fail"
    eval_suite = read_json(run_dir / "eval_suite" / "eval_suite.json")
    generation_quality = read_json(run_dir / "generation-quality" / "generation_quality.json")
    pair_batch = read_json(run_dir / "pair_batch" / "pair_generation_batch.json")
    scorecard = read_json(run_dir / "benchmark-scorecard" / "benchmark_scorecard.json")
    train_history = read_json(run_dir / "history_summary.json")
    return {
        "schema_version": 1,
        "status": status,
        "decision": "evidence-ready" if status == "pass" else "fix-smoke-chain",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "out_dir": str(out_dir),
        "run_dir": str(run_dir),
        "suite_path": str(suite_path),
        "corpus_path": str(corpus_path),
        "commands": command_results,
        "artifacts": artifacts,
        "training": training_summary(train_history),
        "eval_suite": eval_suite_summary(eval_suite),
        "generation_quality": generation_quality_summary(generation_quality),
        "pair_batch": pair_batch_summary(pair_batch),
        "benchmark_scorecard": scorecard_summary(scorecard),
        "outputs": {
            "summary_json": str(out_dir / SUMMARY_JSON_FILENAME),
            "summary_text": str(out_dir / SUMMARY_TEXT_FILENAME),
        },
    }


def artifact_status(run_dir: Path, suite_path: Path, corpus_path: Path) -> dict[str, Any]:
    paths = {
        "corpus": corpus_path,
        "suite": suite_path,
        "checkpoint": run_dir / "checkpoint.pt",
        "tokenizer": run_dir / "tokenizer.json",
        "run_manifest": run_dir / "run_manifest.json",
        "history_summary": run_dir / "history_summary.json",
        "eval_suite": run_dir / "eval_suite" / "eval_suite.json",
        "generation_quality": run_dir / "generation-quality" / "generation_quality.json",
        "pair_batch": run_dir / "pair_batch" / "pair_generation_batch.json",
        "pair_batch_html": run_dir / "pair_batch" / "pair_generation_batch.html",
        "benchmark_scorecard": run_dir / "benchmark-scorecard" / "benchmark_scorecard.json",
    }
    return {f"{key}_path": str(path) for key, path in paths.items()} | {
        f"{key}_exists": path.is_file() for key, path in paths.items()
    }


def training_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "available": bool(payload),
        "record_count": payload.get("record_count"),
        "best_val_loss": payload.get("best_val_loss"),
        "final_val_loss": payload.get("final_val_loss"),
    }


def eval_suite_summary(payload: dict[str, Any]) -> dict[str, Any]:
    coverage = as_dict(payload.get("coverage"))
    return {
        "available": bool(payload),
        "suite_name": as_dict(payload.get("benchmark")).get("suite_name"),
        "suite_version": as_dict(payload.get("benchmark")).get("suite_version"),
        "case_count": payload.get("case_count"),
        "coverage_status": coverage.get("status"),
        "comparison_status": coverage.get("comparison_status"),
        "task_type_count": coverage.get("task_type_count"),
        "difficulty_count": coverage.get("difficulty_count"),
    }


def generation_quality_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(payload.get("summary"))
    flag_summary = as_dict(summary.get("flag_summary"))
    return {
        "available": bool(payload),
        "overall_status": summary.get("overall_status"),
        "case_count": summary.get("case_count"),
        "pass_count": summary.get("pass_count"),
        "warn_count": summary.get("warn_count"),
        "fail_count": summary.get("fail_count"),
        "total_flags": flag_summary.get("total_flags"),
    }


def pair_batch_summary(payload: dict[str, Any]) -> dict[str, Any]:
    results = list_of_dicts(payload.get("results"))
    same_checkpoint = same_checkpoint_pair_baseline(payload, results)
    return {
        "available": bool(payload),
        "case_count": payload.get("case_count"),
        "generated_equal_count": payload.get("generated_equal_count"),
        "generated_difference_count": payload.get("generated_difference_count"),
        "continuation_equal_count": payload.get("continuation_equal_count"),
        "avg_abs_generated_char_delta": payload.get("avg_abs_generated_char_delta"),
        "max_abs_generated_char_delta": max_abs_generated_delta(results),
        "same_checkpoint_baseline": same_checkpoint,
        "comparison_mode": "same_checkpoint_baseline" if same_checkpoint else "cross_checkpoint_or_unknown",
    }


def scorecard_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(payload.get("summary"))
    return {
        "available": bool(payload),
        "overall_status": summary.get("overall_status"),
        "overall_score": summary.get("overall_score"),
        "component_count": summary.get("component_count"),
        "rubric_status": summary.get("rubric_status"),
        "rubric_avg_score": summary.get("rubric_avg_score"),
        "pair_batch_cases": summary.get("pair_batch_cases"),
        "pair_generated_differences": summary.get("pair_generated_differences"),
        "pair_same_checkpoint_baseline": summary.get("pair_same_checkpoint_baseline"),
        "pair_comparison_mode": summary.get("pair_comparison_mode"),
        "warnings": payload.get("warnings") if isinstance(payload.get("warnings"), list) else [],
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def render_summary(summary: dict[str, Any]) -> str:
    training = as_dict(summary.get("training"))
    eval_suite = as_dict(summary.get("eval_suite"))
    quality = as_dict(summary.get("generation_quality"))
    pair_batch = as_dict(summary.get("pair_batch"))
    scorecard = as_dict(summary.get("benchmark_scorecard"))
    rows = [
        ("status", summary.get("status")),
        ("decision", summary.get("decision")),
        ("issue_count", summary.get("issue_count")),
        ("run_dir", summary.get("run_dir")),
        ("suite_path", summary.get("suite_path")),
        ("checkpoint_exists", as_dict(summary.get("artifacts")).get("checkpoint_exists")),
        ("eval_suite_case_count", eval_suite.get("case_count")),
        ("eval_suite_coverage_status", eval_suite.get("coverage_status")),
        ("eval_suite_comparison_status", eval_suite.get("comparison_status")),
        ("generation_quality_status", quality.get("overall_status")),
        ("generation_quality_total_flags", quality.get("total_flags")),
        ("pair_batch_case_count", pair_batch.get("case_count")),
        ("pair_generated_difference_count", pair_batch.get("generated_difference_count")),
        ("pair_same_checkpoint_baseline", pair_batch.get("same_checkpoint_baseline")),
        ("pair_comparison_mode", pair_batch.get("comparison_mode")),
        ("scorecard_overall_status", scorecard.get("overall_status")),
        ("scorecard_overall_score", scorecard.get("overall_score")),
        ("scorecard_pair_batch_cases", scorecard.get("pair_batch_cases")),
        ("scorecard_pair_same_checkpoint_baseline", scorecard.get("pair_same_checkpoint_baseline")),
        ("scorecard_pair_comparison_mode", scorecard.get("pair_comparison_mode")),
        ("training_best_val_loss", training.get("best_val_loss")),
        ("training_final_val_loss", training.get("final_val_loss")),
    ]
    rows.extend((f"command_{item['name']}", item["status"]) for item in list_of_dicts(summary.get("commands")))
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_summary_outputs(summary: dict[str, Any], out_dir: Path) -> dict[str, str]:
    paths = {
        "json": out_dir / SUMMARY_JSON_FILENAME,
        "text": out_dir / SUMMARY_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_summary(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def print_summary(summary: dict[str, Any], outputs: dict[str, str]) -> None:
    print(render_summary(summary), end="")
    print(f"summary_json={outputs['json']}")
    print(f"summary_text={outputs['text']}")


def same_checkpoint_pair_baseline(payload: dict[str, Any], results: list[dict[str, Any]]) -> bool:
    case_count = int(payload.get("case_count") or 0)
    comparisons = [as_dict(result.get("comparison")) for result in results]
    if case_count > 0 and len(comparisons) == case_count:
        return all(item.get("same_checkpoint") is True for item in comparisons)
    left = as_dict(payload.get("left"))
    right = as_dict(payload.get("right"))
    if left.get("checkpoint") is not None and right.get("checkpoint") is not None:
        return str(left.get("checkpoint")) == str(right.get("checkpoint"))
    return bool(left.get("checkpoint_id") and left.get("checkpoint_id") == right.get("checkpoint_id"))


def max_abs_generated_delta(results: list[dict[str, Any]]) -> int | None:
    values = []
    for result in results:
        comparison = as_dict(result.get("comparison"))
        value = comparison.get("generated_char_delta")
        if value is not None:
            values.append(abs(int(value)))
    return max(values) if values else None


if __name__ == "__main__":
    main()
