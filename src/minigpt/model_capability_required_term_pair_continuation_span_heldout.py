from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_continuation_span_stability import (
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_CONTINUATION_SPAN_HELDOUT_JSON_FILENAME = "model_capability_required_term_pair_continuation_span_heldout.json"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_HELDOUT_TEXT_FILENAME = "model_capability_required_term_pair_continuation_span_heldout.txt"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_HELDOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_continuation_span_heldout.md"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_HELDOUT_HTML_FILENAME = "model_capability_required_term_pair_continuation_span_heldout.html"

GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_pair_continuation_span_heldout_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_continuation_span_heldout(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    seed_offset: int = 1200,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    cases = build_heldout_prompt_cases()
    seeds = select_heldout_seed_sources(stability_report)
    issues = _input_issues(stability_report, seeds, cases)
    rows = (
        _run_heldout_generations(
            seeds,
            cases,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            seed_offset=seed_offset,
            device=device,
            generate_func=generate_func,
        )
        if not issues
        else []
    )
    seed_rows = summarize_heldout_seed_rows(seeds, rows)
    case_rows = summarize_heldout_case_rows(cases, rows)
    summary = summarize_continuation_span_heldout(seeds, cases, rows, seed_rows, case_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair continuation-span heldout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_continuation_span_stability": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "seed_offset": seed_offset,
            "device": device,
            "experiment_boundary": "held-out prompt generation only; no additional training",
        },
        "cases": cases,
        "seed_sources": seeds,
        "generation_rows": rows,
        "seed_rows": seed_rows,
        "case_rows": case_rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_heldout_prompt_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "source-fixed", "case_type": "source", "alias_group": "source", "prompt": "fixed:", "expected_term": "fixed"},
        {"case_id": "source-loss", "case_type": "source", "alias_group": "source", "prompt": "loss:", "expected_term": "loss"},
        {"case_id": "heldout-alpha-fixed", "case_type": "heldout", "alias_group": "greek", "prompt": "alpha:", "expected_term": "fixed"},
        {"case_id": "heldout-gamma-fixed", "case_type": "heldout", "alias_group": "greek", "prompt": "gamma:", "expected_term": "fixed"},
        {"case_id": "heldout-delta-fixed", "case_type": "heldout", "alias_group": "greek", "prompt": "delta:", "expected_term": "fixed"},
        {"case_id": "heldout-beta-loss", "case_type": "heldout", "alias_group": "greek", "prompt": "beta:", "expected_term": "loss"},
        {"case_id": "heldout-theta-loss", "case_type": "heldout", "alias_group": "greek", "prompt": "theta:", "expected_term": "loss"},
        {"case_id": "heldout-omega-loss", "case_type": "heldout", "alias_group": "greek", "prompt": "omega:", "expected_term": "loss"},
    ]


