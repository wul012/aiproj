from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_branch_batch_closeout import (
    PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_JSON_FILENAME,
    build_model_capability_required_term_pair_loss_branch_batch_closeout,
    locate_loss_branch_batch_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_branch_batch_closeout_artifacts import (
    render_loss_branch_batch_closeout_html,
    render_loss_branch_batch_closeout_markdown,
    render_loss_branch_batch_closeout_text,
    write_loss_branch_batch_closeout_outputs,
)
from minigpt.report_utils import write_json_payload


ROOT = Path(__file__).resolve().parents[1]


class LossBranchBatchCloseoutTests(unittest.TestCase):
    def test_closeout_passes_for_loss_only_to_fixed_retention_path(self) -> None:
        report = build_model_capability_required_term_pair_loss_branch_batch_closeout(
            corpus_contract=fake_corpus_contract(),
            targeted_seed=fake_seed_report(),
            dual_anchor_seed=fake_seed_report(),
            micro_span_seed=fake_seed_report(),
            comparison=fake_comparison(),
            route_decision=fake_route_decision(),
            stability=fake_stability(),
            diagnostic=fake_diagnostic(),
            readiness=fake_readiness(),
            generated_at="2026-05-31T15:30:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_loss_branch_batch_and_start_fixed_retention_objective")
        self.assertEqual(report["summary"]["single_seed_pair_full_count"], 0)
        self.assertEqual(report["summary"]["diagnostic_first_token_gap_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_if_stability_promotes_pair_full(self) -> None:
        stability = fake_stability()
        stability["summary"]["pair_full_seed_count"] = 1
        report = build_model_capability_required_term_pair_loss_branch_batch_closeout(
            corpus_contract=fake_corpus_contract(),
            targeted_seed=fake_seed_report(),
            dual_anchor_seed=fake_seed_report(),
            micro_span_seed=fake_seed_report(),
            comparison=fake_comparison(),
            route_decision=fake_route_decision(),
            stability=stability,
            diagnostic=fake_diagnostic(),
            readiness=fake_readiness(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("targeted stability unexpectedly reached pair-full", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_branch_batch_closeout(
                corpus_contract=fake_corpus_contract(),
                targeted_seed=fake_seed_report(),
                dual_anchor_seed=fake_seed_report(),
                micro_span_seed=fake_seed_report(),
                comparison=fake_comparison(),
                route_decision=fake_route_decision(),
                stability=fake_stability(),
                diagnostic=fake_diagnostic(),
                readiness=fake_readiness(),
            )
            outputs = write_loss_branch_batch_closeout_outputs(report, Path(tmp))
            text = render_loss_branch_batch_closeout_text(report)
            markdown = render_loss_branch_batch_closeout_markdown(report)
            html = render_loss_branch_batch_closeout_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue((Path(tmp) / PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_JSON_FILENAME).is_file())
            self.assertIn("decision=close_loss_branch_batch_and_start_fixed_retention_objective", text)
            self.assertIn("Loss-Branch Ten-Version Closeout", markdown)
            self.assertIn("MiniGPT loss-branch batch closeout", html)

    def test_locate_report_accepts_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "nested" / "model_capability_required_term_pair_loss_branch_batch_closeout.json"
            write_json_payload({"status": "pass"}, report_path)

            self.assertEqual(
                locate_loss_branch_batch_report(root, "model_capability_required_term_pair_loss_branch_batch_closeout.json"),
                report_path,
            )

    def test_cli_require_pass_returns_nonzero_on_bad_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = write_fake_sources(root)
            bad_stability = fake_stability()
            bad_stability["summary"]["seed_count"] = 2
            write_json_payload(bad_stability, sources["stability"])

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_loss_branch_batch_closeout.py"),
                    "--corpus-contract",
                    str(sources["corpus_contract"].parent),
                    "--targeted-seed",
                    str(sources["targeted_seed"].parent),
                    "--dual-anchor-seed",
                    str(sources["dual_anchor_seed"].parent),
                    "--micro-span-seed",
                    str(sources["micro_span_seed"].parent),
                    "--comparison",
                    str(sources["comparison"].parent),
                    "--route-decision",
                    str(sources["route_decision"].parent),
                    "--stability",
                    str(sources["stability"].parent),
                    "--diagnostic",
                    str(sources["diagnostic"].parent),
                    "--readiness",
                    str(sources["readiness"].parent),
                    "--out-dir",
                    str(root / "out"),
                    "--require-pass",
                    "--force",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("status=fail", result.stdout)


def write_fake_sources(root: Path) -> dict[str, Path]:
    sources = {
        "corpus_contract": root / "corpus" / "model_capability_required_term_pair_loss_branch_objective_corpus_contract.json",
        "targeted_seed": root / "targeted" / "model_capability_required_term_pair_coexistence_refresh.json",
        "dual_anchor_seed": root / "dual" / "model_capability_required_term_pair_coexistence_refresh.json",
        "micro_span_seed": root / "micro" / "model_capability_required_term_pair_coexistence_refresh.json",
        "comparison": root / "comparison" / "model_capability_required_term_pair_loss_branch_objective_comparison.json",
        "route_decision": root / "route" / "model_capability_required_term_pair_loss_branch_route_decision.json",
        "stability": root / "stability" / "model_capability_required_term_pair_colon_immediate_stability.json",
        "diagnostic": root / "diagnostic" / "model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.json",
        "readiness": root / "readiness" / "model_capability_required_term_pair_fixed_retention_objective_readiness.json",
    }
    payloads = {
        "corpus_contract": fake_corpus_contract(),
        "targeted_seed": fake_seed_report(),
        "dual_anchor_seed": fake_seed_report(),
        "micro_span_seed": fake_seed_report(),
        "comparison": fake_comparison(),
        "route_decision": fake_route_decision(),
        "stability": fake_stability(),
        "diagnostic": fake_diagnostic(),
        "readiness": fake_readiness(),
    }
    for key, path in sources.items():
        write_json_payload(payloads[key], path)
    return sources


def fake_corpus_contract() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "loss_branch_objective_corpus_modes_ready",
        "summary": {"new_mode_count": 3, "pair_id_removed": True},
    }


def fake_seed_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "summary": {"pair_full_observed": False, "training_status": "pass"},
    }


def fake_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "loss_branch_objectives_confirm_loss_only_tradeoff",
        "summary": {
            "pair_full_report_count": 0,
            "loss_only_tradeoff_report_count": 3,
            "union_hit_terms": ["loss"],
        },
    }


def fake_route_decision() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "select_targeted_loss_branch_for_seed_stability_not_promotion",
        "summary": {
            "selected_stability_route": "v590-targeted",
            "fixed_retention_objective_required": True,
        },
    }


def fake_stability() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_colon_immediate_not_stable",
        "summary": {
            "seed_count": 3,
            "pair_full_seed_count": 0,
            "stable_pair_full": False,
        },
    }


def fake_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_colon_immediate_first_token_gap",
        "summary": {
            "missed_seed_count": 3,
            "missed_first_token_gap_count": 3,
        },
    }


def fake_readiness() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "design_fixed_retention_objective_before_more_loss_branch_training",
        "summary": {
            "fixed_retention_objective_required": True,
            "ready_for_fixed_retention_objective_design": True,
            "required_requirement_count": 3,
        },
    }


if __name__ == "__main__":
    unittest.main()
