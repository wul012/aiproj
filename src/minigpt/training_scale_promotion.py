from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


REQUIRED_VARIANT_ARTIFACTS = [
    "checkpoint",
    "run_manifest",
    "eval_suite",
    "generation_quality",
    "benchmark_scorecard",
    "dataset_card",
    "registry",
    "maturity_summary",
    "maturity_narrative",
]


def load_training_scale_handoff(path: str | Path) -> dict[str, Any]:
    handoff_path = _resolve_handoff_path(Path(path))
    payload = json.loads(handoff_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale handoff must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(handoff_path)
    return payload


def build_training_scale_promotion(
    handoff_path: str | Path,
    *,
    generated_at: str | None = None,
    title: str = "MiniGPT training scale promotion",
) -> dict[str, Any]:
    handoff = load_training_scale_handoff(handoff_path)
    handoff_file = Path(str(handoff.get("_source_path")))
    handoff_dir = handoff_file.parent
    command = _string_list(handoff.get("command"))
    project_root = _project_root(command, handoff_dir)
    out_root = _out_root(command, handoff, project_root, handoff_dir)

    scale_run_path = _handoff_artifact_path(handoff, "training_scale_run_json", out_root / "training_scale_run.json", project_root, handoff_dir)
    batch_path = _handoff_artifact_path(handoff, "batch_json", out_root / "batch" / "training_portfolio_batch.json", project_root, handoff_dir)
    scale_run = _read_json(scale_run_path)
    batch = _read_json(batch_path)
    variants = _variant_rows(batch, project_root, handoff_dir)
    evidence_rows = _evidence_rows(handoff_file, handoff, scale_run_path, batch_path, variants, project_root, handoff_dir)
    blockers, review_items = _issues(handoff, scale_run, batch, variants, evidence_rows)
    summary = _summary(handoff, scale_run, batch, variants, evidence_rows, blockers, review_items)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "handoff_path": str(handoff_file),
        "project_root": str(project_root),
        "out_root": str(out_root),
        "handoff_summary": _dict(handoff.get("summary")),
        "training_scale_run_path": str(scale_run_path),
        "training_scale_run": _scale_run_digest(scale_run),
        "batch_path": str(batch_path),
        "batch": _batch_digest(batch),
        "variants": variants,
        "evidence_rows": evidence_rows,
        "summary": summary,
        "blockers": blockers,
        "review_items": review_items,
        "recommendations": _recommendations(summary, blockers, review_items),
    }


def write_training_scale_promotion_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_training_scale_promotion_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "promotion_status",
        "handoff_status",
        "scale_run_status",
        "batch_status",
        "variant",
        "variant_status",
        "checkpoint_exists",
        "run_manifest_exists",
        "registry_exists",
        "maturity_narrative_exists",
        "missing_required",
        "portfolio_json",
    ]
    summary = _dict(report.get("summary"))
    rows = _list_of_dicts(report.get("variants")) or [{}]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "promotion_status": summary.get("promotion_status"),
                    "handoff_status": summary.get("handoff_status"),
                    "scale_run_status": summary.get("scale_run_status"),
                    "batch_status": summary.get("batch_status"),
                    "variant": row.get("name"),
                    "variant_status": row.get("promotion_status"),
                    "checkpoint_exists": row.get("checkpoint_exists"),
                    "run_manifest_exists": row.get("run_manifest_exists"),
                    "registry_exists": row.get("registry_exists"),
                    "maturity_narrative_exists": row.get("maturity_narrative_exists"),
                    "missing_required": ", ".join(_string_list(row.get("missing_required"))),
                    "portfolio_json": row.get("portfolio_json"),
                }
            )


