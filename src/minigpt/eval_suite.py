from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from minigpt.eval_suite_artifacts import (
    render_eval_suite_html,  # noqa: F401
    write_eval_suite_csv,  # noqa: F401
    write_eval_suite_html,  # noqa: F401
    write_eval_suite_json,  # noqa: F401
    write_eval_suite_outputs,  # noqa: F401
    write_eval_suite_svg,  # noqa: F401
)

RECOMMENDED_TASK_TYPES = ("continuation", "qa", "summary", "structured", "factual-consistency")
RECOMMENDED_DIFFICULTIES = ("easy", "medium")
COMPARISON_RECOMMENDED_DIFFICULTIES = ("hard",)
MIN_RECOMMENDED_CASES = 5
MIN_RECOMMENDED_TAGS = 4
MIN_COMPARISON_CASES = 8
MIN_COMPARISON_TASK_TYPES = 8
MIN_COMPARISON_TAGS = 8


@dataclass(frozen=True)
class PromptCase:
    name: str
    prompt: str
    max_new_tokens: int = 60
    temperature: float = 0.8
    top_k: int | None = 30
    seed: int = 42
    task_type: str = "general"
    difficulty: str = "medium"
    expected_behavior: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("prompt case name cannot be empty")
        if not self.prompt:
            raise ValueError("prompt cannot be empty")
        if self.max_new_tokens < 1:
            raise ValueError("max_new_tokens must be at least 1")
        if self.temperature <= 0:
            raise ValueError("temperature must be greater than 0")
        if self.top_k is not None and self.top_k < 1:
            raise ValueError("top_k must be at least 1 when provided")
        if not self.task_type.strip():
            raise ValueError("task_type cannot be empty")
        if not self.difficulty.strip():
            raise ValueError("difficulty cannot be empty")
        raw_tags: Any = self.tags
        if isinstance(raw_tags, str):
            tags = tuple(tag.strip() for tag in raw_tags.split(",") if tag.strip())
        elif raw_tags is None:
            tags = ()
        else:
            tags = tuple(str(tag) for tag in raw_tags if str(tag).strip())
        object.__setattr__(self, "tags", tags)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptSuite:
    name: str
    version: str = "1"
    description: str = ""
    language: str = "zh-CN"
    cases: tuple[PromptCase, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("prompt suite name cannot be empty")
        if not self.version.strip():
            raise ValueError("prompt suite version cannot be empty")
        if not self.cases:
            raise ValueError("prompt suite requires at least one case")
        object.__setattr__(self, "cases", tuple(self.cases))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "language": self.language,
            "cases": [case.to_dict() for case in self.cases],
        }


@dataclass(frozen=True)
class PromptResult:
    name: str
    prompt: str
    task_type: str
    difficulty: str
    expected_behavior: str
    tags: tuple[str, ...]
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int
    generated: str
    continuation: str
    char_count: int
    unique_char_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_prompt_suite() -> PromptSuite:
    return PromptSuite(
        name="minigpt-zh-benchmark",
        version="1",
        description="Small fixed Chinese benchmark prompts for MiniGPT learning runs.",
        language="zh-CN",
        cases=(
            PromptCase(
                "continuation-basic",
                "人工智能正在改变",
                max_new_tokens=60,
                temperature=0.7,
                top_k=20,
                seed=101,
                task_type="continuation",
                difficulty="easy",
                expected_behavior="Continue the sentence with coherent Chinese text.",
                tags=("zh", "continuation"),
            ),
            PromptCase(
                "qa-training",
                "问题：什么是模型训练？\n回答：",
                max_new_tokens=70,
                temperature=0.7,
                top_k=25,
                seed=102,
                task_type="qa",
                difficulty="easy",
                expected_behavior="Answer the question briefly and stay on the topic of model training.",
                tags=("zh", "qa", "training"),
            ),
            PromptCase(
                "summary-data-quality",
                "请用一句话总结：数据质量会影响模型训练稳定性、评估可信度和最终生成效果。\n总结：",
                max_new_tokens=70,
                temperature=0.6,
                top_k=25,
                seed=103,
                task_type="summary",
                difficulty="medium",
                expected_behavior="Produce a one-sentence summary that mentions data quality and model outcomes.",
                tags=("zh", "summary", "data"),
            ),
            PromptCase(
                "structured-run-record",
                "请按 JSON 风格列出一次 MiniGPT 实验需要记录的三项信息：",
                max_new_tokens=90,
                temperature=0.6,
                top_k=30,
                seed=104,
                task_type="structured",
                difficulty="medium",
                expected_behavior="Generate a compact structured list with experiment metadata fields.",
                tags=("zh", "structured", "experiment"),
            ),
            PromptCase(
                "consistency-val-loss",
                "判断：如果验证集损失持续上升，模型一定更好吗？请回答原因：",
                max_new_tokens=80,
                temperature=0.7,
                top_k=30,
                seed=105,
                task_type="factual-consistency",
                difficulty="medium",
                expected_behavior="Reject the false premise and explain that rising validation loss is usually worse.",
                tags=("zh", "reasoning", "evaluation"),
            ),
        ),
    )


