from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_required_term_scaffold_probe import (
    build_model_capability_required_term_scaffold_probe,
    locate_model_capability_required_term_uptake,
    read_json_report,
    summarize_required_term_scaffold_probe,
)
from minigpt.model_capability_required_term_scaffold_probe_artifacts import (
    render_model_capability_required_term_scaffold_probe_markdown,
    render_model_capability_required_term_scaffold_probe_text,
    write_model_capability_required_term_scaffold_probe_outputs,
)
from scripts.run_model_capability_required_term_scaffold_probe import resolve_exit_code


def test_scaffold_probe_detects_explicit_scaffold_still_no_uptake(tmp_path: Path) -> None:
    source = write_scaffold_fixture(tmp_path)

    report = build_model_capability_required_term_scaffold_probe(
        read_json_report(source),
        out_dir=tmp_path / "probe",
        source_path=source,
        search_base=tmp_path,
        generated_at="2026-05-29T00:00:00Z",
        generate_func=fake_generator("noise only"),
    )
    summary = report["summary"]
    text = render_model_capability_required_term_scaffold_probe_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "required_term_scaffold_probe_ready"
    assert summary["probe_decision"] == "explicit_scaffold_still_no_required_term_uptake"
    assert summary["baseline_continuation_hit_count"] == 0
    assert summary["scaffold_prompt_hit_count"] == 1
    assert summary["scaffold_continuation_hit_count"] == 0
    assert "probe_decision=explicit_scaffold_still_no_required_term_uptake" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_scaffold_probe_detects_partial_scaffold_improvement(tmp_path: Path) -> None:
    source = write_scaffold_fixture(tmp_path)

    report = build_model_capability_required_term_scaffold_probe(
        read_json_report(source),
        out_dir=tmp_path / "probe",
        source_path=source,
        search_base=tmp_path,
        generate_func=fake_generator("data appears now"),
    )

    assert report["summary"]["probe_decision"] == "scaffold_prompt_partially_improves_required_term_uptake"
    assert report["summary"]["scaffold_continuation_hit_count"] == 1


def test_scaffold_probe_reports_missing_checkpoint_material(tmp_path: Path) -> None:
    source = write_scaffold_fixture(tmp_path, checkpoint=False)

    report = build_model_capability_required_term_scaffold_probe(
        read_json_report(source),
        out_dir=tmp_path / "probe",
        source_path=source,
        search_base=tmp_path,
        generate_func=fake_generator("data appears now"),
    )

    assert report["status"] == "fail"
    assert "case classification-risk-level scaffold source is incomplete" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_scaffold_probe_writes_all_outputs(tmp_path: Path) -> None:
    source = write_scaffold_fixture(tmp_path)
    report = build_model_capability_required_term_scaffold_probe(
        read_json_report(source),
        out_dir=tmp_path / "probe",
        source_path=source,
        search_base=tmp_path,
        generate_func=fake_generator("noise only"),
    )

    outputs = write_model_capability_required_term_scaffold_probe_outputs(report, tmp_path / "probe")
    markdown = render_model_capability_required_term_scaffold_probe_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["probe_count"] == 1
    assert "classification-risk-level" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Required-Term Scaffold Probe" in markdown
    assert "explicit_scaffold_still_no_required_term_uptake" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_scaffold_probe_helpers_accept_file_or_directory(tmp_path: Path) -> None:
    source = write_scaffold_fixture(tmp_path)

    assert locate_model_capability_required_term_uptake(source) == source
    assert locate_model_capability_required_term_uptake(source.parent) == source


def test_summarize_scaffold_probe_handles_empty_rows() -> None:
    summary = summarize_required_term_scaffold_probe([], [], [])

    assert summary["probe_decision"] == "no_required_term_gap"
    assert summary["probe_count"] == 0


def write_scaffold_fixture(root: Path, *, checkpoint: bool = True) -> Path:
    eval_suite = (
        root
        / "seeds"
        / "seed-1337"
        / "token-cap-12"
        / "ladder"
        / "rungs"
        / "max-iters-4"
        / "run"
        / "eval_suite"
        / "eval_suite.json"
    )
    write_json(
        eval_suite,
        {
            "results": [
                {
                    "name": "classification-risk-level",
                    "prompt": "Classify the release state.",
                    "expected_behavior": "Must include data and validation.",
                    "generated": "Classify the release state.noise",
                    "continuation": "noise",
                }
            ]
        },
    )
    run_dir = eval_suite.parent.parent
    if checkpoint:
        (run_dir / "checkpoint.pt").write_text("fake", encoding="utf-8")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    source = root / "model_capability_required_term_uptake.json"
    write_json(
        source,
        {
            "summary": {"uptake_decision": "required_terms_never_generated"},
            "observations": [
                {
                    "seed": 1337,
                    "token_cap": 12,
                    "case": "classification-risk-level",
                    "task_type": "classification",
                    "term": "data",
                    "max_iters": 4,
                    "token_cap_root": str(root / "seeds" / "seed-1337" / "token-cap-12"),
                    "eval_suite_path": str(eval_suite),
                },
                {
                    "seed": 1337,
                    "token_cap": 12,
                    "case": "classification-risk-level",
                    "task_type": "classification",
                    "term": "validation",
                    "max_iters": 4,
                    "token_cap_root": str(root / "seeds" / "seed-1337" / "token-cap-12"),
                    "eval_suite_path": str(eval_suite),
                },
            ],
        },
    )
    return source


def fake_generator(continuation: str):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
