from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_coverage import REQUIRED_TERM_COVERAGE_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_UPTAKE_JSON_FILENAME = "model_capability_required_term_uptake.json"
REQUIRED_TERM_UPTAKE_TEXT_FILENAME = "model_capability_required_term_uptake.txt"
REQUIRED_TERM_UPTAKE_MARKDOWN_FILENAME = "model_capability_required_term_uptake.md"
REQUIRED_TERM_UPTAKE_HTML_FILENAME = "model_capability_required_term_uptake.html"


def locate_model_capability_required_term_coverage(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_COVERAGE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def build_model_capability_required_term_uptake(
    coverage_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    search_base: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_dir = _base_dir(source_path, search_base)
    term_rows = list_of_dicts(coverage_report.get("term_rows"))
    source_cache: dict[str, dict[str, Any]] = {}
    observations: list[dict[str, Any]] = []
    issues = _input_issues(coverage_report, term_rows)

    for term_row in term_rows:
        source = _source_for_term_row(term_row, base_dir, source_cache)
        if source.get("status") != "pass":
            issues.append(f"case {term_row.get('case')} has no archived eval-suite generation source")
        observations.extend(_observations_for_term(term_row, source))

    source_rows = [_public_source_row(source) for source in source_cache.values()]
    summary = summarize_required_term_uptake(term_rows, observations, source_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term uptake audit",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "required_term_uptake_audit_ready" if status == "pass" else "fix_required_term_uptake_audit",
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_coverage": str(source_path) if source_path else None,
        "out_dir": str(Path(out_dir)),
        "summary": summary,
        "source_count": len(source_rows),
        "source_rows": source_rows,
        "observation_count": len(observations),
        "observations": observations,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(summary),
            "next_action": _next_action(summary),
        },
    }


def summarize_required_term_uptake(
    term_rows: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    last_observations = _last_rung_observations(observations)
    uptake_keys = {
        _case_term_key(row)
        for row in observations
        if row.get("continuation_hit") or row.get("generated_hit")
    }
    last_uptake_keys = {
        _case_term_key(row)
        for row in last_observations
        if row.get("continuation_hit") or row.get("generated_hit")
    }
    prompt_only_terms = sorted(
        {
            _norm(row.get("term"))
            for row in observations
            if row.get("expected_hit") and not row.get("prompt_hit") and not row.get("continuation_hit")
        }
    )
    return {
        "uptake_decision": _uptake_decision(term_rows, observations, last_observations),
        "required_term_row_count": len(term_rows),
        "generation_observation_count": len(observations),
        "continuation_hit_count": sum(1 for row in observations if row.get("continuation_hit")),
        "generated_hit_count": sum(1 for row in observations if row.get("generated_hit")),
        "prompt_hit_count": sum(1 for row in observations if row.get("prompt_hit")),
        "expected_hit_count": sum(1 for row in observations if row.get("expected_hit")),
        "last_rung_observation_count": len(last_observations),
        "last_rung_continuation_hit_count": sum(1 for row in last_observations if row.get("continuation_hit")),
        "case_term_uptake_count": len(uptake_keys),
        "last_rung_case_term_uptake_count": len(last_uptake_keys),
        "expected_only_unique_term_count": len(prompt_only_terms),
        "expected_only_terms": prompt_only_terms[:20],
        "dominant_missing_terms": _count_values(row.get("term") for row in term_rows),
        "source_count": len(source_rows),
        "source_ready_count": sum(1 for row in source_rows if row.get("status") == "pass"),
        "source_missing_count": sum(1 for row in source_rows if row.get("status") != "pass"),
    }


def _source_for_term_row(
    term_row: dict[str, Any],
    base_dir: Path,
    source_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    token_cap_root = _resolve_dir(term_row.get("token_cap_root"), base_dir)
    key = str(token_cap_root) if token_cap_root else str(term_row.get("token_cap_root") or "")
    if key not in source_cache:
        source_cache[key] = _collect_eval_suite_sources(token_cap_root, term_row.get("token_cap_root"))
    return source_cache[key]


def _collect_eval_suite_sources(token_cap_root: Path | None, raw_value: Any) -> dict[str, Any]:
    if token_cap_root is None:
        return {
            "status": "fail",
            "token_cap_root": str(raw_value or ""),
            "eval_suite_paths": [],
            "rungs": [],
        }
    eval_paths = sorted(token_cap_root.glob("ladder/rungs/max-iters-*/run/eval_suite/eval_suite.json"), key=_rung_order)
    rungs = []
    for path in eval_paths:
        payload = read_json_report(path)
        rungs.append(
            {
                "max_iters": _max_iters_for_path(path),
                "eval_suite_path": str(path),
                "case_count": len(list_of_dicts(payload.get("results"))),
                "results": list_of_dicts(payload.get("results")),
            }
        )
    return {
        "status": "pass" if rungs else "fail",
        "token_cap_root": str(token_cap_root),
        "eval_suite_paths": [str(path) for path in eval_paths],
        "rungs": rungs,
    }


def _observations_for_term(term_row: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    term = str(term_row.get("term") or "").strip()
    case_name = str(term_row.get("case") or "")
    rows = []
    for rung in list_of_dicts(source.get("rungs")):
        result = _find_case_result(list_of_dicts(rung.get("results")), case_name)
        if not result:
            continue
        continuation_occurrences = _count_term(result.get("continuation"), term)
        generated_occurrences = _count_term(result.get("generated"), term)
        prompt_occurrences = _count_term(result.get("prompt"), term)
        expected_occurrences = _count_term(result.get("expected_behavior"), term)
        rows.append(
            {
                "seed": term_row.get("seed"),
                "token_cap": term_row.get("token_cap"),
                "case": term_row.get("case"),
                "task_type": term_row.get("task_type"),
                "stall_reason": term_row.get("stall_reason"),
                "term": term,
                "max_iters": rung.get("max_iters"),
                "continuation_hit": continuation_occurrences > 0,
                "generated_hit": generated_occurrences > 0,
                "prompt_hit": prompt_occurrences > 0,
                "expected_hit": expected_occurrences > 0,
                "continuation_occurrences": continuation_occurrences,
                "generated_occurrences": generated_occurrences,
                "prompt_occurrences": prompt_occurrences,
                "expected_occurrences": expected_occurrences,
                "char_count": result.get("char_count"),
                "unique_char_count": result.get("unique_char_count"),
                "continuation_preview": _preview(result.get("continuation")),
                "eval_suite_path": rung.get("eval_suite_path"),
                "token_cap_root": source.get("token_cap_root"),
            }
        )
    return rows


def _public_source_row(source: dict[str, Any]) -> dict[str, Any]:
    rungs = list_of_dicts(source.get("rungs"))
    return {
        "status": source.get("status"),
        "token_cap_root": source.get("token_cap_root"),
        "eval_suite_count": len(source.get("eval_suite_paths") or []),
        "max_iters_values": [rung.get("max_iters") for rung in rungs],
        "result_count": sum(int(rung.get("case_count") or 0) for rung in rungs),
        "eval_suite_paths": source.get("eval_suite_paths") or [],
    }


def _input_issues(coverage_report: dict[str, Any], term_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not coverage_report:
        issues.append("source required-term coverage report is missing or invalid")
    if not term_rows:
        issues.append("source required-term coverage report has no term rows")
    if as_dict(coverage_report.get("summary")).get("coverage_decision") != "required_terms_present_but_not_generated":
        issues.append("source coverage report is not present-but-not-generated")
    return issues


def _uptake_decision(
    term_rows: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    last_observations: list[dict[str, Any]],
) -> str:
    if not term_rows:
        return "no_required_term_gap"
    if not observations:
        return "missing_generation_observations"
    if any(row.get("continuation_hit") for row in last_observations):
        return "last_rung_required_terms_partially_generated"
    if any(row.get("continuation_hit") for row in observations):
        return "earlier_rung_required_terms_partially_generated"
    return "required_terms_never_generated"


def _interpretation_reason(summary: dict[str, Any]) -> str:
    decision = summary.get("uptake_decision")
    if decision == "required_terms_never_generated":
        return "Archived suite outputs never place the required terms into continuations, even though those terms are present in expected behavior and corpus material."
    if decision == "last_rung_required_terms_partially_generated":
        return "The latest archived tiny rung generated at least some required terms, so the next step is to inspect which cases respond to training scale."
    if decision == "earlier_rung_required_terms_partially_generated":
        return "An earlier rung generated some required terms, but the latest rung did not preserve the behavior."
    if decision == "missing_generation_observations":
        return "The coverage report resolved source material, but archived eval-suite generation outputs were not found."
    return "The source report did not expose required-term rows to inspect."


def _next_action(summary: dict[str, Any]) -> str:
    decision = summary.get("uptake_decision")
    if decision == "required_terms_never_generated":
        return "run a targeted decoding/training probe with explicit required-term scaffolds before increasing benchmark scope"
    if decision == "last_rung_required_terms_partially_generated":
        return "compare the successful case prompts and consider a focused training-scale repeat"
    if decision == "earlier_rung_required_terms_partially_generated":
        return "review seed and sampling variance because the uptake was not stable across rungs"
    return "repair archived eval-suite references before making a model-capability claim"


def _base_dir(source_path: str | Path | None, search_base: str | Path | None) -> Path:
    if search_base is not None:
        return Path(search_base)
    if source_path is not None:
        return Path(source_path).parent
    return Path.cwd()


def _resolve_dir(value: Any, base_dir: Path) -> Path | None:
    if not value:
        return None
    raw = Path(str(value).replace("\\", "/"))
    candidates = [raw, base_dir / raw, Path.cwd() / raw]
    for anchor in (base_dir, *base_dir.parents, Path.cwd()):
        candidates.append(anchor / raw)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _find_case_result(results: list[dict[str, Any]], case_name: str) -> dict[str, Any]:
    return next((row for row in results if str(row.get("name") or "") == case_name), {})


def _last_rung_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_by_source: dict[str, int] = {}
    for row in observations:
        source_key = str(row.get("token_cap_root") or "")
        max_by_source[source_key] = max(max_by_source.get(source_key, 0), _as_int(row.get("max_iters")))
    return [row for row in observations if _as_int(row.get("max_iters")) == max_by_source.get(str(row.get("token_cap_root") or ""), 0)]


def _case_term_key(row: dict[str, Any]) -> str:
    return "|".join(str(row.get(key) or "") for key in ("seed", "case", "term"))


def _count_term(text: Any, term: str) -> int:
    normalized_term = _norm(term)
    if not normalized_term:
        return 0
    return str(text or "").casefold().count(normalized_term)


def _rung_order(path: Path) -> tuple[int, str]:
    return (_max_iters_for_path(path), str(path))


def _max_iters_for_path(path: Path) -> int:
    for part in path.parts:
        if part.startswith("max-iters-"):
            return _as_int(part.removeprefix("max-iters-"))
    return 0


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value).strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _preview(value: Any, limit: int = 80) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
