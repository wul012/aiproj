from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_capacity_sweep import (
    build_model_capability_required_term_pair_capacity_sweep,
    default_pair_capacity_sweep_variants,
    locate_model_capability_required_term_pair_capacity_sweep_source,
    normalize_capacity_sweep_variants,
    read_json_report,
    resolve_exit_code,
    select_pair_capacity_sweep_pairs,
    summarize_capacity_variant_probe_rows,
    summarize_pair_capacity_sweep,
    summarize_required_term_pair_capacity_sweep,
)
from minigpt.model_capability_required_term_pair_capacity_sweep_artifacts import (
    render_model_capability_required_term_pair_capacity_sweep_html,
    render_model_capability_required_term_pair_capacity_sweep_markdown,
    render_model_capability_required_term_pair_capacity_sweep_text,
    write_model_capability_required_term_pair_capacity_sweep_outputs,
)


class ModelCapabilityRequiredTermPairCapacitySweepTests(unittest.TestCase):
    def test_capacity_sweep_reports_recovered_full_hit_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_pair_seed_stability_fixture(root)
            variants = [
                {"variant_id": "baseline-repeat", "label": "baseline", "repeat": 2, "isolated_repeat": 1, "max_iters": 10, "n_embd": 16},
                {"variant_id": "wider-embd", "label": "wider", "repeat": 2, "isolated_repeat": 1, "max_iters": 10, "n_embd": 24},
            ]

            report = build_model_capability_required_term_pair_capacity_sweep(
                read_json_report(source),
                out_dir=root / "capacity",
                source_path=source,
                seed=496,
                capacity_variants=variants,
                generated_at="2026-05-30T00:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-wider-embd-seed-496", "fixed"),
                        ("01-fixed-loss-wider-embd-seed-496", "loss"),
                        ("01-fixed-loss-baseline-repeat-seed-496", "loss"),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_capacity_sweep_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_capacity_sweep_text(report)
            markdown = render_model_capability_required_term_pair_capacity_sweep_markdown(report)
            html = render_model_capability_required_term_pair_capacity_sweep_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_capacity_sweep_recovered")
            self.assertTrue(report["summary"]["capacity_full_hit_observed"])
            self.assertEqual(report["summary"]["variant_pair_full_hit_count"], 1)
            self.assertEqual(report["summary"]["capacity_full_hit_pair_count"], 1)
            self.assertEqual(report["summary"]["best_variant_id"], "wider-embd")
            self.assertIn("pair_capacity_sweep_decision=pair_capacity_sweep_full_hit_recovered", text)
            self.assertIn("Pair Capacity Sweep", markdown)
            self.assertIn("Variant Results", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_capacity_sweep_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_capacity_sweep_reports_partial_and_training_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_pair_seed_stability_fixture(root))
            variants = [{"variant_id": "baseline", "repeat": 1, "isolated_repeat": 1, "max_iters": 8, "n_embd": 16}]

            partial = build_model_capability_required_term_pair_capacity_sweep(
                source_report,
                out_dir=root / "partial",
                capacity_variants=variants,
                train_func=fake_train,
                generate_func=fake_generate({("01-fixed-loss-baseline-seed-496", "loss")}),
            )
            failed = build_model_capability_required_term_pair_capacity_sweep(
                source_report,
                out_dir=root / "failed",
                capacity_variants=variants,
                train_func=fake_train_failure,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(partial["decision"], "required_term_pair_capacity_sweep_partial")
            self.assertEqual(partial["summary"]["variant_pair_partial_hit_count"], 1)
            self.assertFalse(partial["summary"]["capacity_full_hit_observed"])
            self.assertEqual(failed["status"], "fail")
            self.assertEqual(failed["decision"], "fix_required_term_pair_capacity_sweep")
            self.assertEqual(failed["summary"]["pair_capacity_sweep_decision"], "pair_capacity_sweep_training_failed")
            self.assertEqual(resolve_exit_code(failed, require_pass=True), 1)

    def test_capacity_sweep_selection_and_input_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_pair_seed_stability_fixture(root))

            selected = select_pair_capacity_sweep_pairs(source_report)
            limited = select_pair_capacity_sweep_pairs(source_report, pair_limit=0)
            bad_status = build_model_capability_required_term_pair_capacity_sweep(
                {**source_report, "status": "fail"},
                out_dir=root / "bad-status",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )
            bad_source = build_model_capability_required_term_pair_capacity_sweep(
                {**source_report, "summary": {"source_pair_rebalance_decision": "pair_rebalance_no_gain"}},
                out_dir=root / "bad-source",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )
            empty_source = build_model_capability_required_term_pair_capacity_sweep(
                {},
                out_dir=root / "empty-source",
                capacity_variants=[],
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )

            self.assertEqual([row["pair_id"] for row in selected], ["01-fixed-loss"])
            self.assertEqual(limited, [])
            self.assertIn("source pair rebalance seed-stability report is not pass", bad_status["issues"])
            self.assertIn("source seed-stability report is not tied to a v495 full-hit gain", bad_source["issues"])
            self.assertIn("source pair rebalance seed-stability report is missing or invalid", empty_source["issues"])
            self.assertIn("at least one capacity variant is required", empty_source["issues"])

    def test_capacity_sweep_summary_helpers_choose_best_variant(self) -> None:
        pairs = [{"pair_id": "01-fixed-loss", "term_names": ["fixed", "loss"]}]
        variants = normalize_capacity_sweep_variants(
            [
                {"variant_id": "baseline", "repeat": 1, "isolated_repeat": 1, "max_iters": 8, "n_embd": 16},
                {"variant_id": "longer", "repeat": 1, "isolated_repeat": 1, "max_iters": 12, "n_embd": 16},
            ]
        )
        probes = [
            {"pair_id": "01-fixed-loss", "variant_id": "baseline", "term": "fixed", "continuation_hit_count": 0},
            {"pair_id": "01-fixed-loss", "variant_id": "baseline", "term": "loss", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "longer", "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "longer", "term": "loss", "continuation_hit_count": 1},
        ]

        variant_summaries = summarize_capacity_variant_probe_rows(pairs, variants, probes)
        pair_summaries = summarize_pair_capacity_sweep(pairs, variants, variant_summaries)
        summary = summarize_required_term_pair_capacity_sweep(
            pairs,
            variants,
            [{"training_status": "pass", "checkpoint_exists": True}, {"training_status": "pass", "checkpoint_exists": True}],
            probes,
            variant_summaries,
            pair_summaries,
            source_summary={"pair_rebalance_seed_stability_decision": "rebalance_full_pairs_not_reproduced_across_seeds"},
        )

        self.assertTrue(variant_summaries[1]["pair_full_hit"])
        self.assertEqual(pair_summaries[0]["full_hit_variants"], ["longer"])
        self.assertEqual(summary["best_variant_id"], "longer")
        self.assertEqual(summary["pair_capacity_sweep_decision"], "pair_capacity_sweep_full_hit_recovered")
        self.assertGreaterEqual(len(default_pair_capacity_sweep_variants()), 4)


def write_pair_seed_stability_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_rebalance_seed_stability.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "pair_rebalance_seed_stability_decision": "rebalance_full_pairs_not_reproduced_across_seeds",
                "source_pair_rebalance_decision": "pair_rebalance_full_hit_gain",
                "source_pair_full_hit_count": 1,
                "source_pair_full_hit_delta": 1,
                "selected_pair_count": 1,
                "seed_count": 3,
                "pair_seed_full_hit_count": 0,
                "stable_pair_count": 0,
                "pair_rebalance_seed_stable": False,
            },
            "pairs": [
                {
                    "pair_id": "01-fixed-loss",
                    "pair_index": 0,
                    "term_names": ["fixed", "loss"],
                    "v495_hit_terms": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
                }
            ],
            "pair_seed_summaries": [
                {
                    "pair_id": "01-fixed-loss",
                    "term_names": ["fixed", "loss"],
                    "v495_hit_terms": ["fixed", "loss"],
                    "seed_count": 3,
                    "full_hit_seed_count": 0,
                    "full_hit_seeds": [],
                    "missed_full_hit_seeds": [496, 1496, 2496],
                    "full_hit_rate": 0.0,
                    "stable_full_hit_across_seeds": False,
                    "partial_full_hit_across_seeds": False,
                }
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
