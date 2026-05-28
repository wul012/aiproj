from __future__ import annotations

from pathlib import Path

from minigpt.model_capability_token_budget_probe import (
    build_model_capability_token_budget_probe_report,
    parse_token_caps,
    summarize_token_budget_probe,
)
from minigpt.model_capability_token_budget_probe_artifacts import (
    render_model_capability_token_budget_probe_text,
    write_model_capability_token_budget_probe_outputs,
)


def test_token_budget_probe_detects_relief() -> None:
    report = build_model_capability_token_budget_probe_report(
        [
            _diagnostic(token_cap=4, token_stalls=10, improved=0, pass_transitions=0),
            _diagnostic(token_cap=12, token_stalls=6, improved=3, pass_transitions=1),
        ],
        out_dir="runs/probe",
        run_config={"token_caps": [4, 12]},
        generated_at="2026-01-01T00:00:00Z",
    )

    assert report["status"] == "pass"
    assert report["decision"] == "token_budget_probe_ready"
    assert report["summary"]["decision"] == "longer_token_budget_reduces_eval_stall"
    assert report["summary"]["token_budget_or_shape_limit_delta"] == -4.0
    assert report["summary"]["score_improved_count_delta"] == 3.0
    assert report["summary"]["persistent_fail_count_delta"] == -1.0
    assert report["interpretation"]["model_quality_claim"] == "not_claimed"
    assert "summary_decision=longer_token_budget_reduces_eval_stall" in render_model_capability_token_budget_probe_text(report)


def test_token_budget_probe_reports_still_blocked() -> None:
    summary = summarize_token_budget_probe(
        [
            _row(token_cap=4, token_stalls=10, improved=0, pass_transitions=0),
            _row(token_cap=12, token_stalls=10, improved=0, pass_transitions=0),
        ]
    )

    assert summary["decision"] == "longer_token_budget_still_blocked"
    assert summary["token_budget_or_shape_limit_delta"] == 0.0


def test_token_budget_probe_detects_persistent_fail_relief() -> None:
    summary = summarize_token_budget_probe(
        [
            _row(token_cap=4, token_stalls=10, improved=0, pass_transitions=0, persistent_fail_count=10),
            _row(token_cap=12, token_stalls=10, improved=0, pass_transitions=0, persistent_fail_count=2),
        ]
    )

    assert summary["decision"] == "longer_token_budget_reduces_eval_stall"
    assert summary["persistent_fail_count_delta"] == -8.0


def test_token_budget_probe_validates_inputs() -> None:
    report = build_model_capability_token_budget_probe_report(
        [_diagnostic(token_cap=4, token_stalls=10, improved=0, pass_transitions=0)],
        out_dir="runs/probe",
        run_config={},
    )

    assert report["status"] == "fail"
    assert "at least two token budgets are required" in report["issues"]


def test_parse_token_caps_validates_unique_positive_values() -> None:
    assert parse_token_caps("12,4") == [4, 12]

    for value in ("", "0,4", "4,4"):
        try:
            parse_token_caps(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {value!r}")


def test_token_budget_probe_writes_all_outputs(tmp_path: Path) -> None:
    report = build_model_capability_token_budget_probe_report(
        [
            _diagnostic(token_cap=4, token_stalls=10, improved=0, pass_transitions=0),
            _diagnostic(token_cap=12, token_stalls=6, improved=3, pass_transitions=1),
        ],
        out_dir=tmp_path,
        run_config={"token_caps": [4, 12]},
    )

    outputs = write_model_capability_token_budget_probe_outputs(report, tmp_path)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert all(Path(path).is_file() for path in outputs.values())
    assert "MiniGPT Model Capability Token Budget Probe" in Path(outputs["markdown"]).read_text(encoding="utf-8")
    assert "longer_token_budget_reduces_eval_stall" in Path(outputs["html"]).read_text(encoding="utf-8")


def _diagnostic(
    *,
    token_cap: int,
    token_stalls: int,
    improved: int,
    pass_transitions: int,
    persistent_fail_count: int | None = None,
) -> dict[str, object]:
    return {
        "case_token_cap": token_cap,
        "status": "pass",
        "decision": "capability_stall_diagnostic_ready",
        "out_dir": f"runs/token-cap-{token_cap}/stall-diagnostic",
        "summary": {
            "case_count": 10,
            "score_improved_count": improved,
            "score_degraded_count": 0,
            "score_unchanged_count": 10 - improved,
            "persistent_fail_count": 10 - pass_transitions if persistent_fail_count is None else persistent_fail_count,
            "pass_transition_count": pass_transitions,
            "preview_changed_count": improved,
            "token_budget_or_shape_limit_count": token_stalls,
            "avg_score_delta": 0.0,
            "decision": "token_budget_or_shape_limits_block_eval_signal",
        },
    }


def _row(
    *,
    token_cap: int,
    token_stalls: int,
    improved: int,
    pass_transitions: int,
    persistent_fail_count: int | None = None,
) -> dict[str, object]:
    return {
        "case_token_cap": token_cap,
        "status": "pass",
        "token_budget_or_shape_limit_count": token_stalls,
        "score_improved_count": improved,
        "pass_transition_count": pass_transitions,
        "persistent_fail_count": 10 - pass_transitions if persistent_fail_count is None else persistent_fail_count,
        "avg_score_delta": 0.0,
        "summary_decision": "token_budget_or_shape_limits_block_eval_signal",
    }
