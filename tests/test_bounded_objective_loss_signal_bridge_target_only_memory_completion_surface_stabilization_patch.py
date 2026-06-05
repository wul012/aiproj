from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_JSON_FILENAME,
    build_completion_surface_stabilization_patch,
    locate_loss_suffix_replay_regression_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_artifacts import (
    render_completion_surface_stabilization_patch_html,
    render_completion_surface_stabilization_patch_markdown,
    render_completion_surface_stabilization_patch_text,
    write_completion_surface_stabilization_patch_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch import (
    main as cli_main,
)


class CompletionSurfaceStabilizationPatchTests(unittest.TestCase):
    def test_builds_completion_surface_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_completion_surface_stabilization_patch(
                regression_diagnostic(),
                source_corpus_path=write_corpus(Path(tmp)),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_ready"])
        self.assertEqual(report["summary"]["patch_example_count"], 28)
        self.assertEqual(report["summary"]["completion_surface_example_count"], 12)
        self.assertEqual(report["summary"]["answer_surface_carry_forward_count"], 6)
        self.assertEqual(report["summary"]["prefix_fragment_bridge_count"], 6)
        self.assertEqual(report["summary"]["completion_fragment_resistance_count"], 4)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("completion:\nfixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_without_completion_surface_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = regression_diagnostic()
            diagnostic["summary"]["completion_surface_regressed_to_zero"] = False
            diagnostic["regression"]["completion_surface_regressed_to_zero"] = False
            report = build_completion_surface_stabilization_patch(diagnostic, source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("completion_regressed_to_zero", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_patch_fails_without_sample_contract_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = regression_diagnostic()
            diagnostic["summary"]["sample_contract_gap"] = False
            report = build_completion_surface_stabilization_patch(diagnostic, source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("sample_contract_gap", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = write_corpus(root)
            diagnostic_path = root / "diagnostic" / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(regression_diagnostic(), diagnostic_path)
            self.assertEqual(locate_loss_suffix_replay_regression_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_completion_surface_stabilization_patch(regression_diagnostic(), source_corpus_path=corpus)
            outputs = write_completion_surface_stabilization_patch_outputs(report, root / "out")
            cli_main([
                "--regression-diagnostic",
                str(diagnostic_path.parent),
                "--source-corpus",
                str(corpus),
                "--out-dir",
                str(root / "cli-out"),
                "--require-patch-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_JSON_FILENAME))
        self.assertIn("completion_surface_stabilization_patch_ready=True", render_completion_surface_stabilization_patch_text(report))
        self.assertIn("completion_surface_stabilization", render_completion_surface_stabilization_patch_markdown(report))
        self.assertIn("Patch Examples", render_completion_surface_stabilization_patch_html(report))


def regression_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_ready": True,
            "sample_contract_gap": True,
            "completion_surface_regressed_to_zero": True,
        },
        "regression": {
            "completion_surface_regressed_to_zero": True,
            "zero_hit_delta": 1,
            "any_hit_delta": -1,
        },
        "current_case_diagnostics": [
            case("canonical_direct_completion", "fixed_l_partial", "\nfixed l"),
            case("minimal_direct_completion", "fixed_l_partial", "\nfixed l"),
            case("completion_label_surface", "completion_surface_zero_regression", "\nan: fix"),
        ],
        "baseline_case_diagnostics": [
            case("completion_label_surface", "fixed_l_partial", " fixed l"),
        ],
    }


def case(case_id: str, label: str, continuation: str) -> dict[str, object]:
    return {"case_id": case_id, "label": label, "continuation": continuation}


def write_corpus(root: Path) -> Path:
    path = root / "source.txt"
    path.write_text("fixed loss\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