def default_prompt_cases() -> list[PromptCase]:
    return list(default_prompt_suite().cases)


def load_builtin_prompt_suite(name: str) -> PromptSuite:
    from minigpt.eval_suites import named_prompt_suite

    return named_prompt_suite(name)


def load_prompt_suite(path: str | Path | None = None) -> PromptSuite:
    if path is None:
        return default_prompt_suite()
    if str(path).startswith("builtin:"):
        return load_builtin_prompt_suite(str(path).split(":", 1)[1])
    suite_path = Path(path)
    payload = json.loads(suite_path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        raw_cases = payload.get("cases")
        name = str(payload.get("suite_name") or payload.get("name") or suite_path.stem)
        version = str(payload.get("suite_version") or payload.get("version") or "1")
        description = str(payload.get("description") or "")
        language = str(payload.get("language") or "zh-CN")
    else:
        raw_cases = payload
        name = suite_path.stem
        version = "1"
        description = ""
        language = "zh-CN"
    if not isinstance(raw_cases, list):
        raise ValueError("prompt suite must be a list or an object with a cases list")
    cases = tuple(_case_from_dict(item) for item in raw_cases)
    return PromptSuite(name=name, version=version, description=description, language=language, cases=cases)


def load_prompt_cases(path: str | Path | None = None) -> list[PromptCase]:
    return list(load_prompt_suite(path).cases)


def build_prompt_result(case: PromptCase, generated: str) -> PromptResult:
    continuation = generated[len(case.prompt) :] if generated.startswith(case.prompt) else generated
    return PromptResult(
        name=case.name,
        prompt=case.prompt,
        task_type=case.task_type,
        difficulty=case.difficulty,
        expected_behavior=case.expected_behavior,
        tags=case.tags,
        max_new_tokens=case.max_new_tokens,
        temperature=case.temperature,
        top_k=case.top_k,
        seed=case.seed,
        generated=generated,
        continuation=continuation,
        char_count=len(continuation),
        unique_char_count=len(set(continuation)),
    )


def build_eval_suite_report(
    results: list[PromptResult],
    *,
    checkpoint: str | None = None,
    tokenizer: str | None = None,
    suite: str | None = None,
    suite_name: str | None = None,
    suite_version: str | None = None,
    suite_description: str | None = None,
    suite_language: str | None = None,
) -> dict[str, Any]:
    if not results:
        raise ValueError("eval suite report requires at least one result")
    task_type_counts = _count_by(result.task_type for result in results)
    difficulty_counts = _count_by(result.difficulty for result in results)
    coverage = _coverage_summary(results, task_type_counts, difficulty_counts)
    design_summary = _design_summary(
        results,
        suite_name=suite_name,
        suite_version=suite_version,
        suite_description=suite_description,
        suite_language=suite_language,
    )
    return {
        "schema_version": 1,
        "checkpoint": checkpoint,
        "tokenizer": tokenizer,
        "suite": suite,
        "benchmark": {
            "suite_name": suite_name,
            "suite_version": suite_version,
            "description": suite_description,
            "language": suite_language,
            "task_type_counts": task_type_counts,
            "difficulty_counts": difficulty_counts,
            "task_type_summary": _summary_by(results, "task_type"),
            "difficulty_summary": _summary_by(results, "difficulty"),
            "coverage": coverage,
            "design_summary": design_summary,
        },
        "coverage": coverage,
        "design_summary": design_summary,
        "case_count": len(results),
        "avg_continuation_chars": round(sum(result.char_count for result in results) / len(results), 4),
        "avg_unique_chars": round(sum(result.unique_char_count for result in results) / len(results), 4),
        "task_type_counts": task_type_counts,
        "difficulty_counts": difficulty_counts,
        "results": [result.to_dict() for result in results],
    }


def _case_from_dict(payload: Any) -> PromptCase:
    if not isinstance(payload, dict):
        raise ValueError("each prompt case must be an object")
    top_k = payload.get("top_k", 30)
    if top_k in {"", 0, "0", "none", "None", None}:
        top_k = None
    raw_tags = payload.get("tags", ())
    tags = tuple(raw_tags) if isinstance(raw_tags, list) else tuple(str(raw_tags).split(",")) if raw_tags else ()
    return PromptCase(
        name=str(payload["name"]),
        prompt=str(payload["prompt"]),
        max_new_tokens=int(payload.get("max_new_tokens", 60)),
        temperature=float(payload.get("temperature", 0.8)),
        top_k=None if top_k is None else int(top_k),
        seed=int(payload.get("seed", 42)),
        task_type=str(payload.get("task_type") or "general"),
        difficulty=str(payload.get("difficulty") or "medium"),
        expected_behavior=str(payload.get("expected_behavior") or ""),
        tags=tags,
    )


def _count_by(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _coverage_summary(
    results: list[PromptResult],
    task_type_counts: dict[str, int],
    difficulty_counts: dict[str, int],
) -> dict[str, Any]:
    observed_task_types = sorted(task_type_counts)
    observed_difficulties = sorted(difficulty_counts)
    observed_tags = sorted({tag for result in results for tag in result.tags if tag})
    missing_task_types = [task_type for task_type in RECOMMENDED_TASK_TYPES if task_type not in task_type_counts]
    missing_difficulties = [difficulty for difficulty in RECOMMENDED_DIFFICULTIES if difficulty not in difficulty_counts]
    missing_comparison_difficulties = [
        difficulty for difficulty in COMPARISON_RECOMMENDED_DIFFICULTIES if difficulty not in difficulty_counts
    ]
    case_count = len(results)
    tag_count = len(observed_tags)
    ready = (
        case_count >= MIN_RECOMMENDED_CASES
        and not missing_task_types
        and not missing_difficulties
        and tag_count >= MIN_RECOMMENDED_TAGS
    )
    blockers = []
    if case_count < MIN_RECOMMENDED_CASES:
        blockers.append(f"only {case_count} case(s), expected at least {MIN_RECOMMENDED_CASES}")
    if missing_task_types:
        blockers.append("missing recommended task types: " + ", ".join(missing_task_types))
    if missing_difficulties:
        blockers.append("missing recommended difficulties: " + ", ".join(missing_difficulties))
    if tag_count < MIN_RECOMMENDED_TAGS:
        blockers.append(f"only {tag_count} tag(s), expected at least {MIN_RECOMMENDED_TAGS}")
    comparison_blockers = []
    if case_count < MIN_COMPARISON_CASES:
        comparison_blockers.append(f"only {case_count} case(s), expected at least {MIN_COMPARISON_CASES}")
    if len(observed_task_types) < MIN_COMPARISON_TASK_TYPES:
        comparison_blockers.append(
            f"only {len(observed_task_types)} task type(s), expected at least {MIN_COMPARISON_TASK_TYPES}"
        )
    if missing_comparison_difficulties:
        comparison_blockers.append("missing comparison difficulties: " + ", ".join(missing_comparison_difficulties))
    if tag_count < MIN_COMPARISON_TAGS:
        comparison_blockers.append(f"only {tag_count} tag(s), expected at least {MIN_COMPARISON_TAGS}")
    comparison_ready = ready and not comparison_blockers
    return {
        "status": "pass" if ready else "warn",
        "comparison_status": "pass" if comparison_ready else "warn",
        "decision": "suite_has_representative_prompt_coverage" if ready else "expand_prompt_suite_before_model_quality_claims",
        "comparison_decision": "suite_ready_for_repeated_checkpoint_comparison"
        if comparison_ready
        else "prefer_standard_suite_before_checkpoint_quality_claims",
        "case_count": case_count,
        "task_type_count": len(observed_task_types),
        "difficulty_count": len(observed_difficulties),
        "tag_count": tag_count,
        "observed_task_types": observed_task_types,
        "observed_difficulties": observed_difficulties,
        "observed_tags": observed_tags,
        "recommended_task_types": list(RECOMMENDED_TASK_TYPES),
        "recommended_difficulties": list(RECOMMENDED_DIFFICULTIES),
        "comparison_recommended_difficulties": list(COMPARISON_RECOMMENDED_DIFFICULTIES),
        "min_recommended_cases": MIN_RECOMMENDED_CASES,
        "min_recommended_tags": MIN_RECOMMENDED_TAGS,
        "min_comparison_cases": MIN_COMPARISON_CASES,
        "min_comparison_task_types": MIN_COMPARISON_TASK_TYPES,
        "min_comparison_tags": MIN_COMPARISON_TAGS,
        "missing_recommended_task_types": missing_task_types,
        "missing_recommended_difficulties": missing_difficulties,
        "missing_comparison_difficulties": missing_comparison_difficulties,
        "blockers": blockers,
        "comparison_blockers": comparison_blockers,
    }


def _design_summary(
    results: list[PromptResult],
    *,
    suite_name: str | None,
    suite_version: str | None,
    suite_description: str | None,
    suite_language: str | None,
) -> dict[str, Any]:
    from minigpt.eval_suite_design import summarize_prompt_suite_design

    return summarize_prompt_suite_design(
        {
            "suite_name": suite_name,
            "suite_version": suite_version,
            "description": suite_description,
            "language": suite_language,
            "cases": [
                {
                    "name": result.name,
                    "prompt": result.prompt,
                    "max_new_tokens": result.max_new_tokens,
                    "temperature": result.temperature,
                    "top_k": result.top_k,
                    "seed": result.seed,
                    "task_type": result.task_type,
                    "difficulty": result.difficulty,
                    "expected_behavior": result.expected_behavior,
                    "tags": list(result.tags),
                }
                for result in results
            ],
        }
    )


def _summary_by(results: list[PromptResult], attribute: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[PromptResult]] = {}
    for result in results:
        key = str(getattr(result, attribute) or "unknown")
        buckets.setdefault(key, []).append(result)
    summaries = []
    for key in sorted(buckets):
        items = buckets[key]
        summaries.append(
            {
                "key": key,
                "case_count": len(items),
                "avg_continuation_chars": _avg(result.char_count for result in items),
                "avg_unique_chars": _avg(result.unique_char_count for result in items),
            }
        )
    return summaries


def _avg(values: Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 4)
