from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch import (
    CONTRACT_SURFACES,
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_JSON_FILENAME,
    build_stagnation_aware_suffix_patch,
    locate_stagnation_aware_suffix_repair_plan,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_artifacts import (
    render_stagnation_aware_suffix_patch_html,
    render_stagnation_aware_suffix_patch_markdown,
    render_stagnation_aware_suffix_patch_text,
    write_stagnation_aware_suffix_patch_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch import (
    main as cli_main,
)


class StagnationAwareSuffixPatchTests(unittest.TestCase):
    def test_builds_stagnation_aware_suffix_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_stagnation_aware_suffix_patch(repair_plan(), source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_ready"])
        self.assertEqual(report["summary"]["patch_example_count"], 27)
        self.assertEqual(report["summary"]["replay_prompt_boundary_example_count"], 6)
        self.assertEqual(report["summary"]["suffix_position_example_count"], 12)
        self.assertEqual(report["summary"]["surface_format_example_count"], 4)
        self.assertEqual(report["summary"]["training_corpus_ratio_example_count"], 4)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(len(report["contract_surfaces"]), len(CONTRACT_SURFACES))
        self.assertIn("Answer with exactly two tokens: fixed loss\nanswer: fixed l\nloss\nfixed loss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_when_plan_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = repair_plan()
            plan["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready"] = False
            report = build_stagnation_aware_suffix_patch(plan, source_corpus_path=write_corpus(Path(tmp)))

        self.assertEqual(report["status"], "fail")
        self.assertIn("plan_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "plan" / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME
            corpus_path = write_corpus(root)
            write_json_payload(repair_plan(), plan_path)
            self.assertEqual(locate_stagnation_aware_suffix_repair_plan(plan_path.parent), plan_path)
            report = build_stagnation_aware_suffix_patch(repair_plan(), source_corpus_path=corpus_path, repair_plan_path=plan_path)
            outputs = write_stagnation_aware_suffix_patch_outputs(report, root / "out")
            cli_main([
                "--repair-plan",
                str(plan_path.parent),
                "--source-corpus",
                str(corpus_path),
                "--out-dir",
                str(root / "cli-out"),
                "--require-patch-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_JSON_FILENAME))
        self.assertIn("stagnation_aware_suffix_patch_ready=True", render_stagnation_aware_suffix_patch_text(report))
        self.assertIn("Patch Examples", render_stagnation_aware_suffix_patch_markdown(report))
        self.assertIn("Patch Examples", render_stagnation_aware_suffix_patch_html(report))


def repair_plan() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready": True,
            "action_count": 5,
            "source_no_contract_gain_confirmed": True,
        },
        "plan_actions": [
            {"action_id": "suffix-position-bridge", "category": "suffix_position"},
            {"action_id": "surface-format-normalization", "category": "surface_format"},
            {"action_id": "replay-prompt-boundary-lock", "category": "replay_prompt_boundary"},
            {"action_id": "suffix-ratio-increase", "category": "training_corpus_ratio"},
            {"action_id": "contract-gated-training-stop", "category": "verification_gate"},
        ],
    }


def write_corpus(root: Path) -> Path:
    path = root / "source.txt"
    path.write_text("fixed l\nfixed loss\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
