from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt.eval_suite import (
    PromptCase,
    PromptSuite,
    build_eval_suite_report,
    build_prompt_result,
    default_prompt_cases,
    load_builtin_prompt_suite,
    load_prompt_suite,
    load_prompt_cases,
    write_eval_suite_outputs,
)
from minigpt.eval_suite_design import summarize_prompt_suite_design
from minigpt import eval_suite
from minigpt import standard_zh_prompt_suite
from minigpt import eval_suite_artifacts


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

    def test_standard_zh_builtin_suite_has_broader_task_coverage(self) -> None:
        suite = load_builtin_prompt_suite("standard-zh")

        self.assertEqual(suite.name, "minigpt-standard-zh-benchmark")
        self.assertEqual(suite.version, "2")
        self.assertEqual(len(suite.cases), 10)
        self.assertIn("safety-boundary", {case.task_type for case in suite.cases})
        self.assertIn("hard", {case.difficulty for case in suite.cases})
        self.assertTrue(all(case.seed >= 201 for case in suite.cases))
        self.assertEqual(standard_zh_prompt_suite().name, suite.name)

    def test_load_prompt_suite_supports_builtin_uri(self) -> None:
        suite = load_prompt_suite("builtin:standard-zh")

        self.assertEqual(suite.name, "minigpt-standard-zh-benchmark")
        self.assertEqual(suite.cases[-1].name, "comparison-baseline")

    def test_standard_zh_data_file_matches_builtin_suite(self) -> None:
        suite = load_prompt_suite(ROOT / "data" / "standard_zh_eval_prompts.json")
        builtin = load_builtin_prompt_suite("standard-zh")

        self.assertEqual(suite.to_dict(), builtin.to_dict())

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
        self.assertEqual(report["coverage"]["status"], "warn")
        self.assertEqual(report["coverage"]["comparison_status"], "warn")
        self.assertIn("continuation", report["coverage"]["missing_recommended_task_types"])
        self.assertEqual(report["benchmark"]["coverage"], report["coverage"])
        self.assertEqual(report["design_summary"], report["benchmark"]["design_summary"])
        self.assertEqual(report["design_summary"]["coverage_status"], "warn")
        self.assertEqual(report["design_summary"]["min_new_tokens"], 60)
        self.assertEqual(report["design_summary"]["max_new_tokens"], 60)
        self.assertEqual(report["design_summary"]["duplicate_seed_count"], 1)

    def test_standard_zh_report_is_comparison_ready(self) -> None:
        suite = load_builtin_prompt_suite("standard-zh")
        results = [build_prompt_result(case, case.prompt + "输出") for case in suite.cases]

        report = build_eval_suite_report(
            results,
            checkpoint="checkpoint.pt",
            tokenizer="tokenizer.json",
            suite="builtin:standard-zh",
            suite_name=suite.name,
            suite_version=suite.version,
            suite_description=suite.description,
            suite_language=suite.language,
        )

        coverage = report["coverage"]
        self.assertEqual(coverage["status"], "pass")
        self.assertEqual(coverage["comparison_status"], "pass")
        self.assertEqual(coverage["missing_recommended_task_types"], [])
        self.assertEqual(coverage["missing_comparison_difficulties"], [])
        self.assertGreaterEqual(coverage["task_type_count"], 8)
        self.assertIn("safety-boundary", coverage["observed_task_types"])
        self.assertEqual(report["design_summary"]["coverage_status"], "pass")
        self.assertEqual(report["design_summary"]["comparison_status"], "pass")
        self.assertEqual(report["design_summary"]["case_count"], 10)
        self.assertEqual(report["design_summary"]["duplicate_seed_count"], 0)
        self.assertTrue(report["design_summary"]["all_cases_have_expected_behavior"])

    def test_prompt_suite_design_summary_tracks_standard_coverage(self) -> None:
        suite = load_builtin_prompt_suite("standard-zh")

        summary = summarize_prompt_suite_design(suite)

        self.assertEqual(summary["suite_name"], "minigpt-standard-zh-benchmark")
        self.assertEqual(summary["case_count"], 10)
        self.assertEqual(summary["coverage_status"], "pass")
        self.assertEqual(summary["comparison_status"], "pass")
        self.assertEqual(summary["task_type_count"], 10)
        self.assertEqual(summary["difficulty_count"], 3)
        self.assertGreaterEqual(summary["tag_count"], 8)
        self.assertEqual(summary["duplicate_seed_count"], 0)
        self.assertTrue(summary["all_cases_have_expected_behavior"])
        self.assertTrue(summary["all_cases_have_tags"])
        self.assertIn("safety-boundary", summary["observed_task_types"])
        self.assertEqual(summary["missing_recommended_task_types"], [])
        self.assertEqual(summary["missing_comparison_difficulties"], [])

    def test_prompt_suite_design_summary_warns_for_narrow_suite(self) -> None:
        suite = PromptSuite(
            name="narrow",
            cases=(PromptCase("one", "hi", task_type="qa", difficulty="easy", tags=("qa",)),),
        )

        summary = summarize_prompt_suite_design(suite)

        self.assertEqual(summary["coverage_status"], "warn")
        self.assertEqual(summary["comparison_status"], "warn")
        self.assertIn("continuation", summary["missing_recommended_task_types"])
        self.assertIn("hard", summary["missing_comparison_difficulties"])
        self.assertTrue(summary["blockers"])

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
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("Prompt Results", html)
            self.assertIn("Coverage Readiness", html)
            self.assertIn("Suite Design", html)
            self.assertIn("Design comparison", html)

    def test_eval_suite_reexports_artifact_writers(self) -> None:
        self.assertIs(eval_suite.write_eval_suite_outputs, eval_suite_artifacts.write_eval_suite_outputs)
        self.assertIs(eval_suite.render_eval_suite_html, eval_suite_artifacts.render_eval_suite_html)


if __name__ == "__main__":
    unittest.main()
