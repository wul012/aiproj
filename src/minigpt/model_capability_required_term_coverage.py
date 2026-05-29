from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_rubric_signal_audit import RUBRIC_SIGNAL_AUDIT_JSON_FILENAME
from minigpt.model_capability_stall_diagnostic import STALL_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, list_of_strs, utc_now


REQUIRED_TERM_COVERAGE_JSON_FILENAME = "model_capability_required_term_coverage.json"
REQUIRED_TERM_COVERAGE_TEXT_FILENAME = "model_capability_required_term_coverage.txt"
REQUIRED_TERM_COVERAGE_MARKDOWN_FILENAME = "model_capability_required_term_coverage.md"
REQUIRED_TERM_COVERAGE_HTML_FILENAME = "model_capability_required_term_coverage.html"


def locate_model_capability_rubric_signal_audit(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / RUBRIC_SIGNAL_AUDIT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def build_model_capability_required_term_coverage(
    rubric_signal_audit: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    search_base: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_dir = _base_dir(source_path, search_base)
    cases = list_of_dicts(rubric_signal_audit.get("cases"))
    source_cache: dict[str, dict[str, Any]] = {}
    term_rows: list[dict[str, Any]] = []
    issues = _input_issues(rubric_signal_audit, cases)

    for case in cases:
        missing_terms = _unique_terms(case.get("last_missing_terms"))
        if not missing_terms:
            continue
        source = _source_for_case(case, base_dir, source_cache)
        if source.get("status") != "pass":
            issues.append(f"case {case.get('case')} required-term source material is incomplete")
        for term in missing_terms:
            term_rows.append(_term_row(case, term, source))

    source_rows = [_public_source_row(source) for source in source_cache.values()]
    summary = summarize_required_term_coverage(term_rows, source_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term coverage audit",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "required_term_coverage_audit_ready" if status == "pass" else "fix_required_term_coverage_audit",
        "failed_count": len(issues),
        "issues": issues,
        "source_rubric_signal_audit": str(source_path) if source_path else None,
        "out_dir": str(Path(out_dir)),
        "summary": summary,
        "source_count": len(source_rows),
        "source_rows": source_rows,
        "term_row_count": len(term_rows),
        "term_rows": term_rows,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(summary),
            "next_action": _next_action(summary),
        },
    }


def summarize_required_term_coverage(term_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    unique_terms = sorted({_norm(row.get("term")) for row in term_rows if _norm(row.get("term"))})
    missing_by_term = {
        term: any(_as_int(row.get("corpus_occurrences")) <= 0 for row in term_rows if _norm(row.get("term")) == term)
        for term in unique_terms
    }
    suite_missing_by_term = {
        term: any(_as_int(row.get("suite_occurrences")) <= 0 for row in term_rows if _norm(row.get("term")) == term)
        for term in unique_terms
    }
    dominant_terms = _count_values(row.get("term") for row in term_rows)
    corpus_missing_unique = sorted(term for term, missing in missing_by_term.items() if missing)
    suite_missing_unique = sorted(term for term, missing in suite_missing_by_term.items() if missing)
    return {
        "coverage_decision": _coverage_decision(term_rows, corpus_missing_unique),
        "missing_term_row_count": len(term_rows),
        "unique_missing_term_count": len(unique_terms),
        "corpus_covered_term_row_count": sum(1 for row in term_rows if _as_int(row.get("corpus_occurrences")) > 0),
        "corpus_missing_term_row_count": sum(1 for row in term_rows if _as_int(row.get("corpus_occurrences")) <= 0),
        "corpus_fully_covered_unique_term_count": len(unique_terms) - len(corpus_missing_unique),
        "corpus_missing_unique_terms": corpus_missing_unique,
        "suite_covered_term_row_count": sum(1 for row in term_rows if _as_int(row.get("suite_occurrences")) > 0),
        "suite_missing_term_row_count": sum(1 for row in term_rows if _as_int(row.get("suite_occurrences")) <= 0),
        "suite_missing_unique_terms": suite_missing_unique,
        "dominant_missing_terms": dict(list(dominant_terms.items())[:12]),
        "source_count": len(source_rows),
        "source_ready_count": sum(1 for row in source_rows if row.get("status") == "pass"),
        "source_missing_count": sum(1 for row in source_rows if row.get("status") != "pass"),
    }


def _source_for_case(
    case: dict[str, Any],
    base_dir: Path,
    source_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_value = case.get("source_diagnostic")
    diagnostic_path = _resolve_file(source_value, base_dir, filename=STALL_JSON_FILENAME)
    key = str(diagnostic_path) if diagnostic_path else str(source_value or "")
    if key not in source_cache:
        source_cache[key] = _collect_source_materials(diagnostic_path, source_value)
    return source_cache[key]


def _collect_source_materials(diagnostic_path: Path | None, source_value: Any) -> dict[str, Any]:
    if diagnostic_path is None:
        return {
            "status": "fail",
            "source_diagnostic": str(source_value or ""),
            "token_cap_root": None,
            "suite_paths": [],
            "corpus_paths": [],
            "prompt_text": "",
            "expected_text": "",
            "suite_text": "",
            "corpus_text": "",
            "suite_case_count": 0,
        }
    token_cap_root = _token_cap_root(diagnostic_path)
    suite_paths = sorted(token_cap_root.glob("ladder/rungs/max-iters-*/standard-zh-capped-suite.json"), key=_rung_order)
    corpus_paths = sorted(token_cap_root.glob("ladder/rungs/max-iters-*/tiny_corpus.txt"), key=_rung_order)
    prompt_parts: list[str] = []
    expected_parts: list[str] = []
    suite_parts: list[str] = []
    suite_case_count = 0
    for suite_path in suite_paths:
        payload = read_json_report(suite_path)
        suite_parts.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        suite_cases = list_of_dicts(payload.get("cases"))
        suite_case_count += len(suite_cases)
        prompt_parts.extend(str(item.get("prompt") or "") for item in suite_cases)
        expected_parts.extend(str(item.get("expected_behavior") or "") for item in suite_cases)
    corpus_parts = [_read_text(path) for path in corpus_paths]
    return {
        "status": "pass" if suite_paths and corpus_paths else "fail",
        "source_diagnostic": str(diagnostic_path),
        "token_cap_root": str(token_cap_root),
        "suite_paths": [str(path) for path in suite_paths],
        "corpus_paths": [str(path) for path in corpus_paths],
        "prompt_text": "\n".join(prompt_parts),
        "expected_text": "\n".join(expected_parts),
        "suite_text": "\n".join(suite_parts),
        "corpus_text": "\n".join(corpus_parts),
        "suite_case_count": suite_case_count,
    }


def _term_row(case: dict[str, Any], term: str, source: dict[str, Any]) -> dict[str, Any]:
    prompt_occurrences = _count_term(source.get("prompt_text"), term)
    expected_occurrences = _count_term(source.get("expected_text"), term)
    suite_occurrences = _count_term(source.get("suite_text"), term)
    corpus_occurrences = _count_term(source.get("corpus_text"), term)
    return {
        "seed": case.get("seed"),
        "token_cap": case.get("token_cap"),
        "case": case.get("case"),
        "task_type": case.get("task_type"),
        "stall_reason": case.get("stall_reason"),
        "failed_checks": list_of_strs(case.get("last_failed_checks")),
        "term": term,
        "covered_in_corpus": corpus_occurrences > 0,
        "covered_in_suite": suite_occurrences > 0,
        "corpus_occurrences": corpus_occurrences,
        "suite_occurrences": suite_occurrences,
        "suite_prompt_occurrences": prompt_occurrences,
        "suite_expected_occurrences": expected_occurrences,
        "source_diagnostic": source.get("source_diagnostic"),
        "token_cap_root": source.get("token_cap_root"),
    }


def _public_source_row(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": source.get("status"),
        "source_diagnostic": source.get("source_diagnostic"),
        "token_cap_root": source.get("token_cap_root"),
        "suite_count": len(source.get("suite_paths") or []),
        "corpus_count": len(source.get("corpus_paths") or []),
        "suite_case_count": source.get("suite_case_count"),
        "suite_char_count": len(str(source.get("suite_text") or "")),
        "corpus_char_count": len(str(source.get("corpus_text") or "")),
        "suite_paths": source.get("suite_paths") or [],
        "corpus_paths": source.get("corpus_paths") or [],
    }


def _input_issues(rubric_signal_audit: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rubric_signal_audit:
        issues.append("source rubric signal audit is missing or invalid")
    if not cases:
        issues.append("source rubric signal audit has no cases")
    if as_dict(rubric_signal_audit.get("summary")).get("decision") != "rubric_required_terms_dominate_flat_scores":
        issues.append("source rubric signal audit is not dominated by required-term failures")
    return issues


def _coverage_decision(term_rows: list[dict[str, Any]], corpus_missing_unique_terms: list[str]) -> str:
    if not term_rows:
        return "no_required_term_gap"
    if not corpus_missing_unique_terms:
        return "required_terms_present_but_not_generated"
    if len(corpus_missing_unique_terms) == len({_norm(row.get("term")) for row in term_rows if _norm(row.get("term"))}):
        return "required_terms_absent_from_tiny_corpus"
    return "mixed_required_term_coverage"


def _interpretation_reason(summary: dict[str, Any]) -> str:
    decision = summary.get("coverage_decision")
    if decision == "required_terms_present_but_not_generated":
        return "The required terms missing from generations are present in the archived tiny corpus, so data presence alone does not explain the rubric gap."
    if decision == "mixed_required_term_coverage":
        return "Some missing generation terms are present in the tiny corpus while others are absent, so data coverage and model generation both need review."
    if decision == "required_terms_absent_from_tiny_corpus":
        return "The required terms missing from generations are also absent from the archived tiny corpus, so the next step is targeted data coverage."
    return "The source audit did not expose a required-term gap to inspect."


def _next_action(summary: dict[str, Any]) -> str:
    decision = summary.get("coverage_decision")
    if decision == "required_terms_present_but_not_generated":
        return "inspect training scale, sampling, and prompt-to-generation behavior before enlarging the benchmark or model"
    if decision == "mixed_required_term_coverage":
        return "add targeted corpus examples for uncovered required terms and separately inspect covered-but-not-generated terms"
    if decision == "required_terms_absent_from_tiny_corpus":
        return "extend the tiny corpus/data card before spending more training compute"
    return "continue with the existing model-capability ladder only if a new required-term gap appears"


def _base_dir(source_path: str | Path | None, search_base: str | Path | None) -> Path:
    if search_base is not None:
        return Path(search_base)
    if source_path is not None:
        return Path(source_path).parent
    return Path.cwd()


def _resolve_file(value: Any, base_dir: Path, *, filename: str | None = None) -> Path | None:
    if not value:
        return None
    raw = Path(str(value).replace("\\", "/"))
    candidates = [raw, base_dir / raw, Path.cwd() / raw]
    for anchor in (base_dir, *base_dir.parents, Path.cwd()):
        candidates.append(anchor / raw)
    expanded: list[Path] = []
    for candidate in candidates:
        expanded.append(candidate)
        if filename:
            expanded.append(candidate / filename)
    for candidate in expanded:
        if candidate.is_file():
            return candidate
    return None


def _token_cap_root(diagnostic_path: Path) -> Path:
    if diagnostic_path.parent.name == "stall-diagnostic":
        return diagnostic_path.parent.parent
    return diagnostic_path.parent


def _rung_order(path: Path) -> tuple[int, str]:
    for part in path.parts:
        if part.startswith("max-iters-"):
            return (_as_int(part.removeprefix("max-iters-")), str(path))
    return (0, str(path))


def _unique_terms(value: Any) -> list[str]:
    seen: set[str] = set()
    terms: list[str] = []
    for term in list_of_strs(value):
        normalized = _norm(term)
        if normalized and normalized not in seen:
            seen.add(normalized)
            terms.append(str(term).strip())
    return terms


def _count_term(text: Any, term: str) -> int:
    normalized_term = _norm(term)
    if not normalized_term:
        return 0
    return str(text or "").casefold().count(normalized_term)


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value).strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
