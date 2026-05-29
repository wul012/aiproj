from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_prompt_leading_corpus import (
    PROMPT_LEADING_PATTERNS,
    build_model_capability_required_term_prompt_leading_corpus,
    build_required_term_prompt_leading_corpus,
    locate_model_capability_required_term_prompt_leading_source,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_prompt_leading_corpus,
)
from minigpt.model_capability_required_term_prompt_leading_corpus_artifacts import (
    render_model_capability_required_term_prompt_leading_corpus_markdown,
    render_model_capability_required_term_prompt_leading_corpus_text,
    write_model_capability_required_term_prompt_leading_corpus_outputs,
)


def test_prompt_leading_corpus_builds_ready_candidate_from_v488_source(tmp_path: Path) -> None:
    source = write_balanced_training_fixture(tmp_path)

    report = build_model_capability_required_term_prompt_leading_corpus(
        read_json_report(source),
        out_dir=tmp_path / "prompt-leading",
        source_path=source,
        repeat=3,
        generated_at="2026-05-29T00:00:00Z",
    )
    text = render_model_capability_required_term_prompt_leading_corpus_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_prompt_leading_corpus_candidate_ready"
    assert report["summary"]["prompt_alignment_ready"] is True
    assert report["summary"]["previous_prompt_alignment_ready"] is False
    assert report["summary"]["previous_prompt_leading_line_count"] == 0
    assert report["summary"]["prompt_leading_line_count"] == 2 * 3 * len(PROMPT_LEADING_PATTERNS)
    assert "prompt_leading_corpus_decision=prompt_leading_corpus_candidate_ready" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_prompt_leading_corpus_lines_start_with_scaffold_prompt() -> None:
    corpus, rows = build_required_term_prompt_leading_corpus(
        [
            {"case": "alpha", "term": "data", "scaffold_prompt": "data:"},
            {"case": "beta", "term": "model", "scaffold_prompt": "model:"},
        ],
        repeat=2,
    )
    lines = [line for line in corpus.splitlines() if "pattern=" in line]

    assert len(rows) == 2
    assert rows[0]["line_count"] == 2 * len(PROMPT_LEADING_PATTERNS)
    assert all(line.startswith(("data:", "model:")) for line in lines)
    for pattern in PROMPT_LEADING_PATTERNS:
        assert f"pattern={pattern}" in corpus


def test_prompt_leading_summary_requires_prompt_alignment() -> None:
    summary = summarize_required_term_prompt_leading_corpus(
        "header\ncycle=01|pattern=direct|case=alpha|data:data\n",
        [{"case": "alpha", "term": "data", "scaffold_prompt": "data:", "line_count": 1}],
        repeat=1,
        previous={"prompt_alignment_ready": False, "prompt_leading_line_count": 0},
    )

    assert summary["prompt_leading_corpus_decision"] == "prompt_leading_corpus_candidate_needs_review"
    assert summary["prompt_alignment_ready"] is False


def test_prompt_leading_corpus_reports_missing_balanced_source(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_required_term_balanced_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "source_required_term_balanced_corpus": str(tmp_path / "missing.json"),
            "summary": {"prompt_alignment_ready": False, "prompt_leading_line_count": 0},
        },
    )

    report = build_model_capability_required_term_prompt_leading_corpus(
        read_json_report(source),
        out_dir=tmp_path / "prompt-leading",
        source_path=source,
    )

    assert report["status"] == "fail"
    assert "source balanced corpus report could not be resolved" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_prompt_leading_corpus_writes_all_outputs(tmp_path: Path) -> None:
    source = write_balanced_training_fixture(tmp_path)
    report = build_model_capability_required_term_prompt_leading_corpus(
        read_json_report(source),
        out_dir=tmp_path / "prompt-leading",
        source_path=source,
        repeat=2,
    )

    outputs = write_model_capability_required_term_prompt_leading_corpus_outputs(report, tmp_path / "prompt-leading")
    markdown = render_model_capability_required_term_prompt_leading_corpus_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["prompt_alignment_ready"] is True
    assert "MiniGPT Model Capability Required-Term Prompt-Leading Corpus" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_prompt_leading_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_balanced_training_fixture(tmp_path)

    assert locate_model_capability_required_term_prompt_leading_source(source) == source
    assert locate_model_capability_required_term_prompt_leading_source(source.parent) == source


def write_balanced_training_fixture(root: Path) -> Path:
    balanced = root / "model_capability_required_term_balanced_corpus.json"
    write_json(
        balanced,
        {
            "status": "pass",
            "corpus": {"path": str(root / "required_term_balanced_corpus.txt"), "line_count": 2},
            "summary": {"unique_line_rate": 1.0, "term_line_spread": 0},
            "term_rows": [
                {"case": "alpha", "term": "data", "scaffold_prompt": "data:", "line_count": 12, "pattern_count": 6},
                {"case": "beta", "term": "model", "scaffold_prompt": "model:", "line_count": 12, "pattern_count": 6},
            ],
        },
    )
    source = root / "model_capability_required_term_balanced_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "source_required_term_balanced_corpus": str(balanced),
            "summary": {"prompt_alignment_ready": False, "prompt_leading_line_count": 0},
        },
    )
    return source


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
