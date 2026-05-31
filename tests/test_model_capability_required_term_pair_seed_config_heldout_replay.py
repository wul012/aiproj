from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_seed_config_heldout_replay import (
    build_model_capability_required_term_pair_seed_config_heldout_replay,
    locate_pair_seed_config_selection,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_heldout_replay_artifacts import (
    render_model_capability_required_term_pair_seed_config_heldout_replay_html,
    render_model_capability_required_term_pair_seed_config_heldout_replay_markdown,
    render_model_capability_required_term_pair_seed_config_heldout_replay_text,
    write_model_capability_required_term_pair_seed_config_heldout_replay_outputs,
)
from tests.test_model_capability_required_term_pair_seed_config_replay import (
    fake_generate_fixed_only,
    fake_generate_pair_full,
    selection_report,
    source_report,
)


class ModelCapabilityRequiredTermPairSeedConfigHeldoutReplayTests(unittest.TestCase):
    def test_heldout_replay_reports_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_config_heldout_replay(
                selection_report(),
                out_dir=Path(tmp) / "heldout",
                prompt_specs=({"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},),
                source_reports_by_config={"v544": source_report(Path(tmp), 535)},
                generate_func=fake_generate_pair_full,
                generated_at="2026-05-31T02:00:00Z",
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_seed_config_heldout_replay_ready")
            self.assertEqual(report["summary"]["heldout_pair_full_count"], 1)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_heldout_replay_reports_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_config_heldout_replay(
                selection_report(),
                out_dir=Path(tmp) / "heldout",
                prompt_specs=({"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},),
                source_reports_by_config={"v544": source_report(Path(tmp), 535)},
                generate_func=fake_generate_fixed_only,
            )

            self.assertEqual(report["decision"], "required_term_pair_seed_config_heldout_replay_not_ready")
            self.assertEqual(report["summary"]["heldout_pair_full_count"], 0)

    def test_outputs_render_all_formats_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_seed_config_heldout_replay(
                selection_report(),
                out_dir=root / "heldout",
                prompt_specs=({"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},),
                source_reports_by_config={"v544": source_report(root, 535)},
                generate_func=fake_generate_pair_full,
            )
            outputs = write_model_capability_required_term_pair_seed_config_heldout_replay_outputs(report, root / "heldout")
            text = render_model_capability_required_term_pair_seed_config_heldout_replay_text(report)
            markdown = render_model_capability_required_term_pair_seed_config_heldout_replay_markdown(report)
            html = render_model_capability_required_term_pair_seed_config_heldout_replay_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("heldout_all_pair_full=True", text)
            self.assertIn("Held-Out Replay", markdown)
            self.assertIn("MiniGPT pair seed config held-out replay", html)
            self.assertTrue(
                (root / "heldout" / "heldout-replay-reports" / "equals" / "v544" / "seed-535" / "model_capability_required_term_pair_generation_profile_replay.json").is_file()
            )

    def test_locate_accepts_output_directory(self) -> None:
        self.assertEqual(
            locate_pair_seed_config_selection(Path("out-dir")),
            Path("out-dir"),
        )


if __name__ == "__main__":
    unittest.main()
