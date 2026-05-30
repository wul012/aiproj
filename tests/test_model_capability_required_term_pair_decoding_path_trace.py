from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_decoding_path_trace import (
    build_model_capability_required_term_pair_decoding_path_trace,
    locate_model_capability_required_term_pair_decoding_path_trace_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_decoding_path_trace_artifacts import (
    render_model_capability_required_term_pair_decoding_path_trace_html,
    render_model_capability_required_term_pair_decoding_path_trace_markdown,
    render_model_capability_required_term_pair_decoding_path_trace_text,
    write_model_capability_required_term_pair_decoding_path_trace_outputs,
)
from minigpt.model_capability_required_term_pair_decoding_path_trace_components import (
    select_decoding_path_trace_targets,
    summarize_decoding_path_probe_rows,
)


class ModelCapabilityRequiredTermPairDecodingPathTraceTests(unittest.TestCase):
    def test_path_trace_reports_late_expression_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_decoding_gap_probe_fixture(root)
            report = build_model_capability_required_term_pair_decoding_path_trace(
                read_json_report(source),
                out_dir=root / "trace",
                source_path=source,
                generated_at="2026-05-30T07:00:00Z",
                trace_func=fake_trace("f", rank=3, first_match=False, seen_step=4, continuation="dddd fixed"),
            )
            outputs = write_model_capability_required_term_pair_decoding_path_trace_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_decoding_path_trace_text(report)
            markdown = render_model_capability_required_term_pair_decoding_path_trace_markdown(report)
            html = render_model_capability_required_term_pair_decoding_path_trace_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_decoding_path_late_expression")
            self.assertEqual(report["summary"]["late_hit_after_first_miss_count"], 1)
            self.assertIn("decoding_path_trace_decision=decoding_path_trace_late_expression_after_first_miss", text)
            self.assertIn("Decoding Path Trace", markdown)
            self.assertIn("Probe Summaries", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_decoding_path_trace_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_path_trace_first_token_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_decoding_gap_probe_fixture(root)
            first = build_model_capability_required_term_pair_decoding_path_trace(
                read_json_report(source),
                out_dir=root / "first",
                trace_func=fake_trace("f", rank=1, first_match=True, seen_step=0, continuation="fixed"),
            )
            bad = build_model_capability_required_term_pair_decoding_path_trace(
                {**read_json_report(source), "probe_rows": []},
                out_dir=root / "bad",
                trace_func=fake_trace("f"),
            )

            self.assertEqual(first["decision"], "required_term_pair_decoding_path_first_token_expression")
            self.assertEqual(first["summary"]["first_sample_match_count"], 1)
            self.assertEqual(bad["status"], "fail")
            self.assertIn("source decoding-gap probe has no traceable target", bad["issues"])

    def test_path_trace_selection_and_probe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = write_decoding_gap_probe_fixture(Path(tmp))
            targets = select_decoding_path_trace_targets(read_json_report(source))
            summaries = summarize_decoding_path_probe_rows(
                [
                    {
                        "variant_id": "symmetric-anchor",
                        "profile_id": "demo",
                        "prompt_term": "fixed",
                        "expected_term": "fixed",
                        "continuation_hit": True,
                        "first_sample_matches_expected_first_token": False,
                    }
                ]
            )

            self.assertEqual(targets[0]["variant_id"], "symmetric-anchor")
            self.assertTrue(summaries[0]["late_hit_after_first_miss"])


def write_decoding_gap_probe_fixture(root: Path) -> Path:
    path = root / "model_capability_required_term_pair_decoding_gap_probe.json"
    write_json(
        path,
        {
            "status": "pass",
            "summary": {"best_variant_id": "symmetric-anchor"},
            "probe_rows": [
                {
                    "variant_id": "symmetric-anchor",
                    "profile_id": "demo",
                    "prompt_term": "fixed",
                    "expected_term": "fixed",
                    "checkpoint_path": str(root / "checkpoint.pt"),
                    "tokenizer_path": str(root / "tokenizer.json"),
                    "max_new_tokens": 12,
                    "temperature": 0.2,
                    "top_k": 1,
                    "seed": 506,
                    "continuation_hit": True,
                }
            ],
        },
    )
    return path


def fake_trace(sample: str, *, rank: int = 2, first_match: bool = False, seen_step: int | None = None, continuation: str = ""):
    def trace(_: dict[str, object]) -> dict[str, object]:
        return {
            "continuation": continuation,
            "continuation_preview": continuation,
            "first_expected_token_id": 1,
            "first_expected_token_text": "f",
            "first_expected_token_rank": rank,
            "first_expected_token_logprob": -0.2,
            "first_sample_token_id": 1 if first_match else 2,
            "first_sample_text": sample,
            "first_sample_matches_expected_first_token": first_match,
            "expected_first_token_seen_step": seen_step,
            "steps": [{"step": 0, "sampled_token_id": 2, "sampled_text": sample}],
        }

    return trace


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
