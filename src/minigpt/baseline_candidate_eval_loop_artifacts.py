from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, html_escape, string_list


LOOP_JSON_FILENAME = "baseline_candidate_eval_loop.json"
LOOP_TEXT_FILENAME = "baseline_candidate_eval_loop.txt"
LOOP_MARKDOWN_FILENAME = "baseline_candidate_eval_loop.md"
LOOP_HTML_FILENAME = "baseline_candidate_eval_loop.html"


def render_baseline_candidate_eval_loop_text(report: dict[str, Any]) -> str:
    experiment = as_dict(report.get("experiment"))
    baseline = as_dict(report.get("baseline_metrics"))
    candidate = as_dict(report.get("candidate_metrics"))
    delta = as_dict(report.get("delta_report"))
    history = as_dict(report.get("benchmark_history"))
    control = as_dict(report.get("control_summary"))
    acceptance = as_dict(report.get("acceptance_criteria"))
    promotion = as_dict(report.get("promotion_decision"))
    execution = as_dict(report.get("execution"))
    boundary = as_dict(report.get("boundary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("execution_source_mode", execution.get("source_mode")),
        ("execution_gate_mode", execution.get("gate_mode")),
        ("execution_fail_on_reject", execution.get("fail_on_reject")),
        ("execution_expected_exit_code", execution.get("expected_exit_code")),
        ("controlled_variable", experiment.get("controlled_variable")),
        ("suite_name", experiment.get("suite_name")),
        ("baseline_max_iters", experiment.get("baseline_max_iters")),
        ("candidate_max_iters", experiment.get("candidate_max_iters")),
        ("min_overall_score_delta", experiment.get("min_overall_score_delta")),
        ("baseline_score", baseline.get("overall_score")),
        ("candidate_score", candidate.get("overall_score")),
        ("overall_score_delta", delta.get("overall_score_delta")),
        ("baseline_best_val_loss", baseline.get("training_best_val_loss")),
        ("candidate_best_val_loss", candidate.get("training_best_val_loss")),
        ("best_val_loss_delta", delta.get("training_best_val_loss_delta")),
        ("baseline_final_val_loss", baseline.get("training_final_val_loss")),
        ("candidate_final_val_loss", candidate.get("training_final_val_loss")),
        ("final_val_loss_delta", delta.get("training_final_val_loss_delta")),
        ("baseline_generation_flags", baseline.get("generation_quality_total_flags")),
        ("candidate_generation_flags", candidate.get("generation_quality_total_flags")),
        ("generation_flags_delta", delta.get("generation_quality_total_flags_delta")),
        ("case_delta_count", delta.get("case_delta_count")),
        ("case_regression_count", delta.get("case_regression_count")),
        ("benchmark_history_entry_count", history.get("entry_count")),
        ("benchmark_history_ready_count", history.get("ready_count")),
        ("benchmark_history_model_quality_claim", history.get("model_quality_claim")),
        ("control_status", control.get("status")),
        ("control_failed_count", control.get("failed_count")),
        ("acceptance_status", acceptance.get("status")),
        ("acceptance_failed_count", acceptance.get("failed_count")),
        ("promotion_status", promotion.get("status")),
        ("promotion_action", promotion.get("action")),
        ("promotion_selected_name", promotion.get("selected_name")),
        ("promotion_accepted", promotion.get("accepted")),
        ("promotion_rejected_reasons", ",".join(string_list(promotion.get("rejected_reasons")))),
        ("next_action", report.get("next_action")),
        ("model_quality_claim", boundary.get("model_quality_claim")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_baseline_candidate_eval_loop_markdown(report: dict[str, Any]) -> str:
    experiment = as_dict(report.get("experiment"))
    promotion = as_dict(report.get("promotion_decision"))
    delta = as_dict(report.get("delta_report"))
    control = as_dict(report.get("control_summary"))
    acceptance = as_dict(report.get("acceptance_criteria"))
    execution = as_dict(report.get("execution"))
    baseline = as_dict(report.get("baseline_metrics"))
    candidate = as_dict(report.get("candidate_metrics"))
    rejected_reasons = string_list(promotion.get("rejected_reasons"))
    control_failed_reasons = string_list(control.get("failed_reasons"))
    acceptance_failed_reasons = string_list(acceptance.get("failed_reasons"))
    reason_lines = ["- none"] if not rejected_reasons else [f"- {reason}" for reason in rejected_reasons]
    control_lines = ["- none"] if not control_failed_reasons else [f"- {reason}" for reason in control_failed_reasons]
    acceptance_lines = ["- none"] if not acceptance_failed_reasons else [f"- {reason}" for reason in acceptance_failed_reasons]
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Eval Loop",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Source mode: `{execution.get('source_mode')}`",
            f"- Gate mode: `{execution.get('gate_mode')}`",
            f"- Expected exit code: `{execution.get('expected_exit_code')}`",
            f"- Suite: `{experiment.get('suite_name')}`",
            f"- Controlled variable: `{experiment.get('controlled_variable')}`",
            f"- Min overall score delta: `{experiment.get('min_overall_score_delta')}`",
            f"- Overall score delta: `{delta.get('overall_score_delta')}`",
            f"- Best val loss delta: `{delta.get('training_best_val_loss_delta')}`",
            f"- Final val loss delta: `{delta.get('training_final_val_loss_delta')}`",
            f"- Generation flags delta: `{delta.get('generation_quality_total_flags_delta')}`",
            f"- Control status: `{control.get('status')}`",
            f"- Acceptance status: `{acceptance.get('status')}`",
            f"- Promotion status: `{promotion.get('status')}`",
            f"- Candidate accepted: `{promotion.get('accepted')}`",
            f"- Next action: `{report.get('next_action')}`",
            "",
            "## Rejected Reasons",
            "",
            *reason_lines,
            "",
            "## Capability Metrics",
            "",
            "| Metric | Baseline | Candidate | Delta | Direction |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| Overall score | {baseline.get('overall_score')} | {candidate.get('overall_score')} | {delta.get('overall_score_delta')} | higher is better |",
            f"| Best val loss | {baseline.get('training_best_val_loss')} | {candidate.get('training_best_val_loss')} | {delta.get('training_best_val_loss_delta')} | lower is better |",
            f"| Final val loss | {baseline.get('training_final_val_loss')} | {candidate.get('training_final_val_loss')} | {delta.get('training_final_val_loss_delta')} | lower is better |",
            f"| Generation flags | {baseline.get('generation_quality_total_flags')} | {candidate.get('generation_quality_total_flags')} | {delta.get('generation_quality_total_flags_delta')} | lower is better |",
            "",
            "## Control Checks",
            "",
            *control_lines,
            "",
            "## Acceptance Criteria",
            "",
            *acceptance_lines,
            "",
        ]
    )


def render_baseline_candidate_eval_loop_html(report: dict[str, Any]) -> str:
    promotion = as_dict(report.get("promotion_decision"))
    control = as_dict(report.get("control_summary"))
    acceptance = as_dict(report.get("acceptance_criteria"))
    execution = as_dict(report.get("execution"))
    delta = as_dict(report.get("delta_report"))
    reasons = string_list(promotion.get("rejected_reasons"))
    control_reasons = string_list(control.get("failed_reasons"))
    acceptance_reasons = string_list(acceptance.get("failed_reasons"))
    reason_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in reasons) or "<li>none</li>"
    control_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in control_reasons) or "<li>none</li>"
    acceptance_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in acceptance_reasons) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT baseline-candidate eval loop</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f6f8f7; color: #17211d; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dfdb; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dfdb; border-radius: 8px; padding: 10px; background: #fbfcfb; }}
