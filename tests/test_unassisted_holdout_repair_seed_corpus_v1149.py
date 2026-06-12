from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.unassisted_holdout_repair_plan_v1148 import write_unassisted_holdout_repair_plan_v1148_outputs
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import (
    UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM,
    build_unassisted_holdout_repair_seed_corpus_v1149,
    load_seed_blueprint,
    locate_v1148_plan,
    resolve_exit_code,
    write_unassisted_holdout_repair_seed_corpus_v1149_outputs,
)
from scripts.materialize_unassisted_holdout_repair_seed_corpus_v1149 import main as cli_main


class UnassistedHoldoutRepairSeedCorpusV1149Tests(unittest.TestCase):
    def test_materializes_seed_corpus_from_plan_blueprint(self) -> None:
        report = build_unassisted_holdout_repair_seed_corpus_v1149(v1148_plan(), seed_rows())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "unassisted_holdout_repair_seed_corpus_ready")
        self.assertTrue(report["summary"]["unassisted_holdout_repair_seed_corpus_ready"])
        self.assertEqual(report["summary"]["example_count"], 9)
        self.assertGreaterEqual(report["summary"]["target_free_holdout_prompt_count"], 4)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertEqual(report["summary"]["model_quality_claim"], "seed_corpus_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertIn("fixed loss", report["corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_fails_when_plan_is_not_ready(self) -> None:
        plan = v1148_plan()
        plan["summary"]["unassisted_holdout_repair_plan_ready"] = False
        report = build_unassisted_holdout_repair_seed_corpus_v1149(plan, seed_rows())

        self.assertEqual(report["status"], "fail")
        self.assertIn("v1148_plan_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 1)

    def test_fails_when_seed_blueprint_contains_decoder_anchor(self) -> None:
        rows = seed_rows()
        rows[0]["decoder_anchor"] = True
        report = build_unassisted_holdout_repair_seed_corpus_v1149(v1148_plan(), rows)

        self.assertEqual(report["status"], "fail")
        self.assertIn("decoder_anchor_free", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_outputs = write_unassisted_holdout_repair_plan_v1148_outputs(v1148_plan_with_blueprint(), root / "plan")
            self.assertEqual(locate_v1148_plan(Path(plan_outputs["json"]).parent), Path(plan_outputs["json"]))
            loaded_rows = load_seed_blueprint(v1148_plan(), plan_path=plan_outputs["json"])
            self.assertEqual(len(loaded_rows), 9)
            report = build_unassisted_holdout_repair_seed_corpus_v1149(v1148_plan(), loaded_rows)
            outputs = write_unassisted_holdout_repair_seed_corpus_v1149_outputs(report, root / "corpus")
            cli_main(
                [
                    "--plan",
                    str(Path(plan_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-corpus"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html", "corpus", "jsonl", "holdout_prompts", "train_command_hint"})
            self.assertTrue(outputs["json"].endswith(f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"))
            self.assertTrue((root / "cli-corpus" / "unassisted_holdout_repair_seed_corpus.txt").is_file())
            self.assertTrue((root / "cli-corpus" / "unassisted_holdout_repair_holdout_prompts.json").is_file())


def v1148_plan() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "unassisted_holdout_repair_plan_ready": True,
            "next_step": "materialize_unassisted_holdout_repair_seed_corpus",
            "promotion_ready": False,
        },
        "repair_seed_blueprint_rows": seed_rows(),
    }


def v1148_plan_with_blueprint() -> dict[str, object]:
    plan = v1148_plan()
    plan["repair_seed_blueprint_rows"] = seed_rows()
    return plan


def seed_rows() -> list[dict[str, object]]:
    return [
        {"id": "pair-repair-01", "kind": "full_pair", "prompt": "answer:", "completion": " fixed loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False},
        {"id": "pair-repair-02", "kind": "full_pair", "prompt": "answer: ", "completion": "fixed loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False},
        {"id": "pair-repair-03", "kind": "full_pair", "prompt": "completion:", "completion": " fixed loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False},
        {"id": "pair-repair-04", "kind": "full_pair", "prompt": "finish:", "completion": " fixed loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False},
        {"id": "pair-repair-05", "kind": "full_pair", "prompt": "state compact signal\nanswer:", "completion": " fixed loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False},
        {"id": "fixed-first-01", "kind": "fixed_first", "prompt": "answer:", "completion": " fixed", "target_terms": ["fixed"], "decoder_anchor": False},
        {"id": "fixed-first-02", "kind": "fixed_first", "prompt": "completion:", "completion": " fixed", "target_terms": ["fixed"], "decoder_anchor": False},
        {"id": "loss-after-fixed-01", "kind": "loss_after_model_fixed", "prompt": "answer: fixed", "completion": " loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False, "decoder_anchor_boundary": "training_only_context_not_eval"},
        {"id": "pair-short-01", "kind": "short_pair", "prompt": "signal:", "completion": " fixed loss", "target_terms": ["fixed", "loss"], "decoder_anchor": False},
    ]


if __name__ == "__main__":
    unittest.main()
