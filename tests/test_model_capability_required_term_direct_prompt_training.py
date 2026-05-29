from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_direct_prompt_training import (
    build_model_capability_required_term_direct_prompt_training,
    build_required_term_direct_prompt_corpus,
    locate_model_capability_required_term_direct_prompt_training_source,
    read_json_report,
    resolve_exit_code,
    summarize_direct_prompt_corpus,
    summarize_required_term_direct_prompt_training,
)
from minigpt.model_capability_required_term_direct_prompt_training_artifacts import (
    render_model_capability_required_term_direct_prompt_training_markdown,
    render_model_capability_required_term_direct_prompt_training_text,
    write_model_capability_required_term_direct_prompt_training_outputs,
)


def test_direct_prompt_training_detects_improvement_over_previous(tmp_path: Path) -> None:
    source = write_prompt_leading_training_fixture(tmp_path)

    report = build_model_capability_required_term_direct_prompt_training(
        read_json_report(source),
        out_dir=tmp_path / "direct-prompt-training",
        source_path=source,
        repeat=3,
        generated_at="2026-05-29T00:00:00Z",
        train_func=fake_train(tmp_path / "direct-prompt-training" / "direct-prompt-run"),
        generate_func=fake_generate({"data": "data:data", "model": "model:model"}),
    )
    text = render_model_capability_required_term_direct_prompt_training_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_direct_prompt_training_improved"
    assert report["summary"]["continuation_hit_count"] == 2
    assert report["summary"]["previous_continuation_hit_count"] == 0
    assert report["summary"]["continuation_hit_delta"] == 2
    assert report["summary"]["direct_prompt_line_count"] == 12
    assert report["interpretation"]["model_quality_claim"] == "direct_prompt_training_signal_only"
    assert "direct_prompt_training_decision=direct_prompt_training_improved_over_previous" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_direct_prompt_training_reports_no_uptake_without_failing_structure(tmp_path: Path) -> None:
    source = write_prompt_leading_training_fixture(tmp_path)

    report = build_model_capability_required_term_direct_prompt_training(
        read_json_report(source),
        out_dir=tmp_path / "direct-prompt-training",
        source_path=source,
        train_func=fake_train(tmp_path / "direct-prompt-training" / "direct-prompt-run"),
        generate_func=fake_generate({"data": "data: nope", "model": "model: nope"}),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_direct_prompt_training_completed_without_uptake"
    assert report["summary"]["continuation_hit_count"] == 0
    assert report["summary"]["continuation_hit_delta"] == 0


def test_direct_prompt_corpus_uses_only_direct_rows() -> None:
    corpus, rows = build_required_term_direct_prompt_corpus(
        [
            {"case": "alpha", "term": "data", "scaffold_prompt": "data:"},
            {"case": "beta", "term": "model", "scaffold_prompt": "model:"},
        ],
        repeat=2,
    )
    summary = summarize_direct_prompt_corpus(corpus, rows)

    assert rows[0]["direct_prompt_line_count"] == 4
    assert "pattern=" not in corpus
    assert "case=" not in corpus
    assert summary["direct_prompt_ready"] is True
    assert summary["pattern_counts"] == {"direct": 4, "spaced": 4}


def test_direct_prompt_training_reports_bad_source_training(tmp_path: Path) -> None:
    source = write_prompt_leading_training_fixture(tmp_path, training_status="fail")

    report = build_model_capability_required_term_direct_prompt_training(
        read_json_report(source),
        out_dir=tmp_path / "direct-prompt-training",
        source_path=source,
    )

    assert report["status"] == "fail"
    assert "source prompt-leading training did not finish cleanly" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_direct_prompt_training_writes_all_outputs(tmp_path: Path) -> None:
    source = write_prompt_leading_training_fixture(tmp_path)
    report = build_model_capability_required_term_direct_prompt_training(
        read_json_report(source),
        out_dir=tmp_path / "direct-prompt-training",
        source_path=source,
        repeat=2,
        train_func=fake_train(tmp_path / "direct-prompt-training" / "direct-prompt-run"),
        generate_func=fake_generate({"data": "data:data", "model": "model: nope"}),
    )

    outputs = write_model_capability_required_term_direct_prompt_training_outputs(report, tmp_path / "direct-prompt-training")
    markdown = render_model_capability_required_term_direct_prompt_training_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["term_count"] == 2
    assert "MiniGPT Model Capability Required-Term Direct Prompt Training" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_direct_prompt_training_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_prompt_leading_training_fixture(tmp_path)

    assert locate_model_capability_required_term_direct_prompt_training_source(source) == source
    assert locate_model_capability_required_term_direct_prompt_training_source(source.parent) == source


def test_summarize_direct_prompt_training_handles_empty_rows() -> None:
    summary = summarize_required_term_direct_prompt_training(
        [],
        [],
        {"status": "pass"},
        corpus_summary={"direct_prompt_ready": True},
        previous_summary={"continuation_hit_count": 0},
    )

    assert summary["direct_prompt_training_decision"] == "no_required_term_rows"
    assert summary["term_count"] == 0


def write_prompt_leading_training_fixture(root: Path, *, training_status: str = "pass") -> Path:
    source = root / "model_capability_required_term_prompt_leading_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "prompt_leading_training_decision": "prompt_leading_training_completed_without_uptake",
                "continuation_hit_count": 0,
                "training_status": training_status,
                "prompt_alignment_ready": True,
                "prompt_leading_line_count": 360,
            },
            "term_rows": [
                {"case": "alpha", "term": "data", "scaffold_prompt": "data:"},
                {"case": "beta", "term": "model", "scaffold_prompt": "model:"},
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
