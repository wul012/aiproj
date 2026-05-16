from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.generation_quality_artifacts import (
    render_generation_quality_html,
    render_generation_quality_markdown,
    write_generation_quality_csv,
    write_generation_quality_html,
    write_generation_quality_json,
    write_generation_quality_markdown,
    write_generation_quality_outputs,
    write_generation_quality_svg,
)
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)


def build_generation_quality_report(
    source_path: str | Path,
    *,
    source_type: str = "auto",
    min_continuation_chars: int = 8,
    min_unique_ratio: float = 0.25,
    max_repeat_run: int = 8,
    max_repeated_ngram_ratio: float = 0.65,
    ngram_size: int = 2,
    title: str = "MiniGPT generation quality report",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if min_continuation_chars < 1:
        raise ValueError("min_continuation_chars must be at least 1")
    if not 0 < min_unique_ratio <= 1:
        raise ValueError("min_unique_ratio must be in (0, 1]")
    if max_repeat_run < 1:
        raise ValueError("max_repeat_run must be at least 1")
    if not 0 <= max_repeated_ngram_ratio <= 1:
        raise ValueError("max_repeated_ngram_ratio must be in [0, 1]")
    if ngram_size < 1:
        raise ValueError("ngram_size must be at least 1")

    source_file = Path(source_path)
    payload = _read_required_json(source_file)
    inferred_type = _infer_source_type(payload) if source_type == "auto" else source_type
    cases = _build_case_rows(
        payload,
        inferred_type,
        min_continuation_chars=min_continuation_chars,
        min_unique_ratio=min_unique_ratio,
        max_repeat_run=max_repeat_run,
        max_repeated_ngram_ratio=max_repeated_ngram_ratio,
        ngram_size=ngram_size,
    )
    summary = _build_summary(cases, inferred_type)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "source_path": str(source_file),
        "source_type": inferred_type,
        "policy": {
            "min_continuation_chars": min_continuation_chars,
            "min_unique_ratio": min_unique_ratio,
            "max_repeat_run": max_repeat_run,
            "max_repeated_ngram_ratio": max_repeated_ngram_ratio,
            "ngram_size": ngram_size,
        },
        "summary": summary,
        "cases": cases,
        "recommendations": _recommendations(summary, cases),
        "warnings": _warnings(payload, cases),
    }


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"generation quality input must be a JSON object: {path}")
    return payload


def _infer_source_type(payload: dict[str, Any]) -> str:
    if "case_count" in payload and "avg_continuation_chars" in payload:
        return "eval_suite"
    if "max_new_tokens" in payload and "prompt" in payload:
        return "sample_lab"
    return "generic_results"


def _build_case_rows(
    payload: dict[str, Any],
    source_type: str,
    *,
    min_continuation_chars: int,
    min_unique_ratio: float,
    max_repeat_run: int,
    max_repeated_ngram_ratio: float,
    ngram_size: int,
) -> list[dict[str, Any]]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or not raw_results:
        raise ValueError("generation quality input requires a non-empty results list")
    rows = []
    shared_prompt = str(payload.get("prompt") or "")
    for index, item in enumerate(raw_results, start=1):
        if not isinstance(item, dict):
            raise ValueError("each generation result must be an object")
        prompt = str(item.get("prompt") or shared_prompt)
        continuation = _continuation(item, prompt)
        metrics = _metrics(continuation, ngram_size=ngram_size)
        flags = _flags(
            continuation,
            prompt,
            metrics,
            min_continuation_chars=min_continuation_chars,
            min_unique_ratio=min_unique_ratio,
            max_repeat_run=max_repeat_run,
            max_repeated_ngram_ratio=max_repeated_ngram_ratio,
        )
        status = _status(flags)
        rows.append(
            {
                "name": str(item.get("name") or f"case-{index}"),
                "source_type": source_type,
                "status": status,
                "prompt": prompt,
                "temperature": item.get("temperature"),
                "top_k": item.get("top_k"),
                "seed": item.get("seed"),
                "max_new_tokens": item.get("max_new_tokens") or payload.get("max_new_tokens"),
                "char_count": metrics["char_count"],
                "stripped_char_count": metrics["stripped_char_count"],
                "unique_char_count": metrics["unique_char_count"],
                "unique_ratio": metrics["unique_ratio"],
                "repeated_ngram_ratio": metrics["repeated_ngram_ratio"],
                "longest_repeat_run": metrics["longest_repeat_run"],
                "flag_count": len(flags),
                "flags": flags,
                "continuation_preview": _clip(continuation, 96),
            }
        )
    return rows