def render_training_scale_promotion_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale promotion')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Promotion status: `{summary.get('promotion_status')}`",
        f"- Handoff status: `{summary.get('handoff_status')}`",
        f"- Scale run: `{summary.get('scale_run_status')}`",
        f"- Batch: `{summary.get('batch_status')}`",
        f"- Variants: `{summary.get('ready_variant_count')}/{summary.get('variant_count')}` ready",
        f"- Required artifacts: `{summary.get('available_required_artifact_count')}/{summary.get('required_artifact_count')}`",
        "",
        "## Evidence",
        "",
        "| Key | Exists | Path |",
        "| --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("evidence_rows")):
        lines.append(f"| {_md(row.get('key'))} | {_md(row.get('exists'))} | {_md(row.get('path'))} |")
    lines.extend(["", "## Variant Readiness", "", "| Variant | Status | Missing Required | Portfolio |", "| --- | --- | --- | --- |"])
    for row in _list_of_dicts(report.get("variants")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("promotion_status")),
                    _md(", ".join(_string_list(row.get("missing_required")))),
                    _md(row.get("portfolio_json")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    blockers = _string_list(report.get("blockers"))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    review_items = _string_list(report.get("review_items"))
    if review_items:
        lines.extend(["", "## Review Items", ""])
        lines.extend(f"- {item}" for item in review_items)
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_promotion_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_promotion_markdown(report), encoding="utf-8")


