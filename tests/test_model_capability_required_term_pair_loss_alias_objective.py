from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_objective import (
    build_loss_alias_objective_corpus,
    build_model_capability_required_term_pair_loss_alias_objective,
    resolve_exit_code,
    select_loss_alias_objective_cases,
)
from minigpt.model_capability_required_term_pair_loss_alias_objective_artifacts import (
    render_model_capability_required_term_pair_loss_alias_objective_html,
    render_model_capability_required_term_pair_loss_alias_objective_markdown,
    render_model_capability_required_term_pair_loss_alias_objective_text,
    write_model_capability_required_term_pair_loss_alias_objective_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasObjectiveTests(unittest.TestCase):
    def test_loss_alias_objective_reports_full_hit_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_objective(
                heldout_fixture(),
                out_dir=root / "loss-alias",
                source_path=root / "heldout.json",
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-05-30T14:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate_loss,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_objective_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_objective_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_objective_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_objective_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_continuation_full_hit")
            self.assertTrue(report["summary"]["heldout_loss_alias_full_coverage"])
            self.assertEqual(report["summary"]["heldout_loss_alias_hit_case_count"], 3)
            self.assertIn("loss_alias_decision=loss_alias_heldout_full_hit", text)
            self.assertIn("Loss-Alias Objective", markdown)
            self.assertIn("MiniGPT loss-alias objective", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_loss_alias_objective_no_gain_is_structurally_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_objective(
                heldout_fixture(),
                out_dir=root / "loss-alias",
                train_func=fake_train,
                generate_func=fake_generate_empty,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_no_gain")
            self.assertFalse(report["summary"]["source_loss_hit"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_loss_alias_objective_fails_without_alias_matrix_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_objective(
                {"status": "pass", "summary": {"heldout_hit_term_count": 1}, "case_rows": []},
                out_dir=root / "loss-alias",
                train_func=fake_train,
                generate_func=fake_generate_loss,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("source continuation-span heldout report has no loss alias cases", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_select_loss_alias_cases_and_corpus(self) -> None:
        cases = select_loss_alias_objective_cases(heldout_fixture())
        corpus = build_loss_alias_objective_corpus(cases, repeat=1, bridge_repeat=1)

        self.assertEqual([row["case_id"] for row in cases], ["source-loss", "heldout-beta-loss", "heldout-omega-loss", "heldout-theta-loss"])
        self.assertIn("loss:loss", corpus)
        self.assertIn("beta:loss", corpus)
        self.assertIn("omega:loss", corpus)
        self.assertIn("loss alias bridge", corpus)


def heldout_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"heldout_hit_term_count": 1, "heldout_full_term_coverage": False},
        "case_rows": [
            case_row("source-fixed", "source", "source", "fixed:", "fixed", 2, 2),
            case_row("source-loss", "source", "source", "loss:", "loss", 2, 0),
            case_row("heldout-alpha-fixed", "heldout", "greek", "alpha:", "fixed", 2, 2),
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


def fake_generate_empty(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "----", "continuation": "----"}
