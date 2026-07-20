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
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code

DEFAULT_REGISTRY_PATH = Path("docs") / "model-capability-honest-measurement-registry.json"


def build_model_capability_honest_measurement_report(
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    *,
    project_root: str | Path = ".",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    path = _resolve_registry_path(registry_path, root)
    registry = read_json_object(path, description="model capability honest measurement registry")
    checks = _build_checks(registry, registry_path=path, project_root=root)
    failed_checks = [item for item in checks if item.get("status") != "pass"]
    families = list_of_dicts(registry.get("families"))
    status = "pass" if not failed_checks else "fail"
    decision = "continue_with_honest_measurement_gate" if status == "pass" else "repair_honest_measurement_gate"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability honest measurement gate",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "registry_path": _relative_path(path, root),
        "summary": {
            "status": status,
            "decision": decision,
            "family_count": len(families),
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed_checks),
            "failed_check_count": len(failed_checks),
            "cached_artifact_only_family_count": sum(
                1 for family in families if family.get("cached_artifact_only") is True
            ),
            "no_training_required_family_count": sum(
                1 for family in families if family.get("no_training_required") is True
            ),
            "multi_seed_family_count": sum(
                1 for family in families if family.get("seed_evidence_mode") == "multi_seed"
            ),
            "single_seed_family_count": sum(
                1 for family in families if family.get("seed_evidence_mode") == "single_seed"
            ),
        },
        "families": families,
        "checks": checks,
        "recommendations": _recommendations(failed_checks),
    }


def write_model_capability_honest_measurement_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    def write_markdown(path: Path) -> None:
        path.write_text(render_model_capability_honest_measurement_markdown(report), encoding="utf-8")

    def write_html(path: Path) -> None:
        path.write_text(render_model_capability_honest_measurement_html(report), encoding="utf-8")

    return write_output_bundle(
        out_dir,
        {
            "json": "model_capability_honest_measurement.json",
            "csv": "model_capability_honest_measurement.csv",
            "markdown": "model_capability_honest_measurement.md",
            "html": "model_capability_honest_measurement.html",
        },
        {
            "json": lambda path: write_json_payload(report, path),
            "csv": lambda path: _write_csv(report, path),
            "markdown": write_markdown,
            "html": write_html,
        },
    )


