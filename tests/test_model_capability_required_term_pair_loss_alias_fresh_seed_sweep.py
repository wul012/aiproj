from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_fresh_seed_sweep import (
    build_model_capability_required_term_pair_loss_alias_fresh_seed_sweep,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_fresh_seed_sweep_artifacts import (
    render_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_html,
    render_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_markdown,
    render_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_text,
    write_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasFreshSeedSweepTests(unittest.TestCase):
    def test_sweep_reports_stable_baseline_strict_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_alias_fresh_seed_sweep(
                stability_fixture(),
                out_dir=Path(tmp) / "sweep",
                seeds=[527, 528],
                base_repeat=2,
                focus_repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-05-30T22:00:00Z",
                train_func=fake_train,
                focus_generate_func=fake_generate_loss,
                probe_generate_func=fake_probe_generate_loss,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_fresh_seed_sweep_baseline_stably_strict")
            self.assertEqual(report["summary"]["seed_count"], 2)
            self.assertEqual(report["summary"]["baseline_strict_full_seed_count"], 2)
            self.assertEqual(report["summary"]["total_blocked_token_strict_gain_count"], 0)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_sweep_reports_blocked_token_recovery_when_baseline_splits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_alias_fresh_seed_sweep(
                stability_fixture(),
                out_dir=Path(tmp) / "sweep",
                seeds=[527, 528],
                base_repeat=2,
                focus_repeat=2,
                bridge_repeat=1,
                max_iters=4,
                train_func=fake_train,
                focus_generate_func=fake_generate_split_loss,
                probe_generate_func=fake_probe_generate_blocked_loss,
            )

            self.assertEqual(report["decision"], "required_term_pair_loss_alias_fresh_seed_sweep_blocked_token_stably_recovers")
            self.assertEqual(report["summary"]["baseline_strict_full_seed_count"], 0)
            self.assertEqual(report["summary"]["blocked_token_strict_full_seed_count"], 2)
            self.assertEqual(report["summary"]["total_blocked_token_strict_gain_count"], 8)

    def test_outputs_include_sweep_and_compare_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_fresh_seed_sweep(
                stability_fixture(),
                out_dir=root / "sweep",
                seeds=[527],
                base_repeat=2,
                focus_repeat=2,
                bridge_repeat=1,
                max_iters=4,
                train_func=fake_train,
                focus_generate_func=fake_generate_loss,
                probe_generate_func=fake_probe_generate_loss,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_outputs(report, root / "sweep")
            text = render_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_fresh_seed_sweep_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue((root / "sweep" / "fresh-compare-report" / "model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.json").exists())
            self.assertIn("baseline_strict_full_seed_count=1", text)
            self.assertIn("Fresh Seed Sweep", markdown)
            self.assertIn("MiniGPT loss-alias fresh seed sweep", html)


def stability_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "seed_reports": [
            seed_report(526, {"source-loss": 1, "heldout-beta-loss": 1, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
            seed_report(527, {"source-loss": 0, "heldout-beta-loss": 0, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
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


def fake_generate_loss(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "loss", "continuation": "loss"}


def fake_generate_split_loss(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "lo\ns\ns", "continuation": "lo\ns\ns"}


def fake_probe_generate_loss(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "loss", "continuation": "loss", "excluded_token_count": 1 if request.get("exclude_token_texts") else 0}


def fake_probe_generate_blocked_loss(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    if request.get("exclude_token_texts"):
        return {"generated": prompt + "loss", "continuation": "loss", "excluded_token_count": 1}
    return {"generated": prompt + "lo\ns\ns", "continuation": "lo\ns\ns", "excluded_token_count": 0}
