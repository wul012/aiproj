from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_aligned_candidate_seed_stability import (
    PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_surface_policy_replay import (
    DEFAULT_TARGET_TERMS,
    GenerateFunc,
    build_model_capability_required_term_pair_surface_policy_replay,
)
from minigpt.model_capability_required_term_pair_surface_policy_selector import PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, utc_now, write_json_payload


PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_budget_sweep.json"
PAIR_SURFACE_POLICY_BUDGET_SWEEP_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_budget_sweep.csv"
PAIR_SURFACE_POLICY_BUDGET_SWEEP_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_budget_sweep.txt"
PAIR_SURFACE_POLICY_BUDGET_SWEEP_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_budget_sweep.md"
PAIR_SURFACE_POLICY_BUDGET_SWEEP_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_budget_sweep.html"

DEFAULT_BUDGETS = (4, 8, 12, 16)


def locate_budget_sweep_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME
    return source


def locate_budget_sweep_selector_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy budget sweep input must be a JSON object")
    return dict(payload)


def build_surface_policy_budget_sweep(
    stability_report: dict[str, Any],
    selector_report: dict[str, Any],
    *,
    out_dir: str | Path,
    stability_source_path: str | Path | None = None,
    selector_source_path: str | Path | None = None,
    token_budgets: tuple[int, ...] = DEFAULT_BUDGETS,
    temperature: float = 0.2,
    top_k: int = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    selected = as_dict(selector_report.get("selected_policy"))
    budgets = tuple(sorted({int(value) for value in token_budgets if int(value) > 0}))
    issues = _issues(stability_report, selector_report, selected, budgets)
    budget_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    if not issues:
        for budget in budgets:
            replay = build_model_capability_required_term_pair_surface_policy_replay(
                stability_report,
                _single_policy_plan(selected),
                out_dir=Path(out_dir) / f"budget-{budget}",
                stability_source_path=stability_source_path,
                policy_plan_source_path=selector_source_path,
                max_new_tokens=budget,
                temperature=temperature,
                top_k=top_k,
                device=device,
                generate_func=generate_func,
            )
            budget_rows.append(_budget_row(budget, replay))
            case_rows.extend(_case_rows_with_budget(budget, replay))
    summary = _summary(budget_rows, selected)
    status = "pass" if not issues and not any(row.get("status") != "pass" for row in budget_rows) else "fail"
    if status == "fail" and not issues:
        issues = [{"id": "budget_replay_failed", "detail": "one or more budget replay executions failed"}]
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy budget sweep",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_stability_path": str(stability_source_path or ""),
        "source_selector_path": str(selector_source_path or ""),
        "settings": {
            "target_terms": list(DEFAULT_TARGET_TERMS),
            "token_budgets": list(budgets),
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "sweep continuation budget for the selected contextual surface policy without retraining",
        },
        "selected_policy": selected,
        "budget_rows": budget_rows,
        "case_rows": case_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def write_surface_policy_budget_sweep_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_POLICY_BUDGET_SWEEP_CSV_FILENAME,
        "text": root / PAIR_SURFACE_POLICY_BUDGET_SWEEP_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_POLICY_BUDGET_SWEEP_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_POLICY_BUDGET_SWEEP_HTML_FILENAME,
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
            f"selected_policy_id={summary.get('selected_policy_id')}",
            f"stable_budget_count={summary.get('stable_budget_count')}",
            f"stable_budgets={summary.get('stable_budgets')}",
            f"minimal_stable_budget={summary.get('minimal_stable_budget')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = ["| Budget | Pair-full seeds | Hits | Stable |", "| ---: | ---: | ---: | --- |"]
    for row in list_of_dicts(report.get("budget_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("max_new_tokens")),
                    markdown_cell(row.get("pair_full_seed_count")),
                    markdown_cell(row.get("hit_case_count")),
                    markdown_cell(row.get("stable_pair_full")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Policy Budget Sweep",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Selected policy: `{summary.get('selected_policy_id')}`",
            f"- Stable budgets: `{summary.get('stable_budgets')}`",
            f"- Minimal stable budget: `{summary.get('minimal_stable_budget')}`",
            "",
            "## Budget Rows",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Selected", summary.get("selected_policy_id")),
        ("Stable budgets", summary.get("stable_budgets")),
        ("Minimal stable", summary.get("minimal_stable_budget")),
    ]
    budget_rows = "".join(_budget_html(row) for row in list_of_dicts(report.get("budget_rows")))
    case_rows = "".join(_case_html(row) for row in list_of_dicts(report.get("case_rows")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface policy budget sweep</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface policy budget sweep</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Budgets</h2><table><thead><tr><th>Budget</th><th>Seeds</th><th>Hits</th><th>Cases</th><th>Stable</th></tr></thead><tbody>{budget_rows}</tbody></table></section>
<section class="panel"><h2>Cases</h2><table><thead><tr><th>Budget</th><th>Seed</th><th>Term</th><th>Hit</th><th>Continuation</th></tr></thead><tbody>{case_rows}</tbody></table></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _issues(
    stability_report: dict[str, Any],
    selector_report: dict[str, Any],
    selected: dict[str, Any],
    budgets: tuple[int, ...],
) -> list[dict[str, str]]:
    issues = []
    if stability_report.get("status") != "pass":
        issues.append({"id": "bad_stability_source", "detail": "source stability report is not pass"})
    if selector_report.get("status") != "pass":
        issues.append({"id": "bad_selector_source", "detail": "source selector report is not pass"})
    if not selected.get("policy_id"):
        issues.append({"id": "missing_selected_policy", "detail": "selector report has no selected policy"})
    if not budgets:
        issues.append({"id": "missing_budgets", "detail": "at least one positive token budget is required"})
    return issues


def _single_policy_plan(selected: dict[str, Any]) -> dict[str, Any]:
    return {"status": "pass", "policy_rows": [{**selected, "included_in_replay": True}]}


def _budget_row(budget: int, replay: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    policy = list_of_dicts(replay.get("policy_summaries"))
    row = policy[0] if policy else {}
    return {
        "max_new_tokens": budget,
        "status": replay.get("status"),
        "decision": replay.get("decision"),
        "seed_count": summary.get("seed_count"),
        "case_count": summary.get("case_count"),
        "hit_case_count": row.get("hit_case_count", 0),
        "pair_full_seed_count": row.get("pair_full_seed_count", 0),
        "stable_pair_full": row.get("stable_pair_full", False),
    }


def _case_rows_with_budget(budget: int, replay: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in list_of_dicts(replay.get("case_rows")):
        rows.append({"max_new_tokens": budget, **row})
    return rows


def _summary(budget_rows: list[dict[str, Any]], selected: dict[str, Any]) -> dict[str, Any]:
    stable = [int(row.get("max_new_tokens") or 0) for row in budget_rows if row.get("stable_pair_full")]
    return {
        "selected_policy_id": selected.get("policy_id", ""),
        "budget_count": len(budget_rows),
        "stable_budget_count": len(stable),
        "stable_budgets": stable,
        "minimal_stable_budget": min(stable) if stable else None,
        "promotion_ready": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_budget_sweep"
    if summary.get("stable_budget_count"):
        return "required_term_pair_surface_policy_budget_stable_window_found"
    return "required_term_pair_surface_policy_budget_no_stable_window"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Budget sweep execution failed.", "next_action": "repair sweep inputs"}
    if summary.get("stable_budget_count"):
        return {
            "model_quality_claim": "contextual_decode_budget_candidate",
            "reason": "The selected contextual policy has at least one stable continuation budget.",
            "next_action": "select the smallest stable budget and test surface variants",
        }
    return {
        "model_quality_claim": "contextual_decode_budget_not_stable",
        "reason": "No tested continuation budget produced stable pair-full across seeds.",
        "next_action": "return to corpus/objective design instead of decoding policy",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["max_new_tokens", "status", "decision", "seed_count", "case_count", "hit_case_count", "pair_full_seed_count", "stable_pair_full"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("budget_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _budget_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('max_new_tokens'))}</td>"
        f"<td>{html_escape(row.get('pair_full_seed_count'))}</td>"
        f"<td>{html_escape(row.get('hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('stable_pair_full'))}</td>"
        "</tr>"
    )


def _case_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('max_new_tokens'))}</td>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1160px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid #d8dee4;border-radius:8px}.card{padding:14px}.panel{padding:16px;margin:14px 0}
.card span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}.card strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
th{background:#f7f9fb;color:#334155}
</style>"""


__all__ = [
    "DEFAULT_BUDGETS",
    "PAIR_SURFACE_POLICY_BUDGET_SWEEP_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_BUDGET_SWEEP_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_BUDGET_SWEEP_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_BUDGET_SWEEP_TEXT_FILENAME",
    "build_surface_policy_budget_sweep",
    "locate_budget_sweep_selector_source",
    "locate_budget_sweep_stability_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_policy_budget_sweep_outputs",
]
