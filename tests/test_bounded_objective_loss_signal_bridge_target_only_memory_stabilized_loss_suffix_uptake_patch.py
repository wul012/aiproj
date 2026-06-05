from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_JSON_FILENAME,
    build_stabilized_loss_suffix_uptake_patch,
    locate_completion_surface_stabilization_partial_hit_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_artifacts import (
    render_stabilized_loss_suffix_uptake_patch_html,
    render_stabilized_loss_suffix_uptake_patch_markdown,
    render_stabilized_loss_suffix_uptake_patch_text,
    write_stabilized_loss_suffix_uptake_patch_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch import (
    main as cli_main,
)


class StabilizedLossSuffixUptakePatchTests(unittest.TestCase):
    def test_builds_stabilized_loss_suffix_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_stabilized_loss_suffix_uptake_patch(
                partial_hit_diagnostic(),
                source_corpus_path=write_corpus(Path(tmp)),
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_ready"])
        self.assertEqual(report["summary"]["patch_example_count"], 24)
        self.assertEqual(report["summary"]["fixed_l_to_loss_uptake_count"], 6)
        self.assertEqual(report["summary"]["fixed_lo_to_loss_uptake_count"], 3)
        self.assertEqual(report["summary"]["global_suffix_uptake_count"], 6)
        self.assertEqual(report["summary"]["surface_pair_carry_forward_count"], 9)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("fixed l\nfixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_when_surface_not_stabilized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = partial_hit_diagnostic()
            diagnostic["summary"]["completion_surface_stabilized"] = False
            report = build_stabilized_loss_suffix_uptake_patch(diagnostic, source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("surface_stabilized", [issue["id"] for issue in report["issues"]])

    def test_patch_fails_when_loss_already_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic = partial_hit_diagnostic()
            diagnostic["summary"]["loss_hit_case_count"] = 1
            report = build_stabilized_loss_suffix_uptake_patch(diagnostic, source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("loss_still_missing", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = write_corpus(root)
            diagnostic_path = root / "diagnostic" / TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(partial_hit_diagnostic(), diagnostic_path)
            self.assertEqual(locate_completion_surface_stabilization_partial_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_stabilized_loss_suffix_uptake_patch(partial_hit_diagnostic(), source_corpus_path=corpus)
            outputs = write_stabilized_loss_suffix_uptake_patch_outputs(report, root / "out")
            cli_main([
                "--partial-hit-diagnostic",
                str(diagnostic_path.parent),
                "--source-corpus",
                str(corpus),
                "--out-dir",
                str(root / "cli-out"),
                "--require-patch-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_JSON_FILENAME))
        self.assertIn("stabilized_loss_suffix_uptake_patch_ready=True", render_stabilized_loss_suffix_uptake_patch_text(report))
        self.assertIn("Patch Examples", render_stabilized_loss_suffix_uptake_patch_markdown(report))
        self.assertIn("Patch Examples", render_stabilized_loss_suffix_uptake_patch_html(report))


def partial_hit_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic_ready": True,
            "completion_surface_stabilized": True,
            "all_cases_fixed_l_partial": True,
            "fixed_l_partial_case_count": 3,
            "loss_hit_case_count": 0,
        },
        "diagnostic": {
            "suffix_gap_after_surface_stabilization": True,
        },
        "case_diagnostics": [
            row("canonical_direct_completion"),
            row("minimal_direct_completion"),
            row("completion_label_surface"),
        ],
    }


def row(case_id: str) -> dict[str, object]:
    return {"case_id": case_id, "continuation": " fixed l"}


def write_corpus(root: Path) -> Path:
    path = root / "source.txt"
    path.write_text("fixed l\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
