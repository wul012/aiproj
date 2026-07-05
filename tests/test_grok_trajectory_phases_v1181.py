from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.grok_trajectory_phases_v1181 import (  # noqa: E402
    build_grok_trajectory_phase_report,
    write_grok_trajectory_phase_outputs,
)


def _curve(*, t_mem: int, t_gen: int | None, final_val: float) -> list[dict[str, float | int]]:
    points: list[dict[str, float | int]] = [
        {"step": 0, "train_acc": 0.0, "val_acc": 0.01},
        {"step": t_mem, "train_acc": 1.0, "val_acc": 0.10},
    ]
    if t_gen is None:
        points.extend(
            [
                {"step": 1000, "train_acc": 1.0, "val_acc": 0.11},
                {"step": 40000, "train_acc": 1.0, "val_acc": final_val},
            ]
        )
    else:
        points.extend(
            [
                {"step": t_gen - 100, "train_acc": 1.0, "val_acc": 0.20},
                {"step": t_gen, "train_acc": 1.0, "val_acc": 0.91},
                {"step": t_gen + 100, "train_acc": 1.0, "val_acc": final_val},
            ]
        )
    return points


def _grok_report() -> dict:
    rows = []
    curves = {"1.0": [], "0.0": []}
    for seed, t_gen in [(101, 3000), (102, 5000)]:
        rows.append(
            {
                "seed": seed,
                "weight_decay": 1.0,
                "memorized": True,
                "grokked": True,
                "t_mem": 100,
                "t_gen": t_gen,
                "grok_gap": t_gen - 100,
                "val_at_mem": 0.1001,
                "final_train_acc": 1.0,
                "final_val_acc": 0.95,
                "steps_run": t_gen + 100,
            }
        )
        curves["1.0"].append(_curve(t_mem=100, t_gen=t_gen, final_val=0.95))
        rows.append(
            {
                "seed": seed,
                "weight_decay": 0.0,
                "memorized": True,
                "grokked": False,
                "t_mem": 100,
                "t_gen": None,
                "grok_gap": None,
                "val_at_mem": 0.1002,
                "final_train_acc": 1.0,
                "final_val_acc": 0.15,
                "steps_run": 40000,
            }
        )
        curves["0.0"].append(_curve(t_mem=100, t_gen=None, final_val=0.15))
    return {
        "schema_version": 1,
        "title": "fixture grokking",
        "status": "pass",
        "decision": "grokking_reproduced_wd_driven",
        "summary": {
            "seeds": 2,
            "weight_decay_on": 1.0,
            "weight_decay_off": 0.0,
            "verdict": "grokking_reproduced_wd_driven",
            "boundary": "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
        },
        "rows": rows,
        "curves": curves,
    }


def test_builds_phase_profile_from_curve_rows() -> None:
    report = build_grok_trajectory_phase_report(_grok_report(), generated_at="now")

    assert report["status"] == "pass"
    assert report["decision"] == "grokking_phase_profile_consistent"
    assert report["summary"]["wd_on_delayed_grok_count"] == 2
    assert report["summary"]["wd_off_memorized_censored_count"] == 2
    assert report["summary"]["paired_phase_separation_count"] == 2
    assert {row["phase"] for row in report["rows"]} == {"delayed_grok", "memorized_only_censored"}


def test_missing_curves_fail_the_profile() -> None:
    payload = _grok_report()
    payload["curves"] = {}

    report = build_grok_trajectory_phase_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "curve_grid_complete" in {issue["id"] for issue in report["issues"]}
    assert "rows_have_matching_curves" in {issue["id"] for issue in report["issues"]}


def test_endpoint_tamper_is_detected() -> None:
    payload = _grok_report()
    payload["curves"]["1.0"][0][-1]["val_acc"] = 0.44

    report = build_grok_trajectory_phase_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "curve_endpoints_match_rows" in {issue["id"] for issue in report["issues"]}


def test_no_decay_grok_breaks_paired_phase_separation() -> None:
    payload = _grok_report()
    payload["rows"][1]["grokked"] = True
    payload["rows"][1]["t_gen"] = 3000
    payload["rows"][1]["grok_gap"] = 2900
    payload["rows"][1]["final_val_acc"] = 0.95
    payload["curves"]["0.0"][0] = _curve(t_mem=100, t_gen=3000, final_val=0.95)

    report = build_grok_trajectory_phase_report(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "wd_off_memorized_censored_all_seeds" in {issue["id"] for issue in report["issues"]}
    assert "paired_phase_separation" in {issue["id"] for issue in report["issues"]}


def test_outputs_and_cli_are_wired(tmp_path: Path) -> None:
    source = tmp_path / "grok_v1179.json"
    source.write_text(json.dumps(_grok_report()), encoding="utf-8")
    report = build_grok_trajectory_phase_report(source, generated_at="now")
    outputs = write_grok_trajectory_phase_outputs(report, tmp_path / "out")

    assert Path(outputs["json"]).is_file()
    assert Path(outputs["html"]).read_text(encoding="utf-8").startswith("<!doctype html>")

    cli_out = tmp_path / "cli"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "analyze_grok_trajectory_v1181.py"),
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
    assert (cli_out / "grok_trajectory_phases_v1181.json").is_file()
