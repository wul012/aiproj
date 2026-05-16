from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any

from minigpt.training_portfolio_artifacts import (
    render_training_portfolio_html,
    render_training_portfolio_markdown,
    write_training_portfolio_html,
    write_training_portfolio_json,
    write_training_portfolio_markdown,
    write_training_portfolio_outputs,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_training_portfolio_plan(
    project_root: str | Path,
    sources: list[str | Path],
    *,
    out_root: str | Path,
    run_name: str = "portfolio-run",
    dataset_name: str = "portfolio-zh",
    dataset_version: str = "v1",
    dataset_description: str = "MiniGPT training portfolio dataset.",
    suite_path: str | Path | None = None,
    request_log_path: str | Path | None = None,
    python_executable: str = "python",
    device: str = "cpu",
    max_iters: int = 100,
    eval_interval: int = 25,
    eval_iters: int = 5,
    batch_size: int = 16,
    block_size: int = 64,
    n_layer: int = 2,
    n_head: int = 2,
    n_embd: int = 64,
    learning_rate: float = 3e-4,
    seed: int = 1337,
    sample_prompt: str = "MiniGPT",
    sample_tokens: int = 40,
    title: str = "MiniGPT training portfolio pipeline",
) -> dict[str, Any]:
    if not sources:
        raise ValueError("at least one training source is required")

    root = Path(project_root)
    out = Path(out_root)
    dataset_root = out / "datasets"
    dataset_dir = dataset_root / dataset_name / dataset_version
    run_dir = out / "runs" / run_name
    eval_dir = run_dir / "eval_suite"
    generation_quality_dir = eval_dir / "generation-quality"
    scorecard_dir = run_dir / "benchmark-scorecard"
    registry_dir = out / "registry"
    maturity_dir = out / "maturity-summary"
    request_summary_dir = out / "request-history-summary"
    narrative_dir = out / "maturity-narrative"
    suite = Path(suite_path) if suite_path is not None else root / "data" / "eval_prompts.json"

    artifacts = {
        "dataset_dir": str(dataset_dir),
        "corpus": str(dataset_dir / "corpus.txt"),
        "dataset_version": str(dataset_dir / "dataset_version.json"),
        "dataset_quality": str(dataset_dir / "dataset_quality.json"),
        "dataset_card": str(dataset_dir / "dataset_card.json"),
        "run_dir": str(run_dir),
        "checkpoint": str(run_dir / "checkpoint.pt"),
        "run_manifest": str(run_dir / "run_manifest.json"),
        "eval_suite": str(eval_dir / "eval_suite.json"),
        "generation_quality": str(generation_quality_dir / "generation_quality.json"),
        "benchmark_scorecard": str(scorecard_dir / "benchmark_scorecard.json"),
        "registry": str(registry_dir / "registry.json"),
        "maturity_summary": str(maturity_dir / "maturity_summary.json"),
        "maturity_narrative": str(narrative_dir / "maturity_narrative.json"),
    }
    if request_log_path is not None:
        artifacts["request_history_summary"] = str(request_summary_dir / "request_history_summary.json")

    steps = [
        _step(
            "prepare_dataset",
            "Prepare a versioned training dataset",
            [
                python_executable,
                str(root / "scripts" / "prepare_dataset.py"),
                *[str(Path(source)) for source in sources],
                "--dataset-name",
                dataset_name,
                "--dataset-version",
                dataset_version,
                "--dataset-description",
                dataset_description,
                "--dataset-root",
                str(dataset_root),
            ],
            [artifacts["corpus"], artifacts["dataset_version"], artifacts["dataset_quality"]],
        ),
        _step(
            "train",
            "Train a MiniGPT checkpoint from the prepared corpus",
            _train_command(
                python_executable=python_executable,
                script=root / "scripts" / "train.py",
                corpus=dataset_dir / "corpus.txt",
                run_dir=run_dir,
                device=device,
                max_iters=max_iters,
                eval_interval=eval_interval,
                eval_iters=eval_iters,
                batch_size=batch_size,
                block_size=block_size,
                n_layer=n_layer,
                n_head=n_head,
                n_embd=n_embd,
                learning_rate=learning_rate,
                seed=seed,
                sample_prompt=sample_prompt,
                sample_tokens=sample_tokens,
            ),
            [artifacts["checkpoint"], artifacts["run_manifest"]],
        ),
        _step(
            "eval_suite",
            "Run the fixed prompt benchmark suite",
            [
                python_executable,
                str(root / "scripts" / "eval_suite.py"),
                "--checkpoint",
                str(run_dir / "checkpoint.pt"),
                "--suite",
                str(suite),
                "--out-dir",
                str(eval_dir),
                "--device",
                device,
            ],
            [artifacts["eval_suite"]],
        ),
        _step(
            "generation_quality",
            "Analyze generation quality from eval outputs",
            [
                python_executable,
                str(root / "scripts" / "analyze_generation_quality.py"),
                "--input",
                str(eval_dir / "eval_suite.json"),
                "--out-dir",
                str(generation_quality_dir),
            ],
            [artifacts["generation_quality"]],
        ),
        _step(
            "benchmark_scorecard",
            "Build a benchmark scorecard for the trained run",
            [
                python_executable,
                str(root / "scripts" / "build_benchmark_scorecard.py"),
                "--run-dir",
                str(run_dir),
                "--out-dir",
                str(scorecard_dir),
            ],
            [artifacts["benchmark_scorecard"]],
        ),
        _step(
            "dataset_card",
            "Build a dataset card for the training corpus",
            [
                python_executable,
                str(root / "scripts" / "build_dataset_card.py"),
                "--dataset-dir",
                str(dataset_dir),
            ],
            [artifacts["dataset_card"]],
        ),
        _step(
            "registry",
            "Register the trained run",
            [
                python_executable,
                str(root / "scripts" / "register_runs.py"),
                str(run_dir),
                "--name",
                run_name,
                "--out-dir",
                str(registry_dir),
            ],
            [artifacts["registry"]],
        ),
        _step(
            "maturity_summary",
            "Build maturity summary with registry context",
            [
                python_executable,
                str(root / "scripts" / "build_maturity_summary.py"),
                "--project-root",
                str(root),
                "--registry",
                str(registry_dir / "registry.json"),
                "--out-dir",
                str(maturity_dir),
            ],
            [artifacts["maturity_summary"]],
        ),
    ]

    request_summary_path = None
    if request_log_path is not None:
        request_summary_path = request_summary_dir / "request_history_summary.json"
        steps.append(
            _step(
                "request_history_summary",
                "Summarize optional local inference request log",
                [
                    python_executable,
                    str(root / "scripts" / "summarize_request_history.py"),
                    "--request-log",
                    str(Path(request_log_path)),
                    "--out-dir",
                    str(request_summary_dir),
                ],
                [str(request_summary_path)],
            )
        )

    narrative_command = [
        python_executable,
        str(root / "scripts" / "build_maturity_narrative.py"),
        "--project-root",
        str(root),
        "--maturity",
        str(maturity_dir / "maturity_summary.json"),
        "--registry",
        str(registry_dir / "registry.json"),
        "--benchmark-scorecard",
        str(scorecard_dir / "benchmark_scorecard.json"),
        "--dataset-card",
        str(dataset_dir / "dataset_card.json"),
        "--out-dir",
        str(narrative_dir),
    ]
    if request_summary_path is not None:
        narrative_command.extend(["--request-history-summary", str(request_summary_path)])
    steps.append(
        _step(
            "maturity_narrative",
            "Build release-quality maturity narrative",
            narrative_command,
            [artifacts["maturity_narrative"]],
        )
    )

    return {
        "schema_version": 1,
        "title": title,
        "project_root": str(root),
        "out_root": str(out),
        "run_name": run_name,
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "suite_path": str(suite),
        "request_log_path": str(request_log_path) if request_log_path is not None else None,
        "artifacts": artifacts,
        "steps": steps,
    }


def run_training_portfolio_plan(
    plan: dict[str, Any],
    *,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(str(plan.get("project_root") or "."))
    step_results = []
    failed_key = None
    if execute:
        for step in _list_of_dicts(plan.get("steps")):
            result = _run_step(root, step)
            step_results.append(result)
            if result["returncode"] != 0:
                failed_key = str(step.get("key"))
                break
    status = "planned"
    if execute and failed_key is None:
        status = "completed"
    elif execute:
        status = "failed"
    artifact_rows = _artifact_rows(plan.get("artifacts"), root)
    return {
        **plan,
        "generated_at": generated_at or utc_now(),
        "execution": {
            "status": status,
            "execute": execute,
            "step_count": len(_list_of_dicts(plan.get("steps"))),
            "completed_steps": sum(1 for item in step_results if item.get("returncode") == 0),
            "failed_step": failed_key,
            "artifact_count": len(artifact_rows),
            "available_artifact_count": sum(1 for item in artifact_rows if item["exists"]),
        },
        "step_results": step_results,
        "artifact_rows": artifact_rows,
        "recommendations": _recommendations(status, artifact_rows, failed_key),
    }


def _step(key: str, title: str, command: list[str], expected_outputs: list[str]) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "command": [str(part) for part in command],
        "expected_outputs": [str(path) for path in expected_outputs],
    }


def _train_command(
    *,
    python_executable: str,
    script: Path,
    corpus: Path,
    run_dir: Path,
    device: str,
    max_iters: int,
    eval_interval: int,
    eval_iters: int,
    batch_size: int,
    block_size: int,
    n_layer: int,
    n_head: int,
    n_embd: int,
    learning_rate: float,
    seed: int,
    sample_prompt: str,
    sample_tokens: int,
) -> list[str]:
    command = [
        python_executable,
        str(script),
        "--prepared-data",
        str(corpus),
        "--out-dir",
        str(run_dir),
        "--device",
        device,
        "--max-iters",
        str(max_iters),
        "--eval-interval",
        str(eval_interval),
        "--eval-iters",
        str(eval_iters),
        "--batch-size",
        str(batch_size),
        "--block-size",
        str(block_size),
        "--n-layer",
        str(n_layer),
        "--n-head",
        str(n_head),
        "--n-embd",
        str(n_embd),
        "--learning-rate",
        str(learning_rate),
        "--seed",
        str(seed),
        "--sample-prompt",
        sample_prompt,
    ]
    if sample_tokens <= 0:
        command.append("--no-sample")
    else:
        command.extend(["--sample-tokens", str(sample_tokens)])
    return command


def _run_step(root: Path, step: dict[str, Any]) -> dict[str, Any]:
    command = _string_list(step.get("command"))
    started_at = utc_now()
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
    finished_at = utc_now()
    return {
        "key": step.get("key"),
        "title": step.get("title"),
        "returncode": completed.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
    }


def _artifact_rows(artifacts: Any, base_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(_dict(artifacts).items()):
        path = Path(str(value))
        check_path = path if path.is_absolute() else base_dir / path
        rows.append({"key": key, "path": str(path), "exists": check_path.exists()})
    return rows


def _recommendations(status: str, artifacts: list[dict[str, Any]], failed_key: str | None) -> list[str]:
    if status == "planned":
        return ["Run the pipeline with --execute when you want to create the training portfolio artifacts."]
    if status == "failed":
        return [f"Inspect the `{failed_key}` step stdout/stderr before trusting downstream artifacts."]
    missing = [row["key"] for row in artifacts if not row.get("exists")]
    if missing:
        return ["Pipeline completed, but these expected artifacts are missing: " + ", ".join(missing)]
    return ["Use training_portfolio.html as the run-level entry point, then open the linked dataset, benchmark, and maturity artifacts."]


def _tail(text: str, line_count: int = 8) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return " / ".join(lines[-line_count:])


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
