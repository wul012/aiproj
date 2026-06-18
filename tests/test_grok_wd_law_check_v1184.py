from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.grok_wd_law_check_v1184 import (  # noqa: E402
    build_grok_wd_law_check,
    write_grok_wd_law_check_outputs,
)


def _wd_report() -> dict:
    wds = [0.0, 0.1, 0.3, 1.0, 3.0]
    rows = [
        _dose_row(0.0, grok_rate=0.0, n_grokked=0, t_gen_mean=None, final_val_mean=0.16),
        _dose_row(0.1, grok_rate=0.2, n_grokked=1, t_gen_mean=38000.0, final_val_mean=0.72),
        _dose_row(0.3, grok_rate=1.0, n_grokked=5, t_gen_mean=26560.0, final_val_mean=0.96),
        _dose_row(1.0, grok_rate=1.0, n_grokked=5, t_gen_mean=14920.0, final_val_mean=0.96),
        _dose_row(3.0, grok_rate=0.0, n_grokked=0, t_gen_mean=None, final_val_mean=0.20),
    ]
    return {
        "schema_version": 1,
        "title": "fixture wd law",
        "status": "pass",
        "decision": "wd_dose_response_interior_optimum",
        "summary": {
            "seeds": 5,
            "wds": wds,
            "verdict": "wd_dose_response_interior_optimum",
            "g0_task_correct": True,
            "g1_memorization": True,
            "g2_grid_complete": True,
            "grok_wds": [0.3, 1.0],
            "grok_threshold_wd": 0.3,
            "fastest_grok_wd": 1.0,
            "censored_below_threshold": True,
            "high_end_grok_censored": True,
            "interior_optimum": True,
            "too_much_wd_breaks_memorization": False,
            "monotone_t_gen_decrease": True,
            "strongest_groks_sooner_significant": True,
            "boundary": "toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim",
        },
        "rows": rows,
        "seed_rows": _seed_rows(wds),
    }


def _dose_row(wd: float, *, grok_rate: float, n_grokked: int, t_gen_mean: float | None, final_val_mean: float) -> dict:
    return {
        "weight_decay": wd,
        "grok_rate": grok_rate,
        "mem_rate": 1.0,
        "n_grokked": n_grokked,
        "t_gen_mean": t_gen_mean,
        "t_gen_std": 100.0 if t_gen_mean is not None else 0.0,
        "grok_gap_mean": (t_gen_mean - 200) if t_gen_mean is not None else None,
        "final_val_mean": final_val_mean,
    }


def _seed_rows(wds: list[float]) -> list[dict]:
    rows = []
    for seed in range(5):
        for wd in wds:
            grokked = wd in {0.3, 1.0}
            rows.append(
                {
                    "seed": seed,
                    "weight_decay": wd,
                    "memorized": True,
                    "grokked": grokked,
                    "t_mem": 200,
                    "t_gen": 26560 if wd == 0.3 else (14920 if wd == 1.0 else None),
                    "grok_gap": 26360 if wd == 0.3 else (14720 if wd == 1.0 else None),
                    "final_train_acc": 1.0,
                    "final_val_acc": 0.96 if grokked else 0.16,
                    "steps_run": 40000,
                }
            )
    return rows


def test_reconstructs_interior_optimum_from_rows() -> None:
    report = build_grok_wd_law_check(_wd_report(), generated_at="now")

    assert report["status"] == "pass"
    assert report["decision"] == "wd_law_interior_optimum_reconstructed"
    assert report["summary"]["computed_threshold_wd"] == 0.3
    assert report["summary"]["computed_fastest_wd"] == 1.0
    assert report["summary"]["low_end_censored"] is True
    assert report["summary"]["high_end_censored"] is True
    assert report["failed_count"] == 0


def test_monotone_overclaim_is_rejected() -> None:
    payload = _wd_report()
    payload["decision"] = "wd_dose_response_monotone_acceleration"
    payload["summary"]["verdict"] = "wd_dose_response_monotone_acceleration"
    payload["summary"]["interior_optimum"] = False

    report = build_grok_wd_law_check(payload, generated_at="now")

    assert report["status"] == "fail"
    issue_ids = {issue["id"] for issue in report["issues"]}
    assert "source_verdict_interior_optimum" in issue_ids
    assert "not_monotone_acceleration_claim" in issue_ids


def test_strongest_dose_grokking_breaks_high_end_censoring() -> None:
    payload = _wd_report()
    payload["rows"][-1]["grok_rate"] = 1.0
    payload["rows"][-1]["n_grokked"] = 5
    payload["rows"][-1]["t_gen_mean"] = 8000.0
    payload["summary"]["high_end_grok_censored"] = False
    payload["summary"]["fastest_grok_wd"] = 3.0

    report = build_grok_wd_law_check(payload, generated_at="now")

    assert report["status"] == "fail"
    issue_ids = {issue["id"] for issue in report["issues"]}
    assert "fastest_is_interior" in issue_ids
    assert "high_end_censored_not_broken" in issue_ids


def test_threshold_mismatch_is_detected() -> None:
    payload = _wd_report()
    payload["summary"]["grok_threshold_wd"] = 0.1

    report = build_grok_wd_law_check(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "grok_threshold_matches_summary" in {issue["id"] for issue in report["issues"]}


def test_strongest_seed_rows_must_memorize_but_not_grok() -> None:
    payload = _wd_report()
    for row in payload["seed_rows"]:
        if row["weight_decay"] == 3.0:
            row["grokked"] = True
            row["t_gen"] = 9000

    report = build_grok_wd_law_check(payload, generated_at="now")

    assert report["status"] == "fail"
    assert "strongest_seed_rows_memorize_not_grok" in {issue["id"] for issue in report["issues"]}


def test_outputs_and_cli_are_wired(tmp_path: Path) -> None:
    source = tmp_path / "grok_wd_law_v1183.json"
    source.write_text(json.dumps(_wd_report()), encoding="utf-8")
    report = build_grok_wd_law_check(source, generated_at="now")
    outputs = write_grok_wd_law_check_outputs(report, tmp_path / "out")

    assert Path(outputs["json"]).is_file()
    assert Path(outputs["html"]).read_text(encoding="utf-8").startswith("<!doctype html>")

    cli_out = tmp_path / "cli"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_grok_wd_law_v1184.py"),
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
    assert (cli_out / "grok_wd_law_check_v1184.json").is_file()