def render_training_scale_promotion_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Promotion", summary.get("promotion_status")),
        ("Handoff", summary.get("handoff_status")),
        ("Scale run", summary.get("scale_run_status")),
        ("Batch", summary.get("batch_status")),
        ("Ready variants", f"{summary.get('ready_variant_count')}/{summary.get('variant_count')}"),
        (
            "Required artifacts",
            f"{summary.get('available_required_artifact_count')}/{summary.get('required_artifact_count')}",
        ),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale promotion'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale promotion'))}</h1><p>{_e(report.get('handoff_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _evidence_section(report),
            _variant_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            _list_section("Blockers", report.get("blockers")),
            _list_section("Review Items", report.get("review_items")),
            "<footer>Generated by MiniGPT training scale promotion.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_promotion_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_promotion_html(report), encoding="utf-8")


def write_training_scale_promotion_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_promotion.json",
        "csv": root / "training_scale_promotion.csv",
        "markdown": root / "training_scale_promotion.md",
        "html": root / "training_scale_promotion.html",
    }
    write_training_scale_promotion_json(report, paths["json"])
    write_training_scale_promotion_csv(report, paths["csv"])
    write_training_scale_promotion_markdown(report, paths["markdown"])
    write_training_scale_promotion_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_handoff_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.append(path / "training_scale_handoff.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _project_root(command: list[str], handoff_dir: Path) -> Path:
    value = _option_value(command, "--project-root")
    if value:
        return Path(value)
    return Path.cwd()


def _out_root(command: list[str], handoff: dict[str, Any], project_root: Path, handoff_dir: Path) -> Path:
    value = _option_value(command, "--out-root")
    if value:
        return _resolve_path(value, project_root, handoff_dir)
    for row in _list_of_dicts(handoff.get("artifact_rows")):
        if row.get("key") == "training_scale_run_json":
            return _resolve_path(row.get("path"), project_root, handoff_dir).parent
    return project_root


def _handoff_artifact_path(
    handoff: dict[str, Any],
    key: str,
    fallback: Path,
    project_root: Path,
    handoff_dir: Path,
) -> Path:
    for row in _list_of_dicts(handoff.get("artifact_rows")):
        if row.get("key") == key and row.get("path"):
            return _resolve_path(row.get("path"), project_root, handoff_dir)
    return fallback


def _variant_rows(batch: dict[str, Any], project_root: Path, handoff_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for item in _list_of_dicts(batch.get("variant_results")):
        portfolio_json = _resolve_path(item.get("portfolio_json") or item.get("portfolio_path"), project_root, handoff_dir)
        portfolio = _read_json(portfolio_json)
        artifact_rows = _portfolio_artifact_rows(portfolio, project_root, handoff_dir)
        missing_required = [key for key in REQUIRED_VARIANT_ARTIFACTS if not _artifact_exists(artifact_rows, key)]
        blocked = item.get("status") != "completed" or _dict(portfolio.get("execution")).get("status") != "completed"
        status = "blocked" if blocked else "review" if missing_required else "ready"
        artifacts = _dict(portfolio.get("artifacts"))
        rows.append(
            {
                "name": item.get("name"),
                "description": item.get("description"),
                "promotion_status": status,
                "status": item.get("status"),
                "run_name": portfolio.get("run_name"),
                "dataset_name": portfolio.get("dataset_name"),
                "dataset_version": portfolio.get("dataset_version"),
                "portfolio_json": str(portfolio_json),
                "portfolio_html": str(_resolve_path(item.get("portfolio_html"), project_root, handoff_dir)) if item.get("portfolio_html") else None,
                "run_dir": artifacts.get("run_dir"),
                "step_count": _dict(portfolio.get("execution")).get("step_count") or item.get("step_count"),
                "completed_steps": _dict(portfolio.get("execution")).get("completed_steps") or item.get("completed_steps"),
                "failed_step": _dict(portfolio.get("execution")).get("failed_step") or item.get("failed_step"),
                "required_artifact_count": len(REQUIRED_VARIANT_ARTIFACTS),
                "available_required_artifact_count": len(REQUIRED_VARIANT_ARTIFACTS) - len(missing_required),
                "missing_required": missing_required,
                "checkpoint_exists": _artifact_exists(artifact_rows, "checkpoint"),
                "run_manifest_exists": _artifact_exists(artifact_rows, "run_manifest"),
                "registry_exists": _artifact_exists(artifact_rows, "registry"),
                "maturity_narrative_exists": _artifact_exists(artifact_rows, "maturity_narrative"),
                "artifact_rows": artifact_rows,
            }
        )
    return rows


def _portfolio_artifact_rows(portfolio: dict[str, Any], project_root: Path, handoff_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(_dict(portfolio.get("artifacts")).items()):
        path = _resolve_path(value, project_root, handoff_dir)
        rows.append({"key": key, "path": str(path), "exists": path.exists()})
    return rows


def _evidence_rows(
    handoff_file: Path,
    handoff: dict[str, Any],
    scale_run_path: Path,
    batch_path: Path,
    variants: list[dict[str, Any]],
    project_root: Path,
    handoff_dir: Path,
) -> list[dict[str, Any]]:
    rows = [
        {"key": "handoff_json", "path": str(handoff_file), "exists": handoff_file.exists()},
        {"key": "training_scale_run_json", "path": str(scale_run_path), "exists": scale_run_path.exists()},
        {"key": "batch_json", "path": str(batch_path), "exists": batch_path.exists()},
    ]
    for row in _list_of_dicts(handoff.get("artifact_rows")):
        path = _resolve_path(row.get("path"), project_root, handoff_dir)
        rows.append({"key": f"handoff:{row.get('key')}", "path": str(path), "exists": path.exists()})
    for variant in variants:
        for artifact in _list_of_dicts(variant.get("artifact_rows")):
            if artifact.get("key") in REQUIRED_VARIANT_ARTIFACTS:
                rows.append(
                    {
                        "key": f"variant:{variant.get('name')}:{artifact.get('key')}",
                        "path": artifact.get("path"),
                        "exists": artifact.get("exists"),
                    }
                )
    return rows


def _issues(
    handoff: dict[str, Any],
    scale_run: dict[str, Any],
    batch: dict[str, Any],
    variants: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    blockers = []
    review_items = []
    handoff_summary = _dict(handoff.get("summary"))
    handoff_status = handoff_summary.get("handoff_status") or _dict(handoff.get("execution")).get("status")
    if handoff_status != "completed":
        blockers.append(f"handoff status is {handoff_status or 'missing'}")
    if _dict(handoff.get("execution")).get("returncode") not in (0, None):
        blockers.append("handoff execute command returned non-zero")
    if scale_run.get("status") != "completed":
        blockers.append(f"training scale run status is {scale_run.get('status') or 'missing'}")
    batch_status = _nested(batch, "execution", "status") or _nested(scale_run, "batch_summary", "status")
    if batch_status != "completed":
        blockers.append(f"training portfolio batch status is {batch_status or 'missing'}")
    if not variants:
        blockers.append("no variant portfolio results were found")
    blocked_variants = [str(row.get("name")) for row in variants if row.get("promotion_status") == "blocked"]
    if blocked_variants:
        blockers.append("variant portfolios failed: " + ", ".join(blocked_variants))
    missing_required = [
        f"{row.get('name')} missing {', '.join(_string_list(row.get('missing_required')))}"
        for row in variants
        if _string_list(row.get("missing_required"))
    ]
    review_items.extend(missing_required)
    missing_evidence = [str(row.get("key")) for row in evidence_rows if not row.get("exists")]
    if missing_evidence:
        review_items.append("missing evidence rows: " + ", ".join(missing_evidence[:8]))
    return blockers, review_items


def _summary(
    handoff: dict[str, Any],
    scale_run: dict[str, Any],
    batch: dict[str, Any],
    variants: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    blockers: list[str],
    review_items: list[str],
) -> dict[str, Any]:
    ready_variants = [row for row in variants if row.get("promotion_status") == "ready"]
    required_total = sum(int(row.get("required_artifact_count") or 0) for row in variants)
    required_available = sum(int(row.get("available_required_artifact_count") or 0) for row in variants)
    promotion_status = "blocked" if blockers else "review" if review_items else "promoted"
    return {
        "promotion_status": promotion_status,
        "handoff_status": _dict(handoff.get("summary")).get("handoff_status") or _dict(handoff.get("execution")).get("status"),
        "scale_run_status": scale_run.get("status"),
        "batch_status": _nested(batch, "execution", "status") or _nested(scale_run, "batch_summary", "status"),
        "variant_count": len(variants),
        "ready_variant_count": len(ready_variants),
        "checkpoint_count": sum(1 for row in variants if row.get("checkpoint_exists")),
        "registry_count": sum(1 for row in variants if row.get("registry_exists")),
        "maturity_narrative_count": sum(1 for row in variants if row.get("maturity_narrative_exists")),
        "required_artifact_count": required_total,
        "available_required_artifact_count": required_available,
        "evidence_count": len(evidence_rows),
        "available_evidence_count": sum(1 for row in evidence_rows if row.get("exists")),
        "blocker_count": len(blockers),
        "review_item_count": len(review_items),
    }


def _scale_run_digest(scale_run: dict[str, Any]) -> dict[str, Any]:
    gate = _dict(scale_run.get("gate"))
    batch = _dict(scale_run.get("batch_summary"))
    return {
        "status": scale_run.get("status"),
        "allowed": scale_run.get("allowed"),
        "gate_profile": scale_run.get("gate_profile"),
        "gate_status": gate.get("overall_status"),
        "batch_status": batch.get("status"),
        "completed_variant_count": batch.get("completed_variant_count"),
        "variant_count": batch.get("variant_count"),
    }


def _batch_digest(batch: dict[str, Any]) -> dict[str, Any]:
    execution = _dict(batch.get("execution"))
    return {
        "status": execution.get("status"),
        "variant_count": execution.get("variant_count") or batch.get("variant_count"),
        "completed_variant_count": execution.get("completed_variant_count"),
        "comparison_status": execution.get("comparison_status"),
        "failed_variant": execution.get("failed_variant"),
    }


def _recommendations(summary: dict[str, Any], blockers: list[str], review_items: list[str]) -> list[str]:
    status = str(summary.get("promotion_status") or "")
    if status == "promoted":
        return [
            "Use the promoted variant as a stable local baseline for the next training-scale comparison.",
            "Keep the handoff and promotion JSON together when sharing this run as project evidence.",
        ]
    if blockers:
        return ["Stop promotion and inspect the blocking execution or batch status before continuing."]
    if review_items:
        return ["Review missing optional evidence before treating this handoff as a mature baseline."]
    return ["Inspect the promotion summary before selecting the next larger training profile."]


def _evidence_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("evidence_rows")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('key'))}</td>"
            f"<td>{_e(row.get('exists'))}</td>"
            f"<td>{_e(row.get('path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Evidence</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Key</th><th>Exists</th><th>Path</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _variant_section(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("variants")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('promotion_status'))}</td>"
            f"<td>{_e(row.get('checkpoint_exists'))}</td>"
            f"<td>{_e(row.get('registry_exists'))}</td>"
            f"<td>{_e(row.get('maturity_narrative_exists'))}</td>"
            f"<td>{_e(', '.join(_string_list(row.get('missing_required'))))}</td>"
            f"<td>{_e(row.get('portfolio_json'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Variant Readiness</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Variant</th><th>Status</th><th>Checkpoint</th><th>Registry</th><th>Narrative</th><th>Missing</th><th>Portfolio</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f3; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 900px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _artifact_exists(rows: list[dict[str, Any]], key: str) -> bool:
    return any(row.get("key") == key and bool(row.get("exists")) for row in rows)


def _resolve_path(value: Any, project_root: Path, handoff_dir: Path) -> Path:
    if value is None:
        return project_root
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [project_root / path, handoff_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def _option_value(command: list[str], option: str) -> str | None:
    for index, part in enumerate(command):
        if part == option and index + 1 < len(command):
            return command[index + 1]
    return None


def _nested(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
