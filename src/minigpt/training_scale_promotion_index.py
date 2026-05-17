from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_json_payload,
)
from minigpt.training_scale_promotion_index_helpers import (
    _comparison_inputs,
    _promotion_row,
    _recommendations,
    _resolve_names,
    _summary,
)


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
    write_json_payload(report, path)


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