def render_model_capability_honest_measurement_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# MiniGPT Model Capability Honest Measurement Gate",
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
    for key in (
        "family_count",
        "check_count",
        "passed_check_count",
        "failed_check_count",
        "cached_artifact_only_family_count",
        "no_training_required_family_count",
        "multi_seed_family_count",
        "single_seed_family_count",
    ):
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(summary.get(key))} |")
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Family | Check | Expected | Actual | Status | Detail |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in _checks(report):
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(item.get(field))
                for field in ("family_id", "check_id", "expected", "actual", "status", "detail")
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    recommendations = report.get("recommendations")
    if isinstance(recommendations, list) and recommendations:
        lines.extend(f"- {markdown_cell(item)}" for item in recommendations)
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_honest_measurement_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    check_rows = "".join(
        "<tr>"
        f"<td>{html_escape(item.get('family_id'))}</td>"
        f"<td>{html_escape(item.get('check_id'))}</td>"
        f"<td>{html_escape(item.get('expected'))}</td>"
        f"<td>{html_escape(item.get('actual'))}</td>"
        f"<td>{html_escape(item.get('status'))}</td>"
        f"<td>{html_escape(item.get('detail'))}</td>"
        "</tr>"
        for item in _checks(report)
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MiniGPT honest measurement gate</title><style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f5f7f6;color:#172026;margin:0}}
main{{max-width:1160px;margin:auto;padding:28px}}header,.panel{{background:white;border:1px solid #d8dee4;border-radius:8px;padding:18px;margin-bottom:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.stat{{background:#eef4f0;padding:12px;border-radius:6px}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}code{{overflow-wrap:anywhere}}
</style></head><body><main>
<header><h1>MiniGPT honest measurement gate</h1><p>Status: <strong>{html_escape(report.get("status"))}</strong> | Decision: <code>{html_escape(report.get("decision"))}</code></p><p>Registry: <code>{html_escape(report.get("registry_path"))}</code></p></header>
<section class="panel stats"><div class="stat">Families<br><strong>{html_escape(summary.get("family_count"))}</strong></div><div class="stat">Checks<br><strong>{html_escape(summary.get("check_count"))}</strong></div><div class="stat">Failures<br><strong>{html_escape(summary.get("failed_check_count"))}</strong></div><div class="stat">Single-seed<br><strong>{html_escape(summary.get("single_seed_family_count"))}</strong></div></section>
<section class="panel"><h2>Checks</h2><table><thead><tr><th>Family</th><th>Check</th><th>Expected</th><th>Actual</th><th>Status</th><th>Detail</th></tr></thead><tbody>{check_rows}</tbody></table></section>
</main></body></html>"""


def _build_checks(registry: dict[str, Any], *, registry_path: Path, project_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    families = list_of_dicts(registry.get("families"))
    checks.append(
        _check("registry", "schema_version", "1", registry.get("schema_version"), registry.get("schema_version") == 1)
    )
    checks.append(
        _check(
            "registry",
            "scope",
            "engineering_governance_lane_only",
            registry.get("scope"),
            registry.get("scope") == "engineering_governance_lane_only",
        )
    )
    checks.append(_check("registry", "family_count", ">=1", len(families), bool(families)))
    seen: set[str] = set()
    for family in families:
        family_id = str(family.get("family_id") or "")
        duplicate = family_id in seen
        if family_id:
            seen.add(family_id)
        checks.extend(
            _family_checks(
                family, family_id=family_id, duplicate=duplicate, registry_path=registry_path, project_root=project_root
            )
        )
    return checks


def _family_checks(
    family: dict[str, Any],
    *,
    family_id: str,
    duplicate: bool,
    registry_path: Path,
    project_root: Path,
) -> list[dict[str, Any]]:
    checks = [
        _check(
            family_id,
            "family_id_present",
            "non-empty unique id",
            family_id or "missing",
            bool(family_id) and not duplicate,
        ),
        _check(
            family_id,
            "cached_artifact_only",
            "true",
            family.get("cached_artifact_only"),
            family.get("cached_artifact_only") is True,
        ),
        _check(
            family_id,
            "no_training_required",
            "true",
            family.get("no_training_required"),
            family.get("no_training_required") is True,
        ),
        _check(
            family_id,
            "promotion_authority",
            "none",
            family.get("promotion_authority"),
            family.get("promotion_authority") == "none",
        ),
        _check(
            family_id,
            "promotion_ready_expected",
            "false",
            family.get("promotion_ready_expected"),
            family.get("promotion_ready_expected") is False,
        ),
    ]
    checks.extend(_seed_policy_checks(family, family_id=family_id))
    checks.extend(_path_list_checks(family, key="source_artifacts", family_id=family_id, project_root=project_root))
    checks.extend(
        _path_list_checks(family, key="contract_test_modules", family_id=family_id, project_root=project_root)
    )
    checks.extend(_test_marker_checks(family, family_id=family_id, project_root=project_root))
    checks.extend(
        _artifact_guard_checks(family, family_id=family_id, registry_path=registry_path, project_root=project_root)
    )
    return checks


def _seed_policy_checks(family: dict[str, Any], *, family_id: str) -> list[dict[str, Any]]:
    mode = str(family.get("seed_evidence_mode") or "")
    seed_count = _int_or_none(family.get("seed_count"))
    label = str(family.get("single_seed_label") or "")
    stochastic = family.get("stochastic_metric") is True
    checks = [
        _check(
            family_id,
            "seed_evidence_mode",
            "single_seed|multi_seed|not_applicable",
            mode,
            mode in {"single_seed", "multi_seed", "not_applicable"},
        ),
    ]
    if stochastic and mode == "multi_seed":
        checks.append(
            _check(
                family_id,
                "multi_seed_count",
                ">=2",
                seed_count if seed_count is not None else "missing",
                seed_count is not None and seed_count >= 2,
            )
        )
    if stochastic and mode == "single_seed":
        bounded = any(token in label for token in ("exploratory", "not_claimed", "no_promotion"))
        checks.append(_check(family_id, "single_seed_label", "exploratory/not_claimed/no_promotion", label, bounded))
    return checks


def _path_list_checks(family: dict[str, Any], *, key: str, family_id: str, project_root: Path) -> list[dict[str, Any]]:
    raw_items = family.get(key)
    items = [str(item) for item in raw_items] if isinstance(raw_items, list) else []
    checks = [_check(family_id, f"{key}_present", "non-empty list", len(items), bool(items))]
    for index, item in enumerate(items):
        path = _resolve_inside_root(item, project_root)
        checks.append(
            _check(
                family_id,
                f"{key}[{index}]",
                "exists inside project",
                _relative_path(path, project_root),
                path.is_file(),
            )
        )
    return checks


def _test_marker_checks(family: dict[str, Any], *, family_id: str, project_root: Path) -> list[dict[str, Any]]:
    modules = [str(item) for item in family.get("contract_test_modules", []) if isinstance(item, str)]
    module_text = "\n".join(_read_if_file(_resolve_inside_root(module, project_root)) for module in modules)
    checks: list[dict[str, Any]] = []
    for marker_key in ("positive_test_markers", "negative_test_markers"):
        markers = [str(item) for item in family.get(marker_key, []) if isinstance(item, str)]
        checks.append(_check(family_id, f"{marker_key}_present", "non-empty list", len(markers), bool(markers)))
        for marker in markers:
            checks.append(
                _check(family_id, f"marker:{marker}", "present in contract tests", marker, marker in module_text)
            )
    return checks


def _artifact_guard_checks(
    family: dict[str, Any], *, family_id: str, registry_path: Path, project_root: Path
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for guard_index, guard in enumerate(list_of_dicts(family.get("artifact_guards"))):
        raw_path = guard.get("path")
        path = _resolve_inside_root(str(raw_path or ""), project_root)
        exists = path.is_file()
        checks.append(
            _check(
                family_id, f"artifact_guard[{guard_index}].path", "exists", _relative_path(path, project_root), exists
            )
        )
        payload = read_json_object(path, description=f"artifact guard source for {family_id}") if exists else {}
        for field in [str(item) for item in guard.get("required_fields", []) if isinstance(item, str)]:
            value = _nested_value(payload, field)
            checks.append(
                _check(
                    family_id,
                    f"artifact_field:{field}",
                    "present",
                    "present" if value is not None else "missing",
                    value is not None,
                )
            )
        expected_values = as_dict(guard.get("expected_values"))
        for field, expected in expected_values.items():
            actual = _nested_value(payload, str(field))
            checks.append(_check(family_id, f"artifact_value:{field}", expected, actual, actual == expected))
    if family.get("artifact_guards") is None:
        checks.append(_check(family_id, "artifact_guards_present", "non-empty list", 0, False))
    return checks


def _check(family_id: str, check_id: str, expected: Any, actual: Any, passed: bool) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "check_id": check_id,
        "expected": expected,
        "actual": actual,
        "status": "pass" if passed else "fail",
        "detail": "Honest measurement contract holds."
        if passed
        else "Honest measurement contract is missing or widened.",
    }


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("checks"))


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["family_id", "check_id", "expected", "actual", "status", "detail"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _checks(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def _recommendations(failed_checks: list[dict[str, Any]]) -> list[str]:
    if not failed_checks:
        return ["Keep new capability families registered before claiming bounded model capability progress."]
    return [
        "Repair the registry, source artifact, or contract test marker before widening any capability claim.",
        "Single-seed stochastic evidence must stay exploratory/no-promotion unless multi-seed evidence is registered.",
    ]


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


def _read_if_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _nested_value(payload: dict[str, Any], dotted_key: str) -> Any:
    value: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "build_model_capability_honest_measurement_report",
    "render_model_capability_honest_measurement_html",
    "render_model_capability_honest_measurement_markdown",
    "resolve_exit_code",
    "write_model_capability_honest_measurement_outputs",
]
