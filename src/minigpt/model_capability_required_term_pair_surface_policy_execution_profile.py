from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_budget_sweep import PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_policy_leakage_risk import PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, markdown_cell, utc_now, write_json_payload
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SURFACE_POLICY_EXECUTION_PROFILE_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_execution_profile.json"
PAIR_SURFACE_POLICY_EXECUTION_PROFILE_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_execution_profile.csv"
PAIR_SURFACE_POLICY_EXECUTION_PROFILE_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_execution_profile.txt"
PAIR_SURFACE_POLICY_EXECUTION_PROFILE_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_execution_profile.md"
PAIR_SURFACE_POLICY_EXECUTION_PROFILE_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_execution_profile.html"


def locate_execution_profile_leakage_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME
    return source


def locate_execution_profile_budget_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy execution profile input must be a JSON object")
    return dict(payload)


def build_surface_policy_execution_profile(
    leakage_report: dict[str, Any],
    budget_report: dict[str, Any],
    *,
    leakage_source_path: str | Path | None = None,
    budget_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    leakage_summary = as_dict(leakage_report.get("summary"))
    budget_summary = as_dict(budget_report.get("summary"))
    selected = as_dict(budget_report.get("selected_policy"))
    settings = as_dict(budget_report.get("settings"))
    issues = _issues(leakage_report, budget_report, leakage_summary, budget_summary, selected)
    profile = _profile(selected, settings, budget_summary, leakage_summary) if not issues else {}
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy execution profile",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, profile),
        "failed_count": len(issues),
        "issues": issues,
        "source_leakage_path": str(leakage_source_path or ""),
        "source_budget_path": str(budget_source_path or ""),
        "profile": profile,
        "summary": _summary(profile),
        "interpretation": _interpretation(status, profile),
    }


def write_surface_policy_execution_profile_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_POLICY_EXECUTION_PROFILE_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_POLICY_EXECUTION_PROFILE_CSV_FILENAME,
        "text": root / PAIR_SURFACE_POLICY_EXECUTION_PROFILE_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_POLICY_EXECUTION_PROFILE_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_POLICY_EXECUTION_PROFILE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_text(report: dict[str, Any]) -> str:
    profile = as_dict(report.get("profile"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"profile_id={profile.get('profile_id')}",
            f"policy_id={profile.get('policy_id')}",
            f"max_new_tokens={profile.get('max_new_tokens')}",
            f"promotion_allowed={profile.get('promotion_allowed')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    profile = as_dict(report.get("profile"))
    rows = ["| Field | Value |", "| --- | --- |"]
    for key in ("profile_id", "policy_id", "prompt_template", "max_new_tokens", "temperature", "top_k", "allowed_use", "promotion_allowed"):
        rows.append(f"| {markdown_cell(key)} | {markdown_cell(profile.get(key))} |")
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Policy Execution Profile",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    profile = as_dict(report.get("profile"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(
        f"<tr><td>{html_escape(key)}</td><td>{html_escape(profile.get(key))}</td></tr>"
        for key in ("profile_id", "policy_id", "prompt_template", "max_new_tokens", "temperature", "top_k", "allowed_use", "promotion_allowed")
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface policy execution profile</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface policy execution profile</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Profile</span><strong>{html_escape(profile.get('profile_id'))}</strong></div>
<div><span>Budget</span><strong>{html_escape(profile.get('max_new_tokens'))}</strong></div>
<div><span>Promotion</span><strong>{html_escape(profile.get('promotion_allowed'))}</strong></div>
</section>
<section><h2>Profile Fields</h2><table><tbody>{rows}</tbody></table></section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def _issues(
    leakage_report: dict[str, Any],
    budget_report: dict[str, Any],
    leakage_summary: dict[str, Any],
    budget_summary: dict[str, Any],
    selected: dict[str, Any],
) -> list[dict[str, str]]:
    issues = []
    if leakage_report.get("status") != "pass":
        issues.append({"id": "bad_leakage_source", "detail": "source leakage report is not pass"})
    if budget_report.get("status") != "pass":
        issues.append({"id": "bad_budget_source", "detail": "source budget report is not pass"})
    if not selected.get("policy_id"):
        issues.append({"id": "missing_selected_policy", "detail": "budget report has no selected policy"})
    if leakage_summary.get("promotion_allowed") is not False:
        issues.append({"id": "promotion_boundary_missing", "detail": "leakage report must block promotion"})
    if not budget_summary.get("minimal_stable_budget"):
        issues.append({"id": "missing_minimal_budget", "detail": "budget report has no minimal stable budget"})
    return issues


def _profile(
    selected: dict[str, Any],
    settings: dict[str, Any],
    budget_summary: dict[str, Any],
    leakage_summary: dict[str, Any],
) -> dict[str, Any]:
    policy_id = str(selected.get("policy_id") or "")
    budget = int(budget_summary.get("minimal_stable_budget") or 0)
    return {
        "profile_id": f"{policy_id}_budget_{budget}",
        "policy_id": policy_id,
        "prompt_template": selected.get("prompt_template", ""),
        "max_new_tokens": budget,
        "temperature": settings.get("temperature"),
        "top_k": settings.get("top_k"),
        "device": settings.get("device"),
        "leakage_level": selected.get("leakage_level"),
        "risk_level": leakage_summary.get("risk_level"),
        "allowed_use": "contextual_decode_surface_variant_replay",
        "promotion_allowed": False,
    }


def _summary(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile_id": profile.get("profile_id", ""),
        "policy_id": profile.get("policy_id", ""),
        "max_new_tokens": profile.get("max_new_tokens"),
        "promotion_ready": False,
    }


def _decision(status: str, profile: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_execution_profile"
    if profile.get("profile_id"):
        return "required_term_pair_surface_policy_execution_profile_selected"
    return "required_term_pair_surface_policy_execution_profile_not_selected"


def _interpretation(status: str, profile: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Execution profile inputs are invalid.", "next_action": "repair leakage or budget evidence"}
    return {
        "model_quality_claim": "contextual_decode_execution_profile",
        "reason": "The selected profile carries the minimal stable budget while preserving the promotion block.",
        "next_action": "run surface-variant replay with this profile",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    profile = as_dict(report.get("profile"))
    fieldnames = ["profile_id", "policy_id", "prompt_template", "max_new_tokens", "temperature", "top_k", "allowed_use", "promotion_allowed"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({field: csv_cell(profile.get(field)) for field in fieldnames})


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
</style>"""


__all__ = [
    "PAIR_SURFACE_POLICY_EXECUTION_PROFILE_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_EXECUTION_PROFILE_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_EXECUTION_PROFILE_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_EXECUTION_PROFILE_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_EXECUTION_PROFILE_TEXT_FILENAME",
    "build_surface_policy_execution_profile",
    "locate_execution_profile_budget_source",
    "locate_execution_profile_leakage_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_policy_execution_profile_outputs",
]
