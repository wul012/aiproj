from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_scaffold_probe import (
    REQUIRED_TERM_SCAFFOLD_PROBE_JSON_FILENAME,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_MICRO_TRAINING_JSON_FILENAME = "model_capability_required_term_micro_training.json"
REQUIRED_TERM_MICRO_TRAINING_TEXT_FILENAME = "model_capability_required_term_micro_training.txt"
REQUIRED_TERM_MICRO_TRAINING_MARKDOWN_FILENAME = "model_capability_required_term_micro_training.md"
REQUIRED_TERM_MICRO_TRAINING_HTML_FILENAME = "model_capability_required_term_micro_training.html"
REQUIRED_TERM_MICRO_TRAINING_CORPUS_FILENAME = "required_term_micro_corpus.txt"

ROOT = Path(__file__).resolve().parents[2]

TrainFunc = Callable[[dict[str, Any]], dict[str, Any]]
GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_scaffold_probe(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_SCAFFOLD_PROBE_JSON_FILENAME
    return source


def build_model_capability_required_term_micro_training(
    scaffold_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    max_iters: int = 300,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 32,
    learning_rate: float = 0.02,
    term_repeat: int = 24,
    max_new_tokens: int = 8,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 483,
    case_limit: int | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    examples = _select_micro_examples(scaffold_report, case_limit=case_limit)
    issues = _input_issues(scaffold_report, examples)
    corpus_text = build_required_term_micro_corpus(examples, repeat=term_repeat)
    corpus_path = root / REQUIRED_TERM_MICRO_TRAINING_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    train_dir = root / "micro-run"
    training = _train_micro_checkpoint(
        {
            "corpus_path": str(corpus_path),
            "train_dir": str(train_dir),
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "seed": generation_seed,
            "device": device,
            "sample_prompt": _sample_prompt(examples),
        },
        train_func,
    )
    if training.get("status") != "pass":
        issues.append("micro training command did not complete successfully")

    generation_rows: list[dict[str, Any]] = []
    if training.get("status") == "pass":
        generation_rows = [
            _generation_row(
                example,
                training,
                index=index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=generation_seed,
                device=device,
                generate_func=generate_func,
            )
            for index, example in enumerate(examples)
        ]

    summary = summarize_required_term_micro_training(examples, generation_rows, training)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term micro-training",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_scaffold_probe": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "term_repeat": term_repeat,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "case_limit": case_limit,
            "device": device,
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
            "repeat": term_repeat,
        },
        "training": training,
        "summary": summary,
        "example_count": len(examples),
        "examples": examples,
        "generation_count": len(generation_rows),
        "generation_rows": generation_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_required_term_micro_corpus(examples: list[dict[str, Any]], *, repeat: int) -> str:
    repeat_count = max(1, int(repeat))
    lines = [
        "MiniGPT required-term micro training corpus.",
        "Each short scaffold is paired with the exact required term to test targeted continuation uptake.",
    ]
    for example in examples:
        term = str(example.get("term") or "")
        prompt = str(example.get("scaffold_prompt") or f"{term}:")
        case = str(example.get("case") or "unknown-case")
        for _ in range(repeat_count):
            lines.append(f"{prompt}{term}")
            lines.append(f"{prompt} {term}")
            lines.append(f"{case}|{prompt}{term}")
    return "\n".join(lines) + "\n"


def summarize_required_term_micro_training(
    examples: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    training: dict[str, Any],
) -> dict[str, Any]:
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in generation_rows)
    generated_hits = sum(int(row.get("generated_hit_count") or 0) for row in generation_rows)
    case_hits = sum(1 for row in generation_rows if int(row.get("continuation_hit_count") or 0) > 0)
    return {
        "micro_training_decision": _micro_training_decision(examples, generation_rows, continuation_hits, training),
        "example_count": len(examples),
        "required_term_count": sum(1 for row in examples if row.get("term")),
        "generation_count": len(generation_rows),
        "continuation_hit_count": continuation_hits,
        "generated_hit_count": generated_hits,
        "prompt_hit_count": sum(int(row.get("prompt_hit_count") or 0) for row in generation_rows),
        "case_with_continuation_hit_count": case_hits,
        "continuation_hit_rate": round(case_hits / len(generation_rows), 4) if generation_rows else 0.0,
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "train_config_exists": bool(training.get("train_config_exists")),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _select_micro_examples(scaffold_report: dict[str, Any], *, case_limit: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(scaffold_report.get("probe_rows")):
        terms = [str(term) for term in row.get("terms") or [] if str(term).strip()]
        if not terms:
            continue
        if row.get("prompt_truncated") or row.get("prompt_over_block"):
            continue
        term = sorted(terms, key=lambda value: (len(value), value))[0]
        prompt = str(row.get("scaffold_prompt") or f"{term}:")
        rows.append(
            {
                "seed": row.get("seed"),
                "token_cap": row.get("token_cap"),
                "case": row.get("case"),
                "task_type": row.get("task_type"),
                "source_max_iters": row.get("max_iters"),
                "term": term,
                "scaffold_prompt": prompt,
                "scaffold_prompt_char_count": len(prompt),
                "source_checkpoint_path": row.get("checkpoint_path"),
                "source_tokenizer_path": row.get("tokenizer_path"),
                "source_eval_suite_path": row.get("eval_suite_path"),
            }
        )
    rows.sort(key=lambda item: (str(item.get("seed") or ""), str(item.get("case") or ""), str(item.get("term") or "")))
    if case_limit is not None and case_limit >= 0:
        return rows[:case_limit]
    return rows


def _input_issues(scaffold_report: dict[str, Any], examples: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not scaffold_report:
        issues.append("source scaffold probe report is missing or invalid")
    if scaffold_report and scaffold_report.get("status") != "pass":
        issues.append("source scaffold probe report is not pass")
    if as_dict(scaffold_report.get("summary")).get("probe_decision") != "explicit_scaffold_still_no_required_term_uptake":
        issues.append("source scaffold probe is not the no-uptake baseline expected by this repeat")
    if not examples:
        issues.append("source scaffold probe has no eligible non-truncated examples")
    return issues


def _train_micro_checkpoint(context: dict[str, Any], train_func: TrainFunc | None) -> dict[str, Any]:
    if train_func is not None:
        return train_func(context)
    train_dir = Path(str(context["train_dir"]))
    logs_dir = train_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "train.py"),
        "--data",
        str(context["corpus_path"]),
        "--out-dir",
        str(train_dir),
        "--device",
        str(context["device"]),
        "--tokenizer",
        "char",
        "--max-iters",
        str(context["max_iters"]),
        "--eval-interval",
        str(max(1, int(context["max_iters"]) // 4)),
        "--eval-iters",
        str(context["eval_iters"]),
        "--batch-size",
        str(context["batch_size"]),
        "--block-size",
        str(context["block_size"]),
        "--n-layer",
        str(context["n_layer"]),
        "--n-head",
        str(context["n_head"]),
        "--n-embd",
        str(context["n_embd"]),
        "--learning-rate",
        str(context["learning_rate"]),
        "--seed",
        str(context["seed"]),
        "--sample-prompt",
        str(context["sample_prompt"]),
        "--sample-tokens",
        "8",
        "--sample-temperature",
        "0.2",
        "--sample-top-k",
        "1",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / "train_stdout.txt"
    stderr_path = logs_dir / "train_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return _training_result(train_dir, command, completed.returncode, stdout_path, stderr_path)


def _training_result(
    train_dir: Path,
    command: list[str],
    returncode: int,
    stdout_path: Path | None,
    stderr_path: Path | None,
) -> dict[str, Any]:
    checkpoint_path = train_dir / "checkpoint.pt"
    tokenizer_path = train_dir / "tokenizer.json"
    metrics_path = train_dir / "metrics.jsonl"
    train_config_path = train_dir / "train_config.json"
    return {
        "status": "pass" if returncode == 0 and checkpoint_path.is_file() and tokenizer_path.is_file() else "fail",
        "returncode": returncode,
        "command": command,
        "command_text": " ".join(command),
        "stdout": str(stdout_path) if stdout_path else None,
        "stderr": str(stderr_path) if stderr_path else None,
        "run_dir": str(train_dir),
        "checkpoint_path": str(checkpoint_path),
        "tokenizer_path": str(tokenizer_path),
        "metrics_path": str(metrics_path),
        "train_config_path": str(train_config_path),
        "checkpoint_exists": checkpoint_path.is_file(),
        "tokenizer_exists": tokenizer_path.is_file(),
        "metrics_exists": metrics_path.is_file(),
        "train_config_exists": train_config_path.is_file(),
        "train_config": read_json_report(train_config_path),
    }


def _generation_row(
    example: dict[str, Any],
    training: dict[str, Any],
    *,
    index: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    prompt = str(example.get("scaffold_prompt") or "")
    term = str(example.get("term") or "")
    request = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": generation_seed + index,
        "checkpoint_path": training.get("checkpoint_path"),
        "tokenizer_path": training.get("tokenizer_path"),
        "device": device,
    }
    response = _generate(request, generate_func)
    generated = str(response.get("generated") or "")
    prompt_truncated = not generated.startswith(prompt)
    continuation = generated[len(prompt) :] if not prompt_truncated else str(response.get("continuation") or "")
    return {
        **example,
        "generation_seed": request["seed"],
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "generated": generated,
        "continuation": continuation,
        "prompt_truncated": prompt_truncated,
        "prompt_hit_count": _hit_count(prompt, [term]),
        "generated_hit_count": _hit_count(generated, [term]),
        "continuation_hit_count": _hit_count(continuation, [term]),
        "generated_preview": _preview(generated),
        "continuation_preview": _preview(continuation),
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


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_micro_training"
    if summary.get("continuation_hit_count"):
        return "required_term_micro_training_uptake_observed"
    return "required_term_micro_training_completed_without_uptake"


def _micro_training_decision(
    examples: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    continuation_hits: int,
    training: dict[str, Any],
) -> str:
    if training.get("status") != "pass":
        return "micro_training_run_failed"
    if not examples:
        return "no_required_term_examples"
    if not generation_rows:
        return "micro_training_generation_missing"
    if continuation_hits > 0:
        return "targeted_micro_training_partially_learned_required_terms"
    return "targeted_micro_training_still_no_required_term_uptake"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("continuation_hit_count"):
        return "targeted_micro_training_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The targeted micro-training repeat did not complete, so no model capability conclusion is available."
    if summary.get("continuation_hit_count"):
        return "A tiny model trained on explicit scaffold-to-term examples emitted required terms in continuation for at least one probe."
    return "The targeted micro-training run completed, but the generated continuations still did not include the required terms."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the micro-training run before comparing model capability"
    if summary.get("continuation_hit_count"):
        return "repeat with a held-out required-term slice and compare whether the signal survives beyond copied scaffolds"
    return "increase targeted iterations or simplify the corpus before expanding benchmark scope"


def _sample_prompt(examples: list[dict[str, Any]]) -> str:
    for example in examples:
        prompt = str(example.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "data:"


def _hit_count(text: Any, terms: list[str]) -> int:
    lowered = str(text or "").casefold()
    return sum(1 for term in terms if str(term).casefold() in lowered)


def _preview(value: Any, limit: int = 90) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."
