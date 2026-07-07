from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict,
    csv_cell,
    html_escape,
    list_of_dicts,
    markdown_cell,
    read_json_object,
    utc_now,
    write_json_payload,
    write_output_bundle,
)

DEFAULT_SCHEMA_REGISTRY_PATH = Path("docs") / "artifact-schema-guard-registry.json"
ALLOWED_TYPES = {"dict", "list", "str", "int", "float", "bool", "none"}


def build_artifact_schema_guard_report(
    registry_path: str | Path = DEFAULT_SCHEMA_REGISTRY_PATH,
    *,
    project_root: str | Path = ".",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    path = _resolve_registry_path(registry_path, root)
    registry = read_json_object(path, description="artifact schema guard registry")
    checks = _build_checks(registry, registry_path=path, project_root=root)
    failed_checks = [item for item in checks if item.get("status") != "pass"]
    schemas = list_of_dicts(registry.get("schemas"))
    status = "pass" if not failed_checks else "fail"
    decision = "continue_with_artifact_schema_guard" if status == "pass" else "repair_artifact_schema_guard"
    return {
        "schema_version": 1,
        "title": "MiniGPT artifact schema guard",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "registry_path": _relative_path(path, root),
        "summary": {
            "status": status,
            "decision": decision,
            "schema_count": len(schemas),
            "artifact_count": sum(_artifact_count(schema) for schema in schemas),
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed_checks),
            "failed_check_count": len(failed_checks),
        },
        "schemas": schemas,
        "checks": checks,
        "recommendations": _recommendations(failed_checks),
    }


def write_artifact_schema_guard_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    def write_markdown(path: Path) -> None:
        path.write_text(render_artifact_schema_guard_markdown(report), encoding="utf-8")

    def write_html(path: Path) -> None:
        path.write_text(render_artifact_schema_guard_html(report), encoding="utf-8")

    return write_output_bundle(
        out_dir,
        {
            "json": "artifact_schema_guard.json",
            "csv": "artifact_schema_guard.csv",
            "markdown": "artifact_schema_guard.md",
            "html": "artifact_schema_guard.html",
        },
        {
            "json": lambda path: write_json_payload(report, path),
            "csv": lambda path: _write_csv(report, path),
            "markdown": write_markdown,
            "html": write_html,
        },
    )


