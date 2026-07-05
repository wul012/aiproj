from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import minigpt.model_capability_required_term_pair_decoding_sweep as facade
import minigpt.model_capability_required_term_pair_decoding_sweep_core as core
from minigpt.model_capability_required_term_pair_decoding_sweep import (
    build_model_capability_required_term_pair_decoding_sweep,
    default_pair_decoding_profiles,
    locate_model_capability_required_term_pair_decoding_sweep_source,
    normalize_decoding_profiles,
    read_json_report,
    resolve_exit_code,
    select_pair_decoding_sweep_targets,
    summarize_decoding_profile_probe_rows,
    summarize_pair_decoding_targets,
    summarize_required_term_pair_decoding_sweep,
)
from minigpt.model_capability_required_term_pair_decoding_sweep_artifacts import (
    render_model_capability_required_term_pair_decoding_sweep_html,
    render_model_capability_required_term_pair_decoding_sweep_markdown,
    render_model_capability_required_term_pair_decoding_sweep_text,
    write_model_capability_required_term_pair_decoding_sweep_outputs,
)


class ModelCapabilityRequiredTermPairDecodingSweepTests(unittest.TestCase):
    def test_facade_reexports_decoding_sweep_core_contract(self) -> None:
        names = (
            "normalize_decoding_profiles",
            "resolve_exit_code",
            "select_pair_decoding_sweep_targets",
            "summarize_decoding_profile_probe_rows",
            "summarize_pair_decoding_targets",
            "summarize_required_term_pair_decoding_sweep",
        )
        for name in names:
            self.assertIs(getattr(facade, name), getattr(core, name))

    def test_decoding_sweep_reports_recovered_full_hit_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = write_pair_capacity_fixture(root)
            profiles = [
                {"profile_id": "short", "max_new_tokens": 12, "temperature": 0.2, "top_k": 1},
                {"profile_id": "long", "max_new_tokens": 24, "temperature": 0.2, "top_k": 1},
            ]

            report = build_model_capability_required_term_pair_decoding_sweep(
                read_json_report(source),
                out_dir=root / "decode",
                source_path=source,
                seed=498,
                decoding_profiles=profiles,
                generated_at="2026-05-30T00:00:00Z",
                generate_func=fake_generate(
                    {
                        ("01-fixed-loss-longer-iters-seed-496", "fixed", 24),
                        ("01-fixed-loss-longer-iters-seed-496", "loss", 24),
                    }
                ),
            )
            outputs = write_model_capability_required_term_pair_decoding_sweep_outputs(report, root / "outputs")
            text = render_model_capability_required_term_pair_decoding_sweep_text(report)
            markdown = render_model_capability_required_term_pair_decoding_sweep_markdown(report)
            html = render_model_capability_required_term_pair_decoding_sweep_html(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "required_term_pair_decoding_sweep_recovered")
            self.assertTrue(report["summary"]["decoding_full_hit_observed"])
            self.assertEqual(report["summary"]["profile_target_full_hit_count"], 1)
            self.assertEqual(report["summary"]["best_profile_id"], "long")
            self.assertIn("pair_decoding_sweep_decision=pair_decoding_sweep_full_hit_recovered", text)
            self.assertIn("Pair Decoding Sweep", markdown)
            self.assertIn("Profile Results", html)
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertEqual(locate_model_capability_required_term_pair_decoding_sweep_source(source.parent), source)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decoding_sweep_reports_partial_and_input_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_pair_capacity_fixture(root))
            profiles = [{"profile_id": "short", "max_new_tokens": 12, "temperature": 0.2, "top_k": 1}]

            partial = build_model_capability_required_term_pair_decoding_sweep(
                source_report,
                out_dir=root / "partial",
                decoding_profiles=profiles,
                generate_func=fake_generate({("01-fixed-loss-longer-iters-seed-496", "loss", 12)}),
            )
            bad_status = build_model_capability_required_term_pair_decoding_sweep(
                {**source_report, "status": "fail"},
                out_dir=root / "bad-status",
                decoding_profiles=profiles,
                generate_func=fake_generate(set()),
            )

            self.assertEqual(partial["decision"], "required_term_pair_decoding_sweep_partial")
            self.assertEqual(partial["summary"]["profile_target_partial_hit_count"], 1)
            self.assertFalse(partial["summary"]["decoding_full_hit_observed"])
            self.assertEqual(bad_status["status"], "fail")
            self.assertEqual(bad_status["decision"], "fix_required_term_pair_decoding_sweep")
            self.assertIn("source pair capacity sweep report is not pass", bad_status["issues"])
            self.assertEqual(resolve_exit_code(bad_status, require_pass=True), 1)

    def test_decoding_sweep_selection_and_input_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_report = read_json_report(write_pair_capacity_fixture(root))

            selected = select_pair_decoding_sweep_targets(source_report)
            limited = select_pair_decoding_sweep_targets(source_report, target_limit=0)
            bad_decision = build_model_capability_required_term_pair_decoding_sweep(
                {**source_report, "summary": {"pair_capacity_sweep_decision": "pair_capacity_sweep_not_recovered"}},
                out_dir=root / "bad-decision",
                generate_func=fake_generate(set()),
            )
            empty_source = build_model_capability_required_term_pair_decoding_sweep(
                {},
                out_dir=root / "empty-source",
                decoding_profiles=[],
                generate_func=fake_generate(set()),
            )

            self.assertEqual([row["target_id"] for row in selected], ["01-fixed-loss-longer-iters"])
            self.assertEqual(limited, [])
            self.assertIn("source pair capacity sweep is not the expected partial-only decoding target", bad_decision["issues"])
            self.assertIn("source pair capacity sweep report is missing or invalid", empty_source["issues"])
            self.assertIn("at least one decoding profile is required", empty_source["issues"])

    def test_decoding_sweep_summary_helpers_choose_best_profile(self) -> None:
        targets = [{"target_id": "target-a", "pair_id": "01", "variant_id": "longer", "term_names": ["fixed", "loss"]}]
        profiles = normalize_decoding_profiles(
            [
                {"profile_id": "short", "max_new_tokens": 12},
                {"profile_id": "long", "max_new_tokens": 24},
            ]
        )
        probes = [
            {"target_id": "target-a", "profile_id": "short", "term": "fixed", "continuation_hit_count": 0},
            {"target_id": "target-a", "profile_id": "short", "term": "loss", "continuation_hit_count": 1},
            {"target_id": "target-a", "profile_id": "long", "term": "fixed", "continuation_hit_count": 1},
            {"target_id": "target-a", "profile_id": "long", "term": "loss", "continuation_hit_count": 1},
        ]

        profile_summaries = summarize_decoding_profile_probe_rows(targets, profiles, probes)
        target_summaries = summarize_pair_decoding_targets(targets, profiles, profile_summaries)
        summary = summarize_required_term_pair_decoding_sweep(
            targets,
            profiles,
            probes,
            profile_summaries,
            target_summaries,
            source_summary={"pair_capacity_sweep_decision": "pair_capacity_sweep_partial_only"},
        )

        self.assertTrue(profile_summaries[1]["pair_full_hit"])
        self.assertEqual(target_summaries[0]["full_hit_profiles"], ["long"])
        self.assertEqual(summary["best_profile_id"], "long")
        self.assertEqual(summary["pair_decoding_sweep_decision"], "pair_decoding_sweep_full_hit_recovered")
        self.assertGreaterEqual(len(default_pair_decoding_profiles()), 4)


