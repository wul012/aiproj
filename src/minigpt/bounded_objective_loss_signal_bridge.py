from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_curriculum_patch_profile_sweep import CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


LOSS_SIGNAL_BRIDGE_JSON_FILENAME = "bounded_objective_loss_signal_bridge.json"
LOSS_SIGNAL_BRIDGE_CSV_FILENAME = "bounded_objective_loss_signal_bridge.csv"
LOSS_SIGNAL_BRIDGE_JSONL_FILENAME = "bounded_objective_loss_signal_bridge_examples.jsonl"
LOSS_SIGNAL_BRIDGE_CORPUS_FILENAME = "bounded_objective_loss_signal_bridge_corpus.txt"
LOSS_SIGNAL_BRIDGE_TEXT_FILENAME = "bounded_objective_loss_signal_bridge.txt"
LOSS_SIGNAL_BRIDGE_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge.md"
LOSS_SIGNAL_BRIDGE_HTML_FILENAME = "bounded_objective_loss_signal_bridge.html"


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def locate_profile_sweep(path: str | Path) -> Path:
    return _locate(path, CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME)


def build_bounded_objective_loss_signal_bridge(
    profile_sweep_report: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    profile_sweep_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge",
    generated_at: str | None = None,
) -> dict[str, Any]:
    sweep_summary = as_dict(profile_sweep_report.get("summary"))
    sweep_rows = list_of_dicts(profile_sweep_report.get("sweep_rows"))
    source_corpus = Path(source_corpus_path).read_text(encoding="utf-8")
    bridge_examples = _bridge_examples(sweep_rows)
    bridged_corpus = _bridge_corpus(source_corpus, bridge_examples)
    checks = _checks(profile_sweep_report, sweep_summary, sweep_rows, bridge_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    bridge = _bridge(status, bridge_examples, bridged_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_profile_sweep": str(profile_sweep_path or ""),
        "source_corpus": str(source_corpus_path),
        "profile_sweep_summary": sweep_summary,
        "source_signal_summary": _source_signal_summary(sweep_rows),
        "bridge_examples": bridge_examples if status == "pass" else [],
        "bridged_corpus_text": bridged_corpus if status == "pass" else "",
        "check_rows": checks,
        "loss_signal_bridge": bridge,
        "summary": _summary(status, checks, bridge_examples, source_corpus, bridged_corpus, bridge),
        "interpretation": _interpretation(status, bridge),
    }


def resolve_exit_code(report: dict[str, Any], *, require_bridge_ready: bool) -> int:
    return 1 if require_bridge_ready and report.get("status") != "pass" else 0


def _bridge_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    loss_rows = [row for row in rows if row.get("loss_hit") is True and row.get("fixed_hit") is not True]
    fixed_rows = [row for row in rows if row.get("fixed_hit") is True and row.get("loss_hit") is not True]
    for row in loss_rows:
        examples.extend(_loss_signal_examples(row))
    for row in fixed_rows[:6]:
        examples.append(_example(f"{_row_id(row)}-fixed-to-pair", "fixed_signal_pair_bridge", str(row.get("prompt") or ""), "fixed loss", row))
    examples.extend(_pair_reinforcement_examples())
    return examples


def _loss_signal_examples(row: dict[str, Any]) -> list[dict[str, Any]]:
    prompt = str(row.get("prompt") or "")
    return [
        _example(f"{_row_id(row)}-loss-to-pair", "loss_signal_pair_bridge", prompt, "fixed loss", row),
        _example(f"{_row_id(row)}-loss-prefix-repair", "loss_signal_prefix_repair", f"{prompt}\nloss", "fixed loss", row),
    ]


def _pair_reinforcement_examples() -> list[dict[str, Any]]:
    return [
        _example("pair-direct-repeat-a", "pair_reinforcement", "answer:", "fixed loss", {}),
        _example("pair-direct-repeat-b", "pair_reinforcement", "completion:", "fixed loss", {}),
        _example("fixed-loss-line-bridge", "pair_reinforcement", "fixed", "loss", {}),
        _example("loss-needs-fixed-context", "pair_reinforcement", "loss belongs with", "fixed loss", {}),
    ]


def _example(example_id: str, kind: str, prompt: str, completion: str, source_row: dict[str, Any]) -> dict[str, Any]:
    text = f"{prompt.rstrip()}\n{completion}".strip()
    return {
        "example_id": example_id,
        "kind": kind,
        "prompt": prompt,
        "completion": completion,
        "text": text,
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_profile_id": source_row.get("profile_id"),
        "source_case_id": source_row.get("case_id"),
        "source_continuation": source_row.get("continuation"),
        "purpose": _purpose(kind),
    }


def _checks(profile_sweep: dict[str, Any], summary: dict[str, Any], rows: list[dict[str, Any]], examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("profile_sweep_passed", profile_sweep.get("status") == "pass", profile_sweep.get("status"), "profile sweep must pass structurally"),
        _check("profile_sweep_ready", summary.get("bounded_objective_curriculum_patch_profile_sweep_ready") is True, summary.get("bounded_objective_curriculum_patch_profile_sweep_ready"), "profile sweep must be ready"),
        _check("loss_signal_present", int(summary.get("max_loss_hit_case_count") or 0) > 0, summary.get("max_loss_hit_case_count"), "bridge should only follow a profile sweep with loss signal"),
        _check("contract_not_recovered", summary.get("any_profile_recovered") is not True, summary.get("any_profile_recovered"), "bridge should not replace holdout if a profile already recovered the contract"),
        _check("sweep_rows_present", bool(rows), len(rows), "profile sweep rows must be present"),
        _check("bridge_examples_present", bool(examples), len(examples), "bridge examples must be generated"),
        _check("decoder_anchor_free", all(example.get("decoder_anchor") is False for example in examples), False, "bridge examples must stay no-anchor"),
    ]


def _bridge(status: str, examples: list[dict[str, Any]], corpus: str) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "bridge_example_count": len(examples) if ready else 0,
        "loss_signal_bridge_example_count": sum(1 for example in examples if str(example.get("kind")).startswith("loss_signal")) if ready else 0,
        "fixed_signal_bridge_example_count": sum(1 for example in examples if str(example.get("kind")).startswith("fixed_signal")) if ready else 0,
        "pair_reinforcement_example_count": sum(1 for example in examples if str(example.get("kind")) == "pair_reinforcement") if ready else 0,
        "decoder_anchor_example_count": 0,
        "bridged_corpus_char_count": len(corpus) if ready else 0,
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge" if ready else "repair_bounded_objective_loss_signal_bridge_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], examples: list[dict[str, Any]], source_corpus: str, bridged_corpus: str, bridge: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_ready": status == "pass",
        "bridge_example_count": bridge.get("bridge_example_count"),
        "loss_signal_bridge_example_count": bridge.get("loss_signal_bridge_example_count"),
        "fixed_signal_bridge_example_count": bridge.get("fixed_signal_bridge_example_count"),
        "pair_reinforcement_example_count": bridge.get("pair_reinforcement_example_count"),
        "decoder_anchor_example_count": 0,
        "original_corpus_char_count": len(source_corpus),
        "bridged_corpus_char_count": bridge.get("bridged_corpus_char_count"),
        "bridge_kinds": sorted({str(example.get("kind")) for example in examples}) if status == "pass" else [],
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "model_quality_claim": "bridge_corpus_only" if status == "pass" else "not_claimed",
        "proposed_next_artifact": bridge.get("proposed_next_artifact"),
        "next_step": bridge.get("next_step"),
    }


