from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_rebalance_seed_stability import (
    build_model_capability_required_term_pair_rebalance_seed_stability,
    locate_model_capability_required_term_pair_rebalance_seed_stability_source,
    read_json_report,
    resolve_exit_code,
    select_rebalance_seed_stability_pairs,
    summarize_pair_seed_stability,
    summarize_required_term_pair_rebalance_seed_stability,
    summarize_seed_pair_probe_rows,
)
from minigpt.model_capability_required_term_pair_rebalance_seed_stability_artifacts import (
    render_model_capability_required_term_pair_rebalance_seed_stability_html,
    render_model_capability_required_term_pair_rebalance_seed_stability_markdown,
    render_model_capability_required_term_pair_rebalance_seed_stability_text,
    write_model_capability_required_term_pair_rebalance_seed_stability_outputs,
)


class ModelCapabilityRequiredTermPairRebalanceSeedStabilityTests(unittest.TestCase):
    def test_seed_stability_reports_stable_full_hit_pair_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_pair_rebalance_fixture(root)

            report = build_model_capability_required_term_pair_rebalance_seed_stability(
                read_json_report(source),
                out_dir=root / "seed-stability",
                source_path=source,
                seeds=(496, 1496),
                repeat=2,
                isolated_repeat=1,
                generated_at="2026-05-30T00:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-seed-496", "fixed"),
                        ("01-fixed-loss-seed-496", "loss"),
                        ("01-fixed-loss-seed-1496", "fixed"),
                        ("01-fixed-loss-seed-1496", "loss"),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_rebalance_seed_stability_outputs(
                report,
                root / "outputs",
            )
            text = render_model_capability_required_term_pair_rebalance_seed_stability_text(report)
            markdown = render_model_capability_required_term_pair_rebalance_seed_stability_markdown(report)
            html = render_model_capability_required_term_pair_rebalance_seed_stability_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_rebalance_seed_stability_observed")
            self.assertEqual(report["summary"]["stable_pair_count"], 1)
            self.assertEqual(report["summary"]["pair_seed_full_hit_count"], 2)
            self.assertTrue(report["summary"]["pair_rebalance_seed_stable"])
            self.assertIn("pair_rebalance_seed_stability_decision=all_rebalance_full_pairs_seed_stable", text)
            self.assertIn("Pair Rebalance Seed Stability", markdown)
            self.assertIn("Pair Stability", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_rebalance_seed_stability_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_seed_stability_reports_partial_and_training_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_pair_rebalance_fixture(root))

            partial = build_model_capability_required_term_pair_rebalance_seed_stability(
                source_report,
                out_dir=root / "partial",
                seeds=(496, 1496),
                repeat=1,
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-seed-496", "fixed"),
                        ("01-fixed-loss-seed-496", "loss"),
                        ("01-fixed-loss-seed-1496", "fixed"),
                    }
                ),
            )
            failed = build_model_capability_required_term_pair_rebalance_seed_stability(
                source_report,
                out_dir=root / "failed",
                seeds=(496,),
                repeat=1,
                train_func=fake_train_failure,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(partial["decision"], "required_term_pair_rebalance_seed_stability_partial")
            self.assertEqual(partial["summary"]["stable_pair_count"], 0)
            self.assertEqual(partial["summary"]["partial_stable_pair_count"], 1)
            self.assertEqual(failed["status"], "fail")
            self.assertEqual(failed["decision"], "fix_required_term_pair_rebalance_seed_stability")
            self.assertEqual(failed["summary"]["pair_rebalance_seed_stability_decision"], "pair_rebalance_seed_training_failed")
            self.assertEqual(resolve_exit_code(failed, require_pass=True), 1)

    def test_seed_stability_selection_and_input_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_pair_rebalance_fixture(root))

            selected = select_rebalance_seed_stability_pairs(source_report)
            limited = select_rebalance_seed_stability_pairs(source_report, pair_limit=0)
            bad_status = build_model_capability_required_term_pair_rebalance_seed_stability(
                {**source_report, "status": "fail"},
                out_dir=root / "bad-status",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )
            bad_decision = build_model_capability_required_term_pair_rebalance_seed_stability(
                {**source_report, "summary": {"pair_rebalance_decision": "pair_rebalance_no_gain"}},
                out_dir=root / "bad-decision",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )
            empty_source = build_model_capability_required_term_pair_rebalance_seed_stability(
                {},
                out_dir=root / "empty-source",
                seeds=(),
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )

            self.assertEqual([row["pair_id"] for row in selected], ["01-fixed-loss"])
            self.assertEqual(limited, [])
            self.assertIn("source pair rebalance report is not pass", bad_status["issues"])
            self.assertIn("source pair rebalance did not produce a full-hit gain", bad_decision["issues"])
            self.assertIn("source pair rebalance report is missing or invalid", empty_source["issues"])
            self.assertIn("at least one seed is required", empty_source["issues"])

    def test_seed_stability_summary_helpers_group_pair_seed_hits(self) -> None:
        pairs = [
            {
                "pair_id": "01-fixed-loss",
                "term_names": ["fixed", "loss"],
                "v495_hit_terms": ["fixed", "loss"],
            }
        ]
        probes = [
            {"pair_id": "01-fixed-loss", "seed": 496, "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "seed": 496, "term": "loss", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "seed": 1496, "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "seed": 1496, "term": "loss", "continuation_hit_count": 0},
        ]

        seed_pair_summaries = summarize_seed_pair_probe_rows(pairs, probes, [496, 1496])
        pair_seed_summaries = summarize_pair_seed_stability(pairs, seed_pair_summaries, [496, 1496])
        summary = summarize_required_term_pair_rebalance_seed_stability(
            pairs,
            [{"training_status": "pass", "checkpoint_exists": True}, {"training_status": "pass", "checkpoint_exists": True}],
            probes,
            seed_pair_summaries,
            pair_seed_summaries,
            [496, 1496],
            source_summary={"pair_rebalance_decision": "pair_rebalance_full_hit_gain"},
        )

        self.assertEqual(seed_pair_summaries[0]["hit_terms"], ["fixed", "loss"])
        self.assertTrue(seed_pair_summaries[0]["pair_full_hit"])
        self.assertTrue(pair_seed_summaries[0]["partial_full_hit_across_seeds"])
        self.assertEqual(summary["pair_rebalance_seed_stability_decision"], "pair_rebalance_seed_stability_partial_only")


