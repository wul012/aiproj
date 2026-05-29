from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_balanced_corpus import (
    BALANCED_CORPUS_PATTERNS,
    build_model_capability_required_term_balanced_corpus,
    build_required_term_balanced_corpus,
    locate_model_capability_required_term_balanced_corpus_source,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_balanced_corpus,
)
from minigpt.model_capability_required_term_balanced_corpus_artifacts import (
    render_model_capability_required_term_balanced_corpus_markdown,
    render_model_capability_required_term_balanced_corpus_text,
    write_model_capability_required_term_balanced_corpus_outputs,
)


def test_balanced_corpus_builds_ready_candidate_from_seed_stability_source(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)

    report = build_model_capability_required_term_balanced_corpus(
        read_json_report(source),
        out_dir=tmp_path / "balanced",
        source_path=source,
        repeat=3,
        generated_at="2026-05-29T00:00:00Z",
    )
    text = render_model_capability_required_term_balanced_corpus_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_balanced_corpus_candidate_ready"
    assert report["summary"]["term_line_balance_ready"] is True
    assert report["summary"]["unique_line_rate"] > report["summary"]["legacy_unique_line_rate"]
    assert report["summary"]["term_line_spread"] == 0
    assert "balanced_corpus_decision=balanced_corpus_candidate_ready" in text
    assert resolve_exit_code(report, require_pass=True) == 0
    assert (tmp_path / "balanced" / "required_term_balanced_corpus.txt").is_file()


def test_balanced_corpus_builder_emits_all_patterns_without_duplicate_lines() -> None:
    corpus, rows = build_required_term_balanced_corpus(
        [
            {"case": "alpha", "term": "data", "scaffold_prompt": "Data:"},
            {"case": "beta", "term": "model", "scaffold_prompt": "Model:"},
        ],
        repeat=2,
    )
    lines = [line for line in corpus.splitlines() if "pattern=" in line]

    assert len(rows) == 2
    assert rows[0]["line_count"] == 2 * len(BALANCED_CORPUS_PATTERNS)
    assert len(lines) == len(set(lines))
    for pattern in BALANCED_CORPUS_PATTERNS:
        assert f"pattern={pattern}" in corpus


def test_balanced_corpus_summary_detects_review_needed_when_lines_repeat() -> None:
    summary = summarize_required_term_balanced_corpus(
        "header\npattern=direct|term=data\npattern=direct|term=data\n",
        [{"term": "data", "line_count": 2}],
        "header\nterm=data\nterm=data\n",
        repeat=1,
    )

    assert summary["balanced_corpus_decision"] == "balanced_corpus_candidate_needs_review"
    assert summary["duplicate_line_count"] == 1


def test_balanced_corpus_reports_missing_micro_source(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_required_term_split_seed_stability.json"
    write_json(
        source,
        {
            "status": "pass",
            "source_required_term_micro_training": str(tmp_path / "missing.json"),
        },
    )

    report = build_model_capability_required_term_balanced_corpus(
        read_json_report(source),
        out_dir=tmp_path / "balanced",
        source_path=source,
    )

    assert report["status"] == "fail"
    assert "source required-term micro-training report could not be resolved" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_balanced_corpus_writes_all_outputs(tmp_path: Path) -> None:
    source = write_micro_training_fixture(tmp_path)
    report = build_model_capability_required_term_balanced_corpus(
        read_json_report(source),
        out_dir=tmp_path / "balanced",
        source_path=source,
        repeat=2,
    )

    outputs = write_model_capability_required_term_balanced_corpus_outputs(report, tmp_path / "balanced")
    markdown = render_model_capability_required_term_balanced_corpus_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["example_count"] == 3
    assert "MiniGPT Model Capability Required-Term Balanced Corpus" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_balanced_corpus_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)

    assert locate_model_capability_required_term_balanced_corpus_source(source) == source
    assert locate_model_capability_required_term_balanced_corpus_source(source.parent) == source


def write_seed_stability_fixture(root: Path) -> Path:
    micro = write_micro_training_fixture(root)
    source = root / "model_capability_required_term_split_seed_stability.json"
    write_json(
        source,
        {
            "status": "pass",
            "source_required_term_micro_training": str(micro),
            "summary": {"seed_stability_decision": "train_slice_uptake_partial_without_holdout"},
        },
    )
    return source


def write_micro_training_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_micro_training.json"
    write_json(
        source,
        {
            "title": "MiniGPT model capability required-term micro-training",
            "status": "pass",
            "examples": [
                {"case": "alpha", "task_type": "qa", "term": "data", "scaffold_prompt": "Data:"},
                {"case": "beta", "task_type": "summary", "term": "model", "scaffold_prompt": "Model:"},
                {"case": "gamma", "task_type": "format", "term": "token", "scaffold_prompt": "Token:"},
            ],
        },
    )
    return source


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
