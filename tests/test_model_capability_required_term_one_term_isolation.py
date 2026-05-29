from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_one_term_isolation import (
    build_model_capability_required_term_one_term_isolation,
    build_required_term_one_term_corpus,
    locate_model_capability_required_term_one_term_isolation_source,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_one_term_isolation,
)
from minigpt.model_capability_required_term_one_term_isolation_artifacts import (
    render_model_capability_required_term_one_term_isolation_markdown,
    render_model_capability_required_term_one_term_isolation_text,
    write_model_capability_required_term_one_term_isolation_outputs,
)


def test_one_term_isolation_detects_single_term_capacity(tmp_path: Path) -> None:
    source = write_direct_prompt_training_fixture(tmp_path)

    report = build_model_capability_required_term_one_term_isolation(
        read_json_report(source),
        out_dir=tmp_path / "one-term-isolation",
        source_path=source,
        repeat=2,
        generated_at="2026-05-29T00:00:00Z",
        train_func=fake_train,
        generate_func=fake_generate({"data": "data:data", "model": "model:model"}),
    )
    text = render_model_capability_required_term_one_term_isolation_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_one_term_capacity_observed"
    assert report["summary"]["continuation_hit_count"] == 2
    assert report["summary"]["term_with_continuation_hit_count"] == 2
    assert report["summary"]["single_term_capacity_observed"] is True
    assert report["interpretation"]["model_quality_claim"] == "one_term_capacity_signal_only"
    assert "one_term_isolation_decision=one_term_isolation_capacity_observed" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_one_term_isolation_reports_no_uptake_without_failing_structure(tmp_path: Path) -> None:
    source = write_direct_prompt_training_fixture(tmp_path)

    report = build_model_capability_required_term_one_term_isolation(
        read_json_report(source),
        out_dir=tmp_path / "one-term-isolation",
        source_path=source,
        train_func=fake_train,
        generate_func=fake_generate({"data": "data: nope", "model": "model: nope"}),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_one_term_isolation_completed_without_uptake"
    assert report["summary"]["continuation_hit_count"] == 0
    assert report["summary"]["training_pass_count"] == 2


def test_one_term_corpus_contains_only_one_target() -> None:
    corpus = build_required_term_one_term_corpus(
        {"case": "alpha", "term": "data", "scaffold_prompt": "data:"},
        repeat=3,
    )

    assert corpus.count("data:data") == 3
    assert corpus.count("data: data") == 3
    assert "model:model" not in corpus


def test_one_term_isolation_reports_bad_source_training(tmp_path: Path) -> None:
    source = write_direct_prompt_training_fixture(tmp_path, training_status="fail")

    report = build_model_capability_required_term_one_term_isolation(
        read_json_report(source),
        out_dir=tmp_path / "one-term-isolation",
        source_path=source,
    )

    assert report["status"] == "fail"
    assert "source direct prompt training did not finish cleanly" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_one_term_isolation_writes_all_outputs(tmp_path: Path) -> None:
    source = write_direct_prompt_training_fixture(tmp_path)
    report = build_model_capability_required_term_one_term_isolation(
        read_json_report(source),
        out_dir=tmp_path / "one-term-isolation",
        source_path=source,
        repeat=2,
        train_func=fake_train,
        generate_func=fake_generate({"data": "data:data", "model": "model: nope"}),
    )

    outputs = write_model_capability_required_term_one_term_isolation_outputs(report, tmp_path / "one-term-isolation")
    markdown = render_model_capability_required_term_one_term_isolation_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["term_count"] == 2
    assert "MiniGPT Model Capability Required-Term One-Term Isolation" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_one_term_isolation_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_direct_prompt_training_fixture(tmp_path)

    assert locate_model_capability_required_term_one_term_isolation_source(source) == source
    assert locate_model_capability_required_term_one_term_isolation_source(source.parent) == source


def test_summarize_one_term_isolation_handles_empty_rows() -> None:
    summary = summarize_required_term_one_term_isolation([], [], previous_summary={"continuation_hit_count": 0})

    assert summary["one_term_isolation_decision"] == "no_required_term_rows"
    assert summary["term_count"] == 0


def write_direct_prompt_training_fixture(root: Path, *, training_status: str = "pass") -> Path:
    source = root / "model_capability_required_term_direct_prompt_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "direct_prompt_training_decision": "direct_prompt_training_completed_without_uptake",
                "continuation_hit_count": 0,
                "training_status": training_status,
                "direct_prompt_ready": True,
                "direct_prompt_line_count": 320,
            },
            "term_rows": [
                {"case": "alpha", "term": "data", "scaffold_prompt": "data:"},
                {"case": "beta", "term": "model", "scaffold_prompt": "model:"},
            ],
        },
    )
    return source


def fake_train(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
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
