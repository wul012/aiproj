from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, html_escape, string_list, utc_now


LOOP_JSON_FILENAME = "baseline_candidate_eval_loop.json"
HANDOFF_JSON_FILENAME = "baseline_candidate_handoff.json"
HANDOFF_TEXT_FILENAME = "baseline_candidate_handoff.txt"
HANDOFF_MARKDOWN_FILENAME = "baseline_candidate_handoff.md"
HANDOFF_HTML_FILENAME = "baseline_candidate_handoff.html"


def resolve_baseline_candidate_loop_report(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / LOOP_JSON_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def load_baseline_candidate_loop_report(path: str | Path) -> dict[str, Any]:
    resolved = resolve_baseline_candidate_loop_report(path)
    payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("baseline-candidate loop report must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(resolved)
    return payload


def build_baseline_candidate_handoff(
    loop_report_path: str | Path,
    *,
    title: str = "MiniGPT baseline-candidate handoff",
    generated_at: str | None = None,
) -> dict[str, Any]:
    loop = load_baseline_candidate_loop_report(loop_report_path)
    experiment = as_dict(loop.get("experiment"))
    baseline = as_dict(loop.get("baseline_metrics"))
    candidate = as_dict(loop.get("candidate_metrics"))
    delta = as_dict(loop.get("delta_report"))
    control = as_dict(loop.get("control_summary"))
    acceptance = as_dict(loop.get("acceptance_criteria"))
    promotion = as_dict(loop.get("promotion_decision"))
    execution = as_dict(loop.get("execution"))
    boundary = as_dict(loop.get("boundary"))
    source_evidence = _source_evidence(loop)
    accepted = _candidate_accepted(loop, control, acceptance, promotion)
    status = "pass" if loop.get("status") == "pass" else "fail"
    decision = _handoff_decision(status=status, accepted=accepted)
    baseline_name = str(experiment.get("baseline_name") or "baseline")
    candidate_name = str(experiment.get("candidate_name") or promotion.get("selected_name") or "candidate")
    next_baseline_name = candidate_name if accepted else baseline_name
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "handoff_ready": accepted,
        "source_loop_report": loop.get("_source_path"),
        "source_smoke_summary": loop.get("source_smoke_summary"),
        "next_baseline": {
            "name": next_baseline_name,
            "source": "candidate" if accepted else "current_baseline",
            "ready": accepted,
            "checkpoint": source_evidence.get("candidate_checkpoint") if accepted else source_evidence.get("baseline_checkpoint"),
            "checkpoint_exists": source_evidence.get("candidate_checkpoint_exists") if accepted else source_evidence.get("baseline_checkpoint_exists"),
            "reason": "candidate accepted by loop criteria" if accepted else "candidate rejected; keep current baseline",
        },
        "baseline": {
            "name": baseline_name,
            "status": baseline.get("status"),
            "scorecard_status": baseline.get("scorecard_status"),
            "overall_score": baseline.get("overall_score"),
            "checkpoint": source_evidence.get("baseline_checkpoint"),
            "checkpoint_exists": source_evidence.get("baseline_checkpoint_exists"),
        },
        "candidate": {
            "name": candidate_name,
            "selected_name": promotion.get("selected_name"),
            "status": candidate.get("status"),
            "scorecard_status": candidate.get("scorecard_status"),
            "overall_score": candidate.get("overall_score"),
            "accepted": accepted,
            "checkpoint": source_evidence.get("candidate_checkpoint"),
            "checkpoint_exists": source_evidence.get("candidate_checkpoint_exists"),
            "scorecard": source_evidence.get("candidate_scorecard"),
            "pair_batch": source_evidence.get("candidate_pair_batch"),
        },
        "delta": {
            "overall_score_delta": delta.get("overall_score_delta"),
            "min_overall_score_delta": experiment.get("min_overall_score_delta"),
            "case_delta_count": delta.get("case_delta_count"),
            "case_regression_count": delta.get("case_regression_count"),
        },
        "guardrails": {
            "control_status": control.get("status"),
            "acceptance_status": acceptance.get("status"),
            "promotion_status": promotion.get("status"),
            "promotion_accepted": promotion.get("accepted"),
            "rejected_reasons": string_list(promotion.get("rejected_reasons")),
            "acceptance_failed_reasons": string_list(acceptance.get("failed_reasons")),
            "model_quality_claim": boundary.get("model_quality_claim") or "not_claimed",
        },
        "execution": {
            "source_mode": execution.get("source_mode"),
            "gate_mode": execution.get("gate_mode"),
            "expected_exit_code": execution.get("expected_exit_code"),
            "loop_decision": loop.get("decision"),
        },
        "source_evidence": source_evidence,
        "actions": _handoff_actions(accepted=accepted, status=status),
        "boundary": {
            "model_quality_claim": boundary.get("model_quality_claim") or "not_claimed",
            "reason": boundary.get("reason")
            or "This handoff records tiny benchmark loop readiness; it is not a production model-quality claim.",
        },
    }


def render_baseline_candidate_handoff_text(handoff: dict[str, Any]) -> str:
    next_baseline = as_dict(handoff.get("next_baseline"))
    candidate = as_dict(handoff.get("candidate"))
    delta = as_dict(handoff.get("delta"))
    guardrails = as_dict(handoff.get("guardrails"))
    execution = as_dict(handoff.get("execution"))
    handoff_check = as_dict(handoff.get("handoff_check"))
    rows = [
        ("status", handoff.get("status")),
        ("decision", handoff.get("decision")),
        ("handoff_ready", handoff.get("handoff_ready")),
        ("next_baseline_name", next_baseline.get("name")),
        ("next_baseline_source", next_baseline.get("source")),
        ("next_baseline_checkpoint_exists", next_baseline.get("checkpoint_exists")),
        ("candidate_name", candidate.get("name")),
        ("candidate_accepted", candidate.get("accepted")),
        ("overall_score_delta", delta.get("overall_score_delta")),
        ("min_overall_score_delta", delta.get("min_overall_score_delta")),
        ("control_status", guardrails.get("control_status")),
        ("acceptance_status", guardrails.get("acceptance_status")),
        ("promotion_status", guardrails.get("promotion_status")),
        ("execution_source_mode", execution.get("source_mode")),
        ("execution_gate_mode", execution.get("gate_mode")),
        ("execution_expected_exit_code", execution.get("expected_exit_code")),
        ("handoff_check_status", handoff_check.get("status")),
        ("handoff_check_failed_count", handoff_check.get("failed_count")),
        ("rejected_reasons", ",".join(string_list(guardrails.get("rejected_reasons")))),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_baseline_candidate_handoff_markdown(handoff: dict[str, Any]) -> str:
    next_baseline = as_dict(handoff.get("next_baseline"))
    delta = as_dict(handoff.get("delta"))
    guardrails = as_dict(handoff.get("guardrails"))
    handoff_check = as_dict(handoff.get("handoff_check"))
    reasons = string_list(guardrails.get("rejected_reasons"))
    reason_lines = ["- none"] if not reasons else [f"- {reason}" for reason in reasons]
    check_lines = (
        ["- none"]
        if not handoff_check
        else [
            f"- Status: `{handoff_check.get('status')}`",
            f"- Failed count: `{handoff_check.get('failed_count')}`",
        ]
    )
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Handoff",
            "",
            f"- Status: `{handoff.get('status')}`",
            f"- Decision: `{handoff.get('decision')}`",
            f"- Handoff ready: `{handoff.get('handoff_ready')}`",
            f"- Next baseline: `{next_baseline.get('name')}`",
            f"- Next source: `{next_baseline.get('source')}`",
            f"- Overall score delta: `{delta.get('overall_score_delta')}`",
            f"- Min overall score delta: `{delta.get('min_overall_score_delta')}`",
            f"- Acceptance status: `{guardrails.get('acceptance_status')}`",
            "",
            "## Embedded Handoff Check",
            "",
            *check_lines,
            "",
            "## Rejected Reasons",
            "",
            *reason_lines,
            "",
        ]
    )


