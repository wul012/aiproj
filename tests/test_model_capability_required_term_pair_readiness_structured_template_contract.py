from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import build_pair_readiness_corpus_materialization
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.model_capability_required_term_pair_readiness_structured_template_contract import (
    STRUCTURED_TEMPLATE_ROWS,
    build_structured_template_contract,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_structured_template_contract_artifacts import (
    render_structured_template_contract_html,
    render_structured_template_contract_markdown,
    render_structured_template_contract_text,
    write_structured_template_contract_outputs,
)


class PairReadinessStructuredTemplateContractTests(unittest.TestCase):
    def test_contract_ready_from_regressed_repair_comparison(self) -> None:
        report = build_structured_template_contract(comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_structured_template_contract_ready")
        self.assertTrue(report["summary"]["contract_ready"])
        self.assertEqual(report["summary"]["structured_training_row_count"], len(STRUCTURED_TEMPLATE_ROWS))
        self.assertNotIn(HELDOUT_PAIR_PROBE, report["contract"]["training_rows"])
        self.assertEqual(report["interpretation"]["model_quality_claim"], "contract_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_can_be_materialized_by_existing_materializer(self) -> None:
        report = build_structured_template_contract(comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            materialized = build_pair_readiness_corpus_materialization(report, out_dir=tmp, repeat=1)

        self.assertEqual(materialized["status"], "pass")
        self.assertEqual(materialized["decision"], "pair_readiness_corpus_materialized")

    def test_contract_fails_for_non_regressed_source(self) -> None:
        source = comparison_fixture()
        source["decision"] = "pair_readiness_repair_candidate_flat"
        source["summary"]["candidate_regressed"] = False
        source["summary"]["default_hit_delta"] = 0
        report = build_structured_template_contract(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_comparison_decision", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_training_rows_do_not_exactly_overlap_eval_prompts(self) -> None:
        report = build_structured_template_contract(comparison_fixture())
        training_rows = set(report["contract"]["training_rows"])
        probe_prompts = {row["prompt"] for row in report["contract"]["evaluation_probes"]}

        self.assertFalse(training_rows & probe_prompts)

    def test_outputs_render_all_formats(self) -> None:
        report = build_structured_template_contract(comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_structured_template_contract_outputs(report, Path(tmp) / "contract")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_structured_template_contract_ready", render_structured_template_contract_text(report))
        self.assertIn("Structured-Template Contract", render_structured_template_contract_markdown(report))
        self.assertIn("MiniGPT pair-readiness structured-template contract", render_structured_template_contract_html(report))


def comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_loss_retention_patch_regressed",
        "failed_count": 0,
        "summary": {
            "baseline_default_hit_count": 1,
            "candidate_default_hit_count": 0,
            "default_hit_delta": -1,
            "candidate_improved": False,
            "candidate_regressed": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
