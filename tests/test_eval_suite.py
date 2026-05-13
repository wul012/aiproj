from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.eval_suite import (
    PromptCase,
    PromptSuite,
    build_eval_suite_report,
    build_prompt_result,
    default_prompt_cases,
    load_prompt_suite,
    load_prompt_cases,
    write_eval_suite_outputs,
)


class EvalSuiteTests(unittest.TestCase):
    def test_default_prompt_cases_are_valid(self) -> None:
        cases = default_prompt_cases()

        self.assertGreaterEqual(len(cases), 5)
        self.assertTrue(all(case.prompt for case in cases))
        self.assertIn("qa", {case.task_type for case in cases})
        self.assertIn("medium", {case.difficulty for case in cases})

    def test_load_prompt_cases_reads_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.json"
            path.write_text(
                json.dumps(
                    {
                        "suite_name": "demo-benchmark",
                        "suite_version": "2",
                        "description": "demo suite",
                        "language": "zh-CN",
                        "cases": [
                            {
                                "name": "one",
                                "prompt": "人工智能",
                                "top_k": 0,
                                "seed": 7,
                                "task_type": "qa",
                                "difficulty": "easy",
                                "expected_behavior": "stay on topic",
                                "tags": ["demo", "qa"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            suite = load_prompt_suite(path)
            cases = load_prompt_cases(path)

            self.assertIsInstance(suite, PromptSuite)
            self.assertEqual(suite.name, "demo-benchmark")
            self.assertEqual(suite.version, "2")
            self.assertEqual(cases[0].name, "one")
            self.assertIsNone(cases[0].top_k)
            self.assertEqual(cases[0].seed, 7)
            self.assertEqual(cases[0].task_type, "qa")
            self.assertEqual(cases[0].difficulty, "easy")
            self.assertEqual(cases[0].tags, ("demo", "qa"))

    def test_load_prompt_suite_supports_legacy_list_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.json"
            path.write_text(json.dumps([{"name": "one", "prompt": "人工智能"}]), encoding="utf-8")

            suite = load_prompt_suite(path)

            self.assertEqual(suite.name, "legacy")
            self.assertEqual(suite.cases[0].task_type, "general")
            self.assertEqual(suite.cases[0].difficulty, "medium")

    def test_build_prompt_result_counts_continuation(self) -> None:
        case = PromptCase("one", "人工智能", max_new_tokens=4, task_type="qa", difficulty="easy", tags="qa,demo")

        result = build_prompt_result(case, "人工智能模型")

        self.assertEqual(result.continuation, "模型")
        self.assertEqual(result.char_count, 2)
        self.assertEqual(result.task_type, "qa")
        self.assertEqual(result.difficulty, "easy")
        self.assertEqual(result.tags, ("qa", "demo"))

    def test_build_eval_suite_report_adds_benchmark_summaries(self) -> None:
        result_a = build_prompt_result(PromptCase("qa", "问题", task_type="qa", difficulty="easy"), "问题回答")
        result_b = build_prompt_result(PromptCase("summary", "总结", task_type="summary", difficulty="medium"), "总结内容")

        report = build_eval_suite_report(
            [result_a, result_b],
            checkpoint="checkpoint.pt",
            tokenizer="tokenizer.json",
            suite="suite.json",
            suite_name="demo",
            suite_version="1",
            suite_description="demo benchmark",
            suite_language="zh-CN",
        )

        self.assertEqual(report["benchmark"]["suite_name"], "demo")
        self.assertEqual(report["task_type_counts"], {"qa": 1, "summary": 1})
        self.assertEqual(report["difficulty_counts"], {"easy": 1, "medium": 1})
        self.assertEqual(len(report["benchmark"]["task_type_summary"]), 2)

    def test_write_eval_suite_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = build_prompt_result(PromptCase("one", "AI", task_type="qa", difficulty="easy"), "AI model")
            report = build_eval_suite_report([result], checkpoint="checkpoint.pt", tokenizer="tokenizer.json", suite_name="demo")

            outputs = write_eval_suite_outputs(report, tmp)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("task_type,difficulty", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("<svg", Path(outputs["svg"]).read_text(encoding="utf-8"))
            self.assertIn("Prompt Results", Path(outputs["html"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
