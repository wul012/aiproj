from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_balanced_training import (
    build_model_capability_required_term_balanced_training,
    locate_model_capability_required_term_balanced_corpus,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_balanced_training,
)
from minigpt.model_capability_required_term_balanced_training_artifacts import (
    render_model_capability_required_term_balanced_training_markdown,
    render_model_capability_required_term_balanced_training_text,
    write_model_capability_required_term_balanced_training_outputs,
)


def test_balanced_training_detects_required_term_continuation_uptake(tmp_path: Path) -> None:
    source = write_balanced_corpus_fixture(tmp_path)

    report = build_model_capability_required_term_balanced_training(
        read_json_report(source),
        out_dir=tmp_path / "balanced-training",
        source_path=source,
        generated_at="2026-05-29T00:00:00Z",
        train_func=fake_train(tmp_path / "balanced-training" / "balanced-run"),
        generate_func=fake_generate({"data": "data: data", "model": "model: model"}),
    )
    text = render_model_capability_required_term_balanced_training_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_balanced_training_uptake_observed"
    assert report["summary"]["continuation_hit_count"] == 2
    assert report["summary"]["case_with_continuation_hit_count"] == 2
    assert report["summary"]["prompt_alignment_ready"] is True
    assert "balanced_training_decision=balanced_training_required_term_uptake_observed" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_balanced_training_reports_completed_without_uptake(tmp_path: Path) -> None:
    source = write_balanced_corpus_fixture(tmp_path)

    report = build_model_capability_required_term_balanced_training(
        read_json_report(source),
        out_dir=tmp_path / "balanced-training",
        source_path=source,
        train_func=fake_train(tmp_path / "balanced-training" / "balanced-run"),
        generate_func=fake_generate({"data": "data: nope", "model": "model: nope"}),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_balanced_training_completed_without_uptake"
    assert report["summary"]["continuation_hit_count"] == 0


def test_balanced_training_reports_missing_corpus_file(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_required_term_balanced_corpus.json"
    write_json(
        source,
        {
            "status": "pass",
            "corpus": {"path": str(tmp_path / "missing.txt")},
            "term_rows": [{"case": "alpha", "term": "data", "scaffold_prompt": "data:"}],
        },
    )

    report = build_model_capability_required_term_balanced_training(
        read_json_report(source),
        out_dir=tmp_path / "balanced-training",
        source_path=source,
    )

    assert report["status"] == "fail"
    assert "source balanced corpus file could not be resolved" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_balanced_training_writes_all_outputs(tmp_path: Path) -> None:
    source = write_balanced_corpus_fixture(tmp_path)
    report = build_model_capability_required_term_balanced_training(
        read_json_report(source),
        out_dir=tmp_path / "balanced-training",
        source_path=source,
        train_func=fake_train(tmp_path / "balanced-training" / "balanced-run"),
        generate_func=fake_generate({"data": "data: data", "model": "model: nope"}),
    )

    outputs = write_model_capability_required_term_balanced_training_outputs(report, tmp_path / "balanced-training")
    markdown = render_model_capability_required_term_balanced_training_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["term_count"] == 2
    assert "MiniGPT Model Capability Required-Term Balanced Training" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_balanced_training_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_balanced_corpus_fixture(tmp_path)

    assert locate_model_capability_required_term_balanced_corpus(source) == source
    assert locate_model_capability_required_term_balanced_corpus(source.parent) == source


def test_summarize_balanced_training_handles_empty_rows() -> None:
    summary = summarize_required_term_balanced_training([], [], {"status": "pass"})

    assert summary["balanced_training_decision"] == "no_required_term_rows"
    assert summary["term_count"] == 0


def test_balanced_training_reports_missing_prompt_alignment(tmp_path: Path) -> None:
    corpus = tmp_path / "required_term_balanced_corpus.txt"
    corpus.write_text("cycle=01|pattern=direct|case=alpha|data:data\n", encoding="utf-8")
    source = tmp_path / "model_capability_required_term_balanced_corpus.json"
    write_json(
        source,
        {
            "status": "pass",
            "corpus": {"path": str(corpus), "line_count": 1},
            "summary": {"unique_line_rate": 1.0, "term_line_spread": 0},
            "term_rows": [{"case": "alpha", "term": "data", "scaffold_prompt": "data:"}],
        },
    )

    report = build_model_capability_required_term_balanced_training(
        read_json_report(source),
        out_dir=tmp_path / "balanced-training",
        source_path=source,
        train_func=fake_train(tmp_path / "balanced-training" / "balanced-run"),
        generate_func=fake_generate({"data": "data: nope"}),
    )

    assert report["summary"]["prompt_alignment_ready"] is False
    assert report["summary"]["prompt_leading_line_count"] == 0
    assert report["interpretation"]["next_action"].startswith("rebuild the balanced corpus")


def write_balanced_corpus_fixture(root: Path) -> Path:
    corpus = root / "required_term_balanced_corpus.txt"
    corpus.write_text("data:data\nmodel:model\n", encoding="utf-8")
    source = root / "model_capability_required_term_balanced_corpus.json"
    write_json(
        source,
        {
            "status": "pass",
            "corpus": {"path": str(corpus), "line_count": 2},
            "summary": {"unique_line_rate": 1.0, "term_line_spread": 0},
            "term_rows": [
                {"case": "alpha", "term": "data", "scaffold_prompt": "data:", "line_count": 12, "pattern_count": 6},
                {"case": "beta", "term": "model", "scaffold_prompt": "model:", "line_count": 12, "pattern_count": 6},
            ],
        },
    )
    return source


def fake_train(run_dir: Path):
    def train(_context: dict[str, object]) -> dict[str, object]:
        run_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = run_dir / "checkpoint.pt"
        tokenizer = run_dir / "tokenizer.json"
        metrics = run_dir / "metrics.jsonl"
        config = run_dir / "train_config.json"
        checkpoint.write_bytes(b"fake")
        tokenizer.write_text("{}", encoding="utf-8")
        metrics.write_text("{}", encoding="utf-8")
        config.write_text("{}", encoding="utf-8")
        return {
            "status": "pass",
            "returncode": 0,
            "run_dir": str(run_dir),
            "checkpoint_path": str(checkpoint),
            "tokenizer_path": str(tokenizer),
            "metrics_path": str(metrics),
            "train_config_path": str(config),
            "checkpoint_exists": True,
            "tokenizer_exists": True,
            "metrics_exists": True,
            "train_config_exists": True,
            "command_text": "fake train",
        }

    return train


def fake_generate(outputs: dict[str, str]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        key = prompt.strip(":")
        generated = outputs.get(key, prompt)
        return {"generated": generated, "continuation": generated[len(prompt) :]}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
