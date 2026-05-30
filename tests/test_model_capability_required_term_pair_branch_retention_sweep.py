from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_branch_retention_sweep import (
    build_model_capability_required_term_pair_branch_retention_sweep,
    build_required_term_pair_branch_retention_corpus,
    default_pair_branch_retention_sweep_variants,
    locate_model_capability_required_term_pair_branch_retention_sweep_source,
    normalize_branch_retention_variants,
    read_json_report,
    resolve_exit_code,
    select_branch_retention_targets,
    summarize_branch_retention_variant_probe_rows,
)
from minigpt.model_capability_required_term_pair_branch_retention_sweep_artifacts import (
    render_model_capability_required_term_pair_branch_retention_sweep_html,
    render_model_capability_required_term_pair_branch_retention_sweep_markdown,
    render_model_capability_required_term_pair_branch_retention_sweep_text,
    write_model_capability_required_term_pair_branch_retention_sweep_outputs,
)


class ModelCapabilityRequiredTermPairBranchRetentionSweepTests(unittest.TestCase):
    def test_branch_retention_sweep_reports_full_hit_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_loss_branch_sweep_fixture(root)
            variants = [
                {"variant_id": "alternating", "cycle_strategy": "alternating", "repeat": 2, "max_iters": 8, "n_embd": 16},
                {"variant_id": "symmetric", "cycle_strategy": "alternating", "repeat": 2, "term_weight": 2, "max_iters": 8, "n_embd": 16},
            ]

            report = build_model_capability_required_term_pair_branch_retention_sweep(
                read_json_report(source),
                out_dir=root / "retention",
                source_path=source,
                seed=502,
                variants=variants,
                generated_at="2026-05-30T03:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-symmetric-seed-502", "fixed"),
                        ("01-fixed-loss-symmetric-seed-502", "loss"),
                        ("01-fixed-loss-alternating-seed-502", "fixed"),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_branch_retention_sweep_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_branch_retention_sweep_text(report)
            markdown = render_model_capability_required_term_pair_branch_retention_sweep_markdown(report)
            html = render_model_capability_required_term_pair_branch_retention_sweep_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_branch_retention_recovered")
            self.assertEqual(report["summary"]["pair_full_hit_variant_count"], 1)
            self.assertEqual(report["summary"]["balanced_retention_variant_count"], 1)
            self.assertEqual(report["summary"]["best_variant_id"], "symmetric")
            self.assertIn("branch_retention_sweep_decision=branch_retention_sweep_full_hit_recovered", text)
            self.assertIn("Branch-Retention Sweep", markdown)
            self.assertIn("Variant Results", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_branch_retention_sweep_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_branch_retention_sweep_reports_tradeoff_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_loss_branch_sweep_fixture(root))
            variants = [{"variant_id": "alternating", "cycle_strategy": "alternating", "repeat": 1, "max_iters": 8, "n_embd": 16}]

            tradeoff = build_model_capability_required_term_pair_branch_retention_sweep(
                source_report,
                out_dir=root / "tradeoff",
                variants=variants,
                train_func=fake_train,
                generate_func=fake_generate({("01-fixed-loss-alternating-seed-502", "loss")}),
            )
            already_full = build_model_capability_required_term_pair_branch_retention_sweep(
                {
                    **source_report,
                    "summary": {
                        **source_report["summary"],
                        "pair_full_hit_variant_count": 1,
                    },
                },
                out_dir=root / "bad",
                variants=variants,
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(tradeoff["decision"], "required_term_pair_branch_retention_partial")
            self.assertEqual(tradeoff["summary"]["retention_tradeoff_variant_count"], 1)
            self.assertEqual(tradeoff["summary"]["pair_full_hit_variant_count"], 0)
            self.assertEqual(already_full["status"], "fail")
            self.assertIn("source loss-branch sweep already has a full-hit variant", already_full["issues"][0])

    def test_branch_retention_target_selection_and_corpus_are_balanced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = read_json_report(write_loss_branch_sweep_fixture(Path(tmp)))
            targets = select_branch_retention_targets(report)
            variants = normalize_branch_retention_variants(
                [{"variant_id": "x"}, {"variant_id": "x"}, {"variant_id": "y", "cycle_strategy": "reverse-order"}]
            )
            corpus = build_required_term_pair_branch_retention_corpus(
                targets[0],
                {"cycle_strategy": "alternating", "repeat": 2, "isolated_repeat": 1, "term_weight": 1, "symmetric_anchor_repeat": 1},
            )

            self.assertEqual(targets[0]["focus_missed_term"], "loss")
            self.assertEqual(targets[0]["source_hit_terms"], ["fixed"])
            self.assertEqual([row["variant_id"] for row in variants], ["x", "y"])
            self.assertEqual(corpus.count("fixed:fixed"), corpus.count("loss:loss"))
            self.assertNotIn("not loss", corpus)
            self.assertNotIn("not fixed", corpus)
            self.assertGreaterEqual(len(default_pair_branch_retention_sweep_variants()), 3)

    def test_branch_retention_summary_rows_mark_source_only(self) -> None:
        targets = [
            {
                "pair_id": "01-fixed-loss",
                "term_names": ["fixed", "loss"],
                "focus_missed_term": "loss",
                "source_hit_terms": ["fixed"],
            }
        ]
        variants = normalize_branch_retention_variants([{"variant_id": "short"}])
        probes = [
            {"pair_id": "01-fixed-loss", "variant_id": "short", "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "short", "term": "loss", "continuation_hit_count": 0},
        ]

        rows = summarize_branch_retention_variant_probe_rows(targets, variants, probes)

        self.assertTrue(rows[0]["source_hit_terms_retained"])
        self.assertFalse(rows[0]["focus_missed_term_hit"])
        self.assertTrue(rows[0]["retention_tradeoff"])
        self.assertEqual(rows[0]["missed_terms"], ["loss"])


def write_loss_branch_sweep_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_loss_branch_sweep.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "loss_branch_sweep_decision": "loss_branch_sweep_tradeoff_only",
                "branch_tradeoff_variant_count": 3,
                "focus_term_hit_variant_count": 3,
                "pair_full_hit_variant_count": 0,
                "best_variant_id": "missed-first-order",
            },
            "targets": [
                {
                    "pair_id": "01-fixed-loss",
                    "term_names": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
                    "focus_missed_term": "loss",
                    "missed_term_names": ["loss"],
                    "hit_term_names": ["fixed"],
                }
            ],
            "target_summaries": [
                {
                    "pair_id": "01-fixed-loss",
                    "focus_missed_term": "loss",
                    "source_hit_terms": ["fixed"],
                    "branch_tradeoff_variant_count": 3,
                    "focus_term_hit_variant_count": 3,
                    "pair_full_hit_variant_count": 0,
                    "best_variant_id": "missed-first-order",
                }
            ],
        },
    )
    return source


def fake_train(context: dict[str, object]) -> dict[str, object]:
    train_dir = Path(str(context["train_dir"]))
    train_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = train_dir / "checkpoint.pt"
    tokenizer = train_dir / "tokenizer.json"
    metrics = train_dir / "metrics.jsonl"
    config = train_dir / "train_config.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    metrics.write_text("{}", encoding="utf-8")
    config.write_text(json.dumps({"seed": context.get("seed")}), encoding="utf-8")
    return {
        "status": "pass",
        "returncode": 0,
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


def fake_generate(hit_rows: set[tuple[str, str]]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.strip(":")
        run_id = Path(str(request["checkpoint_path"])).parent.name
        continuation = term if (run_id, term) in hit_rows else "noop"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
