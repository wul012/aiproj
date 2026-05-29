from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_pair_curriculum import (
    build_model_capability_required_term_pair_curriculum,
    build_pair_curriculum_pairs,
    build_required_term_pair_curriculum_corpus,
    locate_model_capability_required_term_pair_curriculum_source,
    read_json_report,
    resolve_exit_code,
    select_pair_curriculum_terms,
    summarize_required_term_pair_curriculum,
    summarize_pair_probe_rows,
)
from minigpt.model_capability_required_term_pair_curriculum_artifacts import (
    render_model_capability_required_term_pair_curriculum_markdown,
    render_model_capability_required_term_pair_curriculum_text,
    write_model_capability_required_term_pair_curriculum_outputs,
)


def test_pair_curriculum_detects_full_and_partial_pair_capacity(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)

    report = build_model_capability_required_term_pair_curriculum(
        read_json_report(source),
        out_dir=tmp_path / "pair-curriculum",
        source_path=source,
        pair_limit=2,
        repeat=2,
        generated_at="2026-05-30T00:00:00Z",
        train_func=fake_train,
        generate_func=fake_generate(
            {
                ("01-data-fixed", "data"),
                ("01-data-fixed", "fixed"),
                ("02-data-model", "data"),
            }
        ),
    )
    text = render_model_capability_required_term_pair_curriculum_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_pair_curriculum_capacity_observed"
    assert report["summary"]["selected_term_count"] == 3
    assert report["summary"]["pair_count"] == 2
    assert report["summary"]["pair_full_hit_count"] == 1
    assert report["summary"]["pair_partial_hit_count"] == 1
    assert report["summary"]["probe_hit_count"] == 3
    assert report["summary"]["multi_target_pair_capacity_observed"] is True
    assert report["interpretation"]["model_quality_claim"] == "pair_curriculum_capacity_signal_only"
    assert "pair_curriculum_decision=some_pairs_preserve_required_terms" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_pair_curriculum_defaults_to_stable_terms_only(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)
    source_report = read_json_report(source)

    stable_terms = select_pair_curriculum_terms(source_report)
    partial_included = select_pair_curriculum_terms(source_report, include_partial_terms=True)

    assert [row["term"] for row in stable_terms] == ["data", "fixed", "model"]
    assert [row["term"] for row in partial_included] == ["data", "fixed", "loss", "model"]


def test_pair_curriculum_reports_no_uptake_without_failing_structure(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)

    report = build_model_capability_required_term_pair_curriculum(
        read_json_report(source),
        out_dir=tmp_path / "pair-curriculum",
        source_path=source,
        pair_limit=1,
        repeat=2,
        train_func=fake_train,
        generate_func=fake_generate(set()),
    )

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_pair_curriculum_not_reproduced"
    assert report["summary"]["probe_hit_count"] == 0
    assert report["summary"]["pair_full_hit_count"] == 0


def test_pair_curriculum_fails_bad_source(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path, status="fail")

    report = build_model_capability_required_term_pair_curriculum(
        read_json_report(source),
        out_dir=tmp_path / "pair-curriculum",
        source_path=source,
        pair_limit=1,
        train_func=fake_train,
        generate_func=fake_generate(set()),
    )

    assert report["status"] == "fail"
    assert "source one-term seed stability report is not pass" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_pair_curriculum_corpus_contains_balanced_pair_terms(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)
    terms = select_pair_curriculum_terms(read_json_report(source))
    pair = build_pair_curriculum_pairs(terms, pair_limit=1)[0]

    corpus = build_required_term_pair_curriculum_corpus(pair, repeat=3)

    assert corpus.count("data:data") == 3
    assert corpus.count("data: data") == 3
    assert corpus.count("fixed:fixed") == 3
    assert corpus.count("fixed: fixed") == 3
    assert "loss:loss" not in corpus


def test_pair_curriculum_writes_all_outputs(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)
    report = build_model_capability_required_term_pair_curriculum(
        read_json_report(source),
        out_dir=tmp_path / "pair-curriculum",
        source_path=source,
        pair_limit=1,
        repeat=2,
        train_func=fake_train,
        generate_func=fake_generate({("01-data-fixed", "data"), ("01-data-fixed", "fixed")}),
    )

    outputs = write_model_capability_required_term_pair_curriculum_outputs(report, tmp_path / "pair-curriculum")
    markdown = render_model_capability_required_term_pair_curriculum_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["pair_count"] == 1
    assert "MiniGPT Model Capability Required-Term Pair Curriculum" in markdown
    assert "data" in Path(outputs["csv"]).read_text(encoding="utf-8")


def test_locate_pair_curriculum_source_accepts_file_or_directory(tmp_path: Path) -> None:
    source = write_seed_stability_fixture(tmp_path)

    assert locate_model_capability_required_term_pair_curriculum_source(source) == source
    assert locate_model_capability_required_term_pair_curriculum_source(source.parent) == source


def test_summarize_pair_curriculum_handles_empty_rows() -> None:
    summary = summarize_required_term_pair_curriculum(
        [],
        [],
        [],
        [],
        summarize_pair_probe_rows([], []),
        previous_summary={},
    )

    assert summary["pair_curriculum_decision"] == "not_enough_stable_terms"
    assert summary["selected_term_count"] == 0


def write_seed_stability_fixture(root: Path, *, status: str = "pass") -> Path:
    source = root / "model_capability_required_term_one_term_seed_stability.json"
    write_json(
        source,
        {
            "status": status,
            "summary": {
                "one_term_seed_stability_decision": "some_successful_terms_seed_stable",
                "stable_term_count": 3,
                "partial_stable_term_count": 1,
                "term_seed_hit_count": 10,
                "term_seed_success_rate": 0.8333,
                "single_term_capacity_stable": True,
            },
            "term_rows": [
                {"case": "alpha", "term": "data", "scaffold_prompt": "data:"},
                {"case": "gamma", "term": "model", "scaffold_prompt": "model:"},
                {"case": "beta", "term": "fixed", "scaffold_prompt": "fixed:"},
                {"case": "delta", "term": "loss", "scaffold_prompt": "loss:"},
            ],
            "term_seed_summaries": [
                {"case": "alpha", "term": "data", "seed_count": 3, "hit_seed_count": 3, "hit_rate": 1.0, "stable_across_seeds": True},
                {"case": "gamma", "term": "model", "seed_count": 3, "hit_seed_count": 3, "hit_rate": 1.0, "stable_across_seeds": True},
                {"case": "beta", "term": "fixed", "seed_count": 3, "hit_seed_count": 3, "hit_rate": 1.0, "stable_across_seeds": True},
                {"case": "delta", "term": "loss", "seed_count": 3, "hit_seed_count": 2, "hit_rate": 0.6667, "stable_across_seeds": False, "partial_across_seeds": True},
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


def fake_generate(hit_pairs: set[tuple[str, str]]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.strip(":")
        checkpoint_path = Path(str(request["checkpoint_path"]))
        pair_id = checkpoint_path.parent.name
        continuation = term if (pair_id, term) in hit_pairs else "noop"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
