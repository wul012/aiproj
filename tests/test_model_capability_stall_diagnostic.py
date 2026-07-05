from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from minigpt.model_capability_stall_diagnostic import (
    build_model_capability_stall_diagnostic,
    locate_stability_report,
    read_json_report,
    summarize_stall_cases,
)
from minigpt.model_capability_stall_diagnostic_artifacts import write_model_capability_stall_diagnostic_outputs

from tests._bootstrap import ROOT


def test_stall_diagnostic_explains_token_budget_limit(tmp_path: Path) -> None:
    stability_path = write_stability_fixture(tmp_path, first_score=35.0, last_score=35.0)
    report = build_model_capability_stall_diagnostic(
        read_json_report(stability_path),
        out_dir=tmp_path / "out",
        source_path=stability_path,
        search_base=tmp_path,
        generated_at="2026-01-01T00:00:00Z",
    )

    assert report["status"] == "pass"
    assert report["summary"]["decision"] == "token_budget_or_shape_limits_block_eval_signal"
    assert report["summary"]["token_budget_or_shape_limit_count"] == 1
    assert report["cases"][0]["stall_reason"] == "token_budget_or_shape_limit"
    assert report["interpretation"]["model_quality_claim"] == "not_claimed"


def test_stall_diagnostic_detects_partial_progress(tmp_path: Path) -> None:
    stability_path = write_stability_fixture(tmp_path, first_score=35.0, last_score=42.5, failed_checks=["must_include"])
    report = build_model_capability_stall_diagnostic(
        read_json_report(stability_path),
        out_dir=tmp_path / "out",
        source_path=stability_path,
        search_base=tmp_path,
    )

    assert report["summary"]["decision"] == "partial_eval_progress_detected"
    assert report["summary"]["score_improved_count"] == 1
    assert report["cases"][0]["score_delta"] == 7.5
    assert report["cases"][0]["stall_reason"] == "partial_rubric_progress"


def test_stall_diagnostic_fails_when_seed_ladder_is_missing(tmp_path: Path) -> None:
    stability_path = tmp_path / "model_capability_ladder_stability.json"
    write_json(
        stability_path,
        {
            "rows": [
                {
                    "seed": 1337,
                    "report_path": "missing/model_capability_ladder.json",
                    "best_val_loss_delta": -0.1,
                }
            ]
        },
    )

    report = build_model_capability_stall_diagnostic(
        read_json_report(stability_path),
        out_dir=tmp_path / "out",
        source_path=stability_path,
        search_base=tmp_path,
    )

    assert report["status"] == "fail"
    assert "seed-1337 diagnostic inputs are incomplete" in report["issues"]


def test_stall_diagnostic_writes_all_outputs(tmp_path: Path) -> None:
    stability_path = write_stability_fixture(tmp_path, first_score=35.0, last_score=35.0)
    report = build_model_capability_stall_diagnostic(
        read_json_report(stability_path),
        out_dir=tmp_path / "out",
        source_path=stability_path,
        search_base=tmp_path,
    )

    outputs = write_model_capability_stall_diagnostic_outputs(report, tmp_path / "out")

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert all(Path(path).is_file() for path in outputs.values())
    assert "MiniGPT Model Capability Stall Diagnostic" in Path(outputs["markdown"]).read_text(encoding="utf-8")
    assert "token_budget_or_shape_limit" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_stall_diagnostic_cli_require_pass_returns_one_on_failure(tmp_path: Path) -> None:
    missing_source = tmp_path / "missing"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "diagnose_model_capability_stall.py"),
            str(missing_source),
            "--out-dir",
            str(tmp_path / "out"),
            "--require-pass",
            "--force",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "status=fail" in completed.stdout


def test_locate_stability_report_accepts_file_or_directory(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_ladder_stability.json"
    source.write_text("{}", encoding="utf-8")

    assert locate_stability_report(source) == source
    assert locate_stability_report(tmp_path) == source


def test_summarize_stall_cases_counts_dominant_failures() -> None:
    summary = summarize_stall_cases(
        [
            {
                "first_status": "fail",
                "last_status": "fail",
                "score_delta": 0.0,
                "stall_reason": "token_budget_or_shape_limit",
                "last_failed_checks": ["length_bounds", "task_shape"],
                "last_missing_terms": ["chinese"],
            }
        ]
    )

    assert summary["persistent_fail_count"] == 1
    assert summary["dominant_failed_checks"]["length_bounds"] == 1
    assert summary["dominant_missing_terms"]["chinese"] == 1


def write_stability_fixture(
    root: Path,
    *,
    first_score: float,
    last_score: float,
    failed_checks: list[str] | None = None,
) -> Path:
    seed_dir = root / "seeds" / "seed-1337"
    first_run = seed_dir / "rungs" / "max-iters-1" / "run"
    last_run = seed_dir / "rungs" / "max-iters-4" / "run"
    write_rung_artifacts(first_run, score=first_score, preview="abcd", failed_checks=["length_bounds", "task_shape"])
    write_rung_artifacts(last_run, score=last_score, preview="wxyz", failed_checks=failed_checks or ["length_bounds", "task_shape"])
    ladder_path = seed_dir / "model_capability_ladder.json"
    write_json(
        ladder_path,
        {
            "rows": [
                {"max_iters": 1, "run_dir": str(first_run)},
                {"max_iters": 4, "run_dir": str(last_run)},
            ]
        },
    )
    stability_path = root / "model_capability_ladder_stability.json"
    write_json(
        stability_path,
        {
            "rows": [
                {
                    "seed": 1337,
                    "report_path": str(ladder_path),
                    "best_val_loss_delta": -0.1,
                    "score_delta": round(last_score - first_score, 4),
                    "generation_flags_delta": 0.0,
                }
            ]
        },
    )
    return stability_path


def write_rung_artifacts(run_dir: Path, *, score: float, preview: str, failed_checks: list[str]) -> None:
    write_json(
        run_dir / "benchmark-scorecard" / "benchmark_scorecard.json",
        {
            "rubric_scores": {
                "cases": [
                    {
                        "name": "continuation-science",
                        "task_type": "continuation",
                        "difficulty": "easy",
                        "status": "fail",
                        "score": score,
                        "failed_checks": failed_checks,
                        "missing_terms": ["chinese", "research"],
                    }
                ]
            }
        },
    )
    write_json(
        run_dir / "generation-quality" / "generation_quality.json",
        {"cases": [{"name": "continuation-science", "continuation_preview": preview, "flag_count": 0}]},
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
