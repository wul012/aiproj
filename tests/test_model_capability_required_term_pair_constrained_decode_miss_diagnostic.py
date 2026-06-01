from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_constrained_decode_miss_diagnostic import (
    build_model_capability_required_term_pair_constrained_decode_miss_diagnostic,
    locate_pair_constrained_decode_miss_diagnostic_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_constrained_decode_miss_diagnostic_artifacts import (
    render_pair_constrained_decode_miss_diagnostic_html,
    render_pair_constrained_decode_miss_diagnostic_markdown,
    render_pair_constrained_decode_miss_diagnostic_text,
    write_pair_constrained_decode_miss_diagnostic_outputs,
)


class PairConstrainedDecodeMissDiagnosticTests(unittest.TestCase):
    def test_diagnostic_routes_fixed_miss_to_explicit_dual_objective_boundary(self) -> None:
        report = build_model_capability_required_term_pair_constrained_decode_miss_diagnostic(
            feasibility_report(fixed_constrained_hit=False, loss_constrained_hit=True)
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "fixed_branch_still_missed_after_constrained_decode")
        self.assertEqual(report["summary"]["fixed_miss_class"], "prefix_fragment_without_full_term")
        self.assertEqual(report["summary"]["remaining_missed_terms"], ["fixed"])
        self.assertEqual(
            report["summary"]["recommended_next_route"],
            "explicit_dual_objective_boundary_for_fixed_retention",
        )
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_pair_full_decode_has_no_miss(self) -> None:
        report = build_model_capability_required_term_pair_constrained_decode_miss_diagnostic(
            feasibility_report(fixed_constrained_hit=True, loss_constrained_hit=True, constrained_pair_full=True)
        )

        self.assertEqual(report["decision"], "constrained_decode_pair_full_no_miss")
        self.assertEqual(report["summary"]["remaining_missed_terms"], [])

    def test_fails_when_constrained_fixed_case_is_missing(self) -> None:
        source = feasibility_report(fixed_constrained_hit=False, loss_constrained_hit=True)
        source["case_rows"] = [row for row in source["case_rows"] if not (row["term"] == "fixed" and row["profile_id"] == "block_competing_initial")]

        report = build_model_capability_required_term_pair_constrained_decode_miss_diagnostic(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source has no constrained fixed case", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_constrained_decode_miss_diagnostic(
                feasibility_report(fixed_constrained_hit=False, loss_constrained_hit=True)
            )
            outputs = write_pair_constrained_decode_miss_diagnostic_outputs(report, root / "miss")
            text = render_pair_constrained_decode_miss_diagnostic_text(report)
            markdown = render_pair_constrained_decode_miss_diagnostic_markdown(report)
            html = render_pair_constrained_decode_miss_diagnostic_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=fixed_branch_still_missed_after_constrained_decode", text)
            self.assertIn("Constrained Decode Miss Diagnostic", markdown)
            self.assertIn("MiniGPT constrained decode miss diagnostic", html)

    def test_locator_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_pair_constrained_decode_miss_diagnostic_source(root),
                root / "model_capability_required_term_pair_constrained_decode_feasibility.json",
            )


def feasibility_report(
    *,
    fixed_constrained_hit: bool,
    loss_constrained_hit: bool,
    constrained_pair_full: bool = False,
) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_constrained_decode_partial_gain",
        "summary": {
            "hit_delta": 1,
            "constrained_pair_full": constrained_pair_full,
        },
        "case_rows": [
            case_row("fixed", "default", hit=False, continuation=" d= los\\nd=fi"),
            case_row(
                "fixed",
                "block_competing_initial",
                hit=fixed_constrained_hit,
                continuation=" fixed" if fixed_constrained_hit else " d= cans\nfix",
                blocked=["l"],
            ),
            case_row("loss", "default", hit=False, continuation=" fixe fixed="),
            case_row(
                "loss",
                "block_competing_initial",
                hit=loss_constrained_hit,
                continuation=" loss" if loss_constrained_hit else " fixe",
                blocked=["f"],
            ),
        ],
    }


def case_row(term: str, profile_id: str, *, hit: bool, continuation: str, blocked: list[str] | None = None) -> dict[str, object]:
    return {
        "term": term,
        "profile_id": profile_id,
        "continuation_hit": hit,
        "blocked_token_texts": blocked or [],
        "blocked_reason": "test",
        "continuation": continuation,
        "continuation_preview": continuation.replace("\n", "\\n"),
    }


if __name__ == "__main__":
    unittest.main()
