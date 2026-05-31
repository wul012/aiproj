from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_seed_config_replay import (
    build_model_capability_required_term_pair_seed_config_replay,
    locate_pair_seed_config_selection,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_replay_artifacts import (
    render_model_capability_required_term_pair_seed_config_replay_html,
    render_model_capability_required_term_pair_seed_config_replay_markdown,
    render_model_capability_required_term_pair_seed_config_replay_text,
    write_model_capability_required_term_pair_seed_config_replay_outputs,
)


class ModelCapabilityRequiredTermPairSeedConfigReplayTests(unittest.TestCase):
    def test_selected_replay_reports_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_config_replay(
                selection_report(),
                out_dir=Path(tmp) / "replay",
                source_reports_by_config={"v544": source_report(Path(tmp), 535)},
                generate_func=fake_generate_pair_full,
                generated_at="2026-05-31T01:40:00Z",
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_seed_config_replay_ready")
            self.assertEqual(report["summary"]["replay_pair_full_seed_count"], 1)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_selected_replay_reports_partial_policy_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_config_replay(
                selection_report(),
                out_dir=Path(tmp) / "replay",
                source_reports_by_config={"v544": source_report(Path(tmp), 535)},
                generate_func=fake_generate_fixed_only,
            )

            self.assertEqual(report["decision"], "required_term_pair_seed_config_replay_not_ready")
            self.assertEqual(report["summary"]["policy_replay_gap_count"], 1)

    def test_selected_replay_fails_without_source_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_seed_config_replay(
                selection_report(),
                out_dir=Path(tmp) / "replay",
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_seed_config_replay(
                selection_report(),
                out_dir=root / "replay",
                source_reports_by_config={"v544": source_report(root, 535)},
                generate_func=fake_generate_pair_full,
            )
            outputs = write_model_capability_required_term_pair_seed_config_replay_outputs(report, root / "replay")
            text = render_model_capability_required_term_pair_seed_config_replay_text(report)
            markdown = render_model_capability_required_term_pair_seed_config_replay_markdown(report)
            html = render_model_capability_required_term_pair_seed_config_replay_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("selected_replay_ready=True", text)
            self.assertIn("Seed Config Replay", markdown)
            self.assertIn("MiniGPT pair seed config replay", html)
            self.assertTrue(
                (root / "replay" / "replay-reports" / "v544" / "seed-535" / "model_capability_required_term_pair_generation_profile_replay.json").is_file()
            )

    def test_locate_accepts_output_directory(self) -> None:
        self.assertEqual(
            locate_pair_seed_config_selection(Path("out-dir")),
            Path("out-dir"),
        )


def selection_report() -> dict[str, object]:
    return {
        "status": "pass",
        "config_rows": [{"config_id": "v544", "source_path": "missing.json"}],
        "selection_rows": [
            {
                "seed": 535,
                "selected_config_id": "v544",
                "selection_ready": True,
                "selected_pair_full": True,
            }
        ],
    }


def source_report(root: Path, seed: int) -> dict[str, object]:
    checkpoint = root / f"seed-{seed}" / "checkpoint.pt"
    tokenizer = root / f"seed-{seed}" / "tokenizer.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "settings": {"top_k": 2, "temperature": 0.8, "max_new_tokens": 12},
        "seed_reports": [
            {
                "settings": {"seed": seed},
                "training": {"checkpoint_path": str(checkpoint), "tokenizer_path": str(tokenizer)},
            }
        ],
    }


def fake_generate_pair_full(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = str(request["expected_term"])
    return {"generated": prompt + expected, "continuation": expected, "blocked_token_count": 0}


def fake_generate_fixed_only(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "fixed", "continuation": "fixed", "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
