from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay import (
    build_direct_completion_pair_probe_replay,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay_artifacts import (
    render_direct_completion_pair_probe_replay_html,
    render_direct_completion_pair_probe_replay_markdown,
    render_direct_completion_pair_probe_replay_text,
    write_direct_completion_pair_probe_replay_outputs,
)


class DirectCompletionPairProbeReplayTests(unittest.TestCase):
    def test_pair_probe_replay_ready_when_exact_prompt_hits_both_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_direct_completion_pair_probe_replay(
                comparison_fixture(root),
                out_dir=root / "replay",
                selected_training_report=training_fixture(root),
                prompt_specs=({"spec_id": "exact-heldout-pair", "prompt": "fixed=|loss=", "required_for_ready": True},),
                generate_func=fake_generate_pair,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_direct_completion_pair_probe_replay_ready")
        self.assertTrue(report["summary"]["exact_heldout_pair_full"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_pair_probe_replay_not_ready_when_exact_prompt_misses_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_direct_completion_pair_probe_replay(
                comparison_fixture(root),
                out_dir=root / "replay",
                selected_training_report=training_fixture(root),
                prompt_specs=({"spec_id": "exact-heldout-pair", "prompt": "fixed=|loss=", "required_for_ready": True},),
                generate_func=fake_generate_fixed_only,
            )

        self.assertEqual(report["decision"], "pair_readiness_direct_completion_pair_probe_replay_not_ready")
        self.assertFalse(report["summary"]["exact_heldout_pair_full"])

    def test_pair_probe_replay_fails_for_wrong_comparison_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = comparison_fixture(root)
            comparison["decision"] = "pair_readiness_direct_completion_no_improvement"
            report = build_direct_completion_pair_probe_replay(
                comparison,
                out_dir=root / "replay",
                selected_training_report=training_fixture(root),
                generate_func=fake_generate_pair,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("route comparison did not select a direct-completion candidate", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_direct_completion_pair_probe_replay(
                comparison_fixture(root),
                out_dir=root / "replay",
                selected_training_report=training_fixture(root),
                prompt_specs=({"spec_id": "exact-heldout-pair", "prompt": "fixed=|loss=", "required_for_ready": True},),
                generate_func=fake_generate_pair,
            )
            outputs = write_direct_completion_pair_probe_replay_outputs(report, root / "replay")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("exact_heldout_pair_full=True", render_direct_completion_pair_probe_replay_text(report))
        self.assertIn("Pair-Probe Replay", render_direct_completion_pair_probe_replay_markdown(report))
        self.assertIn("MiniGPT direct-completion pair-probe replay", render_direct_completion_pair_probe_replay_html(report))


def comparison_fixture(root: Path) -> dict[str, object]:
    source = root / "training.json"
    source.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "decision": "pair_readiness_direct_completion_route_candidate_found",
        "summary": {"selected_route": "direct-completion-surface"},
        "comparison_rows": [
            {"label": "objective-structure", "path": str(root / "objective.json")},
            {"label": "direct-prompt-bridge", "path": str(root / "bridge.json")},
            {"label": "direct-completion-surface", "path": str(source)},
        ],
    }


def training_fixture(root: Path) -> dict[str, object]:
    run_dir = root / "run"
    run_dir.mkdir(exist_ok=True)
    (run_dir / "checkpoint.pt").write_bytes(b"fake")
    (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "decision": "pair_readiness_training_pair_full_observed",
        "settings": {"seed": 3535, "max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "device": "cpu"},
        "training": {"checkpoint_path": str(run_dir / "checkpoint.pt"), "tokenizer_path": str(run_dir / "tokenizer.json")},
    }


def fake_generate_pair(request: dict[str, object]) -> dict[str, object]:
    term = str(request["expected_term"])
    return {"generated": str(request["prompt"]) + " " + term, "continuation": " " + term, "blocked_token_count": 0}


def fake_generate_fixed_only(request: dict[str, object]) -> dict[str, object]:
    return {"generated": str(request["prompt"]) + " fixed", "continuation": " fixed", "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
