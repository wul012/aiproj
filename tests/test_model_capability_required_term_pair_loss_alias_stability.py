from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_stability import (
    build_model_capability_required_term_pair_loss_alias_stability,
    resolve_exit_code,
    summarize_loss_alias_stability,
)
from minigpt.model_capability_required_term_pair_loss_alias_stability_artifacts import (
    render_model_capability_required_term_pair_loss_alias_stability_html,
    render_model_capability_required_term_pair_loss_alias_stability_markdown,
    render_model_capability_required_term_pair_loss_alias_stability_text,
    write_model_capability_required_term_pair_loss_alias_stability_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasStabilityTests(unittest.TestCase):
    def test_loss_alias_stability_reports_stable_full_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_stability(
                heldout_fixture(),
                out_dir=root / "stability",
                source_path=root / "heldout.json",
                seeds=[514, 515],
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-05-30T15:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate_loss,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_stability_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_stability_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_stability_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_stability_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_stable_full_hit")
            self.assertTrue(report["summary"]["stable_loss_alias_full_coverage"])
            self.assertEqual(report["summary"]["heldout_loss_alias_full_seed_count"], 2)
            self.assertIn("loss_alias_stability_decision=loss_alias_stable_full_hit", text)
            self.assertIn("Loss-Alias Stability", markdown)
            self.assertIn("MiniGPT loss-alias stability", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_loss_alias_stability_reports_seed_dependent_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_stability(
                heldout_fixture(),
                out_dir=root / "stability",
                seeds=[514, 515],
                train_func=fake_train,
                generate_func=fake_generate_seed_514_only,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_seed_dependent")
            self.assertFalse(report["summary"]["stable_loss_alias_full_coverage"])
            self.assertEqual(report["summary"]["heldout_loss_alias_full_seed_count"], 1)

    def test_loss_alias_stability_fails_without_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_stability(
                heldout_fixture(),
                out_dir=root / "stability",
                seeds=[],
                train_func=fake_train,
                generate_func=fake_generate_loss,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("loss-alias stability seed list is empty", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_summarize_loss_alias_stability_handles_no_signal(self) -> None:
        summary = summarize_loss_alias_stability(
            [
                {"status": "pass", "checkpoint_exists": True, "source_loss_hit": False, "heldout_loss_alias_hit_case_count": 0},
                {"status": "pass", "checkpoint_exists": True, "source_loss_hit": False, "heldout_loss_alias_hit_case_count": 0},
            ]
        )

        self.assertEqual(summary["loss_alias_stability_decision"], "loss_alias_no_stable_generation_signal")
        self.assertFalse(summary["stable_loss_alias_full_coverage"])


def heldout_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"heldout_hit_term_count": 1, "heldout_full_term_coverage": False},
        "case_rows": [
            case_row("source-loss", "source", "source", "loss:", "loss", 2, 0),
            case_row("heldout-beta-loss", "heldout", "greek", "beta:", "loss", 2, 0),
            case_row("heldout-theta-loss", "heldout", "greek", "theta:", "loss", 2, 0),
            case_row("heldout-omega-loss", "heldout", "greek", "omega:", "loss", 2, 0),
        ],
    }


def case_row(
    case_id: str,
    case_type: str,
    alias_group: str,
    prompt: str,
    expected: str,
    run_count: int,
    hit_count: int,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_type": case_type,
        "alias_group": alias_group,
        "prompt": prompt,
        "expected_term": expected,
        "run_count": run_count,
        "hit_count": hit_count,
        "hit_rate": round(hit_count / run_count, 4) if run_count else 0.0,
    }


def fake_train(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    metrics = run_dir / "metrics.jsonl"
    train_config = run_dir / "train_config.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    metrics.write_text("{}", encoding="utf-8")
    train_config.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "returncode": 0,
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "metrics_path": str(metrics),
        "train_config_path": str(train_config),
        "checkpoint_exists": True,
        "tokenizer_exists": True,
        "metrics_exists": True,
        "train_config_exists": True,
    }


def fake_generate_loss(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "loss", "continuation": "loss"}


def fake_generate_seed_514_only(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    checkpoint_path = str(request.get("checkpoint_path") or "")
    continuation = "loss" if "seed-514" in checkpoint_path else "----"
    return {"generated": prompt + continuation, "continuation": continuation}
