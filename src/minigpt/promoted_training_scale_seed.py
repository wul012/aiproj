from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_artifacts import (
    render_promoted_training_scale_seed_html,
    render_promoted_training_scale_seed_markdown,
    write_promoted_training_scale_seed_csv,
    write_promoted_training_scale_seed_html,
    write_promoted_training_scale_seed_json,
    write_promoted_training_scale_seed_markdown,
    write_promoted_training_scale_seed_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    display_command as _display_command,
    list_of_dicts as _list_of_dicts,
    utc_now,
)


def load_promoted_training_scale_decision(path: str | Path) -> dict[str, Any]:
    decision_path = _resolve_decision_path(Path(path))
    payload = json.loads(decision_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted training scale decision must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(decision_path)
    return payload


def build_promoted_training_scale_seed(
    decision_path: str | Path,
    sources: list[str | Path] | None = None,
    *,
    project_root: str | Path | None = None,
    plan_out_dir: str | Path = "runs/training-scale-plan-from-promoted-baseline",
    batch_out_root: str | Path = "runs/training-portfolio-batch-from-promoted-baseline",
    dataset_name: str = "portfolio-zh",
    dataset_version_prefix: str = "v81",
    dataset_description: str = "MiniGPT corpus seeded from a promoted training scale baseline.",
    sample_prompt: str = "MiniGPT",
    max_variants: int = 3,
    python_executable: str = "python",
    title: str = "MiniGPT promoted training scale next-cycle seed",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if max_variants < 1:
        raise ValueError("max_variants must be at least 1")
    decision = load_promoted_training_scale_decision(decision_path)
    decision_file = Path(str(decision.get("_source_path")))
    decision_dir = decision_file.parent
    selected = _dict(decision.get("selected_baseline"))
    selected_run_path = _resolve_selected_run_path(selected.get("training_scale_run_path"), decision_dir)
    selected_run = _load_selected_run(selected_run_path)
    source_rows = _source_rows(sources or [])
    root = Path(project_root) if project_root is not None else Path.cwd()
    blockers = _blockers(decision, selected, selected_run_path, source_rows)
    seed_status = _seed_status(str(decision.get("decision_status") or ""), blockers)
    command = [] if blockers else _plan_command(
        source_rows,
        project_root=root,
        plan_out_dir=Path(plan_out_dir),
        batch_out_root=Path(batch_out_root),
        dataset_name=dataset_name,
        dataset_version_prefix=dataset_version_prefix,
        dataset_description=dataset_description,
        sample_prompt=sample_prompt,
        max_variants=max_variants,
        python_executable=python_executable,
    )
    seed = {
        "selected_name": selected.get("name"),
        "decision_status": decision.get("decision_status"),
        "gate_status": selected.get("gate_status"),
        "batch_status": selected.get("batch_status"),
        "readiness_score": selected.get("readiness_score"),
        "training_scale_run_path": str(selected_run_path) if selected_run_path is not None else None,
        "training_scale_run_exists": bool(selected_run_path and selected_run_path.exists()),
        "comparison_path": decision.get("comparison_path"),
        "selected_run_summary": _selected_run_summary(selected_run),
    }
    plan = {
        "project_root": str(root),
        "dataset_name": dataset_name,
        "dataset_version_prefix": dataset_version_prefix,
        "dataset_description": dataset_description,
        "sample_prompt": sample_prompt,
        "max_variants": int(max_variants),
        "plan_out_dir": str(plan_out_dir),
        "batch_out_root": str(batch_out_root),
        "sources": source_rows,
        "command": command,
        "command_text": _display_command(command),
        "command_available": bool(command),
        "execution_ready": seed_status == "ready",
    }
    summary = _summary(seed_status, decision, seed, plan, blockers)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "decision_path": str(decision_file),
        "seed_status": seed_status,
        "baseline_seed": seed,
        "next_plan": plan,
        "blockers": blockers,
        "summary": summary,
        "recommendations": _recommendations(seed_status, seed, plan, blockers),
    }


def _resolve_decision_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "promoted_training_scale_decision.json",
                path / "promoted-decision" / "promoted_training_scale_decision.json",
                path / "decision" / "promoted_training_scale_decision.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _resolve_selected_run_path(value: Any, decision_dir: Path) -> Path | None:
    if value is None:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [decision_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _load_selected_run(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _source_rows(sources: list[str | Path]) -> list[dict[str, Any]]:
    rows = []
    for source in sources:
        path = Path(source)
        exists = path.exists()
        if path.is_dir():
            kind = "directory"
        elif path.is_file():
            kind = "file"
        else:
            kind = "missing"
        rows.append(
            {
                "path": str(path),
                "resolved_path": str(path.resolve()) if exists else str(path),
                "exists": exists,
                "kind": kind,
            }
        )
    return rows


def _blockers(
    decision: dict[str, Any],
    selected: dict[str, Any],
    selected_run_path: Path | None,
    source_rows: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    decision_status = str(decision.get("decision_status") or "")
    if decision_status not in {"accepted", "review"}:
        blockers.append(f"decision status is {decision_status or 'missing'}")
    if not selected:
        blockers.append("decision does not contain selected_baseline")
    if selected_run_path is None:
        blockers.append("selected baseline does not include training_scale_run_path")
    elif not selected_run_path.exists():
        blockers.append("selected training_scale_run.json is missing")
    if not source_rows:
        blockers.append("no corpus sources provided for the next training scale plan")
    missing = [row.get("path") for row in source_rows if not row.get("exists")]
    if missing:
        blockers.append("missing corpus sources: " + ", ".join(str(item) for item in missing))
    return blockers


def _seed_status(decision_status: str, blockers: list[str]) -> str:
    if blockers:
        return "blocked"
    if decision_status == "review":
        return "review"
    return "ready"


def _plan_command(
    source_rows: list[dict[str, Any]],
    *,
    project_root: Path,
    plan_out_dir: Path,
    batch_out_root: Path,
    dataset_name: str,
    dataset_version_prefix: str,
    dataset_description: str,
    sample_prompt: str,
    max_variants: int,
    python_executable: str,
) -> list[str]:
    if not source_rows or any(not row.get("exists") for row in source_rows):
        return []
    return [
        str(python_executable),
        "scripts/plan_training_scale.py",
        *[str(row.get("path")) for row in source_rows],
        "--project-root",
        str(project_root),
        "--out-dir",
        str(plan_out_dir),
        "--batch-out-root",
        str(batch_out_root),
        "--dataset-name",
        dataset_name,
        "--dataset-version-prefix",
        dataset_version_prefix,
        "--dataset-description",
        dataset_description,
        "--sample-prompt",
        sample_prompt,
        "--max-variants",
        str(int(max_variants)),
    ]


def _selected_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    scale = _dict(run.get("scale_plan_summary"))
    batch = _dict(run.get("batch_summary"))
    gate = _dict(run.get("gate"))
    return {
        "name": run.get("name"),
        "status": run.get("status"),
        "allowed": run.get("allowed"),
        "gate_profile": run.get("gate_profile"),
        "gate_status": gate.get("overall_status"),
        "batch_status": batch.get("status"),
        "dataset_name": scale.get("dataset_name"),
        "dataset_version_prefix": scale.get("version_prefix"),
        "scale_tier": scale.get("scale_tier"),
        "char_count": scale.get("char_count"),
        "variant_count": scale.get("variant_count") or batch.get("variant_count"),
    }


def _summary(
    seed_status: str,
    decision: dict[str, Any],
    seed: dict[str, Any],
    plan: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    sources = _list_of_dicts(plan.get("sources"))
    return {
        "seed_status": seed_status,
        "decision_status": decision.get("decision_status"),
        "selected_name": seed.get("selected_name"),
        "selected_gate_status": seed.get("gate_status"),
        "selected_batch_status": seed.get("batch_status"),
        "selected_readiness_score": seed.get("readiness_score"),
        "selected_run_exists": seed.get("training_scale_run_exists"),
        "source_count": len(sources),
        "missing_source_count": sum(1 for row in sources if not row.get("exists")),
        "command_available": plan.get("command_available"),
        "execution_ready": plan.get("execution_ready"),
        "blocker_count": len(blockers),
    }


def _recommendations(
    seed_status: str,
    seed: dict[str, Any],
    plan: dict[str, Any],
    blockers: list[str],
) -> list[str]:
    if seed_status == "ready":
        return [
            "Run the generated plan command on the next corpus, then pass its outputs through the v70-v80 training scale chain.",
            "Keep the selected promoted baseline path in the seed report so the next cycle can explain where it came from.",
        ]
    if seed_status == "review":
        return [
            "Review the promoted baseline decision before running the next plan command.",
            "If the review is accepted, reuse the generated command and keep this seed as the cycle handoff artifact.",
        ]
    if blockers:
        return ["Fix the seed blockers before starting the next training scale planning cycle."]
    return ["Inspect the promoted baseline decision before building a next-cycle plan."]

__all__ = [
    "build_promoted_training_scale_seed",
    "load_promoted_training_scale_decision",
    "render_promoted_training_scale_seed_html",
    "render_promoted_training_scale_seed_markdown",
    "write_promoted_training_scale_seed_csv",
    "write_promoted_training_scale_seed_html",
    "write_promoted_training_scale_seed_json",
    "write_promoted_training_scale_seed_markdown",
    "write_promoted_training_scale_seed_outputs",
]