def write_pair_capacity_fixture(root: Path) -> Path:
    run_dir = root / "capacity-runs" / "01-fixed-loss-longer-iters-seed-496"
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.write_bytes(b"fake")
    tokenizer.write_text("{}", encoding="utf-8")
    source = root / "model_capability_required_term_pair_capacity_sweep.json"
    write_json(
        source,
        {
            "status": "pass",
            "summary": {
                "pair_capacity_sweep_decision": "pair_capacity_sweep_partial_only",
                "capacity_full_hit_observed": False,
                "variant_pair_partial_hit_count": 1,
                "variant_pair_full_hit_count": 0,
                "best_variant_id": "longer-iters",
                "best_variant_hit_count": 1,
            },
            "pairs": [
                {
                    "pair_id": "01-fixed-loss",
                    "term_names": ["fixed", "loss"],
                    "terms": [
                        {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:"},
                        {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:"},
                    ],
                }
            ],
            "capacity_rows": [
                {
                    "capacity_run_id": "01-fixed-loss-longer-iters-seed-496",
                    "pair_id": "01-fixed-loss",
                    "variant_id": "longer-iters",
                    "variant_label": "longer training budget",
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                    "checkpoint_exists": True,
                    "tokenizer_exists": True,
                    "max_iters": 2400,
                    "n_embd": 64,
                    "repeat": 240,
                }
            ],
            "variant_pair_summaries": [
                {
                    "pair_id": "01-fixed-loss",
                    "variant_id": "longer-iters",
                    "variant_label": "longer training budget",
                    "term_names": ["fixed", "loss"],
                    "hit_terms": ["loss"],
                    "missed_terms": ["fixed"],
                    "hit_count": 1,
                    "hit_rate": 0.5,
                    "pair_full_hit": False,
                    "pair_partial_hit": True,
                }
            ],
        },
    )
    return source


def fake_generate(hit_rows: set[tuple[str, str, int]]):
    def generate(request: dict[str, object]) -> dict[str, object]:
        prompt = str(request["prompt"])
        term = prompt.strip(":")
        checkpoint_path = Path(str(request["checkpoint_path"]))
        run_id = checkpoint_path.parent.name
        max_new_tokens = int(request["max_new_tokens"])
        continuation = term if (run_id, term, max_new_tokens) in hit_rows else "noop"
        return {"generated": prompt + continuation, "continuation": continuation}

    return generate


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
