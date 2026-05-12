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
    build_eval_suite_report,
    build_prompt_result,
    default_prompt_cases,
    load_prompt_cases,
    write_eval_suite_outputs,
)


class EvalSuiteTests(unittest.TestCase):
    def test_default_prompt_cases_are_valid(self) -> None:
        cases = default_prompt_cases()

        self.assertGreaterEqual(len(cases), 3)
        self.assertTrue(all(case.prompt for case in cases))

    def test_load_prompt_cases_reads_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.json"
            path.write_text(
                json.dumps({"cases": [{"name": "one", "prompt": "人工智能", "top_k": 0, "seed": 7}]}),
                encoding="utf-8",
            )

            cases = load_prompt_cases(path)

            self.assertEqual(cases[0].name, "one")
            self.assertIsNone(cases[0].top_k)
            self.assertEqual(cases[0].seed, 7)

    def test_build_prompt_result_counts_continuation(self) -> None:
        case = PromptCase("one", "人工智能", max_new_tokens=4)

        result = build_prompt_result(case, "人工智能模型")

        self.assertEqual(result.continuation, "模型")
        self.assertEqual(result.char_count, 2)

    def test_write_eval_suite_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = build_prompt_result(PromptCase("one", "AI"), "AI model")
            report = build_eval_suite_report([result], checkpoint="checkpoint.pt", tokenizer="tokenizer.json")

            outputs = write_eval_suite_outputs(report, tmp)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("<svg", Path(outputs["svg"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
