from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_replay import (
    build_model_capability_required_term_pair_surface_policy_replay,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_policy_replay_artifacts import (
    render_surface_policy_replay_html,
    render_surface_policy_replay_markdown,
    render_surface_policy_replay_text,
    write_surface_policy_replay_outputs,
)


class SurfacePolicyReplayTests(unittest.TestCase):
    def test_replay_finds_stable_pair_context_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_policy_replay(
                stability_fixture(root),
                policy_plan_fixture(),
                out_dir=root / "replay",
                generated_at="2026-06-02T00:40:00Z",
                generate_func=fake_generate_context_policy_pair_full,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_surface_policy_replay_stable_pair_full_policy_found")
            self.assertIn("pair_context_prefix", report["summary"]["stable_pair_full_policy_ids"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_replay_reports_no_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_policy_replay(
                stability_fixture(root),
                policy_plan_fixture(),
                out_dir=root / "replay",
                generate_func=fake_generate_no_hits,
            )

            self.assertEqual(report["decision"], "required_term_pair_surface_policy_replay_no_gain")
            self.assertEqual(report["summary"]["stable_pair_full_policy_count"], 0)

    def test_bad_policy_plan_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = policy_plan_fixture()
            plan["status"] = "fail"
            report = build_model_capability_required_term_pair_surface_policy_replay(
                stability_fixture(root),
                plan,
                out_dir=root / "replay",
                generate_func=fake_generate_context_policy_pair_full,
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_policy_replay(
                stability_fixture(root),
                policy_plan_fixture(),
                out_dir=root / "replay",
                generate_func=fake_generate_context_policy_pair_full,
            )
            outputs = write_surface_policy_replay_outputs(report, root / "outputs")
            text = render_surface_policy_replay_text(report)
            markdown = render_surface_policy_replay_markdown(report)
            html = render_surface_policy_replay_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("stable_pair_full_policy_count=1", text)
            self.assertIn("Surface Policy Replay", markdown)
            self.assertIn("MiniGPT surface policy replay", html)


def stability_fixture(root: Path) -> dict[str, object]:
    seed_reports = []
    for seed in (1535, 2535):
        run_dir = root / f"seed-{seed}"
        checkpoint = run_dir / "checkpoint.pt"
        tokenizer = run_dir / "tokenizer.json"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_bytes(b"fake")
        tokenizer.write_text("{}", encoding="utf-8")
        seed_reports.append(
            {
                "settings": {"seed": seed},
                "training": {
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                    "checkpoint_exists": True,
                    "tokenizer_exists": True,
                },
            }
        )
    return {"status": "pass", "seed_reports": seed_reports}


def policy_plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "policy_rows": [
            {
                "policy_id": "single_label_default",
                "prompt_template": "{term}=",
                "generation_profile": "default",
                "leakage_level": "none",
                "included_in_replay": True,
            },
            {
                "policy_id": "pair_context_prefix",
                "prompt_template": "{other_term}={other_term} {term}=",
                "generation_profile": "suppress_newline_tokens",
                "leakage_level": "contextual_anchor",
                "included_in_replay": True,
            },
            {
                "policy_id": "target_echo_upper_bound",
                "prompt_template": "{term}={term}",
                "generation_profile": "suppress_newline_tokens",
                "leakage_level": "target_echo",
                "included_in_replay": False,
            },
        ],
    }


def fake_generate_context_policy_pair_full(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = str(request["expected_term"])
    if str(request["policy_id"]) == "pair_context_prefix":
        return {"generated": prompt + expected, "continuation": expected, "blocked_token_count": 0}
    return {"generated": prompt + "other", "continuation": "other", "blocked_token_count": 0}


def fake_generate_no_hits(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "other", "continuation": "other", "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