def render_baseline_candidate_handoff_html(handoff: dict[str, Any]) -> str:
    next_baseline = as_dict(handoff.get("next_baseline"))
    candidate = as_dict(handoff.get("candidate"))
    delta = as_dict(handoff.get("delta"))
    guardrails = as_dict(handoff.get("guardrails"))
    handoff_check = as_dict(handoff.get("handoff_check"))
    reasons = string_list(guardrails.get("rejected_reasons"))
    reason_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in reasons) or "<li>none</li>"
    check_status = handoff_check.get("status") if handoff_check else "not-run"
    check_failed_count = handoff_check.get("failed_count") if handoff_check else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT baseline-candidate handoff</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f7f8f5; color: #17211d; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d8ded7; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d8ded7; border-radius: 8px; padding: 10px; background: #fbfcfa; }}
.metric span {{ display: block; color: #607066; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT baseline-candidate handoff</h1>
<section>
<h2>Decision</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(handoff.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(handoff.get('decision'))}</strong></div>
<div class="metric"><span>Ready</span><strong>{html_escape(handoff.get('handoff_ready'))}</strong></div>
<div class="metric"><span>Next baseline</span><strong>{html_escape(next_baseline.get('name'))}</strong></div>
<div class="metric"><span>Source</span><strong>{html_escape(next_baseline.get('source'))}</strong></div>
<div class="metric"><span>Candidate</span><strong>{html_escape(candidate.get('name'))}</strong></div>
<div class="metric"><span>Candidate accepted</span><strong>{html_escape(candidate.get('accepted'))}</strong></div>
<div class="metric"><span>Delta</span><strong>{html_escape(delta.get('overall_score_delta'))}</strong></div>
<div class="metric"><span>Min Delta</span><strong>{html_escape(delta.get('min_overall_score_delta'))}</strong></div>
<div class="metric"><span>Acceptance</span><strong>{html_escape(guardrails.get('acceptance_status'))}</strong></div>
<div class="metric"><span>Handoff check</span><strong>{html_escape(check_status)}</strong></div>
<div class="metric"><span>Check failures</span><strong>{html_escape(check_failed_count)}</strong></div>
</div>
</section>
<section>
<h2>Rejected Reasons</h2>
<ul>
{reason_items}
</ul>
</section>
</main>
</body>
</html>
"""


def write_baseline_candidate_handoff_outputs(handoff: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / HANDOFF_JSON_FILENAME,
        "text": root / HANDOFF_TEXT_FILENAME,
        "markdown": root / HANDOFF_MARKDOWN_FILENAME,
        "html": root / HANDOFF_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_baseline_candidate_handoff_text(handoff), encoding="utf-8")
    paths["markdown"].write_text(render_baseline_candidate_handoff_markdown(handoff), encoding="utf-8")
    paths["html"].write_text(render_baseline_candidate_handoff_html(handoff), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _candidate_accepted(
    loop: dict[str, Any],
    control: dict[str, Any],
    acceptance: dict[str, Any],
    promotion: dict[str, Any],
) -> bool:
    return (
        loop.get("status") == "pass"
        and loop.get("decision") == "accept_candidate"
        and control.get("status") == "pass"
        and acceptance.get("status") == "pass"
        and promotion.get("accepted") is True
    )


def _handoff_decision(*, status: str, accepted: bool) -> str:
    if status != "pass":
        return "fix_loop_before_handoff"
    return "promote_candidate_to_next_baseline" if accepted else "keep_current_baseline"


def _handoff_actions(*, accepted: bool, status: str) -> list[str]:
    if status != "pass":
        return ["fix_loop_execution", "rerun_baseline_candidate_loop"]
    if accepted:
        return ["use_candidate_as_next_baseline", "record_loop_report_as_promotion_evidence"]
    return ["keep_current_baseline", "fix_candidate_before_next_loop"]


def _source_evidence(loop: dict[str, Any]) -> dict[str, Any]:
    loop_path = Path(str(loop.get("_source_path") or "."))
    source_path = _resolve_maybe_relative(loop.get("source_smoke_summary"), loop_path.parent)
    payload = _read_json_object(source_path)
    baseline_dir = _resolve_maybe_relative(payload.get("baseline_dir"), source_path.parent) if payload else None
    candidate_dir = _resolve_maybe_relative(payload.get("candidate_dir"), source_path.parent) if payload else None
    artifacts = as_dict(payload.get("artifacts")) if payload else {}
    baseline_checkpoint = baseline_dir / "run" / "checkpoint.pt" if baseline_dir else None
    candidate_checkpoint = candidate_dir / "run" / "checkpoint.pt" if candidate_dir else None
    return {
        "source_smoke_summary": str(source_path) if source_path else "",
        "source_smoke_summary_exists": bool(source_path and source_path.is_file()),
        "baseline_dir": str(baseline_dir) if baseline_dir else "",
        "candidate_dir": str(candidate_dir) if candidate_dir else "",
        "baseline_checkpoint": str(baseline_checkpoint) if baseline_checkpoint else "",
        "baseline_checkpoint_exists": bool(baseline_checkpoint and baseline_checkpoint.is_file()),
        "candidate_checkpoint": str(candidate_checkpoint) if candidate_checkpoint else "",
        "candidate_checkpoint_exists": bool(candidate_checkpoint and candidate_checkpoint.is_file()),
        "candidate_scorecard": str(artifacts.get("candidate_scorecard_path") or ""),
        "candidate_pair_batch": str(artifacts.get("candidate_pair_batch_path") or ""),
        "benchmark_history_json": str(artifacts.get("benchmark_history_json_path") or ""),
    }


def _read_json_object(path: Path | None) -> dict[str, Any]:
    if not path or not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def _resolve_maybe_relative(value: Any, base_dir: Path) -> Path | None:
    if value is None or value == "":
        return None
    path = Path(str(value))
    if path.is_absolute() or path.exists():
        return path
    return base_dir / path


__all__ = [
    "HANDOFF_HTML_FILENAME",
    "HANDOFF_JSON_FILENAME",
    "HANDOFF_MARKDOWN_FILENAME",
    "HANDOFF_TEXT_FILENAME",
    "build_baseline_candidate_handoff",
    "load_baseline_candidate_loop_report",
    "render_baseline_candidate_handoff_html",
    "render_baseline_candidate_handoff_markdown",
    "render_baseline_candidate_handoff_text",
    "resolve_baseline_candidate_loop_report",
    "write_baseline_candidate_handoff_outputs",
]
