from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_forced_choice_diagnostic import (
    build_model_capability_required_term_pair_forced_choice_diagnostic,
    locate_model_capability_required_term_pair_forced_choice_diagnostic_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_forced_choice_diagnostic_artifacts import (
    render_model_capability_required_term_pair_forced_choice_diagnostic_html,
    render_model_capability_required_term_pair_forced_choice_diagnostic_markdown,
    render_model_capability_required_term_pair_forced_choice_diagnostic_text,
    write_model_capability_required_term_pair_forced_choice_diagnostic_outputs,
)
from minigpt.model_capability_required_term_pair_forced_choice_diagnostic_components import (
    select_forced_choice_runs,
    select_forced_choice_targets,
    summarize_forced_choice_prompt_rows,
    summarize_forced_choice_variants,
)


class ModelCapabilityRequiredTermPairForcedChoiceDiagnosticTests(unittest.TestCase):
    def test_forced_choice_reports_internal_full_match_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_branch_retention_fixture(root)
            report = build_model_capability_required_term_pair_forced_choice_diagnostic(
                read_json_report(source),
                out_dir=root / "diag",
                source_path=source,
                generated_at="2026-05-30T04:00:00Z",
                score_func=fake_score({"fixed": "fixed", "loss": "loss"}),
            )
            outputs = write_model_capability_required_term_pair_forced_choice_diagnostic_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_forced_choice_diagnostic_text(report)
            markdown = render_model_capability_required_term_pair_forced_choice_diagnostic_markdown(report)
            html = render_model_capability_required_term_pair_forced_choice_diagnostic_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_forced_choice_internal_match")
            self.assertEqual(report["summary"]["forced_choice_full_match_variant_count"], 1)
            self.assertEqual(report["summary"]["expected_best_count"], 2)
            self.assertIn("forced_choice_diagnostic_decision=forced_choice_full_match_observed", text)
            self.assertIn("Forced-Choice Diagnostic", markdown)
            self.assertIn("Prompt Choices", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_forced_choice_diagnostic_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_forced_choice_reports_collapse_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_branch_retention_fixture(root))
            collapsed = build_model_capability_required_term_pair_forced_choice_diagnostic(
                source_report,
                out_dir=root / "collapse",
                score_func=fake_score({"fixed": "fixed", "loss": "fixed"}),
            )
            bad = build_model_capability_required_term_pair_forced_choice_diagnostic(
                {**source_report, "training_rows": []},
                out_dir=root / "bad",
                score_func=fake_score({}),
            )

            self.assertEqual(collapsed["decision"], "required_term_pair_forced_choice_partial")
            self.assertEqual(collapsed["summary"]["expected_best_count"], 1)
            self.assertEqual(collapsed["summary"]["collapse_candidate_counts"], {"fixed": 1})
            self.assertEqual(bad["status"], "fail")
            self.assertIn("source branch-retention sweep has no checkpoint runs to score", bad["issues"])

    def test_forced_choice_selection_and_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = read_json_report(write_branch_retention_fixture(Path(tmp)))
            targets = select_forced_choice_targets(report)
            runs = select_forced_choice_runs(report)
            score_rows = [
                score_row("demo-run", "fixed", "fixed", 0.1, True),
                score_row("demo-run", "fixed", "loss", 0.5, False),
                score_row("demo-run", "loss", "fixed", 0.2, False),
                score_row("demo-run", "loss", "loss", 0.6, True),
            ]
            prompt_summaries = summarize_forced_choice_prompt_rows(score_rows)
            variant_summaries = summarize_forced_choice_variants(runs, prompt_summaries)

            self.assertEqual(targets[0]["term_names"], ["fixed", "loss"])
            self.assertEqual(runs[0]["variant_id"], "demo")
            self.assertEqual(prompt_summaries[0]["best_candidate_term"], "fixed")
            self.assertEqual(variant_summaries[0]["expected_best_count"], 1)
            self.assertEqual(variant_summaries[0]["collapse_candidate"], "fixed")


def write_branch_retention_fixture(root: Path) -> Path:
    source = root / "model_capability_required_term_pair_branch_retention_sweep.json"
    run_dir = root / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "branch_retention_sweep_decision": "branch_retention_sweep_tradeoff_remains",
                "pair_full_hit_variant_count": 0,
                "best_variant_id": "demo",
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
                    "source_hit_terms": ["fixed"],
                }
            ],
            "training_rows": [
                {
                    "branch_retention_run_id": "demo-run",
                    "pair_id": "01-fixed-loss",
                    "variant_id": "demo",
                    "variant_label": "demo",
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                    "checkpoint_exists": True,
                }
            ],
        },
    )
    return source


def fake_score(best_by_prompt: dict[str, str]):
    def score(context: dict[str, object]) -> dict[str, object]:
        prompt_term = str(context["prompt_term"])
        candidate = str(context["candidate_term"])
        best = best_by_prompt.get(prompt_term)
        avg_nll = 0.1 if candidate == best else 0.9
        return {
            "status": "pass",
            "token_count": len(candidate),
            "candidate_token_ids": list(range(len(candidate))),
            "total_nll": avg_nll * max(1, len(candidate)),
            "avg_nll": avg_nll,
            "first_token_rank": 1 if candidate == best else 2,
            "first_token_logprob": -avg_nll,
        }

    return score


def score_row(run_id: str, prompt_term: str, candidate: str, avg_nll: float, expected: bool) -> dict[str, object]:
    return {
        "run_id": run_id,
        "pair_id": "01-fixed-loss",
        "variant_id": "demo",
        "variant_label": "demo",
        "prompt_term": prompt_term,
        "prompt": f"{prompt_term}:",
        "candidate_term": candidate,
        "is_expected_candidate": expected,
        "avg_nll": avg_nll,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
