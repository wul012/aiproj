from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_prompt_separation_audit import (
    build_model_capability_required_term_pair_prompt_separation_audit,
    locate_model_capability_required_term_pair_prompt_separation_audit_source,
    read_json_report,
    resolve_exit_code,
    summarize_required_term_pair_prompt_separation_audit,
)
from minigpt.model_capability_required_term_pair_prompt_separation_audit_artifacts import (
    render_model_capability_required_term_pair_prompt_separation_audit_html,
    render_model_capability_required_term_pair_prompt_separation_audit_markdown,
    render_model_capability_required_term_pair_prompt_separation_audit_text,
    write_model_capability_required_term_pair_prompt_separation_audit_outputs,
)


from tests._bootstrap import ROOT


class ModelCapabilityRequiredTermPairPromptSeparationAuditTests(unittest.TestCase):
    def test_prompt_separation_audit_flags_direct_other_term_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decoding = write_pair_decoding_fixture(root, corpus_text=leaky_corpus())

            report = build_model_capability_required_term_pair_prompt_separation_audit(
                read_json_report(decoding),
                out_dir=root / "audit",
                source_path=decoding,
                generated_at="2026-05-30T00:00:00Z",
            )
            outputs = write_model_capability_required_term_pair_prompt_separation_audit_outputs(
                report,
                root / "outputs",
            )
            text = render_model_capability_required_term_pair_prompt_separation_audit_text(report)
            markdown = render_model_capability_required_term_pair_prompt_separation_audit_markdown(report)
            html = render_model_capability_required_term_pair_prompt_separation_audit_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_prompt_separation_revision_needed")
            self.assertEqual(report["summary"]["direct_prompt_other_term_leak_count"], 2)
            self.assertEqual(report["summary"]["negative_contrast_leak_count"], 2)
            self.assertFalse(report["summary"]["prompt_separation_ready"])
            self.assertIn("corpus_revision_recommended=True", text)
            self.assertIn("Prompt Separation Audit", markdown)
            self.assertIn("Term Rows", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_prompt_separation_audit_source(decoding.parent), decoding)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_prompt_separation_audit_can_pass_ready_when_corpus_is_separated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decoding = write_pair_decoding_fixture(root, corpus_text=separated_corpus())

            report = build_model_capability_required_term_pair_prompt_separation_audit(
                read_json_report(decoding),
                out_dir=root / "audit",
                source_path=decoding,
            )

            self.assertEqual(report["decision"], "required_term_pair_prompt_separation_ready")
            self.assertTrue(report["summary"]["prompt_separation_ready"])
            self.assertFalse(report["summary"]["corpus_revision_recommended"])
            self.assertEqual(report["summary"]["direct_prompt_other_term_leak_count"], 0)

    def test_prompt_separation_audit_reports_input_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decoding = write_pair_decoding_fixture(root, corpus_text=separated_corpus())
            source = read_json_report(decoding)
            bad_status = build_model_capability_required_term_pair_prompt_separation_audit(
                {**source, "status": "fail"},
                out_dir=root / "bad-status",
                source_path=decoding,
            )
            missing_capacity = build_model_capability_required_term_pair_prompt_separation_audit(
                {**source, "source_required_term_pair_capacity_sweep": str(root / "missing.json")},
                out_dir=root / "missing-capacity",
                source_path=decoding,
            )

            self.assertEqual(bad_status["status"], "fail")
            self.assertEqual(bad_status["decision"], "fix_required_term_pair_prompt_separation_audit")
            self.assertIn("source pair decoding sweep report is not pass", bad_status["issues"])
            self.assertIn("source pair capacity sweep report is missing or invalid", missing_capacity["issues"])
            self.assertEqual(resolve_exit_code(missing_capacity, require_pass=True), 1)

    def test_prompt_separation_summary_helpers_track_ready_and_leaks(self) -> None:
        summary = summarize_required_term_pair_prompt_separation_audit(
            targets=[{"target_id": "target-a"}],
            target_rows=[
                {
                    "target_id": "target-a",
                    "corpus_exists": True,
                    "prompt_separation_ready": False,
                    "direct_prompt_leak_observed": True,
                    "negative_contrast_leak_observed": True,
                    "shared_pair_context_observed": True,
                }
            ],
            term_rows=[
                {
                    "other_after_prompt_line_count": 1,
                    "negative_contrast_leak_count": 1,
                    "pair_header_shared_context_count": 1,
                }
            ],
            source_summary={"pair_decoding_sweep_decision": "pair_decoding_sweep_partial_only"},
        )

        self.assertEqual(summary["prompt_separation_audit_decision"], "prompt_separation_corpus_revision_needed")
        self.assertTrue(summary["corpus_revision_recommended"])
        self.assertEqual(summary["target_with_direct_leak_count"], 1)

    def test_prompt_separation_audit_cli_require_pass_returns_one_for_missing_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decoding = write_pair_decoding_fixture(root, corpus_text=separated_corpus())
            capacity = read_json_report(read_json_report(decoding)["source_required_term_pair_capacity_sweep"])
            capacity["capacity_rows"][0]["capacity_corpus_path"] = str(root / "missing-corpus.txt")
            write_json(Path(read_json_report(decoding)["source_required_term_pair_capacity_sweep"]), capacity)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_prompt_separation_audit.py"),
                    str(decoding),
                    "--out-dir",
                    str(root / "cli-audit"),
                    "--require-pass",
                    "--force",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("status=fail", completed.stdout)