.metric span {{ display: block; color: #5c6c65; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT baseline-candidate eval loop</h1>
<section>
<h2>Decision</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(report.get('decision'))}</strong></div>
<div class="metric"><span>Source</span><strong>{html_escape(execution.get('source_mode'))}</strong></div>
<div class="metric"><span>Gate</span><strong>{html_escape(execution.get('gate_mode'))}</strong></div>
<div class="metric"><span>Exit</span><strong>{html_escape(execution.get('expected_exit_code'))}</strong></div>
<div class="metric"><span>Promotion</span><strong>{html_escape(promotion.get('status'))}</strong></div>
<div class="metric"><span>Score Delta</span><strong>{html_escape(delta.get('overall_score_delta'))}</strong></div>
<div class="metric"><span>Best Loss Delta</span><strong>{html_escape(delta.get('training_best_val_loss_delta'))}</strong></div>
<div class="metric"><span>Final Loss Delta</span><strong>{html_escape(delta.get('training_final_val_loss_delta'))}</strong></div>
<div class="metric"><span>Gen Flags Delta</span><strong>{html_escape(delta.get('generation_quality_total_flags_delta'))}</strong></div>
<div class="metric"><span>Control</span><strong>{html_escape(control.get('status'))}</strong></div>
<div class="metric"><span>Acceptance</span><strong>{html_escape(acceptance.get('status'))}</strong></div>
<div class="metric"><span>Accepted</span><strong>{html_escape(promotion.get('accepted'))}</strong></div>
<div class="metric"><span>Selected</span><strong>{html_escape(promotion.get('selected_name'))}</strong></div>
<div class="metric"><span>Min Delta</span><strong>{html_escape(acceptance.get('min_overall_score_delta'))}</strong></div>
<div class="metric"><span>Next</span><strong>{html_escape(report.get('next_action'))}</strong></div>
</div>
</section>
<section>
<h2>Rejected Reasons</h2>
<ul>
{reason_items}
</ul>
</section>
<section>
<h2>Control Checks</h2>
<ul>
{control_items}
</ul>
</section>
<section>
<h2>Acceptance Criteria</h2>
<ul>
{acceptance_items}
</ul>
</section>
</main>
</body>
</html>
"""


def write_baseline_candidate_eval_loop_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / LOOP_JSON_FILENAME,
        "text": root / LOOP_TEXT_FILENAME,
        "markdown": root / LOOP_MARKDOWN_FILENAME,
        "html": root / LOOP_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_baseline_candidate_eval_loop_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_baseline_candidate_eval_loop_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_baseline_candidate_eval_loop_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "LOOP_HTML_FILENAME",
    "LOOP_JSON_FILENAME",
    "LOOP_MARKDOWN_FILENAME",
    "LOOP_TEXT_FILENAME",
    "render_baseline_candidate_eval_loop_html",
    "render_baseline_candidate_eval_loop_markdown",
    "render_baseline_candidate_eval_loop_text",
    "write_baseline_candidate_eval_loop_outputs",
]
