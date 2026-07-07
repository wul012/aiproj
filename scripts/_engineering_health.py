from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

try:
    from scripts._bootstrap import HEALTH_ENGINEERING_ENTRYPOINTS
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import HEALTH_ENGINEERING_ENTRYPOINTS  # type: ignore[import-not-found,no-redef]

from minigpt.reports.utils import write_output_bundle

_HEALTH_STEP_IDS_BY_ENTRYPOINT = {
    "scripts/check_source_encoding.py": "source_encoding",
    "scripts/check_project_docs_readability.py": "project_docs_readability",
    "scripts/check_ci_workflow_hygiene.py": "ci_workflow_hygiene",
    "scripts/check_static_analysis.py": "static_analysis",
    "scripts/check_type_analysis.py": "type_analysis",
    "scripts/check_model_capability_honest_measurement.py": "model_capability_honest_measurement",
    "scripts/check_artifact_schema_guard.py": "artifact_schema_guard",
    "scripts/check_normalization_guard.py": "normalization_guard",
}

ENGINEERING_HEALTH_STEP_IDS = tuple(_HEALTH_STEP_IDS_BY_ENTRYPOINT[path] for path in HEALTH_ENGINEERING_ENTRYPOINTS)


@dataclass(frozen=True)
class EngineeringHealthStep:
    step_id: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class EngineeringHealthStepResult:
    step_id: str
    command: tuple[str, ...]
    return_code: int

    @property
    def status(self) -> str:
        return "pass" if self.return_code == 0 else "fail"


def build_steps(out_dir: Path, *, python_executable: str = sys.executable) -> tuple[EngineeringHealthStep, ...]:
    return tuple(
        _build_step(entrypoint, out_dir, python_executable=python_executable)
        for entrypoint in HEALTH_ENGINEERING_ENTRYPOINTS
    )


def _build_step(entrypoint: str, out_dir: Path, *, python_executable: str) -> EngineeringHealthStep:
    if entrypoint == "scripts/check_source_encoding.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "source-encoding"),
            ),
        )
    if entrypoint == "scripts/check_project_docs_readability.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "project-docs-readability"),
                "--require-pass",
                "--force",
            ),
        )
    if entrypoint == "scripts/check_ci_workflow_hygiene.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "ci-workflow-hygiene"),
            ),
        )
    if entrypoint == "scripts/check_static_analysis.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "static-analysis"),
            ),
        )
    if entrypoint == "scripts/check_type_analysis.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "type-analysis"),
            ),
        )
    if entrypoint == "scripts/check_model_capability_honest_measurement.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "model-capability-honest-measurement"),
            ),
        )
    if entrypoint == "scripts/check_artifact_schema_guard.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
                "--out-dir",
                str(out_dir / "artifact-schema-guard"),
            ),
        )
    if entrypoint == "scripts/check_normalization_guard.py":
        return EngineeringHealthStep(
            _HEALTH_STEP_IDS_BY_ENTRYPOINT[entrypoint],
            (
                python_executable,
                "-B",
                entrypoint,
            ),
        )
    raise ValueError(f"Unsupported engineering health entrypoint: {entrypoint}")


def build_summary(results: tuple[EngineeringHealthStepResult, ...], out_dir: Path) -> dict[str, Any]:
    failed = [item for item in results if item.return_code != 0]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT engineering health summary",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": status,
        "decision": "engineering_health_ready" if status == "pass" else "repair_engineering_health",
        "summary": {
            "status": status,
            "decision": "engineering_health_ready" if status == "pass" else "repair_engineering_health",
            "step_count": len(results),
            "passed_step_count": len(results) - len(failed),
            "failed_step_count": len(failed),
            "first_failure_code": failed[0].return_code if failed else 0,
            "output_root": str(out_dir),
        },
        "steps": [
            {
                "step_id": item.step_id,
                "command": list(item.command),
                "return_code": item.return_code,
                "status": item.status,
            }
            for item in results
        ],
    }


def write_summary(summary: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "engineering_health_summary.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def render_summary_markdown(summary: dict[str, Any]) -> str:
    raw_summary = summary.get("summary")
    raw_steps = summary.get("steps")
    summary_block = dict(raw_summary) if isinstance(raw_summary, dict) else {}
    steps = list(raw_steps) if isinstance(raw_steps, list) else []
    lines = [
        f"# {summary.get('title', 'MiniGPT engineering health summary')}",
        "",
        f"- Generated: `{summary.get('generated_at')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "step_count",
        "passed_step_count",
        "failed_step_count",
        "first_failure_code",
        "output_root",
    ]:
        lines.append(f"| {key} | {summary_block.get(key)} |")
    lines.extend(["", "## Steps", "", "| Step | Status | Return Code | Command |", "| --- | --- | --- | --- |"])
    for step in steps:
        if not isinstance(step, dict):
            continue
        command = step.get("command")
        command_text = " ".join(str(item) for item in command) if isinstance(command, list) else str(command)
        lines.append(f"| {step.get('step_id')} | {step.get('status')} | {step.get('return_code')} | `{command_text}` |")
    return "\n".join(lines).rstrip() + "\n"


def write_summary_markdown(summary: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "engineering_health_summary.md"
    path.write_text(render_summary_markdown(summary), encoding="utf-8")
    return path


def write_summary_outputs(summary: dict[str, Any], out_dir: Path) -> dict[str, str]:
    def write_json(path: Path) -> None:
        write_summary(summary, path.parent)

    def write_markdown(path: Path) -> None:
        write_summary_markdown(summary, path.parent)

    return cast(
        dict[str, str],
        write_output_bundle(
            out_dir,
            {
                "json": "engineering_health_summary.json",
                "markdown": "engineering_health_summary.md",
            },
            {
                "json": write_json,
                "markdown": write_markdown,
            },
        ),
    )


__all__ = [
    "ENGINEERING_HEALTH_STEP_IDS",
    "EngineeringHealthStep",
    "EngineeringHealthStepResult",
    "build_steps",
    "build_summary",
    "render_summary_markdown",
    "write_summary",
    "write_summary_markdown",
    "write_summary_outputs",
]