def write_pair_decoding_fixture(root: Path, *, corpus_text: str) -> Path:
    corpus = root / "capacity-corpora" / "01-fixed-loss-baseline-repeat-seed-496.txt"
    corpus.parent.mkdir(parents=True, exist_ok=True)
    corpus.write_text(corpus_text, encoding="utf-8")
    capacity = root / "model_capability_required_term_pair_capacity_sweep.json"
    write_json(
        capacity,
        {
            "status": "pass",
            "summary": {
                "pair_capacity_sweep_decision": "pair_capacity_sweep_partial_only",
                "capacity_full_hit_observed": False,
            },
            "capacity_rows": [
                {
                    "capacity_run_id": "01-fixed-loss-baseline-repeat-seed-496",
                    "capacity_corpus_path": str(corpus),
                    "capacity_line_count": len(corpus_text.splitlines()),
                    "repeat": 1,
                    "isolated_repeat": 1,
                }
            ],
        },
    )
    decoding = root / "model_capability_required_term_pair_decoding_sweep.json"
    write_json(
        decoding,
        {
            "status": "pass",
            "summary": {
                "pair_decoding_sweep_decision": "pair_decoding_sweep_partial_only",
                "decoding_full_hit_observed": False,
            },
            "source_required_term_pair_capacity_sweep": str(capacity),
            "targets": [
                {
                    "target_id": "01-fixed-loss-baseline-repeat",
                    "pair_id": "01-fixed-loss",
                    "variant_id": "baseline-repeat",
                    "capacity_run_id": "01-fixed-loss-baseline-repeat-seed-496",
                    "term_names": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
                }
            ],
        },
    )
    return decoding


def leaky_corpus() -> str:
    return "\n".join(
        [
            "MiniGPT required-term pair rebalance corpus.",
            "fixed:fixed",
            "fixed:fixed not loss",
            "pair fixed loss prompt fixed: target fixed",
            "loss:loss",
            "loss:loss not fixed",
            "pair fixed loss prompt loss: target loss",
        ]
    )


def separated_corpus() -> str:
    return "\n".join(
        [
            "MiniGPT required-term pair separated corpus.",
            "fixed:fixed",
            "fixed: fixed",
            "loss:loss",
            "loss: loss",
        ]
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
