from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan import (
    LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE,
    build_loss_first_token_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan_artifacts import (
    render_loss_first_token_repair_plan_html,
    render_loss_first_token_repair_plan_markdown,
    render_loss_first_token_repair_plan_text,
    write_loss_first_token_repair_plan_outputs,
)


class MinimalPromptLossFirstTokenRepairPlanTests(unittest.TestCase):
    def test_repair_mode_is_registered_and_weights_loss_prefixes(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode=LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE,
        )

        self.assertIn(LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE, PAIR_COEXISTENCE_CORPUS_MODES)
        self.assertEqual(source_prompts(LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE), ("fixed=", "loss="))
        self.assertGreater(corpus.count("loss=l"), corpus.count("fixed=f"))
        self.assertGreater(corpus.count("loss=loss"), corpus.count("fixed=fixed"))
        self.assertIn("loss branch does not start fixed", corpus)
        self.assertNotIn("fixed=fixed|loss=loss", corpus)

    def test_plan_is_ready_from_fixed_absorbs_loss_diagnostic(self) -> None:
        report = build_loss_first_token_repair_plan(branch_bias_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "minimal_prompt_loss_first_token_repair_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_corpus_mode"], LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_without_fixed_bias(self) -> None:
        diagnostic = branch_bias_fixture()
        diagnostic["summary"]["dominant_bias"] = "balanced_or_unknown"
        report = build_loss_first_token_repair_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("dominant_bias_fixed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_loss_first_token_repair_plan(branch_bias_fixture())
            outputs = write_loss_first_token_repair_plan_outputs(report, Path(tmp) / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("plan_ready=True", render_loss_first_token_repair_plan_text(report))
        self.assertIn("Loss First-Token Repair Plan", render_loss_first_token_repair_plan_markdown(report))
        self.assertIn("MiniGPT loss first-token repair plan", render_loss_first_token_repair_plan_html(report))


def branch_bias_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "minimal_prompt_branch_bias_fixed_absorbs_loss",
        "summary": {
            "corpus_mode": "minimal_prompt_equals_surface_objective",
            "seed": 3535,
            "fixed_hit_count": 2,
            "loss_hit_count": 0,
            "loss_prompt_fixed_start_count": 2,
            "dominant_bias": "fixed",
        },
    }


if __name__ == "__main__":
    unittest.main()