def write_pair_rebalance_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_rebalance.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "pair_rebalance_decision": "pair_rebalance_full_hit_gain",
                "source_pair_full_hit_count": 0,
                "pair_full_hit_count": 1,
                "pair_full_hit_delta": 1,
                "probe_hit_count": 5,
                "probe_hit_delta": -1,
                "rebalance_improved": True,
            },
            "pairs": [
                {
                    "pair_id": "01-fixed-loss",
                    "pair_index": 0,
                    "term_names": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
                },
                {
                    "pair_id": "02-fixed-four",
                    "pair_index": 1,
                    "term_names": ["fixed", "four"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "structured-experiment-json", "term": "four", "scaffold_prompt": "four:"},
                    ],
                },
            ],
            "compare_rows": [
                {
                    "pair_id": "01-fixed-loss",
                    "term_names": ["fixed", "loss"],
                    "source_hit_terms": ["fixed"],
                    "source_missed_terms": ["loss"],
                    "rebalance_hit_terms": ["fixed", "loss"],
                    "rebalance_missed_terms": [],
                    "hit_count_delta": 1,
                    "rebalance_pair_full_hit": True,
                },
                {
                    "pair_id": "02-fixed-four",
                    "term_names": ["fixed", "four"],
                    "source_hit_terms": ["four"],
                    "source_missed_terms": ["fixed"],
                    "rebalance_hit_terms": ["four"],
                    "rebalance_missed_terms": ["fixed"],
                    "hit_count_delta": 0,
                    "rebalance_pair_full_hit": False,
                },
            ],
        },
    )
    return source


def fake_train(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    metrics = run_dir / "metrics.jsonl"
    config = run_dir / "train_config.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    metrics.write_text("{}", encoding="utf-8")
    config.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "returncode": 0,
        "run_dir": str(run_dir),
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "metrics_path": str(metrics),
        "train_config_path": str(config),
        "checkpoint_exists": True,
        "tokenizer_exists": True,
        "metrics_exists": True,
        "train_config_exists": True,
        "command_text": "fake train",
    }


def fake_train_failure(context: dict[str, object]) -> dict[str, object]:
    run_dir = Path(str(context["train_dir"]))
    run_dir.mkdir(parents=True, exist_ok=True)
    return {
        "status": "fail",
        "returncode": 2,
        "run_dir": str(run_dir),
        "checkpoint_path": str(run_dir / "checkpoint.pt"),
        "tokenizer_path": str(run_dir / "tokenizer.json"),
        "metrics_path": str(run_dir / "metrics.jsonl"),
        "train_config_path": str(run_dir / "train_config.json"),
        "checkpoint_exists": False,
        "tokenizer_exists": False,
        "metrics_exists": False,
        "train_config_exists": False,
        "command_text": "fake failed train",
    }


def fake_generate(hit_pairs: set[tuple[str, str]]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.strip(":")
        checkpoint_path = Path(str(request["checkpoint_path"]))
        run_id = checkpoint_path.parent.name
        continuation = term if (run_id, term) in hit_pairs else "noop"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
