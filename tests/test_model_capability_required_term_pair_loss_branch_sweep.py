from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_branch_sweep import (
    build_model_capability_required_term_pair_loss_branch_sweep,
    build_required_term_pair_loss_branch_corpus,
    default_pair_loss_branch_sweep_variants,
    locate_model_capability_required_term_pair_loss_branch_sweep_source,
    normalize_loss_branch_variants,
    read_json_report,
    resolve_exit_code,
    select_loss_branch_targets,
    summarize_loss_branch_variant_probe_rows,
)
from minigpt.model_capability_required_term_pair_loss_branch_sweep_artifacts import (
    render_model_capability_required_term_pair_loss_branch_sweep_html,
    render_model_capability_required_term_pair_loss_branch_sweep_markdown,
    render_model_capability_required_term_pair_loss_branch_sweep_text,
    write_model_capability_required_term_pair_loss_branch_sweep_outputs,
)


class ModelCapabilityRequiredTermPairLossBranchSweepTests(unittest.TestCase):
    def test_loss_branch_sweep_reports_full_hit_recovery_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_contrast_free_training_fixture(root)
            variants = [
                {"variant_id": "missed-first", "term_order": "missed-first", "repeat": 2, "max_iters": 8, "n_embd": 16},
                {
                    "variant_id": "missed-boosted",
                    "term_order": "source-order",
                    "repeat": 2,
                    "missed_weight": 2,
                    "max_iters": 8,
                    "n_embd": 16,
                },
            ]

            report = build_model_capability_required_term_pair_loss_branch_sweep(
                read_json_report(source),
                out_dir=root / "loss-branch",
                source_path=source,
                seed=501,
                variants=variants,
                generated_at="2026-05-30T02:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-missed-boosted-seed-501", "fixed"),
                        ("01-fixed-loss-missed-boosted-seed-501", "loss"),
                        ("01-fixed-loss-missed-first-seed-501", "loss"),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_loss_branch_sweep_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_loss_branch_sweep_text(report)
            markdown = render_model_capability_required_term_pair_loss_branch_sweep_markdown(report)
            html = render_model_capability_required_term_pair_loss_branch_sweep_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_loss_branch_recovered")
            self.assertEqual(report["summary"]["focus_term_hit_variant_count"], 2)
            self.assertEqual(report["summary"]["pair_full_hit_variant_count"], 1)
            self.assertEqual(report["summary"]["best_variant_id"], "missed-boosted")
            self.assertIn("loss_branch_sweep_decision=loss_branch_sweep_full_hit_recovered", text)
            self.assertIn("Loss-Branch Sweep", markdown)
            self.assertIn("Variant Results", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_loss_branch_sweep_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_loss_branch_sweep_reports_tradeoff_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_contrast_free_training_fixture(root))
            variants = [{"variant_id": "missed-first", "term_order": "missed-first", "repeat": 1, "max_iters": 8, "n_embd": 16}]

            tradeoff = build_model_capability_required_term_pair_loss_branch_sweep(
                source_report,
                out_dir=root / "tradeoff",
                variants=variants,
                train_func=fake_train,
                generate_func=fake_generate({("01-fixed-loss-missed-first-seed-501", "loss")}),
            )
            already_full = build_model_capability_required_term_pair_loss_branch_sweep(
                {
                    **source_report,
                    "summary": {
                        **source_report["summary"],
                        "contrast_free_full_hit_observed": True,
                        "variant_pair_full_hit_count": 1,
                    },
                },
                out_dir=root / "bad",
                variants=variants,
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(tradeoff["decision"], "required_term_pair_loss_branch_tradeoff")
            self.assertEqual(tradeoff["summary"]["focus_term_hit_variant_count"], 1)
            self.assertEqual(tradeoff["summary"]["branch_tradeoff_variant_count"], 1)
            self.assertEqual(already_full["status"], "fail")
            self.assertIn("source contrast-free training already has a full-hit pair", already_full["issues"][0])

    def test_loss_branch_target_selection_and_corpus_are_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = read_json_report(write_contrast_free_training_fixture(Path(tmp)))
            targets = select_loss_branch_targets(report)
            variants = normalize_loss_branch_variants(
                [{"variant_id": "x"}, {"variant_id": "x"}, {"variant_id": "y", "term_order": "missed-first"}]
            )
            corpus = build_required_term_pair_loss_branch_corpus(
                targets[0],
                {"term_order": "missed-first", "repeat": 2, "isolated_repeat": 1, "missed_weight": 2, "missed_anchor_repeat": 1},
            )
            content_lines = corpus.splitlines()[2:]

            self.assertEqual(targets[0]["focus_missed_term"], "loss")
            self.assertEqual(targets[0]["stable_missed_terms"], ["loss"])
            self.assertEqual([row["variant_id"] for row in variants], ["x", "y"])
            self.assertTrue(content_lines[0].startswith("loss:"))
            self.assertGreater(corpus.count("loss:loss"), corpus.count("fixed:fixed"))
            self.assertNotIn("not loss", corpus)
            self.assertNotIn("not fixed", corpus)
            self.assertGreaterEqual(len(default_pair_loss_branch_sweep_variants()), 3)

    def test_loss_branch_summary_marks_still_missed(self) -> None:
        targets = [
            {
                "pair_id": "01-fixed-loss",
                "term_names": ["fixed", "loss"],
                "focus_missed_term": "loss",
                "hit_term_names": ["fixed"],
            }
        ]
        variants = normalize_loss_branch_variants([{"variant_id": "short"}, {"variant_id": "long"}])
        probes = [
            {"pair_id": "01-fixed-loss", "variant_id": "short", "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "short", "term": "loss", "continuation_hit_count": 0},
            {"pair_id": "01-fixed-loss", "variant_id": "long", "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "long", "term": "loss", "continuation_hit_count": 0},
        ]

        rows = summarize_loss_branch_variant_probe_rows(targets, variants, probes)

        self.assertFalse(rows[0]["focus_missed_term_hit"])
        self.assertFalse(rows[1]["pair_full_hit"])
        self.assertEqual(rows[0]["missed_terms"], ["loss"])


def write_contrast_free_training_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_contrast_free_training.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "contrast_free_training_decision": "contrast_free_training_partial_only",
                "contrast_free_full_hit_observed": False,
                "variant_pair_partial_hit_count": 3,
                "variant_pair_full_hit_count": 0,
                "best_variant_id": "contrast-longer",
            },
            "pairs": [
                {
                    "pair_id": "01-fixed-loss",
                    "source_target_id": "01-fixed-loss-baseline-repeat",
                    "source_variant_id": "baseline-repeat",
                    "source_capacity_run_id": "01-fixed-loss-baseline-repeat-seed-496",
                    "term_names": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
                }
            ],
            "variant_summaries": [
                {
                    "pair_id": "01-fixed-loss",
                    "variant_id": "contrast-baseline",
                    "term_names": ["fixed", "loss"],
                    "hit_terms": ["fixed"],
                    "missed_terms": ["loss"],
                    "pair_partial_hit": True,
                    "pair_full_hit": False,
                },
                {
                    "pair_id": "01-fixed-loss",
                    "variant_id": "contrast-longer",
                    "term_names": ["fixed", "loss"],
                    "hit_terms": ["fixed"],
                    "missed_terms": ["loss"],
                    "pair_partial_hit": True,
                    "pair_full_hit": False,
                },
                {
                    "pair_id": "01-fixed-loss",
                    "variant_id": "contrast-denser",
                    "term_names": ["fixed", "loss"],
                    "hit_terms": ["fixed"],
                    "missed_terms": ["loss"],
                    "pair_partial_hit": True,
                    "pair_full_hit": False,
                },
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
