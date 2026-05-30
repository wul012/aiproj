from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_first_token_repair import (
    build_model_capability_required_term_pair_first_token_repair,
    locate_model_capability_required_term_pair_first_token_repair_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_first_token_repair_artifacts import (
    render_model_capability_required_term_pair_first_token_repair_html,
    render_model_capability_required_term_pair_first_token_repair_markdown,
    render_model_capability_required_term_pair_first_token_repair_text,
    write_model_capability_required_term_pair_first_token_repair_outputs,
)
from minigpt.model_capability_required_term_pair_first_token_repair_components import (
    select_first_token_repair_targets,
    summarize_first_token_repair_profiles,
)


class ModelCapabilityRequiredTermPairFirstTokenRepairTests(unittest.TestCase):
    def test_first_token_repair_reports_full_expression_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_path_trace_fixture(root)
            report = build_model_capability_required_term_pair_first_token_repair(
                read_json_report(source),
                out_dir=root / "repair",
                source_path=source,
                generated_at="2026-05-30T08:00:00Z",
                repair_func=fake_repair({"fixed": "fixed", "loss": "loss"}),
            )
            outputs = write_model_capability_required_term_pair_first_token_repair_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_first_token_repair_text(report)
            markdown = render_model_capability_required_term_pair_first_token_repair_markdown(report)
            html = render_model_capability_required_term_pair_first_token_repair_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_first_token_repair_full_expression")
            self.assertEqual(report["summary"]["repaired_profile_full_hit_count"], 1)
            self.assertIn("first_token_repair_decision=first_token_repair_full_expression_recovered", text)
            self.assertIn("First-Token Repair", markdown)
            self.assertIn("Repair Rows", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_first_token_repair_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_first_token_repair_partial_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_path_trace_fixture(root)
            partial = build_model_capability_required_term_pair_first_token_repair(
                read_json_report(source),
                out_dir=root / "partial",
                repair_func=fake_repair({"fixed": "fixed", "loss": "x"}),
            )
            bad = build_model_capability_required_term_pair_first_token_repair(
                {**read_json_report(source), "probe_rows": []},
                out_dir=root / "bad",
                repair_func=fake_repair({}),
            )

            self.assertEqual(partial["decision"], "required_term_pair_first_token_repair_improved_partial")
            self.assertEqual(partial["summary"]["improved_prompt_count"], 1)
            self.assertEqual(bad["status"], "fail")
            self.assertIn("source decoding-path trace has no first-token repair target", bad["issues"])

    def test_first_token_repair_selection_and_profile_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = write_path_trace_fixture(Path(tmp))
            targets = select_first_token_repair_targets(read_json_report(source))
            summaries = summarize_first_token_repair_profiles(
                targets,
                [
                    repair_row("fixed", True),
                    repair_row("loss", False),
                ],
            )

            self.assertEqual(targets[0]["variant_id"], "symmetric-anchor")
            self.assertFalse(summaries[0]["repaired_profile_full_hit"])
            self.assertEqual(summaries[0]["missed_terms"], ["loss"])


def write_path_trace_fixture(root: Path) -> Path:
    path = root / "model_capability_required_term_pair_decoding_path_trace.json"
    write_json(
        path,
        {
            "status": "pass",
            "probe_rows": [
                trace_row("fixed"),
                trace_row("loss"),
            ],
        },
    )
    return path


def fake_repair(by_prompt: dict[str, str]):
    def repair(request: dict[str, object]) -> dict[str, object]:
        term = str(request["prompt_term"])
        continuation = by_prompt.get(term, "")
        return {
            "forced_first_token_id": request.get("first_expected_token_id"),
            "forced_first_token_text": term[:1],
            "repaired_generated": f"{term}:{continuation}",
            "repaired_continuation": continuation,
        }

    return repair


def trace_row(term: str) -> dict[str, object]:
    return {
        "variant_id": "symmetric-anchor",
        "profile_id": "demo",
        "prompt_term": term,
        "expected_term": term,
        "checkpoint_path": "checkpoint.pt",
        "tokenizer_path": "tokenizer.json",
        "max_new_tokens": 12,
        "temperature": 0.2,
        "top_k": 1,
        "seed": 507,
        "continuation_hit": False,
        "first_expected_token_id": 1,
        "first_sample_matches_expected_first_token": False,
    }


def repair_row(term: str, hit: bool) -> dict[str, object]:
    return {
        "variant_id": "symmetric-anchor",
        "profile_id": "demo",
        "prompt_term": term,
        "expected_term": term,
        "source_continuation_hit": False,
        "repaired_continuation_hit": hit,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
