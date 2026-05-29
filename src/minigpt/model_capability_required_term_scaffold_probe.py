from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_uptake import REQUIRED_TERM_UPTAKE_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_SCAFFOLD_PROBE_JSON_FILENAME = "model_capability_required_term_scaffold_probe.json"
REQUIRED_TERM_SCAFFOLD_PROBE_TEXT_FILENAME = "model_capability_required_term_scaffold_probe.txt"
REQUIRED_TERM_SCAFFOLD_PROBE_MARKDOWN_FILENAME = "model_capability_required_term_scaffold_probe.md"
REQUIRED_TERM_SCAFFOLD_PROBE_HTML_FILENAME = "model_capability_required_term_scaffold_probe.html"

GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_uptake(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_UPTAKE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def build_model_capability_required_term_scaffold_probe(
    uptake_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    search_base: str | Path | None = None,
    max_new_tokens: int = 24,
    temperature: float = 0.7,
    top_k: int | None = 30,
    generation_seed: int = 482,
    term_limit: int = 1,
    case_limit: int | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    base_dir = _base_dir(source_path, search_base)
    observations = list_of_dicts(uptake_report.get("observations"))
    issues = _input_issues(uptake_report, observations)
    case_groups = _select_case_groups(observations, case_limit=case_limit, term_limit=term_limit)
    probe_rows: list[dict[str, Any]] = []
    source_cache: dict[str, dict[str, Any]] = {}

    for index, group in enumerate(case_groups):
        source = _source_for_group(group, base_dir, source_cache)
        if source.get("status") != "pass":
            issues.append(f"case {group.get('case')} scaffold source is incomplete")
            continue
        probe_rows.append(
            _probe_row(
                group,
                source,
                index=index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=generation_seed,
                device=device,
                generate_func=generate_func,
            )
        )

    source_rows = [_public_source_row(source) for source in source_cache.values()]
    summary = summarize_required_term_scaffold_probe(case_groups, probe_rows, source_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term scaffold probe",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "required_term_scaffold_probe_ready" if status == "pass" else "fix_required_term_scaffold_probe",
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_uptake": str(source_path) if source_path else None,
        "out_dir": str(Path(out_dir)),
        "settings": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "term_limit": term_limit,
            "case_limit": case_limit,
            "device": device,
        },
        "summary": summary,
        "source_count": len(source_rows),
        "source_rows": source_rows,
        "case_group_count": len(case_groups),
        "case_groups": case_groups,
        "probe_count": len(probe_rows),
        "probe_rows": probe_rows,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(summary),
            "next_action": _next_action(summary),
        },
    }


