from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import (
    PAIR_READINESS_HELDOUT_EVAL_FIXTURE_FILENAME,
    PAIR_READINESS_TRAINING_CORPUS_FILENAME,
    build_pair_readiness_corpus_materialization,
    locate_pair_readiness_corpus_materialization_source,
    resolve_exit_code,
    write_materialized_pair_readiness_inputs,
)
from minigpt.model_capability_required_term_pair_readiness_structured_template_contract import (
    PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from minigpt.model_capability_required_term_pair_readiness_corpus_materialization_artifacts import (
    render_pair_readiness_corpus_materialization_html,
    render_pair_readiness_corpus_materialization_markdown,
    render_pair_readiness_corpus_materialization_text,
    write_pair_readiness_corpus_materialization_outputs,
)


class PairReadinessCorpusMaterializationTests(unittest.TestCase):
    def test_materialization_ready_from_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_pair_readiness_corpus_materialization(contract_fixture(), out_dir=tmp, repeat=2)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_corpus_materialized")
        self.assertTrue(report["summary"]["materialization_ready"])
        self.assertEqual(report["summary"]["training_line_count"], 16)
        self.assertEqual(report["summary"]["evaluation_probe_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_materialization_blocks_heldout_leak(self) -> None:
        contract = contract_fixture()
        contract["contract"]["training_rows"].append("fixed=|loss=")
        with tempfile.TemporaryDirectory() as tmp:
            report = build_pair_readiness_corpus_materialization(contract, out_dir=tmp, repeat=1)

        self.assertEqual(report["status"], "fail")
        self.assertIn("heldout_not_in_training_rows", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_materialized_files_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_pair_readiness_corpus_materialization(contract_fixture(), out_dir=tmp, repeat=1)
            write_materialized_pair_readiness_inputs(report)
            root = Path(tmp)

            self.assertTrue((root / PAIR_READINESS_TRAINING_CORPUS_FILENAME).is_file())
            self.assertTrue((root / PAIR_READINESS_HELDOUT_EVAL_FIXTURE_FILENAME).is_file())

    def test_locator_accepts_structured_template_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_JSON_FILENAME
            write_json_payload(contract_fixture("pair_readiness_structured_template_contract_ready"), source)

            self.assertEqual(locate_pair_readiness_corpus_materialization_source(root), source)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_pair_readiness_corpus_materialization(contract_fixture(), out_dir=tmp, repeat=1)
            outputs = write_pair_readiness_corpus_materialization_outputs(report, Path(tmp) / "report")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_corpus_materialized", render_pair_readiness_corpus_materialization_text(report))
        self.assertIn("Corpus Materialization", render_pair_readiness_corpus_materialization_markdown(report))
        self.assertIn("MiniGPT pair-readiness corpus materialization", render_pair_readiness_corpus_materialization_html(report))


def contract_fixture(decision: str = "pair_readiness_split_contract_ready") -> dict[str, object]:
    return {
        "status": "pass",
        "decision": decision,
        "summary": {"contract_ready": True},
        "contract": {
            "training_rows": ["fixed=f", "fixed=fi", "fixed=fix", "fixed=fixed", "loss=l", "loss=lo", "loss=los", "loss=loss"],
            "evaluation_probes": [
                {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed"},
                {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss"},
                {"id": "fixed-loss-pair", "prompt": "fixed=|loss=", "expected_term": "fixed+loss"},
            ],
            "heldout_pair_probe": "fixed=|loss=",
            "promotion_requirement": "both direct probes must hit",
        },
    }


if __name__ == "__main__":
    unittest.main()
