from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare import (
    build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_artifacts import (
    render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_html,
    render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_markdown,
    render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_text,
    write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasBlockedTokenFreshCompareTests(unittest.TestCase):
    def test_fresh_compare_recovers_strict_hits_with_blocked_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare(
                stability_fixture(),
                out_dir=Path(tmp) / "fresh",
                source_path="stability.json",
                seeds=[527],
                base_repeat=2,
                focus_repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-05-30T21:00:00Z",
                train_func=fake_train,
                focus_generate_func=fake_generate_split_loss,
                probe_generate_func=fake_probe_generate,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_blocked_token_fresh_strict_recovery")
            self.assertEqual(report["summary"]["baseline_strict_hit_count"], 0)
            self.assertEqual(report["summary"]["blocked_token_strict_hit_count"], 4)
            self.assertEqual(report["summary"]["blocked_token_strict_gain_count"], 4)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_outputs_include_combined_and_sidecar_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare(
                stability_fixture(),
                out_dir=root / "fresh",
                seeds=[527],
                base_repeat=2,
                focus_repeat=2,
                bridge_repeat=1,
                max_iters=4,
                train_func=fake_train,
                focus_generate_func=fake_generate_split_loss,
                probe_generate_func=fake_probe_generate,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_outputs(report, root / "fresh")
            text = render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue((root / "fresh" / "fresh-focus-report" / "model_capability_required_term_pair_loss_alias_focus.json").exists())
            self.assertTrue(
                (root / "fresh" / "blocked-token-probe-report" / "model_capability_required_term_pair_loss_alias_newline_suppression_probe.json").exists()
            )
            self.assertIn("blocked_token_strict_gain_count=4", text)
            self.assertIn("Blocked-Token Fresh Compare", markdown)
            self.assertIn("MiniGPT loss-alias blocked-token fresh compare", html)

    def test_fresh_compare_fails_when_focus_has_no_missed_rows(self) -> None:
        report = build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare(
            stability_without_misses(),
            out_dir="out",
            train_func=fake_train,
            focus_generate_func=fake_generate_split_loss,
            probe_generate_func=fake_probe_generate,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("fresh focus report did not pass structurally", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def stability_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "seed_reports": [
            seed_report(526, {"source-loss": 1, "heldout-beta-loss": 1, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
            seed_report(527, {"source-loss": 0, "heldout-beta-loss": 0, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
        ],
    }


def stability_without_misses() -> dict[str, object]:
    return {
        "status": "pass",
        "seed_reports": [
            seed_report(526, {"source-loss": 1, "heldout-beta-loss": 1, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
            seed_report(527, {"source-loss": 1, "heldout-beta-loss": 1, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
        ],
    }


def seed_report(seed: int, hits: dict[str, int]) -> dict[str, object]:
    return {
        "status": "pass",
        "settings": {"generation_seed": seed},
        "case_rows": [
            case_row("source-loss", "source", "source", "loss:", hits["source-loss"]),
            case_row("heldout-beta-loss", "heldout", "greek", "beta:", hits["heldout-beta-loss"]),
            case_row("heldout-omega-loss", "heldout", "greek", "omega:", hits["heldout-omega-loss"]),
            case_row("heldout-theta-loss", "heldout", "greek", "theta:", hits["heldout-theta-loss"]),
        ],
    }


def case_row(case_id: str, case_type: str, alias_group: str, prompt: str, hit_count: int) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_type": case_type,
        "alias_group": alias_group,
        "prompt": prompt,
        "expected_term": "loss",
        "generation_hit_count": hit_count,
    }


def fake_train(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "returncode": 0,
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "checkpoint_exists": True,
        "tokenizer_exists": True,
    }


def fake_generate_split_loss(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "lo\ns\ns", "continuation": "lo\ns\ns"}


def fake_probe_generate(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    if request.get("exclude_token_texts"):
        return {"generated": prompt + "loss", "continuation": "loss", "excluded_token_count": 1}
    return {"generated": prompt + "lo\ns\ns", "continuation": "lo\ns\ns", "excluded_token_count": 0}
