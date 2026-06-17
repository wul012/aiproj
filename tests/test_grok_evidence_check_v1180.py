from __future__ import annotations

import json
from pathlib import Path
import tempfile

from minigpt.grok_evidence_check_v1180 import (
    build_grok_evidence_check,
    locate_grok_report,
    resolve_exit_code,
    write_grok_evidence_check_outputs,
)
from scripts.check_grok_evidence_v1180 import main as cli_main


def test_reconstructs_v1179_grokking_claim_from_rows():
    report = build_grok_evidence_check(_grok_report(), generated_at="2026-06-17T06:00:00Z")

    assert report["status"] == "pass"
    assert report["decision"] == "grokking_evidence_claim_reconstructed"
    assert report["summary"]["wd_on_grok_count"] == 5
    assert report["summary"]["wd_off_grok_count"] == 0
    assert report["summary"]["wd_on_mean_val_at_mem"] < 0.5
    assert resolve_exit_code(report, require_pass=True) == 0


def test_fails_when_validation_was_already_high_at_memorization():
    source = _grok_report()
    for row in source["rows"]:
        if row["weight_decay"] == 1.0:
            row["val_at_mem"] = 0.82
    report = build_grok_evidence_check(source)

    assert report["status"] == "fail"
    assert "delay_real" in [issue["id"] for issue in report["issues"]]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_fails_when_no_decay_ablation_groks():
    source = _grok_report()
    source["summary"]["wd_off_grok_rate"] = 0.2
    for row in source["rows"]:
        if row["weight_decay"] == 0.0 and row["seed"] == 1337:
            row["grokked"] = True
            row["t_gen"] = 30000
            row["grok_gap"] = 29900
            row["final_val_acc"] = 0.92
    report = build_grok_evidence_check(source)

    assert report["status"] == "fail"
    ids = [issue["id"] for issue in report["issues"]]
    assert "wd_off_did_not_grok" in ids


def test_outputs_and_cli_are_wired():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_dir = root / "source"
        source_dir.mkdir()
        (source_dir / "grok_v1179.json").write_text(json.dumps(_grok_report()), encoding="utf-8")
        assert locate_grok_report(source_dir) == source_dir / "grok_v1179.json"

        outputs = write_grok_evidence_check_outputs(build_grok_evidence_check(source_dir), root / "out")
        exit_code = cli_main([str(source_dir), "--out-dir", str(root / "cli-out"), "--require-pass", "--force"])

    assert exit_code == 0
    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}


def _grok_report() -> dict[str, object]:
    rows = []
    for seed, t_gen, val_at_mem in [
        (1337, 11400, 0.1112),
        (1338, 12700, 0.1951),
        (1339, 10500, 0.1414),
        (1340, 14600, 0.1573),
        (1341, 25200, 0.1295),
    ]:
        rows.append(_row(seed=seed, wd=1.0, grokked=True, t_gen=t_gen, val_at_mem=val_at_mem, final_val=0.96))
        rows.append(_row(seed=seed, wd=0.0, grokked=False, t_gen=None, val_at_mem=val_at_mem, final_val=0.16))
    return {
        "schema_version": 1,
        "title": "MiniGPT v1179 grokking (delayed generalization)",
        "status": "pass",
        "decision": "grokking_reproduced_wd_driven",
        "summary": {
            "seeds": 5,
            "weight_decay_on": 1.0,
            "weight_decay_off": 0.0,
            "verdict": "grokking_reproduced_wd_driven",
            "wd_on_grok_rate": 1.0,
            "wd_off_grok_rate": 0.0,
            "boundary": "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
        },
        "rows": rows,
    }


def _row(*, seed: int, wd: float, grokked: bool, t_gen: int | None, val_at_mem: float, final_val: float) -> dict[str, object]:
    return {
        "seed": seed,
        "weight_decay": wd,
        "memorized": True,
        "grokked": grokked,
        "t_mem": 100,
        "t_gen": t_gen,
        "grok_gap": (t_gen - 100) if t_gen is not None else None,
        "val_at_mem": val_at_mem,
        "final_train_acc": 1.0,
        "final_val_acc": final_val,
        "steps_run": 40000 if t_gen is None else t_gen + 200,
    }
