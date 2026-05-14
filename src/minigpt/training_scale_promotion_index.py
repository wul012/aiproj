from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


def load_training_scale_promotion(path: str | Path) -> dict[str, Any]:
    promotion_path = _resolve_promotion_path(Path(path))
    payload = json.loads(promotion_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale promotion must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(promotion_path)
    return payload


def build_training_scale_promotion_index(
    promotion_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    generated_at: str | None = None,
    title: str = "MiniGPT training scale promotion index",
) -> dict[str, Any]:
    if not promotion_paths:
        raise ValueError("at least one training scale promotion is required")
    if names is not None and len(names) != len(promotion_paths):
        raise ValueError("names length must match promotion_paths length")
    reports = [load_training_scale_promotion(path) for path in promotion_paths]
    resolved_names = _resolve_names(reports, names)
    promotions = [_promotion_row(report, resolved_names[index], index) for index, report in enumerate(reports)]
    comparison_inputs = _comparison_inputs(promotions, baseline)
    summary = _summary(promotions, comparison_inputs)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "promotion_count": len(promotions),
        "promotions": promotions,
        "comparison_inputs": comparison_inputs,
        "summary": summary,
        "recommendations": _recommendations(summary),
    }


def write_training_scale_promotion_index_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_training_scale_promotion_index_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "promotion_status",
        "promoted_for_comparison",
        "handoff_status",
        "scale_run_status",
        "batch_status",
        "variant_count",
        "ready_variant_count",
        "required_artifacts",
        "available_required_artifacts",
        "primary_variant",
        "primary_checkpoint",
        "training_scale_run_path",
        "promotion_source_path",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("promotions")):
            writer.writerow(
                {
                    "name": row.get("name"),
                    "promotion_status": row.get("promotion_status"),
                    "promoted_for_comparison": row.get("promoted_for_comparison"),
                    "handoff_status": row.get("handoff_status"),
                    "scale_run_status": row.get("scale_run_status"),
                    "batch_status": row.get("batch_status"),
                    "variant_count": row.get("variant_count"),
                    "ready_variant_count": row.get("ready_variant_count"),
                    "required_artifacts": row.get("required_artifact_count"),
                    "available_required_artifacts": row.get("available_required_artifact_count"),
                    "primary_variant": row.get("primary_variant"),
                    "primary_checkpoint": row.get("primary_checkpoint"),
                    "training_scale_run_path": row.get("training_scale_run_path"),
                    "promotion_source_path": row.get("promotion_source_path"),
                }
            )


def render_training_scale_promotion_index_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison_inputs"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale promotion index')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Promotions: `{summary.get('promotion_count')}`",
        f"- Promoted: `{summary.get('promoted_count')}`",
        f"- Review: `{summary.get('review_count')}`",
        f"- Blocked: `{summary.get('blocked_count')}`",
        f"- Comparison ready: `{summary.get('comparison_ready_count')}`",
        f"- Compare command ready: `{summary.get('compare_command_ready')}`",
        f"- Baseline: `{comparison.get('baseline_name')}`",
        "",
        "## Promotions",
        "",
        "| Name | Status | Compare | Variants | Required Artifacts | Primary Variant | Scale Run |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("promotions")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("promotion_status")),
                    _md(row.get("promoted_for_comparison")),
                    _md(row.get("variant_count")),
                    _md(f"{row.get('available_required_artifact_count')}/{row.get('required_artifact_count')}"),
                    _md(row.get("primary_variant")),
                    _md(row.get("training_scale_run_path")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Compare Inputs", ""])
    command = _string_list(comparison.get("compare_command"))
    if command:
        lines.append("```powershell")
        lines.append(" ".join(command))
        lines.append("```")
    else:
        lines.append("No comparison command is ready yet.")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_promotion_index_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_promotion_index_markdown(report), encoding="utf-8")


