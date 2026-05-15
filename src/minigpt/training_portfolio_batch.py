from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict as _dict
from minigpt.report_utils import list_of_dicts as _list_of_dicts
from minigpt.training_portfolio import (
    build_training_portfolio_plan,
    run_training_portfolio_plan,
    write_training_portfolio_outputs,
)
from minigpt.training_portfolio_comparison import (
    build_training_portfolio_comparison,
    write_training_portfolio_comparison_outputs,
)
from minigpt.training_portfolio_batch_artifacts import (
    render_training_portfolio_batch_html,
    render_training_portfolio_batch_markdown,
    write_training_portfolio_batch_csv,
    write_training_portfolio_batch_html,
    write_training_portfolio_batch_json,
    write_training_portfolio_batch_markdown,
    write_training_portfolio_batch_outputs,
)


DEFAULT_VARIANTS = [
    {
        "name": "smoke-small",
        "description": "Small smoke baseline for quick local checks.",
        "dataset_version": "v69-small",
        "max_iters": 50,
        "eval_interval": 25,
        "eval_iters": 5,
        "batch_size": 8,
        "block_size": 64,
        "n_layer": 2,
        "n_head": 2,
        "n_embd": 64,
        "seed": 1337,
    },
    {
        "name": "smoke-context",
        "description": "Slightly longer context variant for comparison planning.",
        "dataset_version": "v69-context",
        "max_iters": 50,
        "eval_interval": 25,
        "eval_iters": 5,
        "batch_size": 8,
        "block_size": 96,
        "n_layer": 2,
        "n_head": 2,
        "n_embd": 64,
        "seed": 2026,
    },
]


VARIANT_OVERRIDE_KEYS = {
    "run_name",
    "dataset_name",
    "dataset_version",
    "dataset_description",
    "device",
    "max_iters",
    "eval_interval",
    "eval_iters",
    "batch_size",
    "block_size",
    "n_layer",
    "n_head",
    "n_embd",
    "learning_rate",
    "seed",
    "sample_prompt",
    "sample_tokens",
    "title",
}


