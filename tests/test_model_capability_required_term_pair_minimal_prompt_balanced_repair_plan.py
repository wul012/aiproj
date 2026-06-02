from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_balanced_repair_plan import (
    BALANCED_REPAIR_CORPUS_MODE,
    build_balanced_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_balanced_repair_plan_artifacts import (
    render_balanced_repair_plan_html,
    render_balanced_repair_plan_markdown,
    render_balanced_repair_plan_text,
    write_balanced_repair_plan_outputs,
)


class MinimalPromptBalancedRepairPlanTests(unittest.TestCase):
    def test_balanced_mode_is_registered_and_symmetric(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode=BALANCED_REPAIR_CORPUS_MODE,
        )

        self.assertIn(BALANCED_REPAIR_CORPUS_MODE, PAIR_COEXISTENCE_CORPUS_MODES)
        self.assertEqual(source_prompts(BALANCED_REPAIR_CORPUS_MODE), ("fixed=", "loss="))
        self.assertEqual(corpus.count("fixed=fixed"), corpus.count("loss=loss"))
        self.assertIn("fixed branch does not start loss", corpus)
        self.assertIn("loss branch does not start fixed", corpus)
        self.assertNotIn("fixed=fixed|loss=loss", corpus)

    def test_plan_ready_from_tradeoff(self) -> None:
        report = build_balanced_repair_plan(tradeoff_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "minimal_prompt_balanced_repair_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_corpus_mode"], BALANCED_REPAIR_CORPUS_MODE)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_pair_full_already_exists(self) -> None:
        tradeoff = tradeoff_fixture()
        tradeoff["summary"]["pair_full_report_count"] = 1
        report = build_balanced_repair_plan(tradeoff)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_pair_full_candidate", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_balanced_repair_plan(tradeoff_fixture())
            outputs = write_balanced_repair_plan_outputs(report, Path(tmp) / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("plan_ready=True", render_balanced_repair_plan_text(report))
        self.assertIn("Balanced Repair Plan", render_balanced_repair_plan_markdown(report))
        self.assertIn("MiniGPT balanced repair plan", render_balanced_repair_plan_html(report))


def tradeoff_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "first_token_preference_tradeoff_confirmed",
        "summary": {
            "mixed_branch_tradeoff_confirmed": True,
            "pair_full_report_count": 0,
        },
    }


if __name__ == "__main__":
    unittest.main()
