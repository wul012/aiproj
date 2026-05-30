from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_continuation_span_heldout import (
    build_model_capability_required_term_pair_continuation_span_heldout,
    build_heldout_prompt_cases,
    resolve_exit_code,
    select_heldout_seed_sources,
)
from minigpt.model_capability_required_term_pair_continuation_span_heldout_artifacts import (
    render_model_capability_required_term_pair_continuation_span_heldout_html,
    render_model_capability_required_term_pair_continuation_span_heldout_markdown,
    render_model_capability_required_term_pair_continuation_span_heldout_text,
    write_model_capability_required_term_pair_continuation_span_heldout_outputs,
)


class ModelCapabilityRequiredTermPairContinuationSpanHeldoutTests(unittest.TestCase):
    def test_heldout_reports_source_only_signal_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stability = stability_fixture(root)
            report = build_model_capability_required_term_pair_continuation_span_heldout(
                stability,
                out_dir=root / "heldout",
                source_path=root / "stability.json",
                generated_at="2026-05-30T13:00:00Z",
                generate_func=fake_generate_source_only,
            )
            outputs = write_model_capability_required_term_pair_continuation_span_heldout_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_continuation_span_heldout_text(report)
            markdown = render_model_capability_required_term_pair_continuation_span_heldout_markdown(report)
            html = render_model_capability_required_term_pair_continuation_span_heldout_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_continuation_span_source_only")
            self.assertGreater(report["summary"]["source_hit_case_count"], 0)
            self.assertEqual(report["summary"]["heldout_hit_case_count"], 0)
            self.assertIn("heldout_generalization_observed=False", text)
            self.assertIn("Continuation-Span Heldout", markdown)
            self.assertIn("MiniGPT continuation-span heldout", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_heldout_fails_without_stable_prefix_gain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stability = stability_fixture(root)
            stability["summary"]["stable_prefix_gain"] = False
            report = build_model_capability_required_term_pair_continuation_span_heldout(
                stability,
                out_dir=root / "heldout",
                generate_func=fake_generate_source_only,
            )

            self.assertEqual(report["status"], "fail")
            self.assertIn("source continuation-span stability does not have stable prefix gain", report["issues"])
            self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_select_seed_sources_and_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stability = stability_fixture(root)
            seeds = select_heldout_seed_sources(stability)
            cases = build_heldout_prompt_cases()

            self.assertEqual([row["seed"] for row in seeds], [510, 511])
            self.assertEqual([row["case_type"] for row in cases].count("heldout"), 2)


def stability_fixture(root: Path) -> dict[str, object]:
    checkpoint = root / "checkpoint.pt"
    tokenizer = root / "tokenizer.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    return {
        "status": "pass",
        "summary": {"stable_prefix_gain": True},
        "seed_reports": [
            seed_report(510, checkpoint, tokenizer),
            seed_report(511, checkpoint, tokenizer),
        ],
    }


def seed_report(seed: int, checkpoint: Path, tokenizer: Path) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_continuation_span_prefix_gain",
        "settings": {"generation_seed": seed},
        "summary": {
            "checkpoint_exists": True,
            "prefix_minimum_improved_count": 1,
            "candidate_pair_full_generation_hit": False,
        },
        "training": {
            "checkpoint_path": str(checkpoint),
            "tokenizer_path": str(tokenizer),
        },
    }


def fake_generate_source_only(request: dict[str, object]) -> dict[str, object]:
    prompt = str(request["prompt"])
    expected = "fixed" if prompt == "fixed:" else "loss" if prompt == "loss:" else "zzzz"
    return {"generated": prompt + expected, "continuation": expected}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