def summarize_required_term_scaffold_probe(
    case_groups: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    term_count = sum(len(row.get("terms") or []) for row in case_groups)
    scaffold_hits = sum(int(row.get("scaffold_continuation_hit_count") or 0) for row in probe_rows)
    baseline_hits = sum(int(row.get("baseline_continuation_hit_count") or 0) for row in probe_rows)
    return {
        "probe_decision": _probe_decision(case_groups, probe_rows, scaffold_hits),
        "case_group_count": len(case_groups),
        "probe_count": len(probe_rows),
        "required_term_count": term_count,
        "baseline_continuation_hit_count": baseline_hits,
        "scaffold_continuation_hit_count": scaffold_hits,
        "scaffold_generated_hit_count": sum(int(row.get("scaffold_generated_hit_count") or 0) for row in probe_rows),
        "scaffold_prompt_hit_count": sum(int(row.get("scaffold_prompt_hit_count") or 0) for row in probe_rows),
        "case_with_scaffold_hit_count": sum(1 for row in probe_rows if int(row.get("scaffold_continuation_hit_count") or 0) > 0),
        "prompt_truncated_count": sum(1 for row in probe_rows if row.get("prompt_truncated")),
        "prompt_over_block_count": sum(1 for row in probe_rows if row.get("prompt_over_block")),
        "source_count": len(source_rows),
        "source_ready_count": sum(1 for row in source_rows if row.get("status") == "pass"),
        "source_missing_count": sum(1 for row in source_rows if row.get("status") != "pass"),
    }


def _select_case_groups(
    observations: list[dict[str, Any]],
    *,
    case_limit: int | None,
    term_limit: int,
) -> list[dict[str, Any]]:
    latest = _latest_observations(observations)
    groups: dict[str, dict[str, Any]] = {}
    for row in latest:
        key = "|".join(str(row.get(name) or "") for name in ("token_cap_root", "case"))
        group = groups.setdefault(
            key,
            {
                "seed": row.get("seed"),
                "token_cap": row.get("token_cap"),
                "token_cap_root": row.get("token_cap_root"),
                "case": row.get("case"),
                "task_type": row.get("task_type"),
                "max_iters": row.get("max_iters"),
                "eval_suite_path": row.get("eval_suite_path"),
                "terms": [],
            },
        )
        term = str(row.get("term") or "").strip()
        if term and term not in group["terms"]:
            group["terms"].append(term)
    rows = [row for row in groups.values() if row.get("terms")]
    for row in rows:
        row["terms"] = sorted(row["terms"], key=lambda term: (len(str(term)), str(term)))[:term_limit]
    rows.sort(key=lambda row: (str(row.get("token_cap_root") or ""), str(row.get("case") or "")))
    if case_limit is not None and case_limit >= 0:
        return rows[:case_limit]
    return rows


def _source_for_group(
    group: dict[str, Any],
    base_dir: Path,
    source_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    eval_suite_path = _resolve_file(group.get("eval_suite_path"), base_dir)
    key = str(eval_suite_path) if eval_suite_path else str(group.get("eval_suite_path") or "")
    if key not in source_cache:
        source_cache[key] = _collect_scaffold_source(eval_suite_path, group)
    return source_cache[key]


def _collect_scaffold_source(eval_suite_path: Path | None, group: dict[str, Any]) -> dict[str, Any]:
    if eval_suite_path is None:
        return {"status": "fail", "eval_suite_path": str(group.get("eval_suite_path") or "")}
    result = _find_case_result(list_of_dicts(read_json_report(eval_suite_path).get("results")), str(group.get("case") or ""))
    run_dir = eval_suite_path.parent.parent
    checkpoint_path = run_dir / "checkpoint.pt"
    tokenizer_path = run_dir / "tokenizer.json"
    checkpoint_config = _read_checkpoint_config(checkpoint_path)
    return {
        "status": "pass" if result and checkpoint_path.is_file() and tokenizer_path.is_file() else "fail",
        "eval_suite_path": str(eval_suite_path),
        "checkpoint_path": str(checkpoint_path),
        "tokenizer_path": str(tokenizer_path),
        "run_dir": str(run_dir),
        "checkpoint_config": checkpoint_config,
        "checkpoint_block_size": checkpoint_config.get("block_size"),
        "case_result": result,
        "checkpoint_exists": checkpoint_path.is_file(),
        "tokenizer_exists": tokenizer_path.is_file(),
    }


def _probe_row(
    group: dict[str, Any],
    source: dict[str, Any],
    *,
    index: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    terms = [str(term) for term in group.get("terms") or []]
    baseline = as_dict(source.get("case_result"))
    scaffold_prompt = _scaffold_prompt(group, terms)
    block_size = _as_int(source.get("checkpoint_block_size"))
    request = {
        "prompt": scaffold_prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": generation_seed + index,
        "checkpoint_path": source.get("checkpoint_path"),
        "tokenizer_path": source.get("tokenizer_path"),
        "device": device,
    }
    response = _generate(request, generate_func)
    generated = str(response.get("generated") or "")
    prompt_truncated = not generated.startswith(scaffold_prompt)
    continuation = generated[len(scaffold_prompt) :] if not prompt_truncated else str(response.get("continuation") or "")
    return {
        "seed": group.get("seed"),
        "token_cap": group.get("token_cap"),
        "case": group.get("case"),
        "task_type": group.get("task_type"),
        "max_iters": group.get("max_iters"),
        "terms": terms,
        "term_count": len(terms),
        "generation_seed": request["seed"],
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "baseline_continuation_hit_count": _hit_count(baseline.get("continuation"), terms),
        "scaffold_prompt_hit_count": _hit_count(scaffold_prompt, terms),
        "scaffold_generated_hit_count": _hit_count(generated, terms),
        "scaffold_continuation_hit_count": _hit_count(continuation, terms),
        "prompt_truncated": prompt_truncated,
        "prompt_over_block": block_size > 0 and len(scaffold_prompt) > block_size,
        "checkpoint_block_size": block_size if block_size > 0 else None,
        "scaffold_prompt_char_count": len(scaffold_prompt),
        "scaffold_prompt": scaffold_prompt,
        "baseline_continuation_preview": _preview(baseline.get("continuation")),
        "scaffold_continuation_preview": _preview(continuation),
        "checkpoint_path": source.get("checkpoint_path"),
        "tokenizer_path": source.get("tokenizer_path"),
        "eval_suite_path": source.get("eval_suite_path"),
    }


def _generate(request: dict[str, Any], generate_func: GenerateFunc | None) -> dict[str, Any]:
    if generate_func is not None:
        return generate_func(request)
    from minigpt.server_contracts import GenerationRequest
    from minigpt.server_generator import MiniGPTGenerator

    generator = MiniGPTGenerator(
        request["checkpoint_path"],
        request["tokenizer_path"],
        device=str(request.get("device") or "cpu"),
    )
    response = generator.generate(
        GenerationRequest(
            prompt=str(request["prompt"]),
            max_new_tokens=int(request["max_new_tokens"]),
            temperature=float(request["temperature"]),
            top_k=request.get("top_k"),
            seed=int(request["seed"]),
        )
    )
    return response.to_dict()


def _public_source_row(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": source.get("status"),
        "eval_suite_path": source.get("eval_suite_path"),
        "checkpoint_path": source.get("checkpoint_path"),
        "tokenizer_path": source.get("tokenizer_path"),
        "checkpoint_exists": source.get("checkpoint_exists"),
        "tokenizer_exists": source.get("tokenizer_exists"),
        "checkpoint_block_size": source.get("checkpoint_block_size"),
    }


def _input_issues(uptake_report: dict[str, Any], observations: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not uptake_report:
        issues.append("source required-term uptake report is missing or invalid")
    if not observations:
        issues.append("source required-term uptake report has no observations")
    if as_dict(uptake_report.get("summary")).get("uptake_decision") != "required_terms_never_generated":
        issues.append("source uptake report is not a never-generated required-term report")
    return issues


def _probe_decision(case_groups: list[dict[str, Any]], probe_rows: list[dict[str, Any]], scaffold_hits: int) -> str:
    if not case_groups:
        return "no_required_term_gap"
    if not probe_rows:
        return "missing_scaffold_probe_outputs"
    if scaffold_hits > 0:
        return "scaffold_prompt_partially_improves_required_term_uptake"
    if probe_rows and all(row.get("prompt_over_block") for row in probe_rows):
        return "scaffold_prompt_blocked_by_context_window"
    return "explicit_scaffold_still_no_required_term_uptake"


def _interpretation_reason(summary: dict[str, Any]) -> str:
    decision = summary.get("probe_decision")
    if decision == "scaffold_prompt_partially_improves_required_term_uptake":
        return "At least one explicit required-term scaffold produced a required term in continuation, so prompt shape can influence uptake."
    if decision == "explicit_scaffold_still_no_required_term_uptake":
        return "Even short prompts that list the required terms did not make the archived tiny checkpoint emit those terms in continuation."
    if decision == "scaffold_prompt_blocked_by_context_window":
        return "The checkpoint context window is too small for the scaffold prompts, so this probe cannot fairly test required-term uptake."
    if decision == "missing_scaffold_probe_outputs":
        return "The probe found candidate cases but could not produce scaffold generations from archived checkpoint material."
    return "The source report did not expose required-term generation gaps to probe."


def _next_action(summary: dict[str, Any]) -> str:
    if summary.get("probe_decision") == "scaffold_prompt_partially_improves_required_term_uptake":
        return "compare scaffold-sensitive cases and use them as a small targeted training/eval slice"
    if summary.get("probe_decision") == "explicit_scaffold_still_no_required_term_uptake":
        return "run a targeted micro-training repeat with required-term examples before increasing benchmark scope"
    if summary.get("probe_decision") == "scaffold_prompt_blocked_by_context_window":
        return "increase block size or use single-token scaffolds before judging prompt-based uptake"
    return "repair scaffold probe inputs before making a model-capability claim"


def _latest_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_by_source: dict[str, int] = {}
    for row in observations:
        source_key = str(row.get("token_cap_root") or "")
        max_by_source[source_key] = max(max_by_source.get(source_key, 0), _as_int(row.get("max_iters")))
    return [row for row in observations if _as_int(row.get("max_iters")) == max_by_source.get(str(row.get("token_cap_root") or ""), 0)]


def _scaffold_prompt(group: dict[str, Any], terms: list[str]) -> str:
    return ",".join(terms) + ":"


def _read_checkpoint_config(checkpoint_path: Path) -> dict[str, Any]:
    if not checkpoint_path.is_file():
        return {}
    try:
        import torch

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    except Exception:
        return {}
    return as_dict(checkpoint.get("config")) if isinstance(checkpoint, dict) else {}


def _find_case_result(results: list[dict[str, Any]], case_name: str) -> dict[str, Any]:
    return next((row for row in results if str(row.get("name") or "") == case_name), {})


def _resolve_file(value: Any, base_dir: Path) -> Path | None:
    if not value:
        return None
    raw = Path(str(value).replace("\\", "/"))
    candidates = [raw, base_dir / raw, Path.cwd() / raw]
    for anchor in (base_dir, *base_dir.parents, Path.cwd()):
        candidates.append(anchor / raw)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _base_dir(source_path: str | Path | None, search_base: str | Path | None) -> Path:
    if search_base is not None:
        return Path(search_base)
    if source_path is not None:
        return Path(source_path).parent
    return Path.cwd()


def _hit_count(text: Any, terms: list[str]) -> int:
    lowered = str(text or "").casefold()
    return sum(1 for term in terms if str(term).casefold() in lowered)


def _preview(value: Any, limit: int = 80) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