def render_training_scale_promotion_index_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison_inputs"))
    stats = [
        ("Promotions", summary.get("promotion_count")),
        ("Promoted", summary.get("promoted_count")),
        ("Review", summary.get("review_count")),
        ("Blocked", summary.get("blocked_count")),
        ("Comparison ready", summary.get("comparison_ready_count")),
        ("Command ready", summary.get("compare_command_ready")),
        ("Baseline", comparison.get("baseline_name")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale promotion index'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale promotion index'))}</h1><p>{_e(report.get('generated_at'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _promotions_table(report),
            _compare_section(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale promotion index.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_promotion_index_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_promotion_index_html(report), encoding="utf-8")


def write_training_scale_promotion_index_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_promotion_index.json",
        "csv": root / "training_scale_promotion_index.csv",
        "markdown": root / "training_scale_promotion_index.md",
        "html": root / "training_scale_promotion_index.html",
    }
    write_training_scale_promotion_index_json(report, paths["json"])
    write_training_scale_promotion_index_csv(report, paths["csv"])
    write_training_scale_promotion_index_markdown(report, paths["markdown"])
    write_training_scale_promotion_index_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_promotion_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "training_scale_promotion.json",
                path / "promotion" / "training_scale_promotion.json",
                path / "training-scale-promotion" / "training_scale_promotion.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _resolve_names(reports: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        resolved = [str(name).strip() for name in names]
    else:
        resolved = []
        for index, report in enumerate(reports):
            source = Path(str(report.get("_source_path") or f"promotion-{index + 1}"))
            parent = source.parent
            if parent.name in {"promotion", "training-scale-promotion"} and parent.parent.name:
                resolved.append(parent.parent.name)
            else:
                resolved.append(str(parent.name or source.stem or f"promotion-{index + 1}"))
    if any(not name for name in resolved):
        raise ValueError("promotion names cannot be empty")
    if len(set(resolved)) != len(resolved):
        raise ValueError("promotion names must be unique")
    return resolved


def _promotion_row(report: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    variants = _list_of_dicts(report.get("variants"))
    primary = _primary_variant(variants)
    artifacts = _artifact_map(primary)
    scale_run_path = str(report.get("training_scale_run_path") or "")
    scale_run_exists = bool(scale_run_path and Path(scale_run_path).is_file())
    promotion_status = str(summary.get("promotion_status") or "missing")
    promoted_for_comparison = promotion_status == "promoted" and scale_run_exists
    return {
        "index": index + 1,
        "name": name,
        "promotion_source_path": report.get("_source_path"),
        "promotion_status": promotion_status,
        "promoted_for_comparison": promoted_for_comparison,
        "handoff_path": report.get("handoff_path"),
        "project_root": report.get("project_root"),
        "out_root": report.get("out_root"),
        "training_scale_run_path": scale_run_path,
        "training_scale_run_exists": scale_run_exists,
        "batch_path": report.get("batch_path"),
        "handoff_status": summary.get("handoff_status"),
        "scale_run_status": summary.get("scale_run_status"),
        "batch_status": summary.get("batch_status"),
        "variant_count": summary.get("variant_count") or len(variants),
        "ready_variant_count": summary.get("ready_variant_count") or sum(1 for row in variants if row.get("promotion_status") == "ready"),
        "checkpoint_count": summary.get("checkpoint_count"),
        "registry_count": summary.get("registry_count"),
        "maturity_narrative_count": summary.get("maturity_narrative_count"),
        "required_artifact_count": summary.get("required_artifact_count"),
        "available_required_artifact_count": summary.get("available_required_artifact_count"),
        "blocker_count": summary.get("blocker_count") or len(_string_list(report.get("blockers"))),
        "review_item_count": summary.get("review_item_count") or len(_string_list(report.get("review_items"))),
        "primary_variant": primary.get("name"),
        "primary_variant_status": primary.get("promotion_status"),
        "primary_portfolio_json": primary.get("portfolio_json"),
        "primary_checkpoint": artifacts.get("checkpoint"),
        "primary_registry": artifacts.get("registry"),
        "primary_maturity_narrative": artifacts.get("maturity_narrative"),
        "missing_required": _string_list(primary.get("missing_required")),
        "blockers": _string_list(report.get("blockers")),
        "review_items": _string_list(report.get("review_items")),
    }


def _primary_variant(variants: list[dict[str, Any]]) -> dict[str, Any]:
    for row in variants:
        if row.get("promotion_status") == "ready":
            return row
    return variants[0] if variants else {}


def _artifact_map(variant: dict[str, Any]) -> dict[str, str]:
    rows = _list_of_dicts(variant.get("artifact_rows"))
    result = {}
    for row in rows:
        if row.get("exists"):
            result[str(row.get("key"))] = str(row.get("path") or "")
    return result


def _comparison_inputs(promotions: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    ready = [row for row in promotions if row.get("promoted_for_comparison")]
    baseline_row = _select_baseline(ready, baseline)
    paths = [str(row.get("training_scale_run_path")) for row in ready]
    names = [str(row.get("name")) for row in ready]
    command = []
    if len(ready) >= 2:
        command = ["python", "scripts/compare_training_scale_runs.py"]
        command.extend(paths)
        for name in names:
            command.extend(["--name", name])
        if baseline_row:
            command.extend(["--baseline", str(baseline_row.get("name"))])
    return {
        "run_count": len(ready),
        "names": names,
        "training_scale_run_paths": paths,
        "baseline_name": baseline_row.get("name") if baseline_row else None,
        "compare_command_ready": len(command) > 0,
        "compare_command": command,
    }


def _select_baseline(rows: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if not rows:
        if baseline is not None:
            raise ValueError("baseline cannot be selected without promoted comparison inputs")
        return {}
    if baseline is None:
        return rows[0]
    if isinstance(baseline, int) or (isinstance(baseline, str) and str(baseline).isdigit()):
        index = int(baseline)
        if index < 0 or index >= len(rows):
            raise ValueError("baseline index out of range")
        return rows[index]
    for row in rows:
        if row.get("name") == baseline:
            return row
    raise ValueError(f"baseline is not promoted for comparison: {baseline}")


def _summary(promotions: list[dict[str, Any]], comparison_inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "promotion_count": len(promotions),
        "promoted_count": sum(1 for row in promotions if row.get("promotion_status") == "promoted"),
        "review_count": sum(1 for row in promotions if row.get("promotion_status") == "review"),
        "blocked_count": sum(1 for row in promotions if row.get("promotion_status") == "blocked"),
        "missing_count": sum(1 for row in promotions if row.get("promotion_status") == "missing"),
        "comparison_ready_count": comparison_inputs.get("run_count"),
        "compare_command_ready": comparison_inputs.get("compare_command_ready"),
        "non_comparable_count": sum(1 for row in promotions if not row.get("promoted_for_comparison")),
    }


def _recommendations(summary: dict[str, Any]) -> list[str]:
    ready_count = _int(summary.get("comparison_ready_count"))
    blocked_count = _int(summary.get("blocked_count"))
    review_count = _int(summary.get("review_count"))
    if ready_count >= 2:
        return [
            "Run the generated compare command to compare only promoted training scale runs.",
            "Keep review and blocked promotions out of baseline selection until their evidence is fixed.",
        ]
    if ready_count == 1:
        return [
            "Use the single promoted run as the baseline candidate and add another promoted run before comparison.",
            "Do not compare review or blocked promotions against the baseline as model capability evidence.",
        ]
    if blocked_count or review_count:
        return ["Resolve review or blocked promotions before building a training scale comparison."]
    return ["Create at least one promoted training scale promotion before building the index."]


def _promotions_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("promotions")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('promotion_status'))}</td>"
            f"<td>{_e(row.get('promoted_for_comparison'))}</td>"
            f"<td>{_e(row.get('ready_variant_count'))}/{_e(row.get('variant_count'))}</td>"
            f"<td>{_e(row.get('available_required_artifact_count'))}/{_e(row.get('required_artifact_count'))}</td>"
            f"<td>{_e(row.get('primary_variant'))}</td>"
            f"<td>{_e(row.get('training_scale_run_path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Promotions</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Name</th><th>Status</th><th>Compare</th><th>Variants</th><th>Artifacts</th><th>Primary</th><th>Scale Run</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _compare_section(report: dict[str, Any]) -> str:
    comparison = _dict(report.get("comparison_inputs"))
    command = _string_list(comparison.get("compare_command"))
    body = _e(" ".join(command)) if command else "No comparison command is ready yet."
    return f"<section><h2>Compare Inputs</h2><pre>{body}</pre></section>"


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f8f6; color: #162126; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d6ddd6; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #52635a; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9e1da; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(22, 33, 38, 0.05); }
.card span { display: block; color: #64756c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 940px; }
th, td { text-align: left; border-bottom: 1px solid #e4e9e4; padding: 9px; vertical-align: top; }
th { color: #435249; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #f2f5f1; border: 1px solid #dce4dd; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69786e; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


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


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
