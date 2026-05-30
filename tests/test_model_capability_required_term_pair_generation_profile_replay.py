from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    build_model_capability_required_term_pair_generation_profile_replay,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_profile_replay_artifacts import (
    render_model_capability_required_term_pair_generation_profile_replay_html,
    render_model_capability_required_term_pair_generation_profile_replay_markdown,
    render_model_capability_required_term_pair_generation_profile_replay_text,
    write_model_capability_required_term_pair_generation_profile_replay_outputs,
)


class ModelCapabilityRequiredTermPairGenerationProfileReplayTests(unittest.TestCase):
    def test_replay_reports_no_pair_gain_when_profile_stays_on_fixed_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = source_fixture(root)

            report = build_model_capability_required_term_pair_generation_profile_replay(
                source,
                out_dir=root / "replay",
                generated_at="2026-05-30T23:00:00Z",
                generate_func=fake_generate_fixed_branch,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "generation_profile_no_pair_coexistence_gain")
            self.assertEqual(report["summary"]["default_pair_full_variant_count"], 0)
            self.assertEqual(report["summary"]["suppression_pair_full_variant_count"], 0)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_replay_reports_pair_gain_when_suppression_hits_both_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_model_capability_required_term_pair_generation_profile_replay(
                source_fixture(root),
                out_dir=root / "replay",
                generate_func=fake_generate_suppression_pair_gain,
            )

            self.assertEqual(report["decision"], "generation_profile_improves_pair_coexistence")
            self.assertEqual(report["summary"]["suppression_pair_full_delta"], 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_generation_profile_replay(
                source_fixture(root),
                out_dir=root / "replay",
                generate_func=fake_generate_fixed_branch,
            )
            outputs = write_model_capability_required_term_pair_generation_profile_replay_outputs(report, root / "replay")
            text = render_model_capability_required_term_pair_generation_profile_replay_text(report)
            markdown = render_model_capability_required_term_pair_generation_profile_replay_markdown(report)
            html = render_model_capability_required_term_pair_generation_profile_replay_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("suppression_hit_delta", text)
            self.assertIn("Required-Term Pair Generation Profile Replay", markdown)
            self.assertIn("MiniGPT pair generation profile replay", html)


def source_fixture(root: Path) -> dict[str, object]:
    run_dir = root / "run"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"fake")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    return {
        "targets": [
            {
                "pair_id": "01-fixed-loss",
                "terms": [
                    {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:", "source_hit_rate": 1.0},
                    {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:", "source_hit_rate": 1.0},
                ],
            }
        ],
        "training_rows": [
            {
                "branch_retention_run_id": "01-fixed-loss-test",
                "pair_id": "01-fixed-loss",
                "variant_id": "test",
                "seed": 502,
                "checkpoint_path": str(run_dir / "checkpoint.pt"),
                "tokenizer_path": str(run_dir / "tokenizer.json"),
            }
        ],
        "probe_rows": [
            {"variant_id": "test", "term": "fixed", "generation_seed": 602},
            {"variant_id": "test", "term": "loss", "generation_seed": 603},
        ],
    }


def fake_generate_fixed_branch(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {
        "generated": prompt + " fixed\nfixed",
        "continuation": " fixed\nfixed",
        "blocked_token_count": 1 if request.get("profile_id") == "suppress_newline_tokens" else 0,
    }


def fake_generate_suppression_pair_gain(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    term = str(request["expected_term"])
    if request.get("profile_id") == "suppress_newline_tokens":
        return {"generated": prompt + " " + term, "continuation": " " + term, "blocked_token_count": 1}
    return fake_generate_fixed_branch(request)


if __name__ == "__main__":
    unittest.main()
