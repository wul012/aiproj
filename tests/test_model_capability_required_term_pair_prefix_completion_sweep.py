from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_prefix_completion_sweep import (
    build_model_capability_required_term_pair_prefix_completion_sweep,
    locate_model_capability_required_term_pair_prefix_completion_sweep_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_prefix_completion_sweep_artifacts import (
    render_model_capability_required_term_pair_prefix_completion_sweep_html,
    render_model_capability_required_term_pair_prefix_completion_sweep_markdown,
    render_model_capability_required_term_pair_prefix_completion_sweep_text,
    write_model_capability_required_term_pair_prefix_completion_sweep_outputs,
)
from minigpt.model_capability_required_term_pair_prefix_completion_sweep_components import (
    select_prefix_completion_targets,
    summarize_prefix_completion_probe_rows,
)


class ModelCapabilityRequiredTermPairPrefixCompletionSweepTests(unittest.TestCase):
    def test_prefix_completion_reports_long_prefix_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_path_trace_fixture(root)
            report = build_model_capability_required_term_pair_prefix_completion_sweep(
                read_json_report(source),
                out_dir=root / "sweep",
                source_path=source,
                generated_at="2026-05-30T09:00:00Z",
                sweep_func=fake_sweep(one_token_hit=False, full_hit=True),
            )
            outputs = write_model_capability_required_term_pair_prefix_completion_sweep_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_prefix_completion_sweep_text(report)
            markdown = render_model_capability_required_term_pair_prefix_completion_sweep_markdown(report)
            html = render_model_capability_required_term_pair_prefix_completion_sweep_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_prefix_completion_long_prefix")
            self.assertEqual(report["summary"]["full_prefix_hit_probe_count"], 1)
            self.assertIn("prefix_completion_sweep_decision=prefix_completion_requires_longer_prefix", text)
            self.assertIn("Prefix Completion Sweep", markdown)
            self.assertIn("Probe Summaries", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_prefix_completion_sweep_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_prefix_completion_one_token_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_path_trace_fixture(root)
            one = build_model_capability_required_term_pair_prefix_completion_sweep(
                read_json_report(source),
                out_dir=root / "one",
                sweep_func=fake_sweep(one_token_hit=True, full_hit=True),
            )
            bad = build_model_capability_required_term_pair_prefix_completion_sweep(
                {**read_json_report(source), "probe_rows": []},
                out_dir=root / "bad",
                sweep_func=fake_sweep(),
            )

            self.assertEqual(one["decision"], "required_term_pair_prefix_completion_one_token")
            self.assertEqual(one["summary"]["one_token_prefix_hit_probe_count"], 1)
            self.assertEqual(bad["status"], "fail")
            self.assertIn("source decoding-path trace has no prefix completion target", bad["issues"])

    def test_prefix_completion_selection_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = write_path_trace_fixture(Path(tmp))
            targets = select_prefix_completion_targets(read_json_report(source))
            summaries = summarize_prefix_completion_probe_rows(
                [
                    prefix_row(1, False),
                    prefix_row(2, True),
                ]
            )

            self.assertEqual(targets[0]["variant_id"], "symmetric-anchor")
            self.assertEqual(summaries[0]["minimum_hit_prefix_token_count"], 2)


def write_path_trace_fixture(root: Path) -> Path:
    path = root / "model_capability_required_term_pair_decoding_path_trace.json"
    write_json(
        path,
        {
            "status": "pass",
            "probe_rows": [
                {
                    "variant_id": "symmetric-anchor",
                    "profile_id": "demo",
                    "prompt_term": "fixed",
                    "expected_term": "fixed",
                    "checkpoint_path": "checkpoint.pt",
                    "tokenizer_path": "tokenizer.json",
                    "max_new_tokens": 12,
                    "temperature": 0.2,
                    "top_k": 1,
                    "seed": 508,
                }
            ],
        },
    )
    return path


def fake_sweep(*, one_token_hit: bool = False, full_hit: bool = False):
    def sweep(request: dict[str, object]) -> list[dict[str, object]]:
        return [
            {**request, "expected_token_count": 2, "forced_prefix_token_count": 1, "prefix_completion_hit": one_token_hit},
            {**request, "expected_token_count": 2, "forced_prefix_token_count": 2, "prefix_completion_hit": full_hit},
        ]

    return sweep


def prefix_row(prefix_len: int, hit: bool) -> dict[str, object]:
    return {
        "variant_id": "symmetric-anchor",
        "profile_id": "demo",
        "prompt_term": "fixed",
        "expected_term": "fixed",
        "expected_token_count": 2,
        "forced_prefix_token_count": prefix_len,
        "prefix_completion_hit": hit,
        "completion_preview": "fixed" if hit else "fi",
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
