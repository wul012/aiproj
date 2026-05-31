from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_seed_config_heldout_gap import (
    build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic,
    locate_pair_seed_config_heldout_replay,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_heldout_gap_artifacts import (
    render_model_capability_required_term_pair_seed_config_heldout_gap_html,
    render_model_capability_required_term_pair_seed_config_heldout_gap_markdown,
    render_model_capability_required_term_pair_seed_config_heldout_gap_text,
    write_model_capability_required_term_pair_seed_config_heldout_gap_outputs,
)


class ModelCapabilityRequiredTermPairSeedConfigHeldoutGapTests(unittest.TestCase):
    def test_diagnostic_localizes_fixed_term_surface_gap(self) -> None:
        report = build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic(
            heldout_report_fixture(pair_full=False),
            source_path="heldout.json",
            generated_at="2026-05-31T03:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_seed_config_heldout_gap_fixed_term_surface")
        self.assertEqual(report["summary"]["gap_count"], 1)
        self.assertEqual(report["summary"]["spec_gap_counts"], {"equals": 1})
        self.assertEqual(report["gap_rows"][0]["missed_terms"], ["fixed"])
        self.assertEqual(report["gap_rows"][0]["best_profile_id"], "suppress_newline_tokens")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_reports_gap_free_when_every_row_is_pair_full(self) -> None:
        report = build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic(heldout_report_fixture(pair_full=True))

        self.assertEqual(report["decision"], "required_term_pair_seed_config_heldout_gap_none")
        self.assertEqual(report["summary"]["gap_free"], True)
        self.assertEqual(report["summary"]["gap_count"], 0)

    def test_invalid_source_status_fails_require_pass(self) -> None:
        source = heldout_report_fixture(pair_full=True) | {"status": "fail"}

        report = build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("held-out replay report status is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_seed_config_heldout_gap_diagnostic(heldout_report_fixture(pair_full=False))
            outputs = write_model_capability_required_term_pair_seed_config_heldout_gap_outputs(report, root / "gap")
            text = render_model_capability_required_term_pair_seed_config_heldout_gap_text(report)
            markdown = render_model_capability_required_term_pair_seed_config_heldout_gap_markdown(report)
            html = render_model_capability_required_term_pair_seed_config_heldout_gap_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("gap_count=1", text)
            self.assertIn("fixed_term_surface_gap", markdown)
            self.assertIn("MiniGPT held-out gap diagnostic", html)

    def test_locate_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_pair_seed_config_heldout_replay(root),
                root / "model_capability_required_term_pair_seed_config_heldout_replay.json",
            )


def heldout_report_fixture(*, pair_full: bool) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_seed_config_heldout_replay_ready" if pair_full else "required_term_pair_seed_config_heldout_replay_partial",
        "replay_rows": [
            {
                "spec_id": "equals",
                "seed": 1535,
                "selected_config_id": "v546-loss-calibrated-topk2-t080",
                "status": "pass",
                "replay_decision": "generation_profile_improves_pair_coexistence" if pair_full else "generation_profile_no_pair_coexistence_gain",
                "fixed_prompt": "fixed=",
                "loss_prompt": "loss=",
                "replay_pair_full": pair_full,
                "default_pair_full_variant_count": 1 if pair_full else 0,
                "suppression_pair_full_variant_count": 1 if pair_full else 0,
                "top_k": 2,
                "temperature": 0.8,
                "source_path": "source.json",
            }
        ],
        "replay_reports": [
            {
                "spec_id": "equals",
                "config_id": "v546-loss-calibrated-topk2-t080",
                "seed": 1535,
                "report": child_replay_fixture(pair_full=pair_full),
            }
        ],
    }


def child_replay_fixture(*, pair_full: bool) -> dict[str, object]:
    hit_terms = ["fixed", "loss"] if pair_full else ["loss"]
    missed_terms: list[str] = [] if pair_full else ["fixed"]
    return {
        "variant_rows": [
            {
                "variant_id": "heldout-equals-seed-1535",
                "profile_id": "default",
                "hit_terms": hit_terms,
                "missed_terms": missed_terms,
                "pair_full_hit": pair_full,
            },
            {
                "variant_id": "heldout-equals-seed-1535",
                "profile_id": "suppress_newline_tokens",
                "hit_terms": hit_terms,
                "missed_terms": missed_terms,
                "pair_full_hit": pair_full,
            },
        ],
        "case_rows": [
            {
                "profile_id": "default",
                "term": "fixed",
                "prompt": "fixed=",
                "generation_seed": 1535,
                "continuation_hit": pair_full,
                "generated_preview": "fixed=losss",
                "continuation_preview": "losss",
                "blocked_token_count": 0,
            },
            {
                "profile_id": "default",
                "term": "loss",
                "prompt": "loss=",
                "generation_seed": 1536,
                "continuation_hit": True,
                "generated_preview": "loss=fixel",
                "continuation_preview": "fixel",
                "blocked_token_count": 0,
            },
            {
                "profile_id": "suppress_newline_tokens",
                "term": "fixed",
                "prompt": "fixed=",
                "generation_seed": 1535,
                "continuation_hit": pair_full,
                "generated_preview": "fixed=los:lompromp",
                "continuation_preview": "los:lompromp",
                "blocked_token_count": 1,
            },
            {
                "profile_id": "suppress_newline_tokens",
                "term": "loss",
                "prompt": "loss=",
                "generation_seed": 1536,
                "continuation_hit": True,
                "generated_preview": "loss=fixel",
                "continuation_preview": "fixel",
                "blocked_token_count": 1,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
