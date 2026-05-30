from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_diagnostic_rollup import (
    build_model_capability_required_term_pair_diagnostic_rollup,
    collect_required_term_pair_diagnostic_reports,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_diagnostic_rollup_artifacts import (
    render_model_capability_required_term_pair_diagnostic_rollup_html,
    render_model_capability_required_term_pair_diagnostic_rollup_markdown,
    render_model_capability_required_term_pair_diagnostic_rollup_text,
    write_model_capability_required_term_pair_diagnostic_rollup_outputs,
)


class ModelCapabilityRequiredTermPairDiagnosticRollupTests(unittest.TestCase):
    def test_diagnostic_rollup_reports_next_span_objective_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports, paths = write_rollup_fixtures(root)
            report = build_model_capability_required_term_pair_diagnostic_rollup(
                reports,
                out_dir=root / "rollup",
                source_paths=paths,
                generated_at="2026-05-30T10:00:00Z",
            )
            outputs = write_model_capability_required_term_pair_diagnostic_rollup_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_diagnostic_rollup_text(report)
            markdown = render_model_capability_required_term_pair_diagnostic_rollup_markdown(report)
            html = render_model_capability_required_term_pair_diagnostic_rollup_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_next_span_objective")
            self.assertEqual(report["summary"]["span_completion_gap_probe_count"], 3)
            self.assertEqual(report["next_experiment_plan"]["plan_id"], "continuation_span_objective_fixed_loss")
            self.assertIn("fixed minimum_hit_prefix_token_count drops below 4", report["next_experiment_plan"]["minimum_success_criteria"])
            self.assertIn("rollup_decision=rollup_continue_with_span_objective", text)
            self.assertIn("next_plan_id=continuation_span_objective_fixed_loss", text)
            self.assertIn("Diagnostic Rollup", markdown)
            self.assertIn("Next Experiment Plan", markdown)
            self.assertIn("one_token_hits=3; span_gaps=3", markdown)
            self.assertIn("Stages", html)
            self.assertIn("continuation_span_objective_fixed_loss", html)
            self.assertIn("source_path", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("key_metric", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_rollup_collects_reports_and_fails_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reports, _paths = write_rollup_fixtures(root)
            reports, paths = collect_required_term_pair_diagnostic_reports(root)
            bad = build_model_capability_required_term_pair_diagnostic_rollup(
                {**reports, "prefix_completion": {}},
                out_dir=root / "bad",
                source_paths=paths,
            )

            self.assertTrue(paths["forced_choice"].endswith("model_capability_required_term_pair_forced_choice_diagnostic.json"))
            self.assertEqual(bad["status"], "fail")
            self.assertIn("missing prefix_completion report", bad["issues"])
            self.assertEqual(resolve_exit_code(bad, require_pass=True), 1)


def write_rollup_fixtures(root: Path) -> tuple[dict[str, dict[str, object]], dict[str, str]]:
    payloads: dict[str, dict[str, object]] = {
        "forced_choice": report("required_term_pair_forced_choice_internal_match", {"forced_choice_full_match_variant_count": 1}),
        "generation_gap": report("required_term_pair_generation_gap_observed", {"forced_generation_gap_variant_count": 1}),
        "decoding_gap": report("required_term_pair_decoding_gap_partial_only", {"profile_full_hit_count": 0, "continuation_hit_count": 2}),
        "path_trace": report("required_term_pair_decoding_path_late_expression", {"first_sample_match_count": 0, "late_hit_after_first_miss_count": 2}),
        "first_token_repair": report("required_term_pair_first_token_repair_improved_partial", {"improved_prompt_count": 2, "repaired_profile_full_hit_count": 0}),
        "prefix_completion": report("required_term_pair_prefix_completion_long_prefix", {"one_token_prefix_hit_probe_count": 3, "full_prefix_hit_probe_count": 6, "span_completion_gap_probe_count": 3}),
    }
    filenames = {
        "forced_choice": "model_capability_required_term_pair_forced_choice_diagnostic.json",
        "generation_gap": "model_capability_required_term_pair_generation_gap.json",
        "decoding_gap": "model_capability_required_term_pair_decoding_gap_probe.json",
        "path_trace": "model_capability_required_term_pair_decoding_path_trace.json",
        "first_token_repair": "model_capability_required_term_pair_first_token_repair.json",
        "prefix_completion": "model_capability_required_term_pair_prefix_completion_sweep.json",
    }
    paths: dict[str, str] = {}
    for index, (key, filename) in enumerate(filenames.items(), start=503):
        path = root / str(index) / "解释" / key / filename
        write_json(path, payloads[key])
        paths[key] = str(path)
    return payloads, paths


def report(decision: str, summary: dict[str, object]) -> dict[str, object]:
    return {"status": "pass", "decision": decision, "summary": summary}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
