from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_training_run import (
    build_pair_readiness_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_training_run_artifacts import (
    render_pair_readiness_training_run_html,
    render_pair_readiness_training_run_markdown,
    render_pair_readiness_training_run_text,
    write_pair_readiness_training_run_outputs,
)


class PairReadinessTrainingRunTests(unittest.TestCase):
    def test_training_run_reports_pair_full_with_fake_generation_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            materialization = materialization_fixture(Path(tmp))
            report = build_pair_readiness_training_run(
                materialization,
                out_dir=Path(tmp) / "run",
                train_func=fake_train,
                generate_func=fake_generate_hits,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_training_pair_full_observed")
        self.assertTrue(report["summary"]["pair_full_observed"])
        self.assertEqual(report["interpretation"]["model_quality_claim"], "direct_pair_probe_hit")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_training_run_reports_no_pair_full_when_loss_misses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            materialization = materialization_fixture(Path(tmp))
            report = build_pair_readiness_training_run(
                materialization,
                out_dir=Path(tmp) / "run",
                train_func=fake_train,
                generate_func=fake_generate_fixed_only,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_training_no_pair_full")
        self.assertFalse(report["summary"]["pair_full_observed"])

    def test_training_run_fails_when_corpus_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            materialization = materialization_fixture(Path(tmp))
            Path(materialization["materialized_paths"]["training_corpus"]).unlink()
            report = build_pair_readiness_training_run(materialization, out_dir=Path(tmp) / "run", train_func=fake_train)

        self.assertEqual(report["status"], "fail")
        self.assertIn("pair-readiness training corpus is missing", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_pair_readiness_training_run(
                materialization_fixture(Path(tmp)),
                out_dir=Path(tmp) / "run",
                train_func=fake_train,
                generate_func=fake_generate_hits,
            )
            outputs = write_pair_readiness_training_run_outputs(report, Path(tmp) / "report")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_training_pair_full_observed", render_pair_readiness_training_run_text(report))
        self.assertIn("Pair-Readiness Training Run", render_pair_readiness_training_run_markdown(report))
        self.assertIn("MiniGPT pair-readiness training run", render_pair_readiness_training_run_html(report))


def materialization_fixture(root: Path) -> dict[str, object]:
    corpus = root / "corpus.txt"
    corpus.write_text("fixed=fixed\nloss=loss\n", encoding="utf-8")
    return {
        "status": "pass",
        "decision": "pair_readiness_corpus_materialized",
        "materialized_paths": {"training_corpus": str(corpus)},
        "summary": {"materialization_ready": True},
        "heldout_eval_fixture": {
            "probes": [
                {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed"},
                {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss"},
                {"id": "fixed-loss-pair", "prompt": "fixed=|loss=", "expected_term": "fixed+loss"},
            ]
        },
    }


def fake_train(context: dict[str, object]) -> dict[str, object]:
    train_dir = Path(str(context["train_dir"]))
    train_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = train_dir / "checkpoint.pt"
    tokenizer = train_dir / "tokenizer.json"
    checkpoint.write_text("fake checkpoint", encoding="utf-8")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "run_dir": str(train_dir),
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "checkpoint_exists": True,
        "tokenizer_exists": True,
    }


def fake_generate_hits(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = str(request["expected_term"])
    return {"generated": prompt + expected, "continuation": expected}


def fake_generate_fixed_only(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    if request["expected_term"] == "fixed":
        return {"generated": prompt + "fixed", "continuation": "fixed"}
    return {"generated": prompt + "miss", "continuation": "miss"}


if __name__ == "__main__":
    unittest.main()
