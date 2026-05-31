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

    def test_colon_immediate_corpus_removes_leading_space_after_prompt(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(repeat=2, bridge_repeat=1, corpus_mode="colon_immediate")

        self.assertGreaterEqual(corpus.count("fixed:fixed"), 2)
        self.assertGreaterEqual(corpus.count("loss:loss"), 2)
        self.assertNotIn("fixed: fixed", corpus)
        self.assertNotIn("loss: loss", corpus)

    def test_first_token_boost_corpus_adds_short_prefix_targets(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="colon_immediate_first_token_boost",
        )

        self.assertIn("fixed:f", corpus)
        self.assertIn("loss:l", corpus)
        self.assertIn("fixed:fi", corpus)
        self.assertIn("loss:lo", corpus)
        self.assertNotIn("fixed: fixed", corpus)

    def test_isolated_prompt_corpus_separates_fixed_and_loss_blocks(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="colon_immediate_isolated_prompt",
        )

        self.assertIn("[fixed-objective]", corpus)
        self.assertIn("[loss-objective]", corpus)
        self.assertIn("fixed branch answer fixed", corpus)
        self.assertIn("loss branch answer loss", corpus)
        self.assertNotIn("fixed: fixed", corpus)

    def test_loss_calibrated_corpus_adds_loss_weight_without_spaces(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="colon_immediate_loss_calibrated",
        )

        self.assertGreater(corpus.count("loss:loss"), corpus.count("fixed:fixed"))
        self.assertIn("loss prompt should not continue fixed", corpus)
        self.assertIn("fixed prompt should not continue loss", corpus)
        self.assertNotIn("loss: loss", corpus)

    def test_equals_surface_fixed_repair_targets_equals_prompt(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_fixed_repair",
        )

        self.assertGreater(corpus.count("fixed=fixed"), corpus.count("loss=loss"))
        self.assertIn("prompt=fixed=target=fixed", corpus)
        self.assertIn("fixed= should continue fixed.", corpus)
        self.assertNotIn("fixed:fixed", corpus)

    def test_equals_surface_fixed_repair_replays_equals_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_coexistence_refresh(
                out_dir=Path(tmp) / "refresh",
                corpus_mode="equals_surface_fixed_repair",
                train_func=fake_train,
                generate_func=fake_generate_pair_full,
            )
            case_rows = report["replay_report"]["case_rows"]
            prompts = {row["prompt"] for row in case_rows}

            self.assertIn("fixed=", prompts)
            self.assertIn("loss=", prompts)
            self.assertNotIn("fixed:", prompts)

    def test_equals_surface_balanced_repair_keeps_fixed_and_loss_symmetry(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_balanced_repair",
        )

        lines = corpus.splitlines()

        self.assertEqual(lines.count("fixed=fixed"), lines.count("loss=loss"))
        self.assertIn("fixed= should not continue loss", corpus)
        self.assertIn("loss= should not continue fixed", corpus)
        self.assertNotIn("fixed:fixed", corpus)

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
