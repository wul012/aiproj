from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_micro_training import (
    build_model_capability_required_term_micro_training,
    build_required_term_micro_corpus,
    locate_model_capability_required_term_scaffold_probe,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_micro_training,
)
from minigpt.model_capability_required_term_micro_training_artifacts import (
    render_model_capability_required_term_micro_training_markdown,
    render_model_capability_required_term_micro_training_text,
    write_model_capability_required_term_micro_training_outputs,
)


def test_micro_training_detects_targeted_required_term_uptake(tmp_path: Path) -> None:
    source = write_scaffold_probe_fixture(tmp_path)

    report = build_model_capability_required_term_micro_training(
        read_json_report(source),
        out_dir=tmp_path / "micro",
        source_path=source,
        generated_at="2026-05-29T00:00:00Z",
        train_func=fake_train(tmp_path / "micro" / "micro-run"),
        generate_func=fake_generator("{term} learned"),
    )
    summary = report["summary"]
    text = render_model_capability_required_term_micro_training_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_micro_training_uptake_observed"
    assert summary["micro_training_decision"] == "targeted_micro_training_partially_learned_required_terms"
    assert summary["continuation_hit_count"] == 1
    assert summary["checkpoint_exists"] is True
    assert "micro_training_decision=targeted_micro_training_partially_learned_required_terms" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_micro_training_can_complete_without_uptake(tmp_path: Path) -> None:
    source = write_scaffold_probe_fixture(tmp_path)

    report = build_model_capability_required_term_micro_training(
        read_json_report(source),
        out_dir=tmp_path / "micro",
        source_path=source,
        train_func=fake_train(tmp_path / "micro" / "micro-run"),
        generate_func=fake_generator("noise"),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_micro_training_completed_without_uptake"
    assert report["summary"]["continuation_hit_count"] == 0


def test_micro_training_reports_missing_source_examples(tmp_path: Path) -> None:
    source = write_scaffold_probe_fixture(tmp_path, prompt_over_block=True)

    report = build_model_capability_required_term_micro_training(
        read_json_report(source),
        out_dir=tmp_path / "micro",
        source_path=source,
        train_func=fake_train(tmp_path / "micro" / "micro-run"),
        generate_func=fake_generator("data"),
    )

    assert report["status"] == "fail"
    assert "source scaffold probe has no eligible non-truncated examples" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_micro_training_writes_all_outputs(tmp_path: Path) -> None:
    source = write_scaffold_probe_fixture(tmp_path)
    report = build_model_capability_required_term_micro_training(
        read_json_report(source),
        out_dir=tmp_path / "micro",
        source_path=source,
        train_func=fake_train(tmp_path / "micro" / "micro-run"),
        generate_func=fake_generator("{term} learned"),
    )

    outputs = write_model_capability_required_term_micro_training_outputs(report, tmp_path / "micro")
    markdown = render_model_capability_required_term_micro_training_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["generation_count"] == 1
    assert "qa-training-loop" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Micro-Training" in markdown
    assert "targeted_micro_training_partially_learned_required_terms" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_micro_training_helpers_accept_file_or_directory(tmp_path: Path) -> None:
    source = write_scaffold_probe_fixture(tmp_path)

    assert locate_model_capability_required_term_scaffold_probe(source) == source
    assert locate_model_capability_required_term_scaffold_probe(source.parent) == source


def test_micro_corpus_repeats_prompt_to_term_pairs() -> None:
    corpus = build_required_term_micro_corpus(
        [{"case": "qa-training-loop", "term": "data", "scaffold_prompt": "data:"}],
        repeat=2,
    )

    assert corpus.count("\ndata:data\n") == 2
    assert "qa-training-loop|data:data" in corpus


def test_summarize_micro_training_handles_empty_rows() -> None:
    summary = summarize_required_term_micro_training([], [], {"status": "fail", "returncode": 1})

    assert summary["micro_training_decision"] == "micro_training_run_failed"
    assert summary["generation_count"] == 0


def write_scaffold_probe_fixture(root: Path, *, prompt_over_block: bool = False) -> Path:
    source = root / "model_capability_required_term_scaffold_probe.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {"probe_decision": "explicit_scaffold_still_no_required_term_uptake"},
            "probe_rows": [
                {
                    "seed": 1337,
                    "token_cap": 12,
                    "case": "qa-training-loop",
                    "task_type": "qa",
                    "max_iters": 4,
                    "terms": ["data"],
                    "scaffold_prompt": "data:",
                    "prompt_truncated": False,
                    "prompt_over_block": prompt_over_block,
                    "checkpoint_path": str(root / "source" / "checkpoint.pt"),
                    "tokenizer_path": str(root / "source" / "tokenizer.json"),
                    "eval_suite_path": str(root / "source" / "eval_suite.json"),
                }
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


def fake_generator(template: str):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.rstrip(":")
        continuation = template.format(term=term)
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
