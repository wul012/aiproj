from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_coexistence_refresh import (
    build_model_capability_required_term_pair_coexistence_refresh,
    build_pair_coexistence_refresh_corpus,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_coexistence_refresh_artifacts import (
    render_model_capability_required_term_pair_coexistence_refresh_html,
    render_model_capability_required_term_pair_coexistence_refresh_markdown,
    render_model_capability_required_term_pair_coexistence_refresh_text,
    write_model_capability_required_term_pair_coexistence_refresh_outputs,
)


class ModelCapabilityRequiredTermPairCoexistenceRefreshTests(unittest.TestCase):
    def test_refresh_reports_pair_full_when_fake_generation_hits_both_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_coexistence_refresh(
                out_dir=Path(tmp) / "refresh",
                generated_at="2026-05-30T23:30:00Z",
                train_func=fake_train,
                generate_func=fake_generate_pair_full,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_coexistence_refresh_pair_full_observed")
            self.assertTrue(report["summary"]["pair_full_observed"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_refresh_reports_no_pair_full_when_loss_branch_is_missed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_coexistence_refresh(
                out_dir=Path(tmp) / "refresh",
                train_func=fake_train,
                generate_func=fake_generate_fixed_only,
            )

            self.assertEqual(report["decision"], "required_term_pair_coexistence_refresh_no_pair_full")
            self.assertFalse(report["summary"]["pair_full_observed"])

    def test_corpus_contains_balanced_fixed_and_loss_rows(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(repeat=2, bridge_repeat=1)

        self.assertGreaterEqual(corpus.count("fixed: fixed"), 2)
        self.assertGreaterEqual(corpus.count("loss: loss"), 2)
        self.assertIn("fixed: fixed ; loss: loss", corpus)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_coexistence_refresh(
                out_dir=root / "refresh",
                train_func=fake_train,
                generate_func=fake_generate_pair_full,
            )
            outputs = write_model_capability_required_term_pair_coexistence_refresh_outputs(report, root / "refresh")
            text = render_model_capability_required_term_pair_coexistence_refresh_text(report)
            markdown = render_model_capability_required_term_pair_coexistence_refresh_markdown(report)
            html = render_model_capability_required_term_pair_coexistence_refresh_html(report)

            self.assertEqual(set(outputs), {"json", "text", "markdown", "html"})
            self.assertIn("pair_full_observed=True", text)
            self.assertIn("Required-Term Pair Coexistence Refresh", markdown)
            self.assertIn("MiniGPT pair coexistence refresh", html)


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
        "run_dir": str(run_dir),
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "checkpoint_exists": True,
        "tokenizer_exists": True,
    }


def fake_generate_pair_full(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = str(request["expected_term"])
    return {"generated": prompt + " " + expected, "continuation": " " + expected, "blocked_token_count": 0}


def fake_generate_fixed_only(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + " fixed", "continuation": " fixed", "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
