from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_aligned_candidate_seed_stability import (
    PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_surface_policy_replay import (
    GenerateFunc,
    build_model_capability_required_term_pair_surface_policy_replay,
)
from minigpt.model_capability_required_term_pair_surface_variant_plan import PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, utc_now, write_json_payload


PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME = "model_capability_required_term_pair_surface_variant_replay.json"
PAIR_SURFACE_VARIANT_REPLAY_CSV_FILENAME = "model_capability_required_term_pair_surface_variant_replay.csv"
PAIR_SURFACE_VARIANT_REPLAY_TEXT_FILENAME = "model_capability_required_term_pair_surface_variant_replay.txt"
PAIR_SURFACE_VARIANT_REPLAY_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_variant_replay.md"
PAIR_SURFACE_VARIANT_REPLAY_HTML_FILENAME = "model_capability_required_term_pair_surface_variant_replay.html"


def locate_surface_variant_replay_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME
    return source


def locate_surface_variant_replay_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_VARIANT_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface variant replay input must be a JSON object")
    return dict(payload)


def build_surface_variant_replay(
    stability_report: dict[str, Any],
    variant_plan: dict[str, Any],
    *,
    out_dir: str | Path,
    stability_source_path: str | Path | None = None,
    variant_plan_source_path: str | Path | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    summary = as_dict(variant_plan.get("summary"))
    max_new_tokens = int(summary.get("max_new_tokens") or 0)
    policy_plan = _policy_plan_from_variants(variant_plan)
    issues = _issues(stability_report, variant_plan, policy_plan, max_new_tokens)
    replay: dict[str, Any] = {}
    if not issues:
        replay = build_model_capability_required_term_pair_surface_policy_replay(
            stability_report,
            policy_plan,
            out_dir=out_dir,
            stability_source_path=stability_source_path,
            policy_plan_source_path=variant_plan_source_path,
            max_new_tokens=max_new_tokens,
            temperature=float(as_dict(variant_plan.get("execution_profile")).get("temperature") or 0.2),
            top_k=int(as_dict(variant_plan.get("execution_profile")).get("top_k") or 1),
            device=device,
            generate_func=generate_func,
        )
    variant_summaries = _variant_summaries(replay)
    report_summary = _summary(variant_summaries, replay, max_new_tokens)
    status = "pass" if not issues and replay.get("status") == "pass" else "fail"
    if status == "fail" and not issues:
        issues = [{"id": "variant_replay_failed", "detail": "underlying surface policy replay failed"}]
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface variant replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, report_summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_stability_path": str(stability_source_path or ""),
        "source_variant_plan_path": str(variant_plan_source_path or ""),
        "settings": {
            "max_new_tokens": max_new_tokens,
            "device": device,
            "experiment_boundary": "replay contextual surface variants over existing dual-boundary checkpoints without retraining",
        },
        "variant_summaries": variant_summaries,
        "case_rows": list_of_dicts(replay.get("case_rows")),
        "summary": report_summary,
        "interpretation": _interpretation(status, report_summary),
    }


def write_surface_variant_replay_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_VARIANT_REPLAY_CSV_FILENAME,
        "text": root / PAIR_SURFACE_VARIANT_REPLAY_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_VARIANT_REPLAY_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_VARIANT_REPLAY_HTML_FILENAME,
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
            f"variant_count={summary.get('variant_count')}",
            f"stable_variant_count={summary.get('stable_variant_count')}",
            f"stable_variant_ids={summary.get('stable_variant_ids')}",
            f"max_new_tokens={summary.get('max_new_tokens')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    rows = ["| Variant | Pair-full seeds | Hits | Stable |", "| --- | ---: | ---: | --- |"]
    for row in list_of_dicts(report.get("variant_summaries")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("pair_full_seed_count")),
                    markdown_cell(row.get("hit_case_count")),
                    markdown_cell(row.get("stable_pair_full")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Variant Replay",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            "## Variant Summary",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    variant_rows = "".join(_variant_html(row) for row in list_of_dicts(report.get("variant_summaries")))
    case_rows = "".join(_case_html(row) for row in list_of_dicts(report.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface variant replay</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface variant replay</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Variants</span><strong>{html_escape(summary.get('variant_count'))}</strong></div>
<div><span>Stable</span><strong>{html_escape(summary.get('stable_variant_count'))}</strong></div>
<div><span>Budget</span><strong>{html_escape(summary.get('max_new_tokens'))}</strong></div>
</section>
<section><h2>Variant Summary</h2><table><thead><tr><th>Variant</th><th>Pair-full seeds</th><th>Hits</th><th>Cases</th><th>Stable</th></tr></thead><tbody>{variant_rows}</tbody></table></section>
<section><h2>Cases</h2><table><thead><tr><th>Seed</th><th>Variant</th><th>Term</th><th>Hit</th><th>Continuation</th></tr></thead><tbody>{case_rows}</tbody></table></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _policy_plan_from_variants(variant_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": variant_plan.get("status"),
        "policy_rows": [
            {
                "policy_id": row.get("variant_id"),
                "prompt_template": row.get("prompt_template"),
                "generation_profile": "default",
                "leakage_level": row.get("leakage_level"),
                "included_in_replay": row.get("included_in_replay"),
            }
            for row in list_of_dicts(variant_plan.get("variant_rows"))
        ],
    }


def _issues(stability_report: dict[str, Any], variant_plan: dict[str, Any], policy_plan: dict[str, Any], max_new_tokens: int) -> list[dict[str, str]]:
    issues = []
    if stability_report.get("status") != "pass":
        issues.append({"id": "bad_stability_source", "detail": "source stability report is not pass"})
    if variant_plan.get("status") != "pass":
        issues.append({"id": "bad_variant_plan_source", "detail": "source variant plan is not pass"})
    if not list_of_dicts(policy_plan.get("policy_rows")):
        issues.append({"id": "missing_variants", "detail": "variant plan has no replay variants"})
    if max_new_tokens <= 0:
        issues.append({"id": "missing_budget", "detail": "variant plan has no positive max_new_tokens"})
    return issues


def _variant_summaries(replay: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in list_of_dicts(replay.get("policy_summaries")):
        rows.append(
            {
                "variant_id": row.get("policy_id"),
                "seed_count": row.get("seed_count"),
                "hit_case_count": row.get("hit_case_count"),
                "case_count": row.get("case_count"),
                "pair_full_seed_count": row.get("pair_full_seed_count"),
                "stable_pair_full": row.get("stable_pair_full"),
            }
        )
    return rows


def _summary(variant_summaries: list[dict[str, Any]], replay: dict[str, Any], max_new_tokens: int) -> dict[str, Any]:
    stable = [row.get("variant_id") for row in variant_summaries if row.get("stable_pair_full")]
    return {
        "variant_count": len(variant_summaries),
        "stable_variant_count": len(stable),
        "stable_variant_ids": stable,
        "case_count": len(list_of_dicts(replay.get("case_rows"))),
        "max_new_tokens": max_new_tokens,
        "promotion_ready": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_variant_replay"
    if summary.get("stable_variant_count") == summary.get("variant_count") and summary.get("variant_count"):
        return "required_term_pair_surface_variant_replay_all_variants_stable"
    if summary.get("stable_variant_count"):
        return "required_term_pair_surface_variant_replay_partial_stability"
    return "required_term_pair_surface_variant_replay_no_stable_variants"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Variant replay execution failed.", "next_action": "repair replay inputs"}
    if summary.get("stable_variant_count") == summary.get("variant_count") and summary.get("variant_count"):
        return {
            "model_quality_claim": "contextual_surface_variant_stable",
            "reason": "All planned contextual surface variants are stable across the tested seeds.",
            "next_action": "select a preferred variant while preserving leakage-risk boundaries",
        }
    if summary.get("stable_variant_count"):
        return {
            "model_quality_claim": "contextual_surface_variant_partial_stability",
            "reason": "Some contextual variants are stable, but the policy is surface-sensitive.",
            "next_action": "select the least brittle stable variant or return to prompt design",
        }
    return {
        "model_quality_claim": "contextual_surface_variant_not_stable",
        "reason": "No planned contextual surface variant is stable.",
        "next_action": "return to objective design",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["variant_id", "seed_count", "hit_case_count", "case_count", "pair_full_seed_count", "stable_pair_full"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("variant_summaries")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _variant_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('pair_full_seed_count'))}</td>"
        f"<td>{html_escape(row.get('hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('stable_pair_full'))}</td>"
        "</tr>"
    )


def _case_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('policy_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
th{background:#f7f9fb;color:#334155}
</style>"""


__all__ = [
    "PAIR_SURFACE_VARIANT_REPLAY_CSV_FILENAME",
    "PAIR_SURFACE_VARIANT_REPLAY_HTML_FILENAME",
    "PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME",
    "PAIR_SURFACE_VARIANT_REPLAY_MARKDOWN_FILENAME",
    "PAIR_SURFACE_VARIANT_REPLAY_TEXT_FILENAME",
    "build_surface_variant_replay",
    "locate_surface_variant_replay_plan_source",
    "locate_surface_variant_replay_stability_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_variant_replay_outputs",
]