def render_artifact_schema_guard_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# MiniGPT Artifact Schema Guard",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Registry: `{report.get('registry_path')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in ("schema_count", "artifact_count", "check_count", "passed_check_count", "failed_check_count"):
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(summary.get(key))} |")
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Schema | Artifact | Check | Expected | Actual | Status |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in _checks(report):
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(item.get(field))
                for field in ("schema_id", "artifact_path", "check_id", "expected", "actual", "status")
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_artifact_schema_guard_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = "".join(
        "<tr>"
        f"<td>{html_escape(item.get('schema_id'))}</td>"
        f"<td>{html_escape(item.get('artifact_path'))}</td>"
        f"<td>{html_escape(item.get('check_id'))}</td>"
        f"<td>{html_escape(item.get('expected'))}</td>"
        f"<td>{html_escape(item.get('actual'))}</td>"
        f"<td>{html_escape(item.get('status'))}</td>"
        "</tr>"
        for item in _checks(report)
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MiniGPT artifact schema guard</title><style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f7f9;color:#172026;margin:0}}
main{{max-width:1160px;margin:auto;padding:28px}}header,.panel{{background:white;border:1px solid #d8dee4;border-radius:8px;padding:18px;margin-bottom:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.stat{{background:#eef2f6;padding:12px;border-radius:6px}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}code{{overflow-wrap:anywhere}}
</style></head><body><main>
<header><h1>MiniGPT artifact schema guard</h1><p>Status: <strong>{html_escape(report.get("status"))}</strong> | Decision: <code>{html_escape(report.get("decision"))}</code></p><p>Registry: <code>{html_escape(report.get("registry_path"))}</code></p></header>
<section class="panel stats"><div class="stat">Schemas<br><strong>{html_escape(summary.get("schema_count"))}</strong></div><div class="stat">Artifacts<br><strong>{html_escape(summary.get("artifact_count"))}</strong></div><div class="stat">Checks<br><strong>{html_escape(summary.get("check_count"))}</strong></div><div class="stat">Failures<br><strong>{html_escape(summary.get("failed_check_count"))}</strong></div></section>
<section class="panel"><h2>Checks</h2><table><thead><tr><th>Schema</th><th>Artifact</th><th>Check</th><th>Expected</th><th>Actual</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 0 if not require_pass or report.get("status") == "pass" else 1


def _build_checks(registry: dict[str, Any], *, registry_path: Path, project_root: Path) -> list[dict[str, Any]]:
    schemas = list_of_dicts(registry.get("schemas"))
    checks = [
        _check(
            "registry", "", "schema_version", 1, registry.get("schema_version"), registry.get("schema_version") == 1
        ),
        _check(
            "registry",
            "",
            "scope",
            "cards_and_publication_receipts",
            registry.get("scope"),
            registry.get("scope") == "cards_and_publication_receipts",
        ),
        _check("registry", "", "schemas_present", "non-empty list", len(schemas), bool(schemas)),
    ]
    seen: set[str] = set()
    for schema in schemas:
        schema_id = str(schema.get("schema_id") or "")
        duplicate = schema_id in seen
        if schema_id:
            seen.add(schema_id)
        checks.extend(_schema_checks(schema, schema_id=schema_id, duplicate=duplicate, project_root=project_root))
    return checks


def _schema_checks(
    schema: dict[str, Any], *, schema_id: str, duplicate: bool, project_root: Path
) -> list[dict[str, Any]]:
    checks = [
        _check(
            schema_id,
            "",
            "schema_id_present",
            "non-empty unique id",
            schema_id or "missing",
            bool(schema_id) and not duplicate,
        ),
        _check(
            schema_id,
            "",
            "artifact_kind_present",
            "non-empty",
            schema.get("artifact_kind") or "missing",
            bool(schema.get("artifact_kind")),
        ),
    ]
    required_fields = [str(item) for item in schema.get("required_fields", []) if isinstance(item, str)]
    artifact_paths = [str(item) for item in schema.get("artifact_paths", []) if isinstance(item, str)]
    type_checks = as_dict(schema.get("type_checks"))
    checks.append(
        _check(schema_id, "", "required_fields_present", "non-empty list", len(required_fields), bool(required_fields))
    )
    checks.append(
        _check(schema_id, "", "artifact_paths_present", "non-empty list", len(artifact_paths), bool(artifact_paths))
    )
    for field, expected_type in type_checks.items():
        checks.append(
            _check(
                schema_id, "", f"type_rule:{field}", "known type", expected_type, str(expected_type) in ALLOWED_TYPES
            )
        )
    for raw_path in artifact_paths:
        checks.extend(_artifact_checks(schema, schema_id=schema_id, raw_path=raw_path, project_root=project_root))
    return checks


def _artifact_checks(
    schema: dict[str, Any], *, schema_id: str, raw_path: str, project_root: Path
) -> list[dict[str, Any]]:
    path = _resolve_inside_root(raw_path, project_root)
    rel_path = _relative_path(path, project_root)
    exists = path.is_file()
    checks = [_check(schema_id, rel_path, "artifact_exists", "exists inside project", rel_path, exists)]
    payload = read_json_object(path, description=f"schema guard artifact for {schema_id}") if exists else {}
    for field in [str(item) for item in schema.get("required_fields", []) if isinstance(item, str)]:
        value = _nested_value(payload, field)
        checks.append(
            _check(
                schema_id,
                rel_path,
                f"field:{field}",
                "present",
                "present" if value is not None else "missing",
                value is not None,
            )
        )
    for field, expected in as_dict(schema.get("expected_values")).items():
        actual = _nested_value(payload, str(field))
        checks.append(_check(schema_id, rel_path, f"value:{field}", expected, actual, actual == expected))
    for field, expected_type in as_dict(schema.get("type_checks")).items():
        actual = _nested_value(payload, str(field))
        checks.append(
            _check(
                schema_id,
                rel_path,
                f"type:{field}",
                expected_type,
                _type_name(actual),
                _type_name(actual) == expected_type,
            )
        )
    return checks


def _check(
    schema_id: str, artifact_path: str, check_id: str, expected: Any, actual: Any, passed: bool
) -> dict[str, Any]:
    return {
        "schema_id": schema_id,
        "artifact_path": artifact_path,
        "check_id": check_id,
        "expected": expected,
        "actual": actual,
        "status": "pass" if passed else "fail",
    }


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("checks"))


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["schema_id", "artifact_path", "check_id", "expected", "actual", "status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _checks(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def _recommendations(failed_checks: list[dict[str, Any]]) -> list[str]:
    if not failed_checks:
        return [
            "Register new card or publication receipt shapes before relying on them as stable governance artifacts."
        ]
    return ["Repair the schema registry or artifact shape before accepting the governance output as stable."]


def _artifact_count(schema: dict[str, Any]) -> int:
    paths = schema.get("artifact_paths")
    return len(paths) if isinstance(paths, list) else 0


def _resolve_inside_root(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {path}") from exc
    return resolved


def _resolve_registry_path(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _nested_value(payload: dict[str, Any], dotted_key: str) -> Any:
    value: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _type_name(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


__all__ = [
    "DEFAULT_SCHEMA_REGISTRY_PATH",
    "build_artifact_schema_guard_report",
    "render_artifact_schema_guard_html",
    "render_artifact_schema_guard_markdown",
    "resolve_exit_code",
    "write_artifact_schema_guard_outputs",
]
