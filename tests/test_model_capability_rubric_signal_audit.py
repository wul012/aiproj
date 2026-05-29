from __future__ import annotations

import json
from pathlib import Path

from minigpt.model_capability_rubric_signal_audit import (
    build_model_capability_rubric_signal_audit,
    locate_token_budget_stability_report,
    read_json_report,
    summarize_rubric_signal,
)
from minigpt.model_capability_rubric_signal_audit_artifacts import (
    render_model_capability_rubric_signal_audit_markdown,
    render_model_capability_rubric_signal_audit_text,
    write_model_capability_rubric_signal_audit_outputs,
)
from scripts.audit_model_capability_rubric_signal import resolve_exit_code


def test_rubric_signal_audit_detects_required_terms_domination(tmp_path: Path) -> None:
    source = write_audit_fixture(tmp_path)

    report = build_model_capability_rubric_signal_audit(
        read_json_report(source),
        out_dir=tmp_path / "audit",
        source_path=source,
        search_base=tmp_path,
        target_token_cap=12,
        generated_at="2026-05-29T00:00:00Z",
    )
    summary = report["summary"]
    text = render_model_capability_rubric_signal_audit_text(report)

    assert report["status"] == "pass"
    assert report["decision"] == "rubric_signal_audit_ready"
    assert summary["decision"] == "rubric_required_terms_dominate_flat_scores"
    assert summary["dominant_failed_checks"]["must_include"] == 4
    assert summary["dominant_stall_reasons"]["required_terms_missing"] == 2
    assert summary["cross_seed_failed_checks"] == ["must_include"]
    assert "audit_decision=rubric_required_terms_dominate_flat_scores" in text
    assert resolve_exit_code(report, require_pass=True) == 0


def test_rubric_signal_audit_selects_largest_token_cap_by_default(tmp_path: Path) -> None:
    source = write_audit_fixture(tmp_path)
    report = build_model_capability_rubric_signal_audit(
        read_json_report(source),
        out_dir=tmp_path / "audit",
        source_path=source,
        search_base=tmp_path,
    )

    assert report["target_token_cap"] == 12
    assert {seed["token_cap"] for seed in report["seeds"]} == {12}


def test_rubric_signal_audit_reports_missing_inputs(tmp_path: Path) -> None:
    report = build_model_capability_rubric_signal_audit(
        {"rows": [{"seed": 1337, "report_path": "missing.json"}]},
        out_dir=tmp_path / "audit",
        search_base=tmp_path,
    )

    assert report["status"] == "fail"
    assert "seed-1337 rubric signal inputs are incomplete" in report["issues"]
    assert "no stall diagnostic cases found for rubric signal audit" in report["issues"]
    assert resolve_exit_code(report, require_pass=True) == 1


def test_summarize_rubric_signal_detects_progress() -> None:
    summary = summarize_rubric_signal(
        [
            {
                "first_status": "fail",
                "last_status": "pass",
                "score_delta": 5.0,
                "stall_reason": "case_passed",
                "last_failed_checks": [],
                "last_missing_terms": [],
            }
        ],
        [{"token_cap": 12, "status": "pass"}],
    )

    assert summary["decision"] == "some_rubric_progress_visible"
    assert summary["score_improved_count"] == 1
    assert summary["pass_transition_count"] == 1


def test_rubric_signal_audit_writes_all_outputs(tmp_path: Path) -> None:
    source = write_audit_fixture(tmp_path)
    report = build_model_capability_rubric_signal_audit(
        read_json_report(source),
        out_dir=tmp_path / "audit",
        source_path=source,
        search_base=tmp_path,
        target_token_cap=12,
    )

    outputs = write_model_capability_rubric_signal_audit_outputs(report, tmp_path / "audit")
    markdown = render_model_capability_rubric_signal_audit_markdown(report)

    assert set(outputs) == {"json", "csv", "text", "markdown", "html"}
    assert json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["case_count"] == 4
    assert "must_include" in Path(outputs["csv"]).read_text(encoding="utf-8")
    assert "MiniGPT Model Capability Rubric Signal Audit" in markdown
    assert "rubric_required_terms_dominate_flat_scores" in Path(outputs["html"]).read_text(encoding="utf-8")


def test_locate_token_budget_stability_report_accepts_file_or_directory(tmp_path: Path) -> None:
    source = tmp_path / "model_capability_token_budget_stability.json"
    source.write_text("{}", encoding="utf-8")

    assert locate_token_budget_stability_report(source) == source
    assert locate_token_budget_stability_report(tmp_path) == source


def write_audit_fixture(root: Path) -> Path:
    rows = []
    for seed in (1337, 2026):
        seed_dir = root / "seeds" / f"seed-{seed}"
        probe_path = seed_dir / "model_capability_token_budget_probe.json"
        cap4_diag = seed_dir / "token-cap-4" / "stall-diagnostic"
        cap12_diag = seed_dir / "token-cap-12" / "stall-diagnostic"
        write_json(cap4_diag / "model_capability_stall_diagnostic.json", diagnostic(seed, token_cap=4, task_shape=True))
        write_json(cap12_diag / "model_capability_stall_diagnostic.json", diagnostic(seed, token_cap=12, task_shape=False))
        write_json(
            probe_path,
            {
                "status": "pass",
                "rows": [
                    {"case_token_cap": 4, "status": "pass", "source_diagnostic": str(cap4_diag)},
                    {"case_token_cap": 12, "status": "pass", "source_diagnostic": str(cap12_diag)},
                ],
            },
        )
        rows.append({"seed": seed, "status": "pass", "report_path": str(probe_path)})
    source = root / "model_capability_token_budget_stability.json"
    write_json(source, {"status": "pass", "rows": rows})
    return source


def diagnostic(seed: int, *, token_cap: int, task_shape: bool) -> dict[str, object]:
    failed_checks = ["must_include", "task_shape"] if task_shape else ["must_include"]
    cases = [
        {
            "seed": seed,
            "case": f"case-{token_cap}-terms",
            "task_type": "qa",
            "difficulty": "medium",
            "first_status": "fail",
            "last_status": "fail",
            "first_score": 35.0,
            "last_score": 35.0,
            "score_delta": 0.0,
            "stall_reason": "required_terms_missing",
            "last_failed_checks": failed_checks,
            "last_missing_terms": ["data", "validation"],
            "preview_changed": True,
        },
        {
            "seed": seed,
            "case": f"case-{token_cap}-unchanged",
            "task_type": "summary",
            "difficulty": "easy",
            "first_status": "pass",
            "last_status": "pass",
            "first_score": 83.33,
            "last_score": 83.33,
            "score_delta": 0.0,
            "stall_reason": "case_passed",
            "last_failed_checks": ["must_include"],
            "last_missing_terms": ["concise"],
            "preview_changed": False,
        },
    ]
    return {
        "status": "pass",
        "summary": {
            "case_count": len(cases),
            "score_improved_count": 0,
            "persistent_fail_count": 1,
            "pass_transition_count": 0,
            "preview_changed_count": 1,
            "token_budget_or_shape_limit_count": 1 if task_shape else 0,
            "dominant_stall_reasons": {"required_terms_missing": 1, "case_passed": 1},
            "dominant_failed_checks": {"must_include": 2, "task_shape": 1} if task_shape else {"must_include": 2},
            "dominant_missing_terms": {"data": 1, "validation": 1, "concise": 1},
        },
        "cases": cases,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
