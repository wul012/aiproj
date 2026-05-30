from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_decoding_gap_probe import (
    build_model_capability_required_term_pair_decoding_gap_probe,
    locate_model_capability_required_term_pair_decoding_gap_probe_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_decoding_gap_probe_artifacts import (
    render_model_capability_required_term_pair_decoding_gap_probe_html,
    render_model_capability_required_term_pair_decoding_gap_probe_markdown,
    render_model_capability_required_term_pair_decoding_gap_probe_text,
    write_model_capability_required_term_pair_decoding_gap_probe_outputs,
)
from minigpt.model_capability_required_term_pair_decoding_gap_probe_components import (
    default_decoding_gap_profiles,
    select_decoding_gap_targets,
    summarize_decoding_gap_profiles,
)


class ModelCapabilityRequiredTermPairDecodingGapProbeTests(unittest.TestCase):
    def test_decoding_gap_probe_finds_generation_expression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gap_path, forced_path = write_decoding_gap_fixtures(root)
            profiles = [{"profile_id": "demo", "max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "seed": 505}]
            report = build_model_capability_required_term_pair_decoding_gap_probe(
                read_json_report(gap_path),
                out_dir=root / "probe",
                source_path=gap_path,
                forced_choice_report=read_json_report(forced_path),
                forced_choice_path=forced_path,
                profiles=profiles,
                generated_at="2026-05-30T06:00:00Z",
                generate_func=fake_generate({"fixed": " fixed", "loss": " loss"}),
            )
            outputs = write_model_capability_required_term_pair_decoding_gap_probe_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_decoding_gap_probe_text(report)
            markdown = render_model_capability_required_term_pair_decoding_gap_probe_markdown(report)
            html = render_model_capability_required_term_pair_decoding_gap_probe_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_decoding_gap_expression_found")
            self.assertEqual(report["summary"]["profile_full_hit_count"], 1)
            self.assertIn("decoding_gap_probe_decision=decoding_gap_probe_generation_expression_found", text)
            self.assertIn("Decoding Gap Probe", markdown)
            self.assertIn("Probe Rows", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_decoding_gap_probe_source(gap_path.parent), gap_path)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decoding_gap_probe_reports_partial_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gap_path, forced_path = write_decoding_gap_fixtures(root)
            partial = build_model_capability_required_term_pair_decoding_gap_probe(
                read_json_report(gap_path),
                out_dir=root / "partial",
                forced_choice_report=read_json_report(forced_path),
                profiles=[{"profile_id": "demo", "max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "seed": 505}],
                generate_func=fake_generate({"fixed": " fixed", "loss": " fixed"}),
            )
            bad = build_model_capability_required_term_pair_decoding_gap_probe(
                {**read_json_report(gap_path), "source_required_term_pair_forced_choice_diagnostic": ""},
                out_dir=root / "bad",
                generate_func=fake_generate({}),
            )

            self.assertEqual(partial["decision"], "required_term_pair_decoding_gap_partial_only")
            self.assertEqual(partial["summary"]["continuation_hit_count"], 1)
            self.assertEqual(bad["status"], "fail")
            self.assertIn("source generation-gap report does not point to a forced-choice diagnostic", bad["issues"])

    def test_decoding_gap_target_selection_and_profile_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gap_path, forced_path = write_decoding_gap_fixtures(Path(tmp))
            targets = select_decoding_gap_targets(read_json_report(gap_path), read_json_report(forced_path))
            rows = [
                probe_row("demo", "fixed", True),
                probe_row("demo", "loss", False),
            ]
            summaries = summarize_decoding_gap_profiles(
                targets,
                [{"profile_id": "demo", "max_new_tokens": 12, "temperature": 0.2, "top_k": 1, "seed": 505}],
                rows,
            )

            self.assertEqual(default_decoding_gap_profiles()[0]["profile_id"], "greedy-12")
            self.assertEqual(targets[0]["variant_id"], "symmetric-anchor")
            self.assertFalse(summaries[0]["profile_full_hit"])
            self.assertEqual(summaries[0]["missed_terms"], ["loss"])


def write_decoding_gap_fixtures(root: Path) -> tuple[Path, Path]:
    gap_path = root / "model_capability_required_term_pair_generation_gap.json"
    forced_path = root / "model_capability_required_term_pair_forced_choice_diagnostic.json"
    checkpoint = root / "checkpoint.pt"
    tokenizer = root / "tokenizer.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    write_json(
        gap_path,
        {
            "status": "pass",
            "source_required_term_pair_forced_choice_diagnostic": str(forced_path),
            "gap_rows": [
                gap_row("fixed"),
                gap_row("loss"),
            ],
            "variant_summaries": [
                {
                    "variant_id": "symmetric-anchor",
                    "variant_label": "symmetric anchor",
                    "forced_expected_best_count": 2,
                    "forced_choice_full_match": True,
                    "generation_pair_full_hit": False,
                    "forced_generation_gap": True,
                }
            ],
        },
    )
    write_json(
        forced_path,
        {
            "status": "pass",
            "runs": [
                {
                    "run_id": "demo-run",
                    "pair_id": "01-fixed-loss",
                    "variant_id": "symmetric-anchor",
                    "variant_label": "symmetric anchor",
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                    "checkpoint_exists": True,
                }
            ],
        },
    )
    return gap_path, forced_path


def fake_generate(by_prompt: dict[str, str]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        term = str(request["prompt_term"])
        continuation = by_prompt.get(term, "")
        return {"generated": f"{term}:{continuation}", "continuation": continuation}

    return generate


def gap_row(term: str) -> dict[str, object]:
    return {
        "variant_id": "symmetric-anchor",
        "variant_label": "symmetric anchor",
        "run_id": "demo-run",
        "pair_id": "01-fixed-loss",
        "prompt_term": term,
        "expected_term": term,
        "forced_expected_is_best": True,
        "gap_class": "internal_only",
    }


def probe_row(profile_id: str, term: str, hit: bool) -> dict[str, object]:
    return {
        "variant_id": "symmetric-anchor",
        "profile_id": profile_id,
        "prompt_term": term,
        "expected_term": term,
        "continuation_hit": hit,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
