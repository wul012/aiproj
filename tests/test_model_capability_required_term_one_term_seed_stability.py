from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_one_term_seed_stability import (
    build_model_capability_required_term_one_term_seed_stability,
    locate_model_capability_required_term_one_term_seed_stability_source,
    read_json_report,
    resolve_exit_code,
    select_seed_stability_terms,
    summarize_required_term_one_term_seed_stability,
)
from minigpt.model_capability_required_term_one_term_seed_stability_artifacts import (
    render_model_capability_required_term_one_term_seed_stability_markdown,
    render_model_capability_required_term_one_term_seed_stability_text,
    write_model_capability_required_term_one_term_seed_stability_outputs,
)


def test_one_term_seed_stability_detects_stable_and_partial_terms(tmp_path: Path) -> None:
    source = write_one_term_isolation_fixture(tmp_path)

    report = build_model_capability_required_term_one_term_seed_stability(
        read_json_report(source),
        out_dir=tmp_path / "seed-stability",
        source_path=source,
        seeds=(10, 20),
        repeat=2,
        generated_at="2026-05-29T00:00:00Z",
        train_func=fake_train,
        generate_func=fake_generate({("data", 10), ("data", 20), ("model", 10)}),
    )
    text = render_model_capability_required_term_one_term_seed_stability_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_one_term_seed_stability_observed"
    assert report["summary"]["selected_term_count"] == 2
    assert report["summary"]["seed_run_count"] == 4
    assert report["summary"]["term_seed_hit_count"] == 3
    assert report["summary"]["stable_term_count"] == 1
    assert report["summary"]["partial_stable_term_count"] == 1
    assert report["summary"]["single_term_capacity_stable"] is True
    assert report["interpretation"]["model_quality_claim"] == "one_term_seed_stable_capacity_signal_only"
    assert "one_term_seed_stability_decision=some_successful_terms_seed_stable" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_one_term_seed_stability_defaults_to_v492_hit_terms_only(tmp_path: Path) -> None:
    source = write_one_term_isolation_fixture(tmp_path)
    source_report = read_json_report(source)

    default_terms = select_seed_stability_terms(source_report)
    all_terms = select_seed_stability_terms(source_report, include_all_terms=True)

    assert [row["term"] for row in default_terms] == ["data", "model"]
    assert [row["term"] for row in all_terms] == ["data", "model", "loss"]


def test_one_term_seed_stability_reports_no_reproduction_without_failing_structure(tmp_path: Path) -> None:
    source = write_one_term_isolation_fixture(tmp_path)

    report = build_model_capability_required_term_one_term_seed_stability(
        read_json_report(source),
        out_dir=tmp_path / "seed-stability",
        source_path=source,
        seeds=(10, 20),
        repeat=2,
        train_func=fake_train,
        generate_func=fake_generate(set()),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_one_term_seed_stability_not_reproduced"
    assert report["summary"]["term_seed_hit_count"] == 0
    assert report["summary"]["stable_term_count"] == 0


def test_one_term_seed_stability_fails_bad_source(tmp_path: Path) -> None:
    source = write_one_term_isolation_fixture(tmp_path, status="fail")

    report = build_model_capability_required_term_one_term_seed_stability(
        read_json_report(source),
        out_dir=tmp_path / "seed-stability",
        source_path=source,
        seeds=(10,),
        train_func=fake_train,
        generate_func=fake_generate({("data", 10)}),
    )

    assert report["status"] == "fail"
    assert "source one-term isolation report is not pass" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_one_term_seed_stability_writes_all_outputs(tmp_path: Path) -> None:
    source = write_one_term_isolation_fixture(tmp_path)
    report = build_model_capability_required_term_one_term_seed_stability(
        read_json_report(source),
        out_dir=tmp_path / "seed-stability",
        source_path=source,
        seeds=(10,),
        repeat=2,
        train_func=fake_train,
        generate_func=fake_generate({("data", 10), ("model", 10)}),
    )

    outputs = write_model_capability_required_term_one_term_seed_stability_outputs(
        report,
        tmp_path / "seed-stability",
    )
    markdown = render_model_capability_required_term_one_term_seed_stability_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["selected_term_count"] == 2
    assert "MiniGPT Model Capability Required-Term One-Term Seed Stability" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_one_term_seed_stability_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_one_term_isolation_fixture(tmp_path)

    assert locate_model_capability_required_term_one_term_seed_stability_source(source) == source
    assert locate_model_capability_required_term_one_term_seed_stability_source(source.parent) == source


def test_summarize_one_term_seed_stability_handles_empty_rows() -> None:
    summary = summarize_required_term_one_term_seed_stability([], [], [], previous_summary={})

    assert summary["one_term_seed_stability_decision"] == "no_successful_source_terms"
    assert summary["selected_term_count"] == 0


def write_one_term_isolation_fixture(root: Path, *, status: str = "pass") -> Path:
    source = root / "model_capability_required_term_one_term_isolation.json"
    write_json(
        source,
        {
            "status": status,
            "summary": {
                "one_term_isolation_decision": "one_term_isolation_capacity_observed",
                "term_count": 3,
                "continuation_hit_count": 2,
                "term_with_continuation_hit_count": 2,
                "single_term_capacity_observed": True,
            },
            "isolation_rows": [
                {
                    "case": "alpha",
                    "term": "data",
                    "scaffold_prompt": "data:",
                    "one_term_run_id": "01-data",
                    "generation_seed": 492,
                    "continuation_hit_count": 1,
                    "checkpoint_path": "runs/data/checkpoint.pt",
                    "continuation_preview": "data",
                },
                {
                    "case": "beta",
                    "term": "model",
                    "scaffold_prompt": "model:",
                    "one_term_run_id": "02-model",
                    "generation_seed": 493,
                    "continuation_hit_count": 1,
                    "checkpoint_path": "runs/model/checkpoint.pt",
                    "continuation_preview": "model",
                },
                {
                    "case": "gamma",
                    "term": "loss",
                    "scaffold_prompt": "loss:",
                    "one_term_run_id": "03-loss",
                    "generation_seed": 494,
                    "continuation_hit_count": 0,
                    "checkpoint_path": "runs/loss/checkpoint.pt",
                    "continuation_preview": "nope",
                },
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


def fake_generate(hit_pairs: set[tuple[str, int]]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.strip(":")
        seed = int(request["seed"])
        continuation = term if (term, seed) in hit_pairs else "noop"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
