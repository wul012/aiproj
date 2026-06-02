from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_corpus_contract import (
    build_minimal_prompt_corpus_contract,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_corpus_contract_artifacts import (
    render_minimal_prompt_corpus_contract_html,
    render_minimal_prompt_corpus_contract_markdown,
    render_minimal_prompt_corpus_contract_text,
    write_minimal_prompt_corpus_contract_outputs,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_objective_corpus import (
    PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES,
    is_pair_minimal_prompt_objective_corpus_mode,
)


class MinimalPromptCorpusContractTests(unittest.TestCase):
    def test_minimal_prompt_mode_is_registered_with_equals_prompts(self) -> None:
        for mode in PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, PAIR_COEXISTENCE_CORPUS_MODES)
                self.assertTrue(is_pair_minimal_prompt_objective_corpus_mode(mode))
                self.assertEqual(source_prompts(mode), ("fixed=", "loss="))

    def test_minimal_prompt_corpus_keeps_direct_targets_without_contextual_anchor(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="minimal_prompt_equals_surface_objective",
        )

        self.assertIn("fixed=fixed", corpus)
        self.assertIn("loss=loss", corpus)
        self.assertIn("fixed=fix", corpus)
        self.assertIn("loss=los", corpus)
        self.assertNotIn("fixed=fixed|loss=loss", corpus)
        self.assertNotIn("loss=loss|fixed=fixed", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_contract_passes_from_readiness(self) -> None:
        report = build_minimal_prompt_corpus_contract(readiness_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "minimal_prompt_equals_surface_corpus_contract_ready")
        self.assertTrue(report["summary"]["contract_ready"])
        self.assertEqual(report["summary"]["source_prompts"], ["fixed=", "loss="])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_fails_when_readiness_recommends_unregistered_mode(self) -> None:
        readiness = readiness_fixture()
        readiness["objective"]["recommended_corpus_mode"] = "missing_mode"
        report = build_minimal_prompt_corpus_contract(readiness)

        self.assertEqual(report["status"], "fail")
        self.assertIn("corpus_mode_registered", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_minimal_prompt_corpus_contract(readiness_fixture())
            outputs = write_minimal_prompt_corpus_contract_outputs(report, Path(tmp) / "contract")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("contract_ready=True", render_minimal_prompt_corpus_contract_text(report))
        self.assertIn("Minimal Prompt Corpus Contract", render_minimal_prompt_corpus_contract_markdown(report))
        self.assertIn("MiniGPT minimal prompt corpus contract", render_minimal_prompt_corpus_contract_html(report))


def readiness_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "minimal_prompt_surface_objective_ready_for_corpus_contract",
        "summary": {"objective_ready": True},
        "objective": {
            "ready": True,
            "recommended_corpus_mode": "minimal_prompt_equals_surface_objective",
        },
    }


if __name__ == "__main__":
    unittest.main()