def load_training_portfolio_batch_variants(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    variants = payload.get("variants") if isinstance(payload, dict) else payload
    if not isinstance(variants, list):
        raise ValueError("variant file must be a JSON list or an object with a variants list")
    return [_normalize_variant(item, index) for index, item in enumerate(variants)]


def build_training_portfolio_batch_plan(
    project_root: str | Path,
    sources: list[str | Path],
    *,
    out_root: str | Path,
    variants: list[dict[str, Any]] | None = None,
    dataset_name: str = "portfolio-zh",
    dataset_description: str = "MiniGPT training portfolio batch dataset.",
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
    baseline: str | None = None,
    title: str = "MiniGPT training portfolio batch",
) -> dict[str, Any]:
    if not sources:
        raise ValueError("at least one training source is required")
    root = Path(project_root)
    out = Path(out_root)
    raw_variants = variants or DEFAULT_VARIANTS
    normalized = [_normalize_variant(item, index) for index, item in enumerate(raw_variants)]
    names = [str(item["name"]) for item in normalized]
    if len(names) != len(set(names)):
        raise ValueError("variant names must be unique")

    common = {
        "dataset_name": dataset_name,
        "dataset_description": dataset_description,
        "suite_path": suite_path,
        "request_log_path": request_log_path,
        "python_executable": python_executable,
        "device": device,
        "max_iters": max_iters,
        "eval_interval": eval_interval,
        "eval_iters": eval_iters,
        "batch_size": batch_size,
        "block_size": block_size,
        "n_layer": n_layer,
        "n_head": n_head,
        "n_embd": n_embd,
        "learning_rate": learning_rate,
        "seed": seed,
        "sample_prompt": sample_prompt,
        "sample_tokens": sample_tokens,
    }
    variant_rows = []
    for index, variant in enumerate(normalized, start=1):
        config = _variant_config(common, variant)
        name = str(variant["name"])
        variant_out = Path(str(variant.get("out_root") or out / "variants" / _safe_path_name(name)))
        portfolio_plan = build_training_portfolio_plan(
            root,
            [Path(source) for source in sources],
            out_root=variant_out,
            run_name=str(config["run_name"]),
            dataset_name=str(config["dataset_name"]),
            dataset_version=str(config["dataset_version"]),
            dataset_description=str(config["dataset_description"]),
            suite_path=config.get("suite_path"),
            request_log_path=config.get("request_log_path"),
            python_executable=str(config["python_executable"]),
            device=str(config["device"]),
            max_iters=int(config["max_iters"]),
            eval_interval=int(config["eval_interval"]),
            eval_iters=int(config["eval_iters"]),
            batch_size=int(config["batch_size"]),
            block_size=int(config["block_size"]),
            n_layer=int(config["n_layer"]),
            n_head=int(config["n_head"]),
            n_embd=int(config["n_embd"]),
            learning_rate=float(config["learning_rate"]),
            seed=int(config["seed"]),
            sample_prompt=str(config["sample_prompt"]),
            sample_tokens=int(config["sample_tokens"]),
            title=str(config["title"]),
        )
        variant_rows.append(
            {
                "index": index,
                "name": name,
                "description": variant.get("description"),
                "out_root": str(variant_out),
                "portfolio_path": str(variant_out / "training_portfolio.json"),
                "config": _public_config(config),
                "portfolio_plan": portfolio_plan,
            }
        )

    baseline_name = baseline or names[0]
    portfolio_paths = [row["portfolio_path"] for row in variant_rows]
    comparison_out_dir = out / "comparison"
    comparison_command = [
        python_executable,
        str(root / "scripts" / "compare_training_portfolios.py"),
        *portfolio_paths,
        *[part for name in names for part in ("--name", name)],
        "--baseline",
        baseline_name,
        "--out-dir",
        str(comparison_out_dir),
    ]
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": utc_now(),
        "project_root": str(root),
        "out_root": str(out),
        "sources": [str(Path(source)) for source in sources],
        "variant_count": len(variant_rows),
        "baseline_name": baseline_name,
        "variants": variant_rows,
        "comparison": {
            "baseline_name": baseline_name,
            "out_dir": str(comparison_out_dir),
            "portfolio_paths": portfolio_paths,
            "command": comparison_command,
        },
        "summary": _plan_summary(variant_rows, baseline_name),
    }


