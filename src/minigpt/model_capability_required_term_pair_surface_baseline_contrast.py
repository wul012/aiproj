from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_replay import PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_variant_selector import PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, utc_now, write_json_payload
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME = "model_capability_required_term_pair_surface_baseline_contrast.json"
PAIR_SURFACE_BASELINE_CONTRAST_CSV_FILENAME = "model_capability_required_term_pair_surface_baseline_contrast.csv"
PAIR_SURFACE_BASELINE_CONTRAST_TEXT_FILENAME = "model_capability_required_term_pair_surface_baseline_contrast.txt"
PAIR_SURFACE_BASELINE_CONTRAST_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_baseline_contrast.md"
PAIR_SURFACE_BASELINE_CONTRAST_HTML_FILENAME = "model_capability_required_term_pair_surface_baseline_contrast.html"


def locate_baseline_contrast_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
    return source


def locate_baseline_contrast_selector_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface baseline contrast input must be a JSON object")
    return dict(payload)


def build_surface_baseline_contrast(
    policy_replay: dict[str, Any],
    variant_selector: dict[str, Any],
    *,
    replay_source_path: str | Path | None = None,
    selector_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _contrast_rows(policy_replay, variant_selector)
    issues = _issues(policy_replay, variant_selector, rows)
    summary = _summary(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface baseline contrast",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_policy_replay_path": str(replay_source_path or ""),
        "source_variant_selector_path": str(selector_source_path or ""),
        "contrast_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def write_surface_baseline_contrast_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_BASELINE_CONTRAST_CSV_FILENAME,
        "text": root / PAIR_SURFACE_BASELINE_CONTRAST_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_BASELINE_CONTRAST_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_BASELINE_CONTRAST_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"contextual_stable={summary.get('contextual_stable')}",
            f"non_leaking_baseline_count={summary.get('non_leaking_baseline_count')}",
            f"stable_non_leaking_baseline_count={summary.get('stable_non_leaking_baseline_count')}",
            f"contextual_anchor_required={summary.get('contextual_anchor_required')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    rows = ["| Source | Type | Stable | Pair-full seeds | Hits |", "| --- | --- | --- | ---: | ---: |"]
    for row in list_of_dicts(report.get("contrast_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_id")),
                    markdown_cell(row.get("source_type")),
                    markdown_cell(row.get("stable_pair_full")),
                    markdown_cell(row.get("pair_full_seed_count")),
                    markdown_cell(row.get("hit_case_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Baseline Contrast",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(_row_html(row) for row in list_of_dicts(report.get("contrast_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface baseline contrast</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface baseline contrast</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Contextual stable</span><strong>{html_escape(summary.get('contextual_stable'))}</strong></div>
<div><span>Non-leaking stable</span><strong>{html_escape(summary.get('stable_non_leaking_baseline_count'))}</strong></div>
<div><span>Anchor required</span><strong>{html_escape(summary.get('contextual_anchor_required'))}</strong></div>
</section>
<section><h2>Contrast</h2><table><thead><tr><th>Source</th><th>Type</th><th>Stable</th><th>Pair-full seeds</th><th>Hits</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def _contrast_rows(policy_replay: dict[str, Any], variant_selector: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    selected = as_dict(variant_selector.get("selected_variant"))
    if selected:
        rows.append(
            {
                "source_id": selected.get("variant_id"),
                "source_type": "selected_contextual_variant",
                "stable_pair_full": selected.get("stable_pair_full"),
                "pair_full_seed_count": selected.get("pair_full_seed_count"),
                "hit_case_count": selected.get("hit_case_count"),
            }
        )
    for row in list_of_dicts(policy_replay.get("policy_summaries")):
        policy_id = str(row.get("policy_id") or "")
        if policy_id.startswith("single_label"):
            rows.append(
                {
                    "source_id": policy_id,
                    "source_type": "non_leaking_baseline",
                    "stable_pair_full": row.get("stable_pair_full"),
                    "pair_full_seed_count": row.get("pair_full_seed_count"),
                    "hit_case_count": row.get("hit_case_count"),
                }
            )
    return rows


def _issues(policy_replay: dict[str, Any], variant_selector: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues = []
    if policy_replay.get("status") != "pass":
        issues.append({"id": "bad_policy_replay_source", "detail": "source policy replay is not pass"})
    if variant_selector.get("status") != "pass":
        issues.append({"id": "bad_variant_selector_source", "detail": "source variant selector is not pass"})
    if not any(row.get("source_type") == "selected_contextual_variant" for row in rows):
        issues.append({"id": "missing_contextual_variant", "detail": "selected contextual variant is missing"})
    if not any(row.get("source_type") == "non_leaking_baseline" for row in rows):
        issues.append({"id": "missing_non_leaking_baselines", "detail": "non-leaking baseline rows are missing"})
    return issues


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    contextual = [row for row in rows if row.get("source_type") == "selected_contextual_variant"]
    baselines = [row for row in rows if row.get("source_type") == "non_leaking_baseline"]
    stable_baselines = [row for row in baselines if row.get("stable_pair_full")]
    contextual_stable = any(row.get("stable_pair_full") for row in contextual)
    return {
        "contextual_stable": contextual_stable,
        "non_leaking_baseline_count": len(baselines),
        "stable_non_leaking_baseline_count": len(stable_baselines),
        "contextual_anchor_required": contextual_stable and not stable_baselines,
        "promotion_allowed": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_baseline_contrast"
    if summary.get("contextual_anchor_required"):
        return "required_term_pair_contextual_variant_needed_over_non_leaking_baselines"
    if summary.get("stable_non_leaking_baseline_count"):
        return "required_term_pair_non_leaking_baseline_available"
    return "required_term_pair_surface_baseline_contrast_no_contextual_gain"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Baseline contrast inputs are invalid.", "next_action": "repair replay or selector evidence"}
    if summary.get("contextual_anchor_required"):
        return {
            "model_quality_claim": "contextual_anchor_required_for_surface_stability",
            "reason": "The selected contextual variant is stable while non-leaking baselines are not.",
            "next_action": "close this branch as contextual decode aid unless a new objective targets minimal prompts",
        }
    return {
        "model_quality_claim": "minimal_surface_baseline_possible",
        "reason": "A non-leaking baseline is stable in the replay evidence.",
        "next_action": "promote non-leaking baseline to further held-out checks",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["source_id", "source_type", "stable_pair_full", "pair_full_seed_count", "hit_case_count"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("contrast_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_id'))}</td>"
        f"<td>{html_escape(row.get('source_type'))}</td>"
        f"<td>{html_escape(row.get('stable_pair_full'))}</td>"
        f"<td>{html_escape(row.get('pair_full_seed_count'))}</td>"
        f"<td>{html_escape(row.get('hit_case_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1100px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
th{background:#f7f9fb;color:#334155}
</style>"""


__all__ = [
    "PAIR_SURFACE_BASELINE_CONTRAST_CSV_FILENAME",
    "PAIR_SURFACE_BASELINE_CONTRAST_HTML_FILENAME",
    "PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME",
    "PAIR_SURFACE_BASELINE_CONTRAST_MARKDOWN_FILENAME",
    "PAIR_SURFACE_BASELINE_CONTRAST_TEXT_FILENAME",
    "build_surface_baseline_contrast",
    "locate_baseline_contrast_replay_source",
    "locate_baseline_contrast_selector_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_baseline_contrast_outputs",
]
