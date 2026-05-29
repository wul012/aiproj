from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_coverage import (
    build_model_capability_required_term_coverage,
    locate_model_capability_rubric_signal_audit,
    read_json_report,
    summarize_required_term_coverage,
)
from minigpt.model_capability_required_term_coverage_artifacts import (
    render_model_capability_required_term_coverage_markdown,
    render_model_capability_required_term_coverage_text,
    write_model_capability_required_term_coverage_outputs,
)
from scripts.audit_model_capability_required_term_coverage import resolve_exit_code


def test_required_term_coverage_detects_terms_present_but_not_generated(tmp_path: Path) -> None:
    source = write_coverage_fixture(tmp_path, corpus_text="data validation concise classify blocked")

    report = build_model_capability_required_term_coverage(
        read_json_report(source),
        out_dir=tmp_path / "coverage",
        source_path=source,
        search_base=tmp_path,
        generated_at="2026-05-29T00:00:00Z",
    )
    summary = report["summary"]
    text = render_model_capability_required_term_coverage_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_coverage_audit_ready"
    assert summary["coverage_decision"] == "required_terms_present_but_not_generated"
    assert summary["corpus_missing_term_row_count"] == 0
    assert summary["unique_missing_term_count"] == 5
    assert "coverage_decision=required_terms_present_but_not_generated" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_required_term_coverage_detects_mixed_corpus_coverage(tmp_path: Path) -> None:
    source = write_coverage_fixture(tmp_path, corpus_text="data concise")

    report = build_model_capability_required_term_coverage(
        read_json_report(source),
        out_dir=tmp_path / "coverage",
        source_path=source,
        search_base=tmp_path,
    )
    summary = report["summary"]

    assert report["status"] == "pass"
    assert summary["coverage_decision"] == "mixed_required_term_coverage"
    assert summary["corpus_missing_unique_terms"] == ["blocked", "classify", "validation"]


def test_required_term_coverage_reports_missing_source_material(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_rubric_signal_audit.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {"decision": "rubric_required_terms_dominate_flat_scores"},
            "cases": [
                {
                    "seed": 1337,
                    "case": "missing-source",
                    "last_missing_terms": ["data"],
                    "last_failed_checks": ["must_include"],
                    "source_diagnostic": "missing.json",
                }
            ],
        },
    )

    report = build_model_capability_required_term_coverage(
        read_json_report(source),
        out_dir=tmp_path / "coverage",
        source_path=source,
        search_base=tmp_path,
    )

    assert report["status"] == "fail"
    assert report["failed_count"] == 1
    assert "case missing-source required-term source material is incomplete" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_required_term_coverage_writes_all_outputs(tmp_path: Path) -> None:
    source = write_coverage_fixture(tmp_path, corpus_text="data validation concise classify blocked")
    report = build_model_capability_required_term_coverage(
        read_json_report(source),
        out_dir=tmp_path / "coverage",
        source_path=source,
        search_base=tmp_path,
    )

    outputs = write_model_capability_required_term_coverage_outputs(report, tmp_path / "coverage")
    markdown = render_model_capability_required_term_coverage_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["term_row_count"] == 5
    assert "classification-risk-level" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Coverage" in markdown
    assert "required_terms_present_but_not_generated" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_required_term_coverage_helpers_accept_file_or_directory(tmp_path: Path) -> None:
    source = write_coverage_fixture(tmp_path, corpus_text="data validation concise classify blocked")

    assert locate_model_capability_rubric_signal_audit(source) == source
    assert locate_model_capability_rubric_signal_audit(source.parent) == source


def test_summarize_required_term_coverage_handles_empty_rows() -> None:
    summary = summarize_required_term_coverage([], [])

    assert summary["coverage_decision"] == "no_required_term_gap"
    assert summary["missing_term_row_count"] == 0


def write_coverage_fixture(root: Path, *, corpus_text: str) -> Path:
    diag = root / "seeds" / "seed-1337" / "token-cap-12" / "stall-diagnostic" / "model_capability_stall_diagnostic.json"
    rung = diag.parent.parent / "ladder" / "rungs" / "max-iters-4"
    write_json(diag, {"status": "pass"})
    write_json(
        rung / "standard-zh-capped-suite.json",
        {
            "cases": [
                {
                    "name": "classification-risk-level",
                    "prompt": "Classify whether the release is blocked.",
                    "expected_behavior": "Must include classify, blocked, data, validation, and concise reasoning.",
                }
            ]
        },
    )
    (rung / "tiny_corpus.txt").write_text(corpus_text, encoding="utf-8")
    source = root / "model_capability_rubric_signal_audit.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {"decision": "rubric_required_terms_dominate_flat_scores"},
            "cases": [
                {
                    "seed": 1337,
                    "token_cap": 12,
                    "case": "classification-risk-level",
                    "task_type": "classification",
                    "stall_reason": "required_terms_missing",
                    "last_failed_checks": ["must_include"],
                    "last_missing_terms": ["classify", "blocked", "data", "validation", "concise"],
                    "source_diagnostic": str(diag),
                }
            ],
        },
    )
    return source


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
