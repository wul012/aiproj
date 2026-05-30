from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_alias_focus import (
    build_loss_alias_focus_corpus,
    build_model_capability_required_term_pair_loss_alias_focus,
    resolve_exit_code,
    select_loss_alias_focus_cases,
    select_loss_alias_support_cases,
)
from minigpt.model_capability_required_term_pair_loss_alias_focus_artifacts import (
    render_model_capability_required_term_pair_loss_alias_focus_html,
    render_model_capability_required_term_pair_loss_alias_focus_markdown,
    render_model_capability_required_term_pair_loss_alias_focus_text,
    write_model_capability_required_term_pair_loss_alias_focus_outputs,
)


class ModelCapabilityRequiredTermPairLossAliasFocusTests(unittest.TestCase):
    def test_focus_reports_repaired_rows_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_focus(
                stability_fixture(),
                out_dir=root / "focus",
                source_path=root / "stability.json",
                seeds=[515],
                base_repeat=2,
                focus_repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-05-30T16:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate_loss,
            )
            outputs = write_model_capability_required_term_pair_loss_alias_focus_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_alias_focus_text(report)
            markdown = render_model_capability_required_term_pair_loss_alias_focus_markdown(report)
            html = render_model_capability_required_term_pair_loss_alias_focus_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_focus_support_full_hit")
            self.assertTrue(report["summary"]["stable_focus_full_coverage"])
            self.assertTrue(report["summary"]["stable_support_full_coverage"])
            self.assertIn("loss_alias_focus_decision=loss_alias_focus_support_full_hit", text)
            self.assertIn("Loss-Alias Focus", markdown)
            self.assertIn("MiniGPT loss-alias focus", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_focus_selects_missed_cases_and_corpus_boosts_them(self) -> None:
        support = select_loss_alias_support_cases(stability_fixture())
        focus = select_loss_alias_focus_cases(stability_fixture())
        corpus = build_loss_alias_focus_corpus(support, focus, base_repeat=1, focus_repeat=1, bridge_repeat=1)

        self.assertEqual([row["case_id"] for row in focus], ["source-loss", "heldout-beta-loss"])
        self.assertIn("focus alias beta: means loss", corpus)
        self.assertIn("focused loss alias bridge", corpus)

    def test_focus_no_repair_is_structurally_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_alias_focus(
                stability_fixture(),
                out_dir=root / "focus",
                seeds=[515],
                train_func=fake_train,
                generate_func=fake_generate_empty,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_alias_focus_no_repair")
            self.assertFalse(report["summary"]["stable_focus_full_coverage"])

    def test_focus_fails_without_missed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = stability_fixture()
            for seed_report in fixture["seed_reports"]:  # type: ignore[index]
                for row in seed_report["case_rows"]:  # type: ignore[index]
                    row["generation_hit_count"] = 1
            report = build_model_capability_required_term_pair_loss_alias_focus(
                fixture,
                out_dir=root / "focus",
                train_func=fake_train,
                generate_func=fake_generate_loss,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("source loss-alias stability report has no missed focus cases", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def stability_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "seed_reports": [
            seed_report(514, {"source-loss": 1, "heldout-beta-loss": 1, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
            seed_report(515, {"source-loss": 0, "heldout-beta-loss": 0, "heldout-theta-loss": 1, "heldout-omega-loss": 1}),
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


def fake_generate_empty(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "----", "continuation": "----"}
