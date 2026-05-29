from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_split_scan import (
    build_model_capability_required_term_split_scan,
    default_split_specs,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_split_scan,
)
from minigpt.model_capability_required_term_split_scan_artifacts import (
    render_model_capability_required_term_split_scan_markdown,
    render_model_capability_required_term_split_scan_text,
    write_model_capability_required_term_split_scan_outputs,
)


def test_split_scan_detects_train_slice_only_signal(tmp_path: Path, monkeypatch) -> None:
    source = write_micro_training_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_scan.build_model_capability_required_term_holdout",
        fake_holdout_builder(train_hits={"split-2": 4}, holdout_hits={}),
    )

    report = build_model_capability_required_term_split_scan(
        read_json_report(source),
        out_dir=tmp_path / "scan",
        source_path=source,
        generated_at="2026-05-29T00:00:00Z",
    )
    text = render_model_capability_required_term_split_scan_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_split_scan_train_slice_only"
    assert report["summary"]["train_repro_split_count"] == 1
    assert report["summary"]["holdout_hit_split_count"] == 0
    assert "split_scan_decision=train_slice_uptake_reproduced_without_holdout" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_split_scan_detects_heldout_signal(tmp_path: Path, monkeypatch) -> None:
    source = write_micro_training_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_scan.build_model_capability_required_term_holdout",
        fake_holdout_builder(train_hits={"split-1": 2}, holdout_hits={"split-1": 1}),
    )

    report = build_model_capability_required_term_split_scan(
        read_json_report(source),
        out_dir=tmp_path / "scan",
        source_path=source,
    )

    assert report["decision"] == "required_term_split_scan_holdout_uptake_observed"
    assert report["summary"]["best_holdout_continuation_hit_count"] == 1


def test_split_scan_reports_missing_source_examples(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_required_term_micro_training.json"
    write_json(source, {"status": "pass", "examples": []})

    report = build_model_capability_required_term_split_scan(
        read_json_report(source),
        out_dir=tmp_path / "scan",
        source_path=source,
    )

    assert report["status"] == "fail"
    assert "source required-term micro-training report has no examples" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_split_scan_writes_all_outputs(tmp_path: Path, monkeypatch) -> None:
    source = write_micro_training_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_scan.build_model_capability_required_term_holdout",
        fake_holdout_builder(train_hits={"split-2": 4}, holdout_hits={}),
    )
    report = build_model_capability_required_term_split_scan(
        read_json_report(source),
        out_dir=tmp_path / "scan",
        source_path=source,
    )

    outputs = write_model_capability_required_term_split_scan_outputs(report, tmp_path / "scan")
    markdown = render_model_capability_required_term_split_scan_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["split_spec_count"] > 0
    assert "split-2" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Split Scan" in markdown


def test_default_split_specs_are_unique() -> None:
    report = {
        "examples": [
            {"term": "because"},
            {"term": "chain"},
            {"term": "data"},
            {"term": "fixed"},
            {"term": "four"},
            {"term": "loss"},
            {"term": "real"},
            {"term": "text"},
            {"term": "while"},
        ]
    }
    specs = default_split_specs(report)

    assert specs
    assert len({tuple(spec["holdout_terms"]) for spec in specs}) == len(specs)


def test_summarize_split_scan_handles_empty_rows() -> None:
    summary = summarize_required_term_split_scan([])

    assert summary["split_scan_decision"] == "no_split_scan_rows"
    assert summary["split_count"] == 0


def write_micro_training_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_micro_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "examples": [
                {"term": "because", "case": "a", "scaffold_prompt": "because:"},
                {"term": "chain", "case": "b", "scaffold_prompt": "chain:"},
                {"term": "data", "case": "c", "scaffold_prompt": "data:"},
                {"term": "fixed", "case": "d", "scaffold_prompt": "fixed:"},
                {"term": "four", "case": "e", "scaffold_prompt": "four:"},
                {"term": "while", "case": "f", "scaffold_prompt": "while:"},
            ],
        },
    )
    return source


def fake_holdout_builder(train_hits: dict[str, int], holdout_hits: dict[str, int]):
    def build(_micro_report: dict[str, object], *, out_dir: Path, holdout_terms: list[str], **_kwargs) -> dict[str, object]:
        split_id = out_dir.name
        train_hit = train_hits.get(split_id, 0)
        holdout_hit = holdout_hits.get(split_id, 0)
        status = "pass"
        return {
            "status": status,
            "decision": "required_term_holdout_uptake_observed" if holdout_hit else "required_term_holdout_no_uptake",
            "summary": {
                "holdout_decision": "heldout_required_term_uptake_observed" if holdout_hit else "training_slice_only_without_holdout_uptake",
                "train_example_count": 4,
                "holdout_example_count": len(holdout_terms),
                "train_continuation_hit_count": train_hit,
                "holdout_continuation_hit_count": holdout_hit,
                "train_hit_rate": 0.25 if train_hit else 0.0,
                "holdout_hit_rate": 0.25 if holdout_hit else 0.0,
            },
        }

    return build


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
