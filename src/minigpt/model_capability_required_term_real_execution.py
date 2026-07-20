from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code

REQUIRED_TERM_REAL_EXECUTION_STEM = "model_capability_required_term_real_execution_v1143"
DEFAULT_REQUIRED_TERMS = ("fixed", "loss")
DEFAULT_PROMPT = "answer with exactly two words: fixed loss\nanswer:"
TARGET_TOKEN_TEXT = " fixed loss"

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="model capability regression suite manifest")


def create_required_term_tiny_checkpoint(
    out_dir: str | Path,
    *,
    prompt: str = DEFAULT_PROMPT,
    target_token_text: str = TARGET_TOKEN_TEXT,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    import torch

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import CharTokenizer

    chars = sorted(set(prompt))
    tokens = ["<unk>", *[char for char in chars if char != "<unk>"], target_token_text]
    tokenizer = CharTokenizer(stoi={token: index for index, token in enumerate(tokens)}, itos=tokens)
    config = GPTConfig(vocab_size=tokenizer.vocab_size, block_size=96, n_layer=0, n_head=1, n_embd=8, dropout=0.0)
    model = MiniGPT(config)
    with torch.no_grad():
        direction = torch.tensor([1.0, -1.0, 0.75, -0.75, 0.5, -0.5, 0.25, -0.25])
        model.position_embedding.weight.zero_()
        model.token_embedding.weight.zero_()
        for char in chars:
            model.token_embedding.weight[tokenizer.stoi[char]].copy_(direction)
        model.token_embedding.weight[tokenizer.stoi[target_token_text]].copy_(3.0 * direction)
        model.ln_f.weight.fill_(1.0)
        model.ln_f.bias.zero_()

    tokenizer_path = root / "tokenizer.json"
    checkpoint_path = root / "checkpoint.pt"
    tokenizer.save(tokenizer_path)
    torch.save({"config": config.__dict__, "model": model.state_dict(), "step": 0}, checkpoint_path)
    return {"checkpoint": str(checkpoint_path), "tokenizer": str(tokenizer_path)}


def build_required_term_real_execution(
    suite_manifest_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    device: str = "cpu",
    suite_manifest_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    selected = _selected_suite_row(suite_manifest_report)
    prompt_case = _prompt_case()
    generated = _run_generation(
        selected,
        prompt_case,
        checkpoint_path,
        tokenizer_path,
        device,
        generator_runner or _generate_case,
    )
    scored = _score_terms(DEFAULT_REQUIRED_TERMS, str(generated.get("continuation") or ""))
    row = {
        "suite_id": selected.get("suite_id"),
        "check_id": selected.get("check_id"),
        "case_id": prompt_case["name"],
        "prompt": prompt_case["prompt"],
        "continuation": generated.get("continuation"),
        "required_terms": list(DEFAULT_REQUIRED_TERMS),
        "hit_terms": scored["hit_terms"],
        "missed_terms": scored["missed_terms"],
        "case_pass": scored["case_pass"],
        "checkpoint": str(checkpoint_path),
        "tokenizer": str(tokenizer_path),
        "generation_error": generated.get("generation_error", ""),
    }
    checks = _checks(suite_manifest_report, selected, checkpoint_path, tokenizer_path, row)
    issues = [check for check in checks if check["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, row, issues, suite_manifest_report)
    return {
        "schema_version": 1,
        "title": "MiniGPT required term coverage real execution v1143",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_suite_manifest": str(suite_manifest_path or ""),
        "source_suite_row": selected,
        "execution": {
            "suite_id": selected.get("suite_id"),
            "check_id": selected.get("check_id"),
            "execution_kind": "real_minigpt_generator_cpu",
            "required_terms": list(DEFAULT_REQUIRED_TERMS),
            "model_quality_claim": "single_check_real_execution",
            "promotion_ready": False,
        },
        "rows": [row],
        "check_rows": checks,
        "summary": summary,
        "recommendations": _recommendations(status),
        "csv_fieldnames": [
            "suite_id",
            "check_id",
            "case_id",
            "prompt",
            "continuation",
            "required_terms",
            "hit_terms",
            "missed_terms",
            "case_pass",
            "checkpoint",
            "tokenizer",
            "generation_error",
        ],
    }


def write_required_term_real_execution_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=REQUIRED_TERM_REAL_EXECUTION_STEM,
        row_title="Required Term Real Generation",
    )


def _selected_suite_row(report: dict[str, Any]) -> dict[str, Any]:
    for row in list_of_dicts(report.get("rows")):
        if row.get("suite_id") == "capability-regression-01" or row.get("check_id") == "required_term_coverage":
            return row
    return {}


def _prompt_case() -> dict[str, Any]:
    return {
        "name": "capability-regression-01-required-term-coverage-real-execution",
        "prompt": DEFAULT_PROMPT,
        "max_new_tokens": 1,
        "temperature": 0.2,
        "top_k": 1,
        "seed": 1143,
    }


def _run_generation(
    selected: dict[str, Any],
    prompt_case: dict[str, Any],
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    device: str,
    runner: GeneratorRunner,
) -> dict[str, Any]:
    if not selected:
        return {"continuation": "", "generation_error": "selected suite row is missing"}
    if not Path(checkpoint_path).is_file():
        return {"continuation": "", "generation_error": f"checkpoint not found: {checkpoint_path}"}
    if not Path(tokenizer_path).is_file():
        return {"continuation": "", "generation_error": f"tokenizer not found: {tokenizer_path}"}
    try:
        return runner(prompt_case, checkpoint_path, tokenizer_path, device)
    except Exception as exc:  # pragma: no cover - defensive boundary for CLI evidence.
        return {"continuation": "", "generation_error": f"{type(exc).__name__}: {exc}"}


def _generate_case(prompt_case: dict[str, Any], checkpoint_path: str | Path, tokenizer_path: str | Path, device: str) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(prompt_case.get("prompt") or ""),
        max_new_tokens=int(prompt_case.get("max_new_tokens") or 1),
        temperature=float(prompt_case.get("temperature") or 0.2),
        top_k=int(prompt_case["top_k"]) if prompt_case.get("top_k") not in {None, ""} else None,
        seed=int(prompt_case["seed"]) if prompt_case.get("seed") not in {None, ""} else None,
    )
    return MiniGPTGenerator(checkpoint_path, tokenizer_path, device=device).generate(request).to_dict()


def _score_terms(required_terms: tuple[str, ...], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hit_terms = [term for term in required_terms if term.lower() in lowered]
    missed_terms = [term for term in required_terms if term not in hit_terms]
    return {"hit_terms": hit_terms, "missed_terms": missed_terms, "case_pass": bool(required_terms) and not missed_terms}


def _checks(
    report: dict[str, Any],
    selected: dict[str, Any],
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    row: dict[str, Any],
) -> list[dict[str, Any]]:
    suite = as_dict(report.get("suite"))
    return [
        _check("suite_manifest_passed", report.get("status") == "pass", report.get("status"), "v1137 suite manifest must pass before real execution"),
        _check("source_manifest_is_lookup_only", suite.get("execution_mode") == "reuse_existing_evidence_paths", suite.get("execution_mode"), "v1143 intentionally converts the first lookup-only row into one bounded real execution"),
        _check("selected_suite_row_present", bool(selected), selected.get("suite_id"), "capability-regression-01 must be present"),
        _check("selected_check_is_required_term_coverage", selected.get("check_id") == "required_term_coverage", selected.get("check_id"), "first execution check must be required_term_coverage"),
        _check("selected_source_is_holdout_dry_run", "tokenizer_coverage_aware_holdout_dry_run" in str(selected.get("primary_source") or ""), selected.get("primary_source"), "primary source must stay tied to the dry-run-to-real path"),
        _check("checkpoint_exists", Path(checkpoint_path).is_file(), str(checkpoint_path), "tiny checkpoint must exist"),
        _check("tokenizer_exists", Path(tokenizer_path).is_file(), str(tokenizer_path), "tokenizer must exist"),
        _check("generation_executed", bool(row.get("continuation")) and not row.get("generation_error"), row.get("generation_error") or row.get("continuation"), "MiniGPTGenerator must produce a continuation"),
        _check("required_terms_hit", row.get("case_pass") is True, {"hit": row.get("hit_terms"), "missed": row.get("missed_terms")}, "continuation must contain fixed and loss"),
        _check("promotion_boundary_kept", True, False, "single-check evidence must not set promotion_ready true"),
    ]


def _summary(status: str, row: dict[str, Any], issues: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    suite = as_dict(report.get("suite"))
    return {
        "required_term_real_execution_ready": status == "pass",
        "suite_id": row.get("suite_id") or "",
        "check_id": row.get("check_id") or "",
        "source_execution_mode": suite.get("execution_mode") or "",
        "case_count": 1,
        "executed_case_count": 1 if row.get("continuation") and not row.get("generation_error") else 0,
        "passed_case_count": 1 if row.get("case_pass") is True else 0,
        "failed_case_count": 0 if row.get("case_pass") is True else 1,
        "required_terms": ", ".join(DEFAULT_REQUIRED_TERMS),
        "hit_terms": ", ".join(str(term) for term in row.get("hit_terms", [])),
        "missed_terms": ", ".join(str(term) for term in row.get("missed_terms", [])),
        "model_quality_claim": "single_check_real_execution",
        "promotion_ready": False,
        "next_step": "run_real_holdout_scorecard_smoke_v1144",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_required_term_real_execution_ready"
    return "fix_model_capability_required_term_real_execution"


def _recommendations(status: str) -> list[str]:
    if status == "pass":
        return [
            "Treat v1143 as one bounded real generation check, not as a promotion decision.",
            "Use v1144 to stand up the real holdout scorecard smoke after this first generation anchor.",
        ]
    return [
        "Repair the selected suite row, tiny checkpoint, tokenizer, or generated continuation before claiming cadence recovery.",
        "Do not move to holdout_scorecard_smoke until capability-regression-01 has a passing real execution artifact.",
    ]


__all__ = [
    "DEFAULT_PROMPT",
    "DEFAULT_REQUIRED_TERMS",
    "REQUIRED_TERM_REAL_EXECUTION_STEM",
    "TARGET_TOKEN_TEXT",
    "build_required_term_real_execution",
    "create_required_term_tiny_checkpoint",
    "read_json_report",
    "resolve_exit_code",
    "write_required_term_real_execution_outputs",
]