def run_training_portfolio_batch_plan(
    plan: dict[str, Any],
    *,
    execute: bool = False,
    compare: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    variant_results = []
    failed_variant = None
    for variant in _list_of_dicts(plan.get("variants")):
        report = run_training_portfolio_plan(_dict(variant.get("portfolio_plan")), execute=execute)
        outputs = write_training_portfolio_outputs(report, variant.get("out_root") or ".")
        row = _variant_result(variant, report, outputs)
        variant_results.append(row)
        if row.get("status") == "failed":
            failed_variant = row.get("name")
            break

    comparison_status = "skipped"
    comparison_outputs: dict[str, str] = {}
    comparison_summary: dict[str, Any] | None = None
    warnings: list[str] = []
    if compare and failed_variant is None and variant_results:
        comparison = _dict(plan.get("comparison"))
        try:
            comparison_report = build_training_portfolio_comparison(
                [row["portfolio_json"] for row in variant_results],
                names=[str(row["name"]) for row in variant_results],
                baseline=str(comparison.get("baseline_name") or variant_results[0]["name"]),
                title="MiniGPT training portfolio batch comparison",
            )
            comparison_outputs = write_training_portfolio_comparison_outputs(
                comparison_report,
                comparison.get("out_dir") or Path(str(plan.get("out_root") or ".")) / "comparison",
            )
            comparison_summary = _dict(comparison_report.get("summary"))
            comparison_status = "written"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            comparison_status = "failed"
            warnings.append(f"comparison failed: {exc}")

    status = "planned"
    if execute and failed_variant is None:
        status = "completed"
    elif execute:
        status = "failed"
    execution = {
        "status": status,
        "execute": execute,
        "compare": compare,
        "variant_count": len(_list_of_dicts(plan.get("variants"))),
        "completed_variant_count": sum(1 for row in variant_results if row.get("status") == "completed"),
        "failed_variant": failed_variant,
        "comparison_status": comparison_status,
    }
    return {
        **plan,
        "generated_at": generated_at or utc_now(),
        "execution": execution,
        "variant_results": variant_results,
        "comparison_outputs": comparison_outputs,
        "comparison_summary": comparison_summary,
        "recommendations": _recommendations(execution, comparison_summary, warnings),
        "warnings": warnings,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_variant(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("each variant must be a JSON object")
    variant = dict(value)
    name = str(variant.get("name") or variant.get("run_name") or f"variant-{index + 1}").strip()
    if not name:
        raise ValueError("variant name cannot be empty")
    variant["name"] = name
    return variant


def _variant_config(common: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    config = dict(common)
    config.update({key: variant[key] for key in VARIANT_OVERRIDE_KEYS if key in variant})
    name = str(variant["name"])
    config.setdefault("dataset_version", f"v1-{name}")
    config["run_name"] = str(config.get("run_name") or _safe_path_name(name))
    config["dataset_name"] = str(config.get("dataset_name") or f"{name}-zh")
    config["dataset_version"] = str(config.get("dataset_version") or f"v1-{name}")
    config["dataset_description"] = str(config.get("dataset_description") or "MiniGPT training portfolio batch dataset.")
    config["title"] = str(config.get("title") or f"MiniGPT training portfolio pipeline ({name})")
    return config


def _safe_path_name(value: str) -> str:
    text = "".join("_" if ch in '<>:"/\\|?*' else ch for ch in str(value).strip())
    text = "-".join(part for part in text.split() if part)
    text = text.strip(" .")
    return text or "variant"


def _public_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        key: config.get(key)
        for key in [
            "run_name",
            "dataset_name",
            "dataset_version",
            "device",
            "max_iters",
            "eval_interval",
            "eval_iters",
            "batch_size",
            "block_size",
            "n_layer",
            "n_head",
            "n_embd",
            "learning_rate",
            "seed",
            "sample_tokens",
        ]
    }


def _plan_summary(variants: list[dict[str, Any]], baseline_name: str) -> dict[str, Any]:
    configs = [_dict(row.get("config")) for row in variants]
    return {
        "variant_count": len(variants),
        "variant_names": [row.get("name") for row in variants],
        "baseline_name": baseline_name,
        "total_max_iters": sum(int(config.get("max_iters") or 0) for config in configs),
        "max_block_size": max((int(config.get("block_size") or 0) for config in configs), default=0),
        "max_n_embd": max((int(config.get("n_embd") or 0) for config in configs), default=0),
        "model_shape_count": len({(config.get("n_layer"), config.get("n_head"), config.get("n_embd")) for config in configs}),
        "dataset_version_count": len({config.get("dataset_version") for config in configs}),
    }


def _variant_result(variant: dict[str, Any], report: dict[str, Any], outputs: dict[str, str]) -> dict[str, Any]:
    execution = _dict(report.get("execution"))
    return {
        "name": variant.get("name"),
        "description": variant.get("description"),
        "out_root": variant.get("out_root"),
        "portfolio_json": outputs.get("json"),
        "portfolio_markdown": outputs.get("markdown"),
        "portfolio_html": outputs.get("html"),
        "status": execution.get("status"),
        "execute": execution.get("execute"),
        "step_count": execution.get("step_count"),
        "completed_steps": execution.get("completed_steps"),
        "failed_step": execution.get("failed_step"),
        "artifact_count": execution.get("artifact_count"),
        "available_artifact_count": execution.get("available_artifact_count"),
        "config": variant.get("config"),
    }


def _recommendations(execution: dict[str, Any], comparison_summary: dict[str, Any] | None, warnings: list[str]) -> list[str]:
    if warnings:
        return ["Inspect batch warnings before trusting the comparison outputs."]
    if execution.get("status") == "planned":
        return ["Review the batch HTML, then rerun with --execute when the variant matrix is ready to train."]
    if execution.get("status") == "failed":
        return [f"Inspect failed variant `{execution.get('failed_variant')}` before continuing the batch."]
    if execution.get("comparison_status") == "written" and comparison_summary:
        return ["Open the batch comparison HTML to choose the next baseline for larger-corpus or model-size experiments."]
    return ["Use the generated per-variant training_portfolio.html files to inspect each run before comparing them."]
