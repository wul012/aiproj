from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan import build_model_capability_route_promotion_bounded_real_replay_repair_plan
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan_artifacts import write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed import (
    build_model_capability_route_promotion_bounded_real_replay_repair_seed,
    locate_route_promotion_bounded_real_replay,
    locate_route_promotion_bounded_real_replay_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_repair_seed import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_review import ready_real_replay
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_plan import ready_repair_review


def ready_seed_inputs(root: Path) -> tuple[dict, Path, dict, Path]:
    replay, replay_path = ready_real_replay(root / "replay-source")
    review, _ = ready_repair_review(root / "review-source")
    plan = build_model_capability_route_promotion_bounded_real_replay_repair_plan(review)
    plan_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs(plan, root / "plan")
    return plan, Path(plan_outputs["json"]), replay, replay_path


class ModelCapabilityRoutePromotionBoundedRealReplayRepairSeedTests(unittest.TestCase):
    def test_builds_repair_seed_examples_from_plan_and_replay_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan, plan_path, replay, replay_path = ready_seed_inputs(Path(tmp))
            report = build_model_capability_route_promotion_bounded_real_replay_repair_seed(
                plan,
                replay,
                repair_plan_path=plan_path,
                real_replay_path=replay_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_seed_ready")
        self.assertEqual(report["summary"]["example_count"], 8)
        self.assertEqual(report["summary"]["case_count"], 4)
        self.assertTrue(all(example["completion"] == "fixed loss" for example in report["seed_examples"]))
        self.assertTrue(any("任务" in example["prompt"] for example in report["seed_examples"]))
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_seed_fails_when_plan_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan, _, replay, _ = ready_seed_inputs(Path(tmp))
            plan["status"] = "fail"
            report = build_model_capability_route_promotion_bounded_real_replay_repair_seed(plan, replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("repair_plan_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan, plan_path, replay, replay_path = ready_seed_inputs(root)
            self.assertEqual(locate_route_promotion_bounded_real_replay_repair_plan(plan_path.parent), plan_path)
            self.assertEqual(locate_route_promotion_bounded_real_replay(replay_path.parent), replay_path)
            report = build_model_capability_route_promotion_bounded_real_replay_repair_seed(plan, replay, repair_plan_path=plan_path, real_replay_path=replay_path)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs(report, root / "seed")
            cli_main(["--repair-plan", str(plan_path.parent), "--real-replay", str(replay_path.parent), "--out-dir", str(root / "cli-seed"), "--require-seed-ready", "--force"])

            jsonl_lines = (Path(outputs["jsonl"]).read_text(encoding="utf-8")).strip().splitlines()
            corpus = Path(outputs["corpus"]).read_text(encoding="utf-8")

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertEqual(len(jsonl_lines), report["summary"]["example_count"])
        self.assertEqual(json.loads(jsonl_lines[0])["completion"], "fixed loss")
        self.assertIn("fixed loss", corpus)
        self.assertIn("bounded_real_replay_repair_seed_ready=True", render_model_capability_route_promotion_bounded_real_replay_repair_seed_text(report))
        self.assertIn("Seed Examples", render_model_capability_route_promotion_bounded_real_replay_repair_seed_markdown(report))
        self.assertIn("repair seed", render_model_capability_route_promotion_bounded_real_replay_repair_seed_html(report))


if __name__ == "__main__":
    unittest.main()
