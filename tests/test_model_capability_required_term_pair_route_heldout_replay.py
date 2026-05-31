from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_route_heldout_replay import (
    build_model_capability_required_term_pair_route_heldout_replay,
    locate_pair_route_decision,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_route_heldout_replay_artifacts import (
    render_model_capability_required_term_pair_route_heldout_replay_html,
    render_model_capability_required_term_pair_route_heldout_replay_markdown,
    render_model_capability_required_term_pair_route_heldout_replay_text,
    write_model_capability_required_term_pair_route_heldout_replay_outputs,
)
from scripts.run_model_capability_required_term_pair_route_heldout_replay import _prompt_specs
from tests.test_model_capability_required_term_pair_seed_config_replay import fake_generate_fixed_only, fake_generate_pair_full


class ModelCapabilityRequiredTermPairRouteHeldoutReplayTests(unittest.TestCase):
    def test_route_heldout_replay_reports_ready_for_pair_full_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_route_heldout_replay(
                route_decision(),
                out_dir=Path(tmp) / "heldout",
                prompt_specs=({"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},),
                selected_source_report=source_report(Path(tmp), pair_full=True),
                generate_func=fake_generate_pair_full,
                generated_at="2026-05-31T08:00:00Z",
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_route_heldout_replay_ready")
            self.assertEqual(report["summary"]["heldout_pair_full_count"], 1)
            self.assertEqual(report["replay_rows"][0]["seed"], 1535)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_route_heldout_replay_reports_not_ready_when_generation_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_route_heldout_replay(
                route_decision(),
                out_dir=Path(tmp) / "heldout",
                prompt_specs=({"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},),
                selected_source_report=source_report(Path(tmp), pair_full=True),
                generate_func=fake_generate_fixed_only,
            )

            self.assertEqual(report["decision"], "required_term_pair_route_heldout_replay_not_ready")
            self.assertEqual(report["summary"]["heldout_pair_full_count"], 0)

    def test_invalid_route_decision_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_route_heldout_replay(
            {"status": "fail", "selected_route": {}},
            out_dir="unused",
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("route decision status is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_route_heldout_replay(
                route_decision(),
                out_dir=root / "heldout",
                prompt_specs=({"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},),
                selected_source_report=source_report(root, pair_full=True),
                generate_func=fake_generate_pair_full,
            )
            outputs = write_model_capability_required_term_pair_route_heldout_replay_outputs(report, root / "heldout")
            text = render_model_capability_required_term_pair_route_heldout_replay_text(report)
            markdown = render_model_capability_required_term_pair_route_heldout_replay_markdown(report)
            html = render_model_capability_required_term_pair_route_heldout_replay_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("heldout_all_pair_full=True", text)
            self.assertIn("Route Held-Out Replay", markdown)
            self.assertIn("MiniGPT route held-out replay", html)
            self.assertTrue(
                (root / "heldout" / "route-heldout-replay-reports" / "equals" / "seed-1535" / "model_capability_required_term_pair_generation_profile_replay.json").is_file()
            )

    def test_locate_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_pair_route_decision(root),
                root / "model_capability_required_term_pair_first_token_route_decision.json",
            )

    def test_cli_prompt_specs_allow_larger_heldout_suite(self) -> None:
        specs = _prompt_specs([["colon-tight", "fixed:", "loss:"], ["equals-spaced", "fixed = ", "loss = "]])

        self.assertEqual(
            specs,
            (
                {"spec_id": "colon-tight", "fixed_prompt": "fixed:", "loss_prompt": "loss:"},
                {"spec_id": "equals-spaced", "fixed_prompt": "fixed = ", "loss_prompt": "loss = "},
            ),
        )


def route_decision() -> dict[str, object]:
    return {
        "status": "pass",
        "selected_route": {
            "source_label": "v562-loss-balanced",
            "source_path": "selected.json",
            "corpus_mode": "equals_surface_no_pair_id_loss_balanced_repair",
        },
    }


def source_report(root: Path, *, pair_full: bool) -> dict[str, object]:
    checkpoint = root / "checkpoint.pt"
    tokenizer = root / "tokenizer.json"
    checkpoint.write_text("checkpoint", encoding="utf-8")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "settings": {"max_new_tokens": 12, "temperature": 0.8, "top_k": 2},
        "seed_rows": [{"seed": 1535, "pair_full_observed": pair_full}],
        "seed_reports": [
            {
                "settings": {"seed": 1535},
                "out_dir": str(root),
                "training": {
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                },
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
