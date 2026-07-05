from __future__ import annotations

import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.promoted_training_scale_seed_plan import (
    next_suite_ref,
    plan_command,
    suite_ref_from_selected_run,
)


class PromotedTrainingScaleSeedPlanTests(unittest.TestCase):
    def test_suite_ref_from_selected_run_normalizes_builtin_suite_path(self) -> None:
        run = {
            "scale_plan_summary": {
                "suite_mode": "file",
                "suite_name": "",
                "suite_path": "builtin:standard-zh",
            }
        }

        self.assertEqual(
            suite_ref_from_selected_run(run),
            {
                "mode": "builtin",
                "name": "standard-zh",
                "path": "builtin:standard-zh",
                "source": "selected_run",
            },
        )

    def test_next_suite_ref_rejects_conflicting_overrides(self) -> None:
        with self.assertRaisesRegex(ValueError, "suite_name and suite_path cannot both be provided"):
            next_suite_ref(
                Path("project"),
                {"path": "builtin:standard-zh"},
                suite_path="data/custom_eval.json",
                suite_name="standard-zh",
            )

    def test_next_suite_ref_prefers_inherited_suite_when_no_override_is_given(self) -> None:
        self.assertEqual(
            next_suite_ref(
                Path("project"),
                {"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"},
                suite_path=None,
                suite_name=None,
            ),
            {
                "mode": "builtin",
                "name": "standard-zh",
                "path": "builtin:standard-zh",
                "source": "inherited",
            },
        )

    def test_plan_command_emits_builtin_suite_name_and_skips_missing_sources(self) -> None:
        root = Path("project")
        source_rows = [{"path": "data/corpus.jsonl", "exists": True}]

        command = plan_command(
            source_rows,
            project_root=root,
            plan_out_dir=root / "plan",
            batch_out_root=root / "batch",
            dataset_name="portfolio-zh",
            dataset_version_prefix="v1218",
            dataset_description="Seeded corpus.",
            suite={"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"},
            sample_prompt="MiniGPT",
            max_variants=3,
            python_executable="python",
        )

        self.assertIn("--suite-name", command)
        self.assertIn("standard-zh", command)
        self.assertIn("--max-variants", command)
        self.assertEqual(
            plan_command(
                [{"path": "missing.jsonl", "exists": False}],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_name="portfolio-zh",
                dataset_version_prefix="v1218",
                dataset_description="Seeded corpus.",
                suite={"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"},
                sample_prompt="MiniGPT",
                max_variants=3,
                python_executable="python",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