def _continuation(item: dict[str, Any], prompt: str) -> str:
    continuation = item.get("continuation")
    if isinstance(continuation, str):
        return continuation
    generated = item.get("generated")
    if not isinstance(generated, str):
        return ""
    if prompt and generated.startswith(prompt):
        return generated[len(prompt) :]
    return generated


def _metrics(text: str, *, ngram_size: int) -> dict[str, Any]:
    non_ws = [char for char in text if not char.isspace()]
    ngrams = _ngrams(non_ws, ngram_size)
    unique_ratio = 0.0 if not non_ws else len(set(non_ws)) / len(non_ws)
    repeated_ngram_ratio = 0.0 if not ngrams else 1.0 - len(set(ngrams)) / len(ngrams)
    return {
        "char_count": len(text),
        "stripped_char_count": len(text.strip()),
        "unique_char_count": len(set(non_ws)),
        "unique_ratio": round(unique_ratio, 4),
        "repeated_ngram_ratio": round(repeated_ngram_ratio, 4),
        "longest_repeat_run": _longest_repeat_run(non_ws),
    }


def _ngrams(chars: list[str], size: int) -> list[str]:
    if len(chars) < size:
        return []
    return ["".join(chars[index : index + size]) for index in range(len(chars) - size + 1)]


def _longest_repeat_run(chars: list[str]) -> int:
    if not chars:
        return 0
    longest = 1
    current = 1
    previous = chars[0]
    for char in chars[1:]:
        if char == previous:
            current += 1
        else:
            longest = max(longest, current)
            current = 1
            previous = char
    return max(longest, current)


