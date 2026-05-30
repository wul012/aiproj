from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_continuation_span_stability import (
    build_model_capability_required_term_pair_continuation_span_stability,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_continuation_span_stability_artifacts import (
    render_model_capability_required_term_pair_continuation_span_stability_html,
    render_model_capability_required_term_pair_continuation_span_stability_markdown,
    render_model_capability_required_term_pair_continuation_span_stability_text,
    write_model_capability_required_term_pair_continuation_span_stability_outputs,
)


class ModelCapabilityRequiredTermPairContinuationSpanStabilityTests(unittest.TestCase):
    def test_continuation_span_stability_reports_stable_prefix_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollup_path, rollup = write_rollup_fixture(root)
            report = build_model_capability_required_term_pair_continuation_span_stability(
                rollup,
                out_dir=root / "stability",
                source_path=rollup_path,
                seeds=[510, 511],
                repeat=2,
                max_iters=4,
                train_func=fake_train,
                generate_func=fake_generate_no_hits,
                prefix_sweep_func=fake_prefix_sweep,
            )
            outputs = write_model_capability_required_term_pair_continuation_span_stability_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_continuation_span_stability_text(report)
            markdown = render_model_capability_required_term_pair_continuation_span_stability_markdown(report)
            html = render_model_capability_required_term_pair_continuation_span_stability_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_continuation_span_prefix_gain_stable")
            self.assertEqual(report["summary"]["prefix_gain_seed_count"], 2)
            self.assertTrue(report["summary"]["stable_prefix_gain"])
            self.assertIn("stable_prefix_gain=True", text)
            self.assertIn("Seed | Status", markdown)
            self.assertIn("MiniGPT continuation-span stability", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_continuation_span_stability_fails_without_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollup_path, rollup = write_rollup_fixture(root)
            report = build_model_capability_required_term_pair_continuation_span_stability(
                rollup,
                out_dir=root / "stability",
                source_path=rollup_path,
                seeds=[],
                train_func=fake_train,
                generate_func=fake_generate_no_hits,
                prefix_sweep_func=fake_prefix_sweep,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("at least one seed is required", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)


def write_rollup_fixture(root: Path) -> tuple[Path, dict[str, object]]:
    prefix_path = root / "e" / "508" / "model_capability_required_term_pair_prefix_completion_sweep.json"
    write_json(prefix_path, prefix_fixture())
    rollup = {
        "status": "pass",
        "next_experiment_plan": {"plan_id": "continuation_span_objective_fixed_loss"},
        "stage_rows": [{"stage": "prefix_completion", "source_path": str(prefix_path)}],
    }
    rollup_path = root / "rollup" / "model_capability_required_term_pair_diagnostic_rollup.json"
    write_json(rollup_path, rollup)
    return rollup_path, rollup


def prefix_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "targets": [
            {
                "variant_id": "symmetric-anchor",
                "probes": [
                    {"variant_id": "symmetric-anchor", "pair_id": "01-fixed-loss", "profile_id": "greedy-12", "prompt": "fixed:", "prompt_term": "fixed", "expected_term": "fixed"},
                    {"variant_id": "symmetric-anchor", "pair_id": "01-fixed-loss", "profile_id": "greedy-12", "prompt": "loss:", "prompt_term": "loss", "expected_term": "loss"},
                ],
            }
        ],
        "probe_summaries": [
            {"expected_term": "fixed", "prompt_term": "fixed", "minimum_hit_prefix_token_count": 4, "one_token_prefix_hit": False, "full_prefix_hit": True},
            {"expected_term": "loss", "prompt_term": "loss", "minimum_hit_prefix_token_count": 1, "one_token_prefix_hit": True, "full_prefix_hit": True},
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


def fake_generate_no_hits(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    return {"generated": prompt + "zzzz", "continuation": "zzzz"}


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
