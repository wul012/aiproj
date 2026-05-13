from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.eval_suite import PromptCase, PromptSuite
from minigpt.pair_batch import build_pair_batch_case_result, build_pair_batch_report, write_pair_batch_outputs
from minigpt.server import GenerationResponse


class PairBatchTests(unittest.TestCase):
    def test_build_pair_batch_case_result_compares_outputs(self) -> None:
        case = PromptCase("one", "AI", max_new_tokens=4, task_type="qa", difficulty="easy", seed=7)
        left = GenerationResponse("AI", "AI left", " left", 4, 0.8, 10, 7, "left.pt", "char")
        right = GenerationResponse("AI", "AI right side", " right side", 4, 0.8, 10, 7, "right.pt", "char")

        result = build_pair_batch_case_result(case, left, right, left_checkpoint_id="base", right_checkpoint_id="wide")

        self.assertEqual(result["left"]["checkpoint_id"], "base")
        self.assertEqual(result["right"]["checkpoint_id"], "wide")
        self.assertFalse(result["comparison"]["generated_equal"])
        self.assertEqual(result["comparison"]["generated_char_delta"], len("AI right side") - len("AI left"))
        self.assertEqual(result["comparison"]["continuation_char_delta"], len(" right side") - len(" left"))
        self.assertEqual(result["task_type"], "qa")

    def test_build_pair_batch_report_summarizes_results(self) -> None:
        suite = PromptSuite("demo-suite", version="2", cases=(PromptCase("one", "AI", task_type="qa", difficulty="easy"),))
        result = build_pair_batch_case_result(
            suite.cases[0],
            {"generated": "AI same", "continuation": " same", "checkpoint": "left.pt", "tokenizer": "char"},
            {"generated": "AI same", "continuation": " same", "checkpoint": "right.pt", "tokenizer": "char"},
            left_checkpoint_id="base",
            right_checkpoint_id="wide",
        )

        report = build_pair_batch_report(
            [result],
            suite=suite,
            suite_path="suite.json",
            left_checkpoint="left.pt",
            right_checkpoint="right.pt",
            left_checkpoint_id="base",
            right_checkpoint_id="wide",
            left_tokenizer="left-tokenizer.json",
            right_tokenizer="right-tokenizer.json",
        )

        self.assertEqual(report["kind"], "minigpt_pair_generation_batch")
        self.assertEqual(report["suite"]["name"], "demo-suite")
        self.assertEqual(report["case_count"], 1)
        self.assertEqual(report["generated_equal_count"], 1)
        self.assertEqual(report["generated_difference_count"], 0)
        self.assertEqual(report["task_type_counts"], {"qa": 1})
        self.assertEqual(report["left"]["checkpoint_id"], "base")

    def test_write_pair_batch_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite = PromptSuite("demo-suite", cases=(PromptCase("one", "AI", task_type="qa", difficulty="easy"),))
            result = build_pair_batch_case_result(
                suite.cases[0],
                {"generated": "AI left", "continuation": " left", "checkpoint": "left.pt", "tokenizer": "char"},
                {"generated": "AI right", "continuation": " right", "checkpoint": "right.pt", "tokenizer": "char"},
                left_checkpoint_id="base",
                right_checkpoint_id="wide",
            )
            report = build_pair_batch_report([result], suite=suite, left_checkpoint_id="base", right_checkpoint_id="wide")

            outputs = write_pair_batch_outputs(report, tmp)

            self.assertEqual(set(outputs), {"json", "csv", "md", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["kind"], "minigpt_pair_generation_batch")
            self.assertIn("generated_equal", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT Pair Generation Batch", Path(outputs["md"]).read_text(encoding="utf-8"))
            self.assertIn("Prompt Pair Results", Path(outputs["html"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
