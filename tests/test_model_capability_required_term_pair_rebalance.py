from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import minigpt.model_capability_required_term_pair_rebalance as facade
import minigpt.model_capability_required_term_pair_rebalance_core as core
from minigpt.model_capability_required_term_pair_rebalance import (
    build_model_capability_required_term_pair_rebalance,
    build_required_term_pair_rebalance_corpus,
    compare_rebalance_pairs,
    locate_model_capability_required_term_pair_rebalance_source,
    read_json_report,
    resolve_exit_code,
    select_rebalance_pairs,
    summarize_rebalance_probe_rows,
    summarize_required_term_pair_rebalance,
)
from minigpt.model_capability_required_term_pair_rebalance_artifacts import (
    render_model_capability_required_term_pair_rebalance_html,
    render_model_capability_required_term_pair_rebalance_markdown,
    render_model_capability_required_term_pair_rebalance_text,
    write_model_capability_required_term_pair_rebalance_outputs,
)


class ModelCapabilityRequiredTermPairRebalanceTests(unittest.TestCase):
    def test_facade_reexports_rebalance_core_contract(self) -> None:
        names = (
            "build_required_term_pair_rebalance_corpus",
            "compare_rebalance_pairs",
            "resolve_exit_code",
            "select_rebalance_pairs",
            "summarize_rebalance_probe_rows",
            "summarize_required_term_pair_rebalance",
        )
        for name in names:
            self.assertIs(getattr(facade, name), getattr(core, name))

    def test_rebalance_reports_full_hit_gain_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_pair_curriculum_fixture(root)

            report = build_model_capability_required_term_pair_rebalance(
                read_json_report(source),
                out_dir=root / "rebalance",
                source_path=source,
                pair_limit=2,
                repeat=2,
                isolated_repeat=1,
                generated_at="2026-05-30T00:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss", "fixed"),
                        ("01-fixed-loss", "loss"),
                        ("02-fixed-four", "four"),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_rebalance_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_rebalance_text(report)
            markdown = render_model_capability_required_term_pair_rebalance_markdown(report)
            html = render_model_capability_required_term_pair_rebalance_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_rebalance_capacity_gain")
            self.assertEqual(report["summary"]["pair_full_hit_count"], 1)
            self.assertEqual(report["summary"]["pair_full_hit_delta"], 1)
            self.assertEqual(report["summary"]["probe_hit_delta"], 1)
            self.assertTrue(report["summary"]["rebalance_improved"])
            self.assertIn("pair_rebalance_decision=pair_rebalance_full_hit_gain", text)
            self.assertIn("Required-Term Pair Rebalance", markdown)
            self.assertIn("Pair Comparison", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_rebalance_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_rebalance_reports_no_gain_and_training_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_pair_curriculum_fixture(root)
            source_report = read_json_report(source)

            no_gain = build_model_capability_required_term_pair_rebalance(
                source_report,
                out_dir=root / "no-gain",
                pair_limit=1,
                repeat=1,
                train_func=fake_train,
                generate_func=fake_generate({("01-fixed-loss", "fixed")}),
            )
            failed = build_model_capability_required_term_pair_rebalance(
                source_report,
                out_dir=root / "failed",
                pair_limit=1,
                repeat=1,
                train_func=fake_train_failure,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(no_gain["decision"], "required_term_pair_rebalance_no_gain")
            self.assertEqual(no_gain["summary"]["pair_rebalance_decision"], "pair_rebalance_no_gain")
            self.assertEqual(no_gain["interpretation"]["model_quality_claim"], "not_claimed")
            self.assertEqual(failed["status"], "fail")
            self.assertEqual(failed["decision"], "fix_required_term_pair_rebalance")
            self.assertEqual(failed["summary"]["pair_rebalance_decision"], "pair_rebalance_training_failed")
            self.assertEqual(resolve_exit_code(failed, require_pass=True), 1)

    def test_rebalance_selection_corpus_and_input_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_pair_curriculum_fixture(root)
            source_report = read_json_report(source)

            pairs = select_rebalance_pairs(source_report)
            limited = select_rebalance_pairs(source_report, pair_limit=1)
            corpus = build_required_term_pair_rebalance_corpus(pairs[0], repeat=0, isolated_repeat=0)
            empty_summary = summarize_required_term_pair_rebalance([], [], [], [], [], source_summary={})
            bad_status = build_model_capability_required_term_pair_rebalance(
                {**source_report, "status": "fail"},
                out_dir=root / "bad-status",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )
            bad_decision = build_model_capability_required_term_pair_rebalance(
                {**source_report, "summary": {"pair_curriculum_decision": "some_pairs_preserve_required_terms"}},
                out_dir=root / "bad-decision",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )
            empty_source = build_model_capability_required_term_pair_rebalance(
                {},
                out_dir=root / "empty-source",
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )

            self.assertEqual([row["pair_id"] for row in pairs], ["01-fixed-loss", "02-fixed-four"])
            self.assertEqual([row["pair_id"] for row in limited], ["01-fixed-loss"])
            self.assertIn("fixed:fixed", corpus)
            self.assertIn("not loss", corpus)
            self.assertEqual(empty_summary["pair_rebalance_decision"], "no_partial_pairs_selected")
            self.assertIn("source pair curriculum report is not pass", bad_status["issues"])
            self.assertIn("source pair curriculum is not a partial-only rebalance target", bad_decision["issues"])
            self.assertIn("source pair curriculum report is missing or invalid", empty_source["issues"])

    def test_rebalance_summary_helpers_compare_pair_deltas(self) -> None:
        pairs = [
            {
                "pair_id": "01-fixed-loss",
                "term_names": ["fixed", "loss"],
                "source_hit_terms": ["fixed"],
                "source_missed_terms": ["loss"],
            }
        ]
        probe_rows = [
            {"pair_id": "01-fixed-loss", "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "term": "loss", "continuation_hit_count": 1},
        ]

        pair_summaries = summarize_rebalance_probe_rows(pairs, probe_rows)
        compare_rows = compare_rebalance_pairs(pairs, pair_summaries)

        self.assertTrue(pair_summaries[0]["pair_full_hit"])
        self.assertEqual(compare_rows[0]["hit_count_delta"], 1)


def write_pair_curriculum_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_curriculum.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "pair_curriculum_decision": "pair_curriculum_partial_only",
                "pair_count": 2,
                "probe_hit_count": 2,
                "pair_full_hit_count": 0,
                "pair_partial_hit_count": 2,
                "pair_full_success_rate": 0.0,
                "multi_target_pair_capacity_observed": False,
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
                {
                    "pair_id": "03-fixed-chain",
                    "pair_index": 2,
                    "term_names": ["fixed", "chain"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "summary-evidence-chain", "term": "chain", "scaffold_prompt": "chain:"},
                    ],
                },
            ],
            "pair_summaries": [
                {
                    "pair_id": "01-fixed-loss",
                    "term_names": ["fixed", "loss"],
                    "hit_terms": ["fixed"],
                    "missed_terms": ["loss"],
                    "hit_rate": 0.5,
                    "pair_full_hit": False,
                    "pair_partial_hit": True,
                },
                {
                    "pair_id": "02-fixed-four",
                    "term_names": ["fixed", "four"],
                    "hit_terms": ["four"],
                    "missed_terms": ["fixed"],
                    "hit_rate": 0.5,
                    "pair_full_hit": False,
                    "pair_partial_hit": True,
                },
                {
                    "pair_id": "03-fixed-chain",
                    "term_names": ["fixed", "chain"],
                    "hit_terms": [],
                    "missed_terms": ["fixed", "chain"],
                    "hit_rate": 0.0,
                    "pair_full_hit": False,
                    "pair_partial_hit": False,
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
        pair_id = checkpoint_path.parent.name
        continuation = term if (pair_id, term) in hit_pairs else "noop"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