def select_heldout_seed_sources(stability_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in list_of_dicts(stability_report.get("seed_reports")):
        summary = as_dict(report.get("summary"))
        training = as_dict(report.get("training"))
        if report.get("status") != "pass":
            continue
        if not summary.get("checkpoint_exists"):
            continue
        rows.append(
            {
                "seed": as_dict(report.get("settings")).get("generation_seed"),
                "source_decision": report.get("decision"),
                "checkpoint_path": training.get("checkpoint_path"),
                "tokenizer_path": training.get("tokenizer_path"),
                "source_prefix_minimum_improved_count": summary.get("prefix_minimum_improved_count"),
                "source_pair_full_generation_hit": summary.get("candidate_pair_full_generation_hit"),
            }
        )
    return rows


def summarize_heldout_seed_rows(seeds: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed_rows: list[dict[str, Any]] = []
    for seed in seeds:
        seed_value = seed.get("seed")
        group = [row for row in rows if row.get("seed") == seed_value]
        source = [row for row in group if row.get("case_type") == "source"]
        heldout = [row for row in group if row.get("case_type") == "heldout"]
        seed_rows.append(
            {
                "seed": seed_value,
                "case_count": len(group),
                "source_hit_count": sum(1 for row in source if row.get("continuation_hit")),
                "heldout_hit_count": sum(1 for row in heldout if row.get("continuation_hit")),
                "source_case_count": len(source),
                "heldout_case_count": len(heldout),
                "heldout_full_hit": bool(heldout) and all(row.get("continuation_hit") for row in heldout),
            }
        )
    return seed_rows


def summarize_heldout_case_rows(cases: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_rows: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case.get("case_id") or "")
        group = [row for row in rows if row.get("case_id") == case_id]
        hit_count = sum(1 for row in group if row.get("continuation_hit"))
        case_rows.append(
            {
                **case,
                "run_count": len(group),
                "hit_count": hit_count,
                "hit_rate": round(hit_count / len(group), 4) if group else 0.0,
            }
        )
    return case_rows


def summarize_continuation_span_heldout(
    seeds: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    seed_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_cases = [case for case in case_rows if case.get("case_type") == "source"]
    heldout_cases = [case for case in case_rows if case.get("case_type") == "heldout"]
    source_hit_cases = sum(1 for case in source_cases if int(case.get("hit_count") or 0) > 0)
    heldout_hit_cases = sum(1 for case in heldout_cases if int(case.get("hit_count") or 0) > 0)
    heldout_terms = sorted({str(case.get("expected_term") or "") for case in heldout_cases if case.get("expected_term")})
    heldout_hit_terms = sorted(
        {str(case.get("expected_term") or "") for case in heldout_cases if int(case.get("hit_count") or 0) > 0}
    )
    alias_group_rows = summarize_alias_group_rows(case_rows)
    return {
        "heldout_decision": _heldout_decision(seeds, source_hit_cases, heldout_hit_cases, seed_rows),
        "seed_count": len(seeds),
        "case_count": len(cases),
        "generation_count": len(rows),
        "source_case_count": len(source_cases),
        "heldout_case_count": len(heldout_cases),
        "source_hit_case_count": source_hit_cases,
        "heldout_hit_case_count": heldout_hit_cases,
        "heldout_term_count": len(heldout_terms),
        "heldout_hit_term_count": len(heldout_hit_terms),
        "heldout_hit_terms": heldout_hit_terms,
        "heldout_full_hit_seed_count": sum(1 for row in seed_rows if row.get("heldout_full_hit")),
        "heldout_full_term_coverage": bool(heldout_terms) and len(heldout_hit_terms) == len(heldout_terms),
        "alias_group_rows": alias_group_rows,
        "source_signal_observed": source_hit_cases > 0,
        "heldout_generalization_observed": heldout_hit_cases > 0,
    }


def summarize_alias_group_rows(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in case_rows:
        groups.setdefault(str(row.get("alias_group") or "unknown"), []).append(row)
    rows: list[dict[str, Any]] = []
    for group_name, group in sorted(groups.items()):
        hit_count = sum(1 for row in group if int(row.get("hit_count") or 0) > 0)
        rows.append(
            {
                "alias_group": group_name,
                "case_count": len(group),
                "hit_case_count": hit_count,
                "hit_rate": round(hit_count / len(group), 4) if group else 0.0,
                "hit_terms": sorted({str(row.get("expected_term") or "") for row in group if int(row.get("hit_count") or 0) > 0}),
            }
        )
    return rows


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_heldout_generations(
    seeds: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    *,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    seed_offset: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_index, seed in enumerate(seeds):
        for case_index, case in enumerate(cases):
            request = {
                "prompt": case["prompt"],
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_k": top_k,
                "seed": int(seed.get("seed") or 0) + seed_offset + case_index,
                "checkpoint_path": seed.get("checkpoint_path"),
                "tokenizer_path": seed.get("tokenizer_path"),
                "device": device,
            }
            response = _generate(request, generate_func)
            continuation = str(response.get("continuation") or "")
            expected = str(case.get("expected_term") or "")
            rows.append(
                {
                    **case,
                    "seed": seed.get("seed"),
                    "seed_index": seed_index,
                    "generation_seed": request["seed"],
                    "checkpoint_path": seed.get("checkpoint_path"),
                    "generated": response.get("generated"),
                    "continuation": continuation,
                    "continuation_hit": expected.casefold() in continuation.casefold(),
                    "continuation_preview": _preview(continuation),
                }
            )
    return rows


def _generate(request: dict[str, Any], generate_func: GenerateFunc | None) -> dict[str, Any]:
    if generate_func is not None:
        return generate_func(request)
    from minigpt.server_contracts import GenerationRequest
    from minigpt.server_generator import MiniGPTGenerator

    return MiniGPTGenerator(request["checkpoint_path"], request["tokenizer_path"], device=str(request.get("device") or "cpu")).generate(
        GenerationRequest(
            prompt=str(request["prompt"]),
            max_new_tokens=int(request["max_new_tokens"]),
            temperature=float(request["temperature"]),
            top_k=request.get("top_k"),
            seed=int(request["seed"]),
        )
    ).to_dict()


def _input_issues(stability_report: dict[str, Any], seeds: list[dict[str, Any]], cases: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not stability_report:
        issues.append("source continuation-span stability report is missing or invalid")
    if stability_report and stability_report.get("status") != "pass":
        issues.append("source continuation-span stability report is not pass")
    if stability_report and not as_dict(stability_report.get("summary")).get("stable_prefix_gain"):
        issues.append("source continuation-span stability does not have stable prefix gain")
    if not seeds:
        issues.append("source continuation-span stability report has no usable seed checkpoints")
    if not cases:
        issues.append("held-out prompt cases are empty")
    return issues


def _heldout_decision(seeds: list[dict[str, Any]], source_hit_cases: int, heldout_hit_cases: int, seed_rows: list[dict[str, Any]]) -> str:
    if not seeds:
        return "heldout_no_seed_checkpoints"
    if heldout_hit_cases > 0:
        return "heldout_prompt_generalization_observed"
    if source_hit_cases > 0:
        return "source_prompt_only_signal"
    return "heldout_no_generation_signal"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_continuation_span_heldout"
    if summary.get("heldout_generalization_observed"):
        return "required_term_pair_continuation_span_heldout_signal"
    if summary.get("source_signal_observed"):
        return "required_term_pair_continuation_span_source_only"
    return "required_term_pair_continuation_span_heldout_no_signal"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("heldout_generalization_observed"):
        return "tiny_continuation_span_heldout_signal"
    if summary.get("source_signal_observed"):
        return "tiny_continuation_span_source_prompt_signal_only"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The held-out prompt probe could not be run cleanly."
    if summary.get("heldout_generalization_observed"):
        return "At least one held-out alias prompt emitted its expected required term."
    if summary.get("source_signal_observed"):
        return "The trained checkpoints still express source scaffold signal, but held-out alias prompts did not generalize."
    return "Neither source nor held-out prompts emitted the expected required terms."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair held-out probe inputs before changing the objective"
    if summary.get("heldout_generalization_observed"):
        return "repeat held-out prompts across more aliases before promoting the signal"
    return "add explicit alias-to-term mapping examples or redesign the objective before scaling model size"


def _preview(value: Any, limit: int = 90) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."
