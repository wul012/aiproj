from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_execution_profile import (
    PAIR_SURFACE_POLICY_EXECUTION_PROFILE_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, utc_now, write_json_payload
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME = "model_capability_required_term_pair_surface_variant_plan.json"
PAIR_SURFACE_VARIANT_PLAN_CSV_FILENAME = "model_capability_required_term_pair_surface_variant_plan.csv"
PAIR_SURFACE_VARIANT_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_surface_variant_plan.txt"
PAIR_SURFACE_VARIANT_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_variant_plan.md"
PAIR_SURFACE_VARIANT_PLAN_HTML_FILENAME = "model_capability_required_term_pair_surface_variant_plan.html"


def locate_surface_variant_plan_profile_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_EXECUTION_PROFILE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface variant plan input must be a JSON object")
    return dict(payload)


def build_surface_variant_plan(
    execution_profile_report: dict[str, Any],
    *,
    profile_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    profile = as_dict(execution_profile_report.get("profile"))
    issues = _issues(execution_profile_report, profile)
    variant_rows = _variant_rows(profile) if not issues else []
    summary = _summary(profile, variant_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface variant plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_profile_path": str(profile_source_path or ""),
        "execution_profile": profile,
        "variant_rows": variant_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def write_surface_variant_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_VARIANT_PLAN_CSV_FILENAME,
        "text": root / PAIR_SURFACE_VARIANT_PLAN_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_VARIANT_PLAN_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_VARIANT_PLAN_HTML_FILENAME,
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
            f"profile_id={summary.get('profile_id')}",
            f"variant_count={summary.get('variant_count')}",
            f"included_variant_count={summary.get('included_variant_count')}",
            f"max_new_tokens={summary.get('max_new_tokens')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    rows = ["| Variant | Separator | Template |", "| --- | --- | --- |"]
    for row in list_of_dicts(report.get("variant_rows")):
        rows.append(
            "| "
            + " | ".join(
                [markdown_cell(row.get("variant_id")), markdown_cell(row.get("separator_style")), markdown_cell(row.get("prompt_template"))]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Variant Plan",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            "## Variants",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(
        f"<tr><td>{html_escape(row.get('variant_id'))}</td><td>{html_escape(row.get('separator_style'))}</td><td>{html_escape(row.get('prompt_template'))}</td><td>{html_escape(row.get('rationale'))}</td></tr>"
        for row in list_of_dicts(report.get("variant_rows"))
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface variant plan</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface variant plan</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Profile</span><strong>{html_escape(summary.get('profile_id'))}</strong></div>
<div><span>Variants</span><strong>{html_escape(summary.get('included_variant_count'))}</strong></div>
<div><span>Budget</span><strong>{html_escape(summary.get('max_new_tokens'))}</strong></div>
</section>
<section><h2>Variants</h2><table><thead><tr><th>Variant</th><th>Separator</th><th>Template</th><th>Rationale</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def _issues(report: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, str]]:
    issues = []
    if report.get("status") != "pass":
        issues.append({"id": "bad_execution_profile_source", "detail": "execution profile report is not pass"})
    if not profile.get("profile_id"):
        issues.append({"id": "missing_profile", "detail": "execution profile is missing"})
    if profile.get("promotion_allowed") is not False:
        issues.append({"id": "promotion_boundary_missing", "detail": "execution profile must block promotion"})
    if not profile.get("max_new_tokens"):
        issues.append({"id": "missing_budget", "detail": "execution profile has no max_new_tokens"})
    return issues


def _variant_rows(profile: dict[str, Any]) -> list[dict[str, Any]]:
    base_policy = str(profile.get("policy_id") or "")
    rows = [
        ("space_context_control", "{other_term}={other_term} {term}=", "space", "control variant from the selected profile"),
        ("semicolon_context", "{other_term}={other_term}; {term}=", "semicolon", "tests punctuation-separated contextual anchoring"),
        ("newline_context", "{other_term}={other_term}\n{term}=", "newline", "tests line-break separated contextual anchoring"),
        ("compact_context", "{other_term}={other_term}{term}=", "compact", "tests whether the separator space is essential"),
        ("worded_context", "known {other_term}={other_term}; answer {term}=", "worded", "tests a slightly more natural instruction-like surface"),
    ]
    return [
        {
            "variant_id": variant_id,
            "base_policy_id": base_policy,
            "prompt_template": template,
            "separator_style": separator,
            "leakage_level": "contextual_anchor",
            "included_in_replay": True,
            "rationale": rationale,
        }
        for variant_id, template, separator, rationale in rows
    ]


def _summary(profile: dict[str, Any], variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "profile_id": profile.get("profile_id", ""),
        "policy_id": profile.get("policy_id", ""),
        "max_new_tokens": profile.get("max_new_tokens"),
        "variant_count": len(variant_rows),
        "included_variant_count": sum(1 for row in variant_rows if row.get("included_in_replay")),
        "promotion_ready": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_variant_plan"
    if summary.get("included_variant_count"):
        return "required_term_pair_surface_variant_plan_ready"
    return "required_term_pair_surface_variant_plan_empty"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Variant plan inputs are invalid.", "next_action": "repair execution profile evidence"}
    return {
        "model_quality_claim": "contextual_surface_variant_plan",
        "reason": "The plan tests whether the selected contextual profile is brittle to surface separators.",
        "next_action": "run variant replay over the dual-boundary checkpoints",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["variant_id", "base_policy_id", "prompt_template", "separator_style", "leakage_level", "included_in_replay", "rationale"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("variant_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


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
    "PAIR_SURFACE_VARIANT_PLAN_CSV_FILENAME",
    "PAIR_SURFACE_VARIANT_PLAN_HTML_FILENAME",
    "PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME",
    "PAIR_SURFACE_VARIANT_PLAN_MARKDOWN_FILENAME",
    "PAIR_SURFACE_VARIANT_PLAN_TEXT_FILENAME",
    "build_surface_variant_plan",
    "locate_surface_variant_plan_profile_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_variant_plan_outputs",
]
