from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_variant_plan import PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_variant_replay import PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, utc_now, write_json_payload
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME = "model_capability_required_term_pair_surface_variant_selector.json"
PAIR_SURFACE_VARIANT_SELECTOR_CSV_FILENAME = "model_capability_required_term_pair_surface_variant_selector.csv"
PAIR_SURFACE_VARIANT_SELECTOR_TEXT_FILENAME = "model_capability_required_term_pair_surface_variant_selector.txt"
PAIR_SURFACE_VARIANT_SELECTOR_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_variant_selector.md"
PAIR_SURFACE_VARIANT_SELECTOR_HTML_FILENAME = "model_capability_required_term_pair_surface_variant_selector.html"

VARIANT_STYLE_RANK = {"space": 0, "semicolon": 1, "newline": 2, "worded": 3, "compact": 4}


def locate_surface_variant_selector_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME
    return source


def locate_surface_variant_selector_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface variant selector input must be a JSON object")
    return dict(payload)


def build_surface_variant_selector(
    variant_plan: dict[str, Any],
    variant_replay: dict[str, Any],
    *,
    plan_source_path: str | Path | None = None,
    replay_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _candidate_rows(variant_plan, variant_replay)
    issues = _issues(variant_plan, variant_replay, rows)
    selected = _select(rows)
    summary = _summary(rows, selected, variant_replay)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface variant selector",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_variant_plan_path": str(plan_source_path or ""),
        "source_variant_replay_path": str(replay_source_path or ""),
        "candidate_rows": rows,
        "selected_variant": selected,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def write_surface_variant_selector_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_VARIANT_SELECTOR_CSV_FILENAME,
        "text": root / PAIR_SURFACE_VARIANT_SELECTOR_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_VARIANT_SELECTOR_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_VARIANT_SELECTOR_HTML_FILENAME,
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
            f"selected_variant_id={summary.get('selected_variant_id')}",
            f"stable_variant_count={summary.get('stable_variant_count')}",
            f"promotion_allowed={summary.get('promotion_allowed')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    selected = as_dict(report.get("selected_variant"))
    rows = ["| Variant | Stable | Style rank | Selection score |", "| --- | --- | ---: | ---: |"]
    for row in list_of_dicts(report.get("candidate_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("stable_pair_full")),
                    markdown_cell(row.get("style_rank")),
                    markdown_cell(row.get("selection_score")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Variant Selector",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Selected variant: `{selected.get('variant_id')}`",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(_candidate_html(row) for row in list_of_dicts(report.get("candidate_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface variant selector</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface variant selector</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Selected</span><strong>{html_escape(summary.get('selected_variant_id'))}</strong></div>
<div><span>Stable</span><strong>{html_escape(summary.get('stable_variant_count'))}</strong></div>
<div><span>Promotion</span><strong>{html_escape(summary.get('promotion_allowed'))}</strong></div>
</section>
<section><h2>Candidates</h2><table><thead><tr><th>Variant</th><th>Separator</th><th>Stable</th><th>Score</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def _candidate_rows(variant_plan: dict[str, Any], variant_replay: dict[str, Any]) -> list[dict[str, Any]]:
    plan_by_id = {str(row.get("variant_id")): row for row in list_of_dicts(variant_plan.get("variant_rows"))}
    rows = []
    for replay in list_of_dicts(variant_replay.get("variant_summaries")):
        variant_id = str(replay.get("variant_id") or "")
        plan = as_dict(plan_by_id.get(variant_id))
        stable = replay.get("stable_pair_full") is True
        style = str(plan.get("separator_style") or "")
        rank = VARIANT_STYLE_RANK.get(style, 9)
        rows.append(
            {
                "variant_id": variant_id,
                "prompt_template": plan.get("prompt_template", ""),
                "separator_style": style,
                "stable_pair_full": stable,
                "pair_full_seed_count": replay.get("pair_full_seed_count"),
                "hit_case_count": replay.get("hit_case_count"),
                "style_rank": rank,
                "selection_score": _score(stable, rank, str(plan.get("prompt_template") or "")),
                "selection_reason": _reason(stable, style),
            }
        )
    return rows


def _issues(variant_plan: dict[str, Any], variant_replay: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues = []
    if variant_plan.get("status") != "pass":
        issues.append({"id": "bad_variant_plan_source", "detail": "source variant plan is not pass"})
    if variant_replay.get("status") != "pass":
        issues.append({"id": "bad_variant_replay_source", "detail": "source variant replay is not pass"})
    if not rows:
        issues.append({"id": "missing_candidates", "detail": "variant replay has no candidates"})
    if rows and not any(row.get("stable_pair_full") for row in rows):
        issues.append({"id": "no_stable_variant", "detail": "variant replay has no stable variants"})
    return issues


def _select(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stable = [row for row in rows if row.get("stable_pair_full")]
    if not stable:
        return {}
    return sorted(stable, key=lambda row: (-int(row.get("selection_score") or 0), int(row.get("style_rank") or 9), str(row.get("variant_id") or "")))[0]


def _summary(rows: list[dict[str, Any]], selected: dict[str, Any], variant_replay: dict[str, Any]) -> dict[str, Any]:
    stable = [row.get("variant_id") for row in rows if row.get("stable_pair_full")]
    replay_summary = as_dict(variant_replay.get("summary"))
    return {
        "candidate_count": len(rows),
        "stable_variant_count": len(stable),
        "stable_variant_ids": stable,
        "selected_variant_id": selected.get("variant_id", ""),
        "max_new_tokens": replay_summary.get("max_new_tokens"),
        "promotion_allowed": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_variant_selector"
    if summary.get("selected_variant_id"):
        return "required_term_pair_surface_variant_selected_for_contextual_demo"
    return "required_term_pair_surface_variant_not_selected"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Variant selector inputs are invalid.", "next_action": "repair variant replay evidence"}
    return {
        "model_quality_claim": "contextual_surface_variant_selected",
        "reason": "A stable, readable, profile-aligned contextual variant is selected without changing the promotion boundary.",
        "next_action": "contrast contextual variant success against non-leaking baselines",
    }


def _score(stable: bool, style_rank: int, template: str) -> int:
    if not stable:
        return -1000
    return 100 - (style_rank * 10) - min(len(template), 80)


def _reason(stable: bool, style: str) -> str:
    if not stable:
        return "not stable across tested seeds"
    if style == "space":
        return "stable and matches the original execution profile"
    if style == "compact":
        return "stable but less readable because labels are fused"
    if style == "worded":
        return "stable but adds extra instruction wording"
    return "stable contextual separator variant"


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["variant_id", "separator_style", "stable_pair_full", "pair_full_seed_count", "hit_case_count", "style_rank", "selection_score", "selection_reason"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("candidate_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _candidate_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('separator_style'))}</td>"
        f"<td>{html_escape(row.get('stable_pair_full'))}</td>"
        f"<td>{html_escape(row.get('selection_score'))}</td>"
        f"<td>{html_escape(row.get('selection_reason'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1100px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
th{background:#f7f9fb;color:#334155}
</style>"""


__all__ = [
    "PAIR_SURFACE_VARIANT_SELECTOR_CSV_FILENAME",
    "PAIR_SURFACE_VARIANT_SELECTOR_HTML_FILENAME",
    "PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME",
    "PAIR_SURFACE_VARIANT_SELECTOR_MARKDOWN_FILENAME",
    "PAIR_SURFACE_VARIANT_SELECTOR_TEXT_FILENAME",
    "build_surface_variant_selector",
    "locate_surface_variant_selector_plan_source",
    "locate_surface_variant_selector_replay_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_variant_selector_outputs",
]
