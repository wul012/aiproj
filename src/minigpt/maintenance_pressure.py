from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from minigpt.report_utils import utc_now

DEFAULT_MODULE_WARNING_LINES = 700
DEFAULT_MODULE_CRITICAL_LINES = 1200
DEFAULT_MODULE_TOP_N = 12


def build_module_pressure_report(
    paths: list[str | Path],
    *,
    project_root: str | Path | None = None,
    title: str = "MiniGPT module pressure audit",
    generated_at: str | None = None,
    warning_lines: int = DEFAULT_MODULE_WARNING_LINES,
    critical_lines: int = DEFAULT_MODULE_CRITICAL_LINES,
    top_n: int = DEFAULT_MODULE_TOP_N,
) -> dict[str, Any]:
    root = Path(project_root).resolve() if project_root is not None else None
    modules = [
        _module_pressure_row(Path(path), root, warning_lines=int(warning_lines), critical_lines=int(critical_lines))
        for path in paths
    ]
    modules = sorted(modules, key=lambda item: (-int(item.get("line_count", 0)), str(item.get("path"))))
    summary = _module_pressure_summary(modules, int(warning_lines), int(critical_lines), int(top_n))
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "policy": {
            "warning_lines": int(warning_lines),
            "critical_lines": int(critical_lines),
            "top_n": int(top_n),
            "scope": "python module size and structural pressure",
        },
        "summary": summary,
        "modules": modules,
        "top_modules": modules[: int(top_n)],
        "recommendations": _module_pressure_recommendations(summary, modules),
    }


def _module_pressure_row(path: Path, root: Path | None, *, warning_lines: int, critical_lines: int) -> dict[str, Any]:
    display_path = _display_path(path, root)
    try:
        text = path.read_text(encoding="utf-8")
        parse_error = ""
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
        parse_error = "decode-replacement"
    except OSError as exc:
        return {
            "path": display_path,
            "status": "missing",
            "line_count": 0,
            "byte_count": 0,
            "function_count": 0,
            "class_count": 0,
            "max_function_lines": 0,
            "largest_function": "",
            "parse_error": str(exc),
            "recommendation": "Check why this module path could not be read.",
        }

    line_count = len(text.splitlines())
    byte_count = len(text.encode("utf-8"))
    ast_summary = _python_ast_summary(text)
    parse_error = parse_error or ast_summary.get("parse_error", "")
    status = _module_pressure_status(line_count, warning_lines, critical_lines)
    return {
        "path": display_path,
        "status": status,
        "line_count": line_count,
        "byte_count": byte_count,
        "function_count": ast_summary.get("function_count", 0),
        "class_count": ast_summary.get("class_count", 0),
        "max_function_lines": ast_summary.get("max_function_lines", 0),
        "largest_function": ast_summary.get("largest_function", ""),
        "parse_error": parse_error,
        "recommendation": _module_pressure_recommendation(status, line_count, ast_summary),
    }


def _display_path(path: Path, root: Path | None) -> str:
    if root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def _python_ast_summary(text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {
            "function_count": 0,
            "class_count": 0,
            "max_function_lines": 0,
            "largest_function": "",
            "parse_error": f"syntax-error:{exc.lineno}",
        }
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    largest_name = ""
    largest_lines = 0
    for node in functions:
        end_lineno = getattr(node, "end_lineno", None)
        if end_lineno is None:
            continue
        span = int(end_lineno) - int(node.lineno) + 1
        if span > largest_lines:
            largest_lines = span
            largest_name = str(node.name)
    return {
        "function_count": len(functions),
        "class_count": len(classes),
        "max_function_lines": largest_lines,
        "largest_function": largest_name,
        "parse_error": "",
    }


def _module_pressure_status(line_count: int, warning_lines: int, critical_lines: int) -> str:
    if line_count >= int(critical_lines):
        return "critical"
    if line_count >= int(warning_lines):
        return "warn"
    return "pass"


def _module_pressure_recommendation(status: str, line_count: int, ast_summary: dict[str, Any]) -> str:
    largest_lines = int(ast_summary.get("max_function_lines", 0) or 0)
    if status == "critical":
        return "Plan a targeted split around stable contracts before adding more features."
    if status == "warn":
        return "Prefer extracting cohesive helpers when the next related change touches this module."
    if largest_lines >= 120:
        return "Review the largest function before growing this file further."
    if line_count == 0:
        return "No code pressure detected because the file is empty."
    return "No size pressure detected."


def _module_pressure_summary(
    modules: list[dict[str, Any]],
    warning_lines: int,
    critical_lines: int,
    top_n: int,
) -> dict[str, Any]:
    warn_count = sum(1 for item in modules if item.get("status") == "warn")
    critical_count = sum(1 for item in modules if item.get("status") == "critical")
    largest = modules[0] if modules else {}
    largest_function_module = max(modules, key=lambda item: int(item.get("max_function_lines", 0)), default={})
    if critical_count:
        status = "warn"
        decision = "plan_targeted_split"
    elif warn_count:
        status = "watch"
        decision = "monitor_large_modules"
    else:
        status = "pass"
        decision = "continue"
    return {
        "status": status,
        "decision": decision,
        "module_count": len(modules),
        "warning_lines": int(warning_lines),
        "critical_lines": int(critical_lines),
        "top_n": int(top_n),
        "warn_count": warn_count,
        "critical_count": critical_count,
        "largest_module": largest.get("path", ""),
        "largest_line_count": largest.get("line_count", 0),
        "largest_function": largest_function_module.get("largest_function", ""),
        "largest_function_module": largest_function_module.get("path", ""),
        "largest_function_lines": largest_function_module.get("max_function_lines", 0),
    }


def _module_pressure_recommendations(summary: dict[str, Any], modules: list[dict[str, Any]]) -> list[str]:
    recommendations: list[str] = []
    if int(summary.get("critical_count", 0) or 0):
        recommendations.append("Treat critical-size modules as planned refactor candidates, but split them only behind tests and stable contracts.")
    elif int(summary.get("warn_count", 0) or 0):
        recommendations.append("Watch large modules and fold cohesive helper extraction into the next related feature or maintenance batch.")
    else:
        recommendations.append("Keep the current module boundaries; no size-pressure split is needed.")
    largest = summary.get("largest_module")
    if largest:
        recommendations.append(f"Start reviews with {largest}; it is the largest module in the scanned scope.")
    large_functions = [item for item in modules if int(item.get("max_function_lines", 0) or 0) >= 120]
    if large_functions:
        recommendations.append("Review long functions before file-level rewrites; they are usually lower-risk extraction targets.")
    recommendations.append("Do not rewrite storage, service, or UI modules just to reduce line count; require a concrete follow-up change.")
    return recommendations


__all__ = [
    "DEFAULT_MODULE_CRITICAL_LINES",
    "DEFAULT_MODULE_TOP_N",
    "DEFAULT_MODULE_WARNING_LINES",
    "build_module_pressure_report",
]
