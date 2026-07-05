from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import minigpt.model_capability_required_term_pair_continuation_span_objective as facade
import minigpt.model_capability_required_term_pair_continuation_span_objective_core as core
from minigpt.model_capability_required_term_pair_continuation_span_objective import (
    build_continuation_span_corpus,
    build_model_capability_required_term_pair_continuation_span_objective,
    refresh_training_artifact_status,
    resolve_exit_code,
    select_continuation_span_examples,
)
from minigpt.model_capability_required_term_pair_continuation_span_objective_artifacts import (
    render_model_capability_required_term_pair_continuation_span_objective_html,
    render_model_capability_required_term_pair_continuation_span_objective_markdown,
    render_model_capability_required_term_pair_continuation_span_objective_text,
    write_model_capability_required_term_pair_continuation_span_objective_outputs,
)


class ModelCapabilityRequiredTermPairContinuationSpanObjectiveTests(unittest.TestCase):
    def test_facade_reexports_continuation_span_core_contract(self) -> None:
        names = (
            "build_continuation_span_corpus",
            "compare_span_prefix_summaries",
            "refresh_training_artifact_status",
            "resolve_exit_code",
            "select_continuation_span_examples",
            "summarize_continuation_span_objective",
            "summarize_source_prefix_completion",
        )
        for name in names:
            self.assertIs(getattr(facade, name), getattr(core, name))

    def test_continuation_span_objective_reports_full_generation_and_prefix_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollup = write_rollup_fixture(root)
            report = build_model_capability_required_term_pair_continuation_span_objective(
                rollup,
                out_dir=root / "span",
                source_path=root / "rollup" / "model_capability_required_term_pair_diagnostic_rollup.json",
                repeat=2,
                bridge_repeat=1,
                max_iters=4,
                generated_at="2026-05-30T12:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate,
                prefix_sweep_func=fake_prefix_sweep,
            )
            outputs = write_model_capability_required_term_pair_continuation_span_objective_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_continuation_span_objective_text(report)
            markdown = render_model_capability_required_term_pair_continuation_span_objective_markdown(report)
            html = render_model_capability_required_term_pair_continuation_span_objective_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_continuation_span_full_hit")
            self.assertTrue(report["summary"]["candidate_pair_full_generation_hit"])
            self.assertEqual(report["summary"]["prefix_minimum_improved_count"], 1)
            self.assertIn("continuation_span_decision=continuation_span_full_pair_generation_hit", text)
            self.assertIn("Prefix Comparison", markdown)
            self.assertIn("MiniGPT continuation-span objective", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_continuation_span_objective_fails_without_prefix_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollup = write_rollup_fixture(root)
            rollup["stage_rows"][0]["source_path"] = str(root / "missing.json")

            report = build_model_capability_required_term_pair_continuation_span_objective(
                rollup,
                out_dir=root / "span",
                source_path=root / "rollup" / "model_capability_required_term_pair_diagnostic_rollup.json",
                train_func=fake_train,
                generate_func=fake_generate,
                prefix_sweep_func=fake_prefix_sweep,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("source prefix-completion report is missing or invalid", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_select_examples_and_corpus_keep_fixed_loss_span_targets(self) -> None:
        prefix_report = prefix_fixture(Path("source.json"))
        examples = select_continuation_span_examples(prefix_report)
        corpus = build_continuation_span_corpus(examples, repeat=1, bridge_repeat=1)

        self.assertEqual([row["term"] for row in examples], ["fixed", "loss"])
        self.assertIn("fixed:fixed", corpus)
        self.assertIn("loss:loss", corpus)
        self.assertIn("pair span fixed loss keeps fixed after fixed:", corpus)

    def test_refresh_training_artifact_status_repairs_stale_failed_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"fake")
            tokenizer.write_text("{}", encoding="utf-8")

            refreshed = refresh_training_artifact_status(
                {
                    "status": "fail",
                    "returncode": 0,
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                    "checkpoint_exists": False,
                    "tokenizer_exists": False,
                }
            )

            self.assertEqual(refreshed["status"], "pass")
            self.assertTrue(refreshed["checkpoint_exists"])
            self.assertTrue(refreshed["tokenizer_exists"])


def write_rollup_fixture(root: Path) -> dict[str, object]:
    prefix_path = root / "e" / "508" / "model_capability_required_term_pair_prefix_completion_sweep.json"
    write_json(prefix_path, prefix_fixture(prefix_path))
    rollup = {
        "status": "pass",
        "next_experiment_plan": {"plan_id": "continuation_span_objective_fixed_loss"},
        "stage_rows": [
            {
                "stage": "prefix_completion",
                "source_path": str(prefix_path),
            }
        ],
    }
    rollup_path = root / "rollup" / "model_capability_required_term_pair_diagnostic_rollup.json"
    write_json(rollup_path, rollup)
    return rollup


def prefix_fixture(_path: Path) -> dict[str, object]:
    return {
        "status": "pass",
        "targets": [
            {
                "variant_id": "symmetric-anchor",
                "probes": [
                    {
                        "variant_id": "symmetric-anchor",
                        "pair_id": "01-fixed-loss",
                        "profile_id": "greedy-12",
                        "prompt": "fixed:",
                        "prompt_term": "fixed",
                        "expected_term": "fixed",
                        "checkpoint_path": "checkpoint.pt",
                        "tokenizer_path": "tokenizer.json",
                    },
                    {
                        "variant_id": "symmetric-anchor",
                        "pair_id": "01-fixed-loss",
                        "profile_id": "greedy-12",
                        "prompt": "loss:",
                        "prompt_term": "loss",
                        "expected_term": "loss",
                        "checkpoint_path": "checkpoint.pt",
                        "tokenizer_path": "tokenizer.json",
                    },
                ],
            }
        ],
        "probe_summaries": [
            {
                "expected_term": "fixed",
                "prompt_term": "fixed",
                "source_profile_count": 3,
                "minimum_hit_prefix_token_count": 4,
                "one_token_prefix_hit": False,
                "full_prefix_hit": True,
            },
            {
                "expected_term": "loss",
                "prompt_term": "loss",
                "source_profile_count": 3,
                "minimum_hit_prefix_token_count": 1,
                "one_token_prefix_hit": True,
                "full_prefix_hit": True,
            },
        ],
    }


def fake_train(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    metrics = run_dir / "metrics.jsonl"
    train_config = run_dir / "train_config.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    metrics.write_text("{}\n", encoding="utf-8")
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


def fake_generate(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    term = prompt.replace(":", "")
    return {"generated": prompt + term, "continuation": term}


def fake_prefix_sweep(request: dict[str, object]) -> list[dict[str, object]]:
    term = str(request["expected_term"])
    expected_count = 5 if term == "fixed" else 4
    first_hit = 2 if term == "fixed" else 1
    return [
        {
            **request,
            "expected_token_count": expected_count,
            "forced_prefix_token_count": prefix_len,
            "forced_prefix_text": term[:prefix_len],
            "completion": term if prefix_len >= first_hit else term[:prefix_len],
            "completion_preview": term if prefix_len >= first_hit else term[:prefix_len],
            "prefix_completion_hit": prefix_len >= first_hit,
        }
        for prefix_len in range(1, expected_count + 1)
    ]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
