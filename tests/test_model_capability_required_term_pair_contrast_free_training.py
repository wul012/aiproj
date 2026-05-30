from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_contrast_free_training import (
    build_model_capability_required_term_pair_contrast_free_training,
    build_required_term_pair_contrast_free_corpus,
    default_pair_contrast_free_training_variants,
    locate_model_capability_required_term_pair_contrast_free_training_source,
    normalize_contrast_free_variants,
    read_json_report,
    resolve_exit_code,
    select_contrast_free_pairs,
    summarize_contrast_free_pairs,
    summarize_contrast_free_variant_probe_rows,
    summarize_required_term_pair_contrast_free_training,
)
from minigpt.model_capability_required_term_pair_contrast_free_training_artifacts import (
    render_model_capability_required_term_pair_contrast_free_training_html,
    render_model_capability_required_term_pair_contrast_free_training_markdown,
    render_model_capability_required_term_pair_contrast_free_training_text,
    write_model_capability_required_term_pair_contrast_free_training_outputs,
)


class ModelCapabilityRequiredTermPairContrastFreeTrainingTests(unittest.TestCase):
    def test_contrast_free_training_reports_recovered_full_hit_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_prompt_separation_audit_fixture(root)
            variants = [
                {"variant_id": "contrast-baseline", "repeat": 2, "isolated_repeat": 1, "max_iters": 10, "n_embd": 16},
                {"variant_id": "contrast-longer", "repeat": 2, "isolated_repeat": 1, "max_iters": 20, "n_embd": 16},
            ]

            report = build_model_capability_required_term_pair_contrast_free_training(
                read_json_report(source),
                out_dir=root / "contrast",
                source_path=source,
                seed=500,
                variants=variants,
                generated_at="2026-05-30T00:00:00Z",
                train_func=fake_train,
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-contrast-longer-seed-500", "fixed"),
                        ("01-fixed-loss-contrast-longer-seed-500", "loss"),
                        ("01-fixed-loss-contrast-baseline-seed-500", "loss"),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_contrast_free_training_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_contrast_free_training_text(report)
            markdown = render_model_capability_required_term_pair_contrast_free_training_markdown(report)
            html = render_model_capability_required_term_pair_contrast_free_training_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_contrast_free_training_recovered")
            self.assertTrue(report["summary"]["contrast_free_full_hit_observed"])
            self.assertEqual(report["summary"]["variant_pair_full_hit_count"], 1)
            self.assertEqual(report["summary"]["best_variant_id"], "contrast-longer")
            self.assertIn("contrast_free_training_decision=contrast_free_training_full_hit_recovered", text)
            self.assertIn("Contrast-Free Training", markdown)
            self.assertIn("Variant Results", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_contrast_free_training_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contrast_free_training_reports_partial_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_prompt_separation_audit_fixture(root))
            variants = [{"variant_id": "contrast-baseline", "repeat": 1, "isolated_repeat": 1, "max_iters": 8, "n_embd": 16}]

            partial = build_model_capability_required_term_pair_contrast_free_training(
                source_report,
                out_dir=root / "partial",
                variants=variants,
                train_func=fake_train,
                generate_func=fake_generate({("01-fixed-loss-contrast-baseline-seed-500", "loss")}),
            )
            bad_status = build_model_capability_required_term_pair_contrast_free_training(
                {**source_report, "status": "fail"},
                out_dir=root / "bad-status",
                variants=variants,
                train_func=fake_train,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(partial["decision"], "required_term_pair_contrast_free_training_partial")
            self.assertEqual(partial["summary"]["variant_pair_partial_hit_count"], 1)
            self.assertFalse(partial["summary"]["contrast_free_full_hit_observed"])
            self.assertEqual(bad_status["status"], "fail")
            self.assertIn("source prompt separation audit report is not pass", bad_status["issues"])

    def test_contrast_free_pair_selection_and_corpus_rows_are_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = read_json_report(write_prompt_separation_audit_fixture(Path(tmp)))
            pairs = select_contrast_free_pairs(report)
            corpus = build_required_term_pair_contrast_free_corpus(pairs[0], repeat=2, isolated_repeat=1)
            variants = normalize_contrast_free_variants([{"variant_id": "x"}, {"variant_id": "x"}, {"variant_id": "y"}])

            self.assertEqual([row["pair_id"] for row in pairs], ["01-fixed-loss"])
            self.assertIn("fixed:fixed", corpus)
            self.assertIn("loss:loss", corpus)
            self.assertNotIn("not loss", corpus)
            self.assertNotIn("not fixed", corpus)
            self.assertEqual([row["variant_id"] for row in variants], ["x", "y"])
            self.assertGreaterEqual(len(default_pair_contrast_free_training_variants()), 3)

    def test_contrast_free_summary_helpers_choose_full_hit_variant(self) -> None:
        pairs = [{"pair_id": "01-fixed-loss", "term_names": ["fixed", "loss"]}]
        variants = normalize_contrast_free_variants([{"variant_id": "short"}, {"variant_id": "long"}])
        probes = [
            {"pair_id": "01-fixed-loss", "variant_id": "short", "term": "fixed", "continuation_hit_count": 0},
            {"pair_id": "01-fixed-loss", "variant_id": "short", "term": "loss", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "long", "term": "fixed", "continuation_hit_count": 1},
            {"pair_id": "01-fixed-loss", "variant_id": "long", "term": "loss", "continuation_hit_count": 1},
        ]

        variant_summaries = summarize_contrast_free_variant_probe_rows(pairs, variants, probes)
        pair_summaries = summarize_contrast_free_pairs(pairs, variants, variant_summaries)
        summary = summarize_required_term_pair_contrast_free_training(
            pairs,
            variants,
            training_rows=[{"training_status": "pass", "checkpoint_exists": True}],
            probe_rows=probes,
            variant_summaries=variant_summaries,
            pair_summaries=pair_summaries,
            source_summary={"prompt_separation_audit_decision": "prompt_separation_corpus_revision_needed"},
        )

        self.assertTrue(variant_summaries[1]["pair_full_hit"])
        self.assertEqual(pair_summaries[0]["full_hit_variants"], ["long"])
        self.assertEqual(summary["best_variant_id"], "long")
        self.assertEqual(summary["contrast_free_training_decision"], "contrast_free_training_full_hit_recovered")


def write_prompt_separation_audit_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_prompt_separation_audit.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "prompt_separation_audit_decision": "prompt_separation_corpus_revision_needed",
                "corpus_revision_recommended": True,
                "direct_prompt_other_term_leak_count": 12,
                "negative_contrast_leak_count": 12,
            },
            "targets": [
                {
                    "target_id": "01-fixed-loss-baseline-repeat",
                    "pair_id": "01-fixed-loss",
                    "variant_id": "baseline-repeat",
                    "capacity_run_id": "01-fixed-loss-baseline-repeat-seed-496",
                    "term_names": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
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