def _source_signal_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    loss_rows = [row for row in rows if row.get("loss_hit") is True and row.get("fixed_hit") is not True]
    fixed_rows = [row for row in rows if row.get("fixed_hit") is True and row.get("loss_hit") is not True]
    return {
        "loss_only_row_count": len(loss_rows),
        "fixed_only_row_count": len(fixed_rows),
        "loss_signal_case_ids": sorted({str(row.get("case_id") or "") for row in loss_rows}),
        "fixed_signal_case_ids": sorted({str(row.get("case_id") or "") for row in fixed_rows}),
        "loss_signal_profile_ids": sorted({str(row.get("profile_id") or "") for row in loss_rows}),
    }


def _bridge_corpus(source_corpus: str, examples: list[dict[str, Any]]) -> str:
    parts = [source_corpus.rstrip(), "# v860 loss signal bridge"]
    parts.extend(str(example["text"]) for example in examples)
    return "\n\n".join(parts).strip() + "\n"


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_ready"
    return "bounded_objective_loss_signal_bridge_blocked"


def _interpretation(status: str, bridge: dict[str, Any]) -> dict[str, Any]:
    if status == "pass":
        reason = "Loss appears in profile sweep rows, but fixed/loss co-occurrence still needs bridge training."
    else:
        reason = "The loss signal bridge inputs were not sufficient."
    return {
        "model_quality_claim": "bridge_corpus_only" if status == "pass" else "not_claimed",
        "reason": reason,
        "next_action": bridge.get("next_step"),
    }


def _locate(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    nested = source / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f"cannot locate {filename} under {source}")


def _row_id(row: dict[str, Any]) -> str:
    return (str(row.get("profile_id") or "profile") + "-" + str(row.get("case_id") or "case")).replace("_", "-")


def _purpose(kind: str) -> str:
    return {
        "loss_signal_pair_bridge": "turn a loss-only generation signal into the exact fixed loss pair",
        "loss_signal_prefix_repair": "teach that a loss prefix still needs fixed loss as the canonical pair",
        "fixed_signal_pair_bridge": "retain fixed while adding loss in the same completion",
        "pair_reinforcement": "repeat the exact bounded objective pair without decoder anchors",
    }.get(kind, "bridge fixed and loss without decoder anchors")


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


__all__ = [
    "LOSS_SIGNAL_BRIDGE_CORPUS_FILENAME",
    "LOSS_SIGNAL_BRIDGE_CSV_FILENAME",
    "LOSS_SIGNAL_BRIDGE_HTML_FILENAME",
    "LOSS_SIGNAL_BRIDGE_JSON_FILENAME",
    "LOSS_SIGNAL_BRIDGE_JSONL_FILENAME",
    "LOSS_SIGNAL_BRIDGE_MARKDOWN_FILENAME",
    "LOSS_SIGNAL_BRIDGE_TEXT_FILENAME",
    "build_bounded_objective_loss_signal_bridge",
    "locate_profile_sweep",
    "read_json_report",
    "resolve_exit_code",
]
