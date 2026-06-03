from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    build_objective_level_contrast_acceptance_review,
    locate_objective_level_contrast_acceptance_review_rollup,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review_artifacts import (
    render_objective_level_contrast_acceptance_review_html,
    render_objective_level_contrast_acceptance_review_markdown,
    render_objective_level_contrast_acceptance_review_text,
    write_objective_level_contrast_acceptance_review_outputs,
)
from scripts.run_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (
    main as cli_main,
)


class ObjectiveLevelContrastAcceptanceReviewTests(unittest.TestCase):
    def test_accepts_seed_stable_rollup_inside_pair_probe_boundary(self) -> None:
        report = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_acceptance_review_accepted")
        self.assertTrue(report["summary"]["promotion_allowed"])
        self.assertEqual(report["summary"]["accepted_route"], "objective_level_contrast")
        self.assertEqual(report["summary"]["model_quality_boundary"], "tiny_required_term_pair_probe_only")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "seed_stable_pair_probe_route_accepted")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_rejects_when_pair_full_strength_is_too_weak(self) -> None:
        report = build_objective_level_contrast_acceptance_review(
            ready_rollup_fixture(),
            minimum_pair_full_count=3,
        )

        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["summary"]["promotion_allowed"])
        self.assertIn("minimum_pair_full_strength", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_uniform_strength_can_be_required_explicitly(self) -> None:
        report = build_objective_level_contrast_acceptance_review(
            ready_rollup_fixture(),
            require_uniform_strength=True,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("uniform_strength_when_required", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        report = build_objective_level_contrast_acceptance_review(ready_rollup_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollup_dir = root / "rollup"
            rollup_dir.mkdir()
            rollup_path = rollup_dir / "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.json"
            rollup_path.write_text(json.dumps(ready_rollup_fixture(), ensure_ascii=False), encoding="utf-8")

            self.assertEqual(locate_objective_level_contrast_acceptance_review_rollup(rollup_dir), rollup_path)
            outputs = write_objective_level_contrast_acceptance_review_outputs(report, root / "review")
            cli_main(["--rollup", str(rollup_dir), "--out-dir", str(root / "cli-review"), "--force", "--require-pass"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("promotion_allowed=True", render_objective_level_contrast_acceptance_review_text(report))
        self.assertIn("Objective-Level Contrast Acceptance Review", render_objective_level_contrast_acceptance_review_markdown(report))
        self.assertIn("MiniGPT objective-level contrast acceptance review", render_objective_level_contrast_acceptance_review_html(report))


def ready_rollup_fixture() -> dict[str, object]:
    seed_rows = [
        replay_row(3636, 3),
        replay_row(3737, 2),
        replay_row(3838, 2),
    ]
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_level_contrast_seed_stability_ready_for_acceptance_review",
        "summary": {
            "acceptance_review_ready": True,
            "promotion_allowed": False,
            "expected_seed_count": 3,
            "observed_seed_count": 3,
            "ready_replay_count": 3,
            "minimum_ready_replay_count": 2,
            "pair_full_counts": {"3636": 3, "3737": 2, "3838": 2},
            "failed_check_count": 0,
        },
        "seed_rows": seed_rows,
    }


def replay_row(seed: int, pair_full_count: int) -> dict[str, object]:
    return {
        "seed": seed,
        "source_path": f"seed-{seed}.json",
        "ready": True,
        "pair_full_count": pair_full_count,
        "pair_full_rate": round(pair_full_count / 3, 4),
        "exact_heldout_pair_full": True,
        "required_all_pair_full": True,
    }


if __name__ == "__main__":
    unittest.main()
