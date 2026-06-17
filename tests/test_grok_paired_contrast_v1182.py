from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.grok_paired_contrast_v1182 import (  # noqa: E402
    build_grok_paired_contrast_report,
    write_grok_paired_contrast_outputs,
)


def _phase_report() -> dict:
    rows = []
    for seed, t_gen, final_gain in [(101, 3000, 0.80), (102, 5000, 0.76)]:
        rows.append(
            {
                "seed": seed,
                "arm": "weight_decay_on",
                "weight_decay": 1.0,
                "phase": "delayed_grok",
                "memorized": True,
                "grokked": True,
                "t_mem": 100,
                "t_gen": t_gen,
                "grok_gap": t_gen - 100,
                "steps_run": t_gen + 100,
                "low_val_plateau_rate": 0.9,
                "final_val_acc": 0.95,
            }
        )
        rows.append(
            {
                "seed": seed,
                "arm": "weight_decay_off",
                "weight_decay": 0.0,
                "phase": "memorized_only_censored",
                "memorized": True,
                "grokked": False,
                "t_mem": 100,
                "t_gen": None,
                "grok_gap": None,
                "steps_run": 40000,
                "low_val_plateau_rate": 1.0,
                "final_val_acc": 0.95 - final_gain,
            }
        )
    return {
        "schema_version": 1,
        "title": "fixture phases",
        "status": "pass",
        "decision": "grokking_phase_profile_consistent",
        "summary": {
            "seed_count": 2,
            "row_count": 4,
            "weight_decay_on": 1.0,
            "weight_decay_off": 0.0,
            "boundary": "curve_phase_compression_only_no_training_rerun",
        },
        "rows": rows,
        "phase_rows": rows,
    }


def test_builds_paired_counterfactual_rows() -> None:
    report = build_grok_paired_contrast_report(_phase_report(), generated_at="now")

    assert report["status"] == "pass"
    assert report["decision"] == "grokking_weight_decay_pair_contrast_consistent"
    assert report["summary"]["pair_count"] == 2
    assert report["summary"]["matched_memorization_count"] == 2
    assert report["summary"]["no_decay_censored_count"] == 2
    assert report["summary"]["min_final_val_gain"] == 0.76
    assert {row["pair_status"] for row in report["rows"]} == {"weight_decay_counterfactual"}


def test_missing_off_pair_fails_pair_completeness() -> None:
    payload = _phase_report()
    payload["rows"] = payload["rows"][:-1]
    payload["phase_rows"] = payload["rows"]

    report = build_grok_paired_contrast_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "phase_rows_present" in {issue["id"] for issue in report["issues"]}
    assert "matched_memorization_all_pairs" in {issue["id"] for issue in report["issues"]}


def test_mismatched_memorization_step_fails() -> None:
    payload = _phase_report()
    payload["rows"][1]["t_mem"] = 200
    payload["phase_rows"] = payload["rows"]

    report = build_grok_paired_contrast_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "matched_memorization_all_pairs" in {issue["id"] for issue in report["issues"]}


def test_no_decay_grok_breaks_counterfactual() -> None:
    payload = _phase_report()
    payload["rows"][1]["phase"] = "delayed_grok"
    payload["rows"][1]["grokked"] = True
    payload["rows"][1]["t_gen"] = 3100
    payload["phase_rows"] = payload["rows"]

    report = build_grok_paired_contrast_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "off_memorized_censored_all_pairs" in {issue["id"] for issue in report["issues"]}


def test_small_final_gain_fails_threshold() -> None:
    payload = _phase_report()
    payload["rows"][1]["final_val_acc"] = 0.40
    payload["phase_rows"] = payload["rows"]

    report = build_grok_paired_contrast_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "final_validation_gain_large" in {issue["id"] for issue in report["issues"]}


def test_outputs_and_cli_are_wired(tmp_path: Path) -> None:
    source = tmp_path / "grok_trajectory_phases_v1181.json"
    source.write_text(json.dumps(_phase_report()), encoding="utf-8")
    report = build_grok_paired_contrast_report(source, generated_at="now")
    outputs = write_grok_paired_contrast_outputs(report, tmp_path / "out")

    assert Path(outputs["json"]).is_file()
    assert Path(outputs["html"]).read_text(encoding="utf-8").startswith("<!doctype html>")

    cli_out = tmp_path / "cli"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze_grok_paired_contrast_v1182.py"),
            str(source),
            "--out-dir",
            str(cli_out),
            "--require-pass",
            "--force",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "status=pass" in result.stdout
    assert (cli_out / "grok_paired_contrast_v1182.json").is_file()