def _flags(
    continuation: str,
    prompt: str,
    metrics: dict[str, Any],
    *,
    min_continuation_chars: int,
    min_unique_ratio: float,
    max_repeat_run: int,
    max_repeated_ngram_ratio: float,
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    if metrics["stripped_char_count"] == 0:
        flags.append(_flag("empty_continuation", "fail", "Continuation is empty."))
    elif metrics["char_count"] < min_continuation_chars:
        flags.append(_flag("too_short", "fail", f"Continuation has {metrics['char_count']} chars; minimum is {min_continuation_chars}."))
    if metrics["char_count"] and metrics["unique_ratio"] < min_unique_ratio:
        flags.append(_flag("low_diversity", "warn", f"Unique ratio {_ratio_label(metrics['unique_ratio'])} is below {_ratio_label(min_unique_ratio)}."))
    if metrics["longest_repeat_run"] > max_repeat_run:
        flags.append(_flag("long_repeat_run", "warn", f"Longest repeated character run is {metrics['longest_repeat_run']}; maximum is {max_repeat_run}."))
    if metrics["repeated_ngram_ratio"] > max_repeated_ngram_ratio:
        flags.append(_flag("high_ngram_repetition", "warn", f"Repeated n-gram ratio {_ratio_label(metrics['repeated_ngram_ratio'])} is above {_ratio_label(max_repeated_ngram_ratio)}."))
    if _looks_like_prompt_echo(continuation, prompt):
        flags.append(_flag("prompt_echo", "warn", "Continuation appears to repeat the prompt."))
    return flags


def _looks_like_prompt_echo(continuation: str, prompt: str) -> bool:
    cleaned_prompt = prompt.strip()
    if len(cleaned_prompt) < 4:
        return False
    prefix = cleaned_prompt[: min(12, len(cleaned_prompt))]
    return continuation.strip().startswith(prefix)


def _flag(flag_id: str, level: str, detail: str) -> dict[str, str]:
    return {"id": flag_id, "level": level, "detail": detail}


def _status(flags: list[dict[str, str]]) -> str:
    levels = {flag.get("level") for flag in flags}
    if "fail" in levels:
        return "fail"
    if "warn" in levels:
        return "warn"
    return "pass"


def _build_summary(cases: list[dict[str, Any]], source_type: str) -> dict[str, Any]:
    pass_count = sum(1 for case in cases if case.get("status") == "pass")
    warn_count = sum(1 for case in cases if case.get("status") == "warn")
    fail_count = sum(1 for case in cases if case.get("status") == "fail")
    if fail_count:
        overall_status = "fail"
    elif warn_count:
        overall_status = "warn"
    else:
        overall_status = "pass"
    return {
        "overall_status": overall_status,
        "source_type": source_type,
        "case_count": len(cases),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "avg_continuation_chars": _round_avg(case.get("char_count") for case in cases),
        "avg_unique_ratio": _round_avg(case.get("unique_ratio") for case in cases),
        "avg_repeated_ngram_ratio": _round_avg(case.get("repeated_ngram_ratio") for case in cases),
        "max_repeat_run": max((int(case.get("longest_repeat_run") or 0) for case in cases), default=0),
        "flag_summary": _build_flag_summary(cases),
    }


def _build_flag_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    flag_id_counts: dict[str, int] = {}
    flag_level_counts: dict[str, int] = {"fail": 0, "warn": 0}
    worst_cases: list[dict[str, Any]] = []
    total_flags = 0

    for case in cases:
        flags = _list_of_dicts(case.get("flags"))
        flag_ids = []
        for flag in flags:
            flag_id = str(flag.get("id") or "").strip()
            level = str(flag.get("level") or "").strip()
            if flag_id:
                flag_id_counts[flag_id] = flag_id_counts.get(flag_id, 0) + 1
                flag_ids.append(flag_id)
                total_flags += 1
            if level:
                flag_level_counts[level] = flag_level_counts.get(level, 0) + 1
        if flag_ids:
            worst_cases.append(
                {
                    "name": str(case.get("name") or ""),
                    "status": str(case.get("status") or "warn"),
                    "flag_count": len(flag_ids),
                    "flag_ids": flag_ids,
                }
            )

    severity = {"fail": 2, "warn": 1, "pass": 0}
    worst_cases.sort(
        key=lambda item: (
            -severity.get(str(item.get("status")), 0),
            -int(item.get("flag_count") or 0),
            str(item.get("name") or ""),
        )
    )
    return {
        "total_flags": total_flags,
        "flag_id_counts": dict(sorted(flag_id_counts.items())),
        "flag_level_counts": dict(sorted(flag_level_counts.items())),
        "worst_cases": worst_cases[:5],
    }


def _recommendations(summary: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    if summary.get("overall_status") == "pass":
        return ["Generation quality checks passed; keep this report with eval artifacts."]
    items = []
    if summary.get("fail_count"):
        items.append("Fix failed generation cases before using this checkpoint as a release candidate.")
    if summary.get("warn_count"):
        items.append("Review warning cases for repetition, low diversity, or prompt echo before model-card handoff.")
    flag_id_counts = _dict(_dict(summary.get("flag_summary")).get("flag_id_counts"))
    if flag_id_counts:
        dominant_flag = max(flag_id_counts.items(), key=lambda item: (int(item[1]), item[0]))
        items.append(f"Prioritize dominant generation flag: {dominant_flag[0]} ({dominant_flag[1]} occurrence(s)).")
    for case in cases:
        if case.get("status") != "pass":
            flag_ids = ", ".join(flag["id"] for flag in _list_of_dicts(case.get("flags")))
            items.append(f"{case.get('name')}: {flag_ids}")
    return items or ["Review generation samples manually before sharing the run."]


def _warnings(payload: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    warnings = []
    if not payload.get("checkpoint"):
        warnings.append("source report does not include a checkpoint path")
    if not payload.get("tokenizer"):
        warnings.append("source report does not include a tokenizer path")
    if not cases:
        warnings.append("no generation cases were analyzed")
    return warnings


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_avg(values: Any) -> float:
    numbers = [_number(value) for value in values]
    clean = [number for number in numbers if number is not None]
    return 0.0 if not clean else round(sum(clean) / len(clean), 4)


def _ratio_label(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{number:.1%}"

def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."
