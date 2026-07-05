from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_branch_objective_comparison import (
    build_model_capability_required_term_pair_loss_branch_objective_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_branch_objective_comparison_artifacts import (
    render_loss_branch_objective_comparison_html,
    render_loss_branch_objective_comparison_markdown,
    render_loss_branch_objective_comparison_text,
    write_loss_branch_objective_comparison_outputs,
)


from tests._bootstrap import ROOT


class LossBranchObjectiveComparisonTests(unittest.TestCase):
    def test_comparison_marks_all_loss_only_tradeoffs(self) -> None:
        report = build_model_capability_required_term_pair_loss_branch_objective_comparison(
            [
                fake_refresh_report("targeted", hit_terms=("loss",)),
                fake_refresh_report("dual", hit_terms=("loss",)),
                fake_refresh_report("micro", hit_terms=("loss",)),
            ],
            source_labels=["targeted", "dual", "micro"],
            generated_at="2026-05-31T14:20:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "loss_branch_objectives_confirm_loss_only_tradeoff")
        self.assertEqual(report["summary"]["loss_only_tradeoff_report_count"], 3)
        self.assertEqual(report["summary"]["pair_full_report_count"], 0)
        self.assertEqual(report["summary"]["union_hit_terms"], ["loss"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_promotes_pair_full_candidate_when_present(self) -> None:
        report = build_model_capability_required_term_pair_loss_branch_objective_comparison(
            [
                fake_refresh_report("targeted", hit_terms=("loss",)),
                fake_refresh_report("candidate", hit_terms=("fixed", "loss")),
            ],
            source_labels=["targeted", "candidate"],
        )

        self.assertEqual(report["decision"], "promote_loss_branch_pair_full_candidate")
        self.assertEqual(report["summary"]["pair_full_report_count"], 1)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "pair_full_candidate")

    def test_non_loss_branch_mode_fails_contract(self) -> None:
        report = build_model_capability_required_term_pair_loss_branch_objective_comparison(
            [
                fake_refresh_report("targeted", hit_terms=("loss",)),
                fake_refresh_report("bad", hit_terms=("fixed",), corpus_mode="equals_surface_no_pair_id_repair"),
            ],
            source_labels=["targeted", "bad"],
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("bad is not a loss-branch objective corpus mode", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_model_capability_required_term_pair_loss_branch_objective_comparison(
                [fake_refresh_report("targeted", hit_terms=("loss",)), fake_refresh_report("dual", hit_terms=("loss",))],
                source_labels=["targeted", "dual"],
            )
            outputs = write_loss_branch_objective_comparison_outputs(report, Path(tmp))
            text = render_loss_branch_objective_comparison_text(report)
            markdown = render_loss_branch_objective_comparison_markdown(report)
            html = render_loss_branch_objective_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("loss_only_tradeoff_report_count=2", text)
            self.assertIn("Loss-Branch Objective Comparison", markdown)
            self.assertIn("MiniGPT loss-branch objective comparison", html)

    def test_cli_returns_nonzero_for_bad_input_with_require_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "good" / "model_capability_required_term_pair_coexistence_refresh.json"
            bad = root / "bad" / "model_capability_required_term_pair_coexistence_refresh.json"
            good.parent.mkdir(parents=True)
            bad.parent.mkdir(parents=True)
            good.write_text(json_text(fake_refresh_report("targeted", hit_terms=("loss",))), encoding="utf-8")
            bad.write_text(json_text(fake_refresh_report("bad", hit_terms=("fixed",), corpus_mode="equals_surface_no_pair_id_repair")), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_model_capability_required_term_pair_loss_branch_objective_comparison.py"),
                    str(good.parent),
                    str(bad.parent),
                    "--labels",
                    "targeted",
                    "bad",
                    "--out-dir",
                    str(root / "out"),
                    "--require-pass",
                    "--force",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("status=fail", result.stdout)


def fake_refresh_report(
    name: str,
    *,
    hit_terms: tuple[str, ...],
    corpus_mode: str | None = None,
) -> dict[str, object]:
    mode = corpus_mode or f"equals_surface_no_pair_id_loss_branch_{name}_repair"
    case_rows = []
    for profile_id in ("default", "suppress_newline_tokens"):
        for term in ("fixed", "loss"):
            hit = term in hit_terms
            case_rows.append(
                {
                    "profile_id": profile_id,
                    "term": term,
                    "prompt": f"{term}=",
                    "continuation_hit": hit,
                    "newline_cleanup_hit": hit,
                    "generated_preview": f"{term}={term if hit else 'miss'}",
                    "continuation_preview": term if hit else "miss",
                }
            )
    pair_full = set(hit_terms) == {"fixed", "loss"}
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": mode, "seed": 3535},
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": pair_full,
            "default_continuation_hit_count": len(hit_terms),
            "suppression_continuation_hit_count": len(hit_terms),
            "default_pair_full_variant_count": int(pair_full),
            "suppression_pair_full_variant_count": int(pair_full),
        },
        "replay_report": {"case_rows": case_rows},
    }


def json_text(payload: dict[str, object]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    unittest.main()
