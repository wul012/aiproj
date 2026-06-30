from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict as _dict


def suite_ref_from_selected_run(run: dict[str, Any]) -> dict[str, Any]:
    scale = _dict(run.get("scale_plan_summary"))
    batch = _dict(run.get("batch_summary"))
    mode = _optional_str(scale.get("suite_mode") or batch.get("suite_mode"))
    name = _selected_suite_name(scale.get("suite_name") or batch.get("suite_name"))
    path = _optional_str(scale.get("suite_path") or batch.get("suite_path"))
    if name == "default":
        name = None
    if path and path.startswith("builtin:"):
        builtin_name = path.removeprefix("builtin:") or None
        if builtin_name == "default":
            path = None
        elif builtin_name:
            name = name or builtin_name
            mode = "builtin"
    if name:
        return {
            "mode": "builtin",
            "name": name,
            "path": path or f"builtin:{name}",
            "source": "selected_run",
        }
    if path:
        return {
            "mode": mode or "file",
            "name": None,
            "path": path,
            "source": "selected_run",
        }
    return {"mode": "missing", "name": None, "path": None, "source": "selected_run"}


def next_suite_ref(
    root: Path,
    inherited: dict[str, Any],
    *,
    suite_path: str | Path | None,
    suite_name: str | None,
) -> dict[str, Any]:
    if suite_name is not None and suite_path is not None:
        raise ValueError("suite_name and suite_path cannot both be provided")
    if suite_name == "default":
        return {
            "mode": "file",
            "name": None,
            "path": str(root / "data" / "eval_prompts.json"),
            "source": "default",
        }
    if suite_name:
        return {
            "mode": "builtin",
            "name": suite_name,
            "path": f"builtin:{suite_name}",
            "source": "override",
        }
    if suite_path is not None:
        return {"mode": "file", "name": None, "path": str(Path(suite_path)), "source": "override"}
    if inherited.get("path"):
        return {
            "mode": inherited.get("mode") or "file",
            "name": inherited.get("name"),
            "path": inherited.get("path"),
            "source": "inherited",
        }
    return {
        "mode": "file",
        "name": None,
        "path": str(root / "data" / "eval_prompts.json"),
        "source": "default",
    }


def plan_command(
    source_rows: list[dict[str, Any]],
    *,
    project_root: Path,
    plan_out_dir: Path,
    batch_out_root: Path,
    dataset_name: str,
    dataset_version_prefix: str,
    dataset_description: str,
    suite: dict[str, Any],
    sample_prompt: str,
    max_variants: int,
    python_executable: str,
) -> list[str]:
    if not source_rows or any(not row.get("exists") for row in source_rows):
        return []
    suite_args = _suite_args(project_root, suite)
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
        *suite_args,
        "--sample-prompt",
        sample_prompt,
        "--max-variants",
        str(int(max_variants)),
    ]


def _suite_args(root: Path, suite: dict[str, Any]) -> list[str]:
    if suite.get("mode") == "builtin":
        return ["--suite-name", str(suite.get("name"))]
    if suite.get("mode") == "file" and suite.get("path"):
        path = Path(str(suite.get("path")))
        if path == root / "data" / "eval_prompts.json":
            return []
        return ["--suite", str(path)]
    return []


def _selected_suite_name(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    return text


def _optional_str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


__all__ = ["next_suite_ref", "plan_command", "suite_ref_from_selected_run"]
