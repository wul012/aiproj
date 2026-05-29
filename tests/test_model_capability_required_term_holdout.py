from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_holdout import (
    build_model_capability_required_term_holdout,
    build_required_term_holdout_corpus,
    locate_model_capability_required_term_micro_training,
    read_json_report,
    resolve_exit_code,
    split_required_term_examples,
    summarize_required_term_holdout,
)
from minigpt.model_capability_required_term_holdout_artifacts import (
    render_model_capability_required_term_holdout_markdown,
    render_model_capability_required_term_holdout_text,
    write_model_capability_required_term_holdout_outputs,
)


def test_holdout_detects_heldout_required_term_uptake(tmp_path: Path) -> None:
    source = write_micro_training_fixture(tmp_path)

    report = build_model_capability_required_term_holdout(
        read_json_report(source),
        out_dir=tmp_path / "holdout",
        source_path=source,
        holdout_terms=["data"],
        generated_at="2026-05-29T00:00:00Z",
        train_func=fake_train(tmp_path / "holdout" / "holdout-run"),
        generate_func=fake_generator({"data"}),
    )
    summary = report["summary"]
    text = render_model_capability_required_term_holdout_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_holdout_uptake_observed"
    assert summary["holdout_decision"] == "heldout_required_term_uptake_observed"
    assert summary["holdout_continuation_hit_count"] == 1
    assert summary["train_continuation_hit_count"] == 0
    assert "holdout_decision=heldout_required_term_uptake_observed" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_holdout_detects_training_slice_only_uptake(tmp_path: Path) -> None:
    source = write_micro_training_fixture(tmp_path)

    report = build_model_capability_required_term_holdout(
        read_json_report(source),
        out_dir=tmp_path / "holdout",
        source_path=source,
        holdout_terms=["data"],
        train_func=fake_train(tmp_path / "holdout" / "holdout-run"),
        generate_func=fake_generator({"because"}),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_holdout_no_uptake"
    assert report["summary"]["holdout_decision"] == "training_slice_only_without_holdout_uptake"
    assert report["summary"]["train_continuation_hit_count"] == 1
    assert report["summary"]["holdout_continuation_hit_count"] == 0


def test_holdout_reports_missing_source_examples(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_required_term_micro_training.json"
    write_json(source, {"status": "pass", "summary": {"continuation_hit_count": 0}, "examples": []})

    report = build_model_capability_required_term_holdout(
        read_json_report(source),
        out_dir=tmp_path / "holdout",
        source_path=source,
        train_func=fake_train(tmp_path / "holdout" / "holdout-run"),
        generate_func=fake_generator({"data"}),
    )

    assert report["status"] == "fail"
    assert "source required-term micro-training report has no examples" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_holdout_writes_all_outputs(tmp_path: Path) -> None:
    source = write_micro_training_fixture(tmp_path)
    report = build_model_capability_required_term_holdout(
        read_json_report(source),
        out_dir=tmp_path / "holdout",
        source_path=source,
        holdout_terms=["data"],
        train_func=fake_train(tmp_path / "holdout" / "holdout-run"),
        generate_func=fake_generator({"data"}),
    )

    outputs = write_model_capability_required_term_holdout_outputs(report, tmp_path / "holdout")
    markdown = render_model_capability_required_term_holdout_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["generation_count"] == 3
    assert "holdout" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Holdout" in markdown
    assert "heldout_required_term_uptake_observed" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_holdout_helpers_accept_file_or_directory(tmp_path: Path) -> None:
    source = write_micro_training_fixture(tmp_path)

    assert locate_model_capability_required_term_micro_training(source) == source
    assert locate_model_capability_required_term_micro_training(source.parent) == source


def test_holdout_corpus_excludes_holdout_prompt_to_term_pairs() -> None:
    examples = [
        {"case": "train-case", "term": "because", "scaffold_prompt": "because:"},
        {"case": "holdout-case", "term": "data", "scaffold_prompt": "data:"},
    ]
    split = split_required_term_examples(examples, holdout_terms=["data"], holdout_stride=3, holdout_offset=2)
    corpus = build_required_term_holdout_corpus(split["train_examples"], split["holdout_examples"], repeat=2)

    assert "because:because" in corpus
    assert "data:data" not in corpus
    assert "holdout-prompt-only|holdout-case|data:" in corpus


def test_summarize_holdout_handles_failed_training() -> None:
    summary = summarize_required_term_holdout(
        {"train_examples": [], "holdout_examples": []},
        [],
        {"status": "fail", "returncode": 1},
    )

    assert summary["holdout_decision"] == "holdout_training_run_failed"
    assert summary["generation_count"] == 0


def write_micro_training_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_micro_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {"continuation_hit_count": 1},
            "examples": [
                {"seed": 1337, "case": "classification-risk-level", "task_type": "classification", "term": "because", "scaffold_prompt": "because:"},
                {"seed": 1337, "case": "qa-training-loop", "task_type": "qa", "term": "data", "scaffold_prompt": "data:"},
                {"seed": 1337, "case": "factual-val-loss", "task_type": "factual", "term": "loss", "scaffold_prompt": "loss:"},
            ],
        },
    )
    return source


def fake_train(run_dir: Path):
    def train(context: dict[str, object]) -> dict[str, object]:
        run_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = run_dir / "checkpoint.pt"
        tokenizer = run_dir / "tokenizer.json"
        metrics = run_dir / "metrics.jsonl"
        train_config = run_dir / "train_config.json"
        checkpoint.write_text("fake", encoding="utf-8")
        tokenizer.write_text("{}", encoding="utf-8")
        metrics.write_text('{"step": 1}\n', encoding="utf-8")
        write_json(train_config, {"max_iters": context.get("max_iters")})
        return {
            "status": "pass",
            "returncode": 0,
            "command": ["fake-train"],
            "command_text": "fake-train",
            "run_dir": str(run_dir),
            "checkpoint_path": str(checkpoint),
            "tokenizer_path": str(tokenizer),
            "metrics_path": str(metrics),
            "train_config_path": str(train_config),
            "checkpoint_exists": True,
            "tokenizer_exists": True,
            "metrics_exists": True,
            "train_config_exists": True,
            "train_config": {"max_iters": context.get("max_iters")},
        }

    return train


def fake_generator(hit_terms: set[str]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.rstrip(":")
        continuation = f"{term} learned" if term in hit_terms else "noise"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
