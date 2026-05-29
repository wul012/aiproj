from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_uptake import (
    build_model_capability_required_term_uptake,
    locate_model_capability_required_term_coverage,
    read_json_report,
    summarize_required_term_uptake,
)
from minigpt.model_capability_required_term_uptake_artifacts import (
    render_model_capability_required_term_uptake_markdown,
    render_model_capability_required_term_uptake_text,
    write_model_capability_required_term_uptake_outputs,
)
from scripts.audit_model_capability_required_term_uptake import resolve_exit_code


def test_required_term_uptake_detects_never_generated_terms(tmp_path: Path) -> None:
    source = write_uptake_fixture(tmp_path, continuation="tiny output without target words")

    report = build_model_capability_required_term_uptake(
        read_json_report(source),
        out_dir=tmp_path / "uptake",
        source_path=source,
        search_base=tmp_path,
        generated_at="2026-05-29T00:00:00Z",
    )
    summary = report["summary"]
    text = render_model_capability_required_term_uptake_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_uptake_audit_ready"
    assert summary["uptake_decision"] == "required_terms_never_generated"
    assert summary["generation_observation_count"] == 2
    assert summary["continuation_hit_count"] == 0
    assert summary["expected_hit_count"] == 2
    assert "uptake_decision=required_terms_never_generated" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_required_term_uptake_detects_last_rung_partial_generation(tmp_path: Path) -> None:
    source = write_uptake_fixture(tmp_path, continuation="tiny output includes data", term="data")

    report = build_model_capability_required_term_uptake(
        read_json_report(source),
        out_dir=tmp_path / "uptake",
        source_path=source,
        search_base=tmp_path,
    )

    assert report["summary"]["uptake_decision"] == "last_rung_required_terms_partially_generated"
    assert report["summary"]["last_rung_continuation_hit_count"] == 1


def test_required_term_uptake_reports_missing_eval_suite_sources(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_required_term_coverage.json"
    write_json(
        source,
        {
            "summary": {"coverage_decision": "required_terms_present_but_not_generated"},
            "term_rows": [
                {
                    "seed": 1337,
                    "case": "classification-risk-level",
                    "term": "data",
                    "token_cap_root": str(tmp_path / "missing-token-cap"),
                }
            ],
        },
    )

    report = build_model_capability_required_term_uptake(
        read_json_report(source),
        out_dir=tmp_path / "uptake",
        source_path=source,
        search_base=tmp_path,
    )

    assert report["status"] == "fail"
    assert "case classification-risk-level has no archived eval-suite generation source" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_required_term_uptake_writes_all_outputs(tmp_path: Path) -> None:
    source = write_uptake_fixture(tmp_path, continuation="tiny output without target words")
    report = build_model_capability_required_term_uptake(
        read_json_report(source),
        out_dir=tmp_path / "uptake",
        source_path=source,
        search_base=tmp_path,
    )

    outputs = write_model_capability_required_term_uptake_outputs(report, tmp_path / "uptake")
    markdown = render_model_capability_required_term_uptake_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["observation_count"] == 2
    assert "classification-risk-level" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Uptake" in markdown
    assert "required_terms_never_generated" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_required_term_uptake_helpers_accept_file_or_directory(tmp_path: Path) -> None:
    source = write_uptake_fixture(tmp_path, continuation="tiny output without target words")

    assert locate_model_capability_required_term_coverage(source) == source
    assert locate_model_capability_required_term_coverage(source.parent) == source


def test_summarize_required_term_uptake_handles_empty_rows() -> None:
    summary = summarize_required_term_uptake([], [], [])

    assert summary["uptake_decision"] == "no_required_term_gap"
    assert summary["generation_observation_count"] == 0


def write_uptake_fixture(root: Path, *, continuation: str, term: str = "data") -> Path:
    token_cap_root = root / "seeds" / "seed-1337" / "token-cap-12"
    write_eval_suite(token_cap_root, max_iters=1, continuation="tiny output without target words", term=term)
    write_eval_suite(token_cap_root, max_iters=4, continuation=continuation, term=term)
    source = root / "model_capability_required_term_coverage.json"
    write_json(
        source,
        {
            "summary": {"coverage_decision": "required_terms_present_but_not_generated"},
            "term_rows": [
                {
                    "seed": 1337,
                    "token_cap": 12,
                    "case": "classification-risk-level",
                    "task_type": "classification",
                    "stall_reason": "required_terms_missing",
                    "term": term,
                    "token_cap_root": str(token_cap_root),
                }
            ],
        },
    )
    return source


def write_eval_suite(token_cap_root: Path, *, max_iters: int, continuation: str, term: str) -> None:
    path = token_cap_root / "ladder" / "rungs" / f"max-iters-{max_iters}" / "run" / "eval_suite" / "eval_suite.json"
    write_json(
        path,
        {
            "results": [
                {
                    "name": "classification-risk-level",
                    "prompt": "Classify the release state.",
                    "expected_behavior": f"Must include {term} and validation.",
                    "generated": "Classify the release state." + continuation,
                    "continuation": continuation,
                    "char_count": len(continuation),
                    "unique_char_count": len(set(continuation)),
                }
            ]
        },
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
