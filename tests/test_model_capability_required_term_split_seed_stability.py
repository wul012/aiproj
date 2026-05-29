from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_split_seed_stability import (
    build_model_capability_required_term_split_seed_stability,
    locate_model_capability_required_term_split_scan,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_split_seed_stability,
)
from minigpt.model_capability_required_term_split_seed_stability_artifacts import (
    render_model_capability_required_term_split_seed_stability_markdown,
    render_model_capability_required_term_split_seed_stability_text,
    write_model_capability_required_term_split_seed_stability_outputs,
)


def test_seed_stability_detects_stable_train_slice_without_holdout(tmp_path: Path, monkeypatch) -> None:
    split_scan = write_split_scan_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_seed_stability.build_model_capability_required_term_holdout",
        fake_holdout_builder({11: (4, 0), 22: (3, 0)}),
    )

    report = build_model_capability_required_term_split_seed_stability(
        read_json_report(split_scan),
        out_dir=tmp_path / "stability",
        source_path=split_scan,
        seeds=[11, 22],
        generated_at="2026-05-29T00:00:00Z",
    )
    text = render_model_capability_required_term_split_seed_stability_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_seed_stability_train_slice_stable"
    assert report["summary"]["stable_train_repro"] is True
    assert report["summary"]["stable_holdout_zero"] is True
    assert "seed_stability_decision=train_slice_uptake_stable_without_holdout" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_seed_stability_detects_partial_train_slice_signal(tmp_path: Path, monkeypatch) -> None:
    split_scan = write_split_scan_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_seed_stability.build_model_capability_required_term_holdout",
        fake_holdout_builder({11: (4, 0), 22: (0, 0)}),
    )

    report = build_model_capability_required_term_split_seed_stability(
        read_json_report(split_scan),
        out_dir=tmp_path / "stability",
        source_path=split_scan,
        seeds=[11, 22],
    )

    assert report["decision"] == "required_term_seed_stability_train_slice_partial"
    assert report["summary"]["train_repro_seed_count"] == 1


def test_seed_stability_detects_heldout_seed_signal(tmp_path: Path, monkeypatch) -> None:
    split_scan = write_split_scan_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_seed_stability.build_model_capability_required_term_holdout",
        fake_holdout_builder({11: (4, 1), 22: (4, 0)}),
    )

    report = build_model_capability_required_term_split_seed_stability(
        read_json_report(split_scan),
        out_dir=tmp_path / "stability",
        source_path=split_scan,
        seeds=[11, 22],
    )

    assert report["decision"] == "required_term_seed_stability_holdout_uptake_seen"
    assert report["summary"]["holdout_hit_seed_count"] == 1


def test_seed_stability_reports_missing_micro_source(tmp_path: Path) -> None:
    split_scan = tmp_path / "model_capability_required_term_split_scan.json"
    write_json(
        split_scan,
        {
            "status": "pass",
            "source_required_term_micro_training": str(tmp_path / "missing.json"),
            "summary": {"best_split_id": "split-4"},
            "scan_rows": [{"id": "split-4", "holdout_terms": ["four", "while"], "train_continuation_hit_count": 4}],
        },
    )

    report = build_model_capability_required_term_split_seed_stability(
        read_json_report(split_scan),
        out_dir=tmp_path / "stability",
        source_path=split_scan,
        seeds=[11],
    )

    assert report["status"] == "fail"
    assert "source required-term micro-training report could not be resolved" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_seed_stability_writes_all_outputs(tmp_path: Path, monkeypatch) -> None:
    split_scan = write_split_scan_fixture(tmp_path)
    monkeypatch.setattr(
        "minigpt.model_capability_required_term_split_seed_stability.build_model_capability_required_term_holdout",
        fake_holdout_builder({11: (4, 0)}),
    )
    report = build_model_capability_required_term_split_seed_stability(
        read_json_report(split_scan),
        out_dir=tmp_path / "stability",
        source_path=split_scan,
        seeds=[11],
    )

    outputs = write_model_capability_required_term_split_seed_stability_outputs(report, tmp_path / "stability")
    markdown = render_model_capability_required_term_split_seed_stability_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["seed_count"] == 1
    assert "11" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Split Seed Stability" in markdown


def test_locate_seed_stability_source_accepts_file_or_directory(tmp_path: Path) -> None:
    split_scan = write_split_scan_fixture(tmp_path)

    assert locate_model_capability_required_term_split_scan(split_scan) == split_scan
    assert locate_model_capability_required_term_split_scan(split_scan.parent) == split_scan


def test_summarize_seed_stability_handles_empty_rows() -> None:
    summary = summarize_required_term_split_seed_stability([])

    assert summary["seed_stability_decision"] == "no_seed_stability_rows"
    assert summary["seed_count"] == 0


def write_split_scan_fixture(root: Path) -> Path:
    micro = root / "model_capability_required_term_micro_training.json"
    write_json(micro, {"status": "pass", "examples": [{"term": "four"}, {"term": "while"}, {"term": "data"}]})
    split_scan = root / "model_capability_required_term_split_scan.json"
    write_json(
        split_scan,
        {
            "status": "pass",
            "source_required_term_micro_training": str(micro),
            "settings": {"max_iters": 10, "eval_iters": 1, "batch_size": 2, "block_size": 8, "n_embd": 8},
            "summary": {"best_split_id": "split-4"},
            "scan_rows": [
                {"id": "split-1", "holdout_terms": ["data"], "train_continuation_hit_count": 0},
                {"id": "split-4", "holdout_terms": ["four", "while"], "train_continuation_hit_count": 4},
            ],
        },
    )
    return split_scan


def fake_holdout_builder(results: dict[int, tuple[int, int]]):
    def build(_micro_report: dict[str, object], *, out_dir: Path, generation_seed: int, **_kwargs) -> dict[str, object]:
        train_hit, holdout_hit = results.get(int(generation_seed), (0, 0))
        return {
            "status": "pass",
            "decision": "required_term_holdout_uptake_observed" if holdout_hit else "required_term_holdout_no_uptake",
            "summary": {
                "holdout_decision": "heldout_required_term_uptake_observed" if holdout_hit else "training_slice_only_without_holdout_uptake",
                "train_example_count": 4,
                "holdout_example_count": 2,
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
