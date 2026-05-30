from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_generation_gap import (
    build_model_capability_required_term_pair_generation_gap,
    locate_model_capability_required_term_pair_generation_gap_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_gap_artifacts import (
    render_model_capability_required_term_pair_generation_gap_html,
    render_model_capability_required_term_pair_generation_gap_markdown,
    render_model_capability_required_term_pair_generation_gap_text,
    write_model_capability_required_term_pair_generation_gap_outputs,
)
from minigpt.model_capability_required_term_pair_generation_gap_components import (
    build_generation_gap_rows,
    classify_generation_gap,
    summarize_generation_gap_variants,
)


class ModelCapabilityRequiredTermPairGenerationGapTests(unittest.TestCase):
    def test_generation_gap_reports_internal_signal_not_expressed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forced_path, branch_path = write_generation_gap_fixtures(root)
            report = build_model_capability_required_term_pair_generation_gap(
                read_json_report(forced_path),
                out_dir=root / "gap",
                source_path=forced_path,
                branch_retention_report=read_json_report(branch_path),
                branch_retention_path=branch_path,
                generated_at="2026-05-30T05:00:00Z",
            )
            outputs = write_model_capability_required_term_pair_generation_gap_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_generation_gap_text(report)
            markdown = render_model_capability_required_term_pair_generation_gap_markdown(report)
            html = render_model_capability_required_term_pair_generation_gap_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_generation_gap_observed")
            self.assertEqual(report["summary"]["generation_gap_decision"], "generation_gap_internal_signal_not_expressed")
            self.assertEqual(report["summary"]["internal_only_prompt_count"], 1)
            self.assertEqual(report["summary"]["forced_generation_gap_variant_count"], 1)
            self.assertIn("generation_gap_decision=generation_gap_internal_signal_not_expressed", text)
            self.assertIn("Generation Gap", markdown)
            self.assertIn("Gap Rows", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_generation_gap_source(forced_path.parent), forced_path)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_generation_gap_alignment_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forced_path, branch_path = write_generation_gap_fixtures(root, generation_loss_hit=True)
            aligned = build_model_capability_required_term_pair_generation_gap(
                read_json_report(forced_path),
                out_dir=root / "aligned",
                branch_retention_report=read_json_report(branch_path),
            )
            bad = build_model_capability_required_term_pair_generation_gap(
                {**read_json_report(forced_path), "source_required_term_pair_branch_retention_sweep": ""},
                out_dir=root / "bad",
            )

            self.assertEqual(aligned["decision"], "required_term_pair_generation_aligned")
            self.assertEqual(aligned["summary"]["generation_full_match_variant_count"], 1)
            self.assertEqual(bad["status"], "fail")
            self.assertIn("source forced-choice diagnostic does not point to a branch-retention sweep", bad["issues"])
            self.assertEqual(resolve_exit_code(bad, require_pass=True), 1)

    def test_generation_gap_rows_and_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            forced_path, branch_path = write_generation_gap_fixtures(Path(tmp))
            forced = read_json_report(forced_path)
            branch = read_json_report(branch_path)
            rows = build_generation_gap_rows(forced, branch)
            variants = summarize_generation_gap_variants(forced, branch, rows)

            self.assertEqual(classify_generation_gap(True, True), "aligned_hit")
            self.assertEqual(classify_generation_gap(True, False), "internal_only")
            self.assertEqual(classify_generation_gap(False, True), "generation_only")
            self.assertEqual(classify_generation_gap(False, False), "aligned_miss")
            self.assertEqual(rows[1]["gap_class"], "internal_only")
            self.assertTrue(variants[0]["forced_generation_gap"])


def write_generation_gap_fixtures(root: Path, *, generation_loss_hit: bool = False) -> tuple[Path, Path]:
    branch_path = root / "model_capability_required_term_pair_branch_retention_sweep.json"
    forced_path = root / "model_capability_required_term_pair_forced_choice_diagnostic.json"
    branch_hit_count = 2 if generation_loss_hit else 1
    write_json(
        branch_path,
        {
            "status": "pass",
            "summary": {
                "branch_retention_sweep_decision": "branch_retention_sweep_tradeoff_remains",
                "pair_full_hit_variant_count": 1 if generation_loss_hit else 0,
            },
            "probe_rows": [
                probe_row("fixed", True),
                probe_row("loss", generation_loss_hit),
            ],
            "variant_summaries": [
                {
                    "variant_id": "symmetric-anchor",
                    "variant_label": "symmetric anchor",
                    "hit_count": branch_hit_count,
                    "pair_full_hit": generation_loss_hit,
                    "hit_terms": ["fixed", "loss"] if generation_loss_hit else ["fixed"],
                    "missed_terms": [] if generation_loss_hit else ["loss"],
                }
            ],
        },
    )
    write_json(
        forced_path,
        {
            "status": "pass",
            "source_required_term_pair_branch_retention_sweep": str(branch_path),
            "summary": {
                "forced_choice_diagnostic_decision": "forced_choice_full_match_observed",
                "forced_choice_full_match_variant_count": 1,
            },
            "prompt_summaries": [
                prompt_row("fixed", True),
                prompt_row("loss", True),
            ],
            "variant_summaries": [
                {
                    "run_id": "demo-run",
                    "variant_id": "symmetric-anchor",
                    "variant_label": "symmetric anchor",
                    "expected_best_count": 2,
                    "forced_choice_full_match": True,
                }
            ],
        },
    )
    return forced_path, branch_path


def prompt_row(term: str, expected_best: bool) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "pair_id": "01-fixed-loss",
        "variant_id": "symmetric-anchor",
        "variant_label": "symmetric anchor",
        "prompt_term": term,
        "expected_term": term,
        "best_candidate_term": term if expected_best else "fixed",
        "expected_is_best": expected_best,
        "expected_rank": 1 if expected_best else 2,
        "expected_avg_nll": 0.2,
        "expected_margin_vs_best": 0.0 if expected_best else 0.5,
    }


def probe_row(term: str, hit: bool) -> dict[str, object]:
    return {
        "branch_retention_run_id": "demo-run",
        "variant_id": "symmetric-anchor",
        "variant_label": "symmetric anchor",
        "term": term,
        "continuation_hit_count": 1 if hit else 0,
        "generated_hit_count": 1 if hit else 0,
        "continuation_preview": f" {term}" if hit else " fixed",
        "generated_preview": f"{term}: {term}" if hit else f"{term}: fixed",
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
