from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.sampling import (
    SamplingCase,
    build_sampling_report,
    build_sampling_result,
    default_sampling_cases,
    parse_sampling_case,
    write_sampling_csv,
    write_sampling_outputs,
    write_sampling_svg,
)


class SamplingTests(unittest.TestCase):
    def test_parse_sampling_case(self) -> None:
        case = parse_sampling_case("warm:0.75:20:7")

        self.assertEqual(case.name, "warm")
        self.assertEqual(case.temperature, 0.75)
        self.assertEqual(case.top_k, 20)
        self.assertEqual(case.seed, 7)

    def test_parse_sampling_case_allows_no_top_k(self) -> None:
        case = parse_sampling_case("open:1.1:0:9")

        self.assertIsNone(case.top_k)

    def test_sampling_case_rejects_bad_temperature(self) -> None:
        with self.assertRaises(ValueError):
            SamplingCase("bad", temperature=0.0, top_k=1, seed=1)

    def test_build_sampling_result_counts_continuation(self) -> None:
        case = SamplingCase("balanced", temperature=0.8, top_k=30, seed=1)

        result = build_sampling_result(case, prompt="abc", max_new_tokens=4, generated="abcdeed")

        self.assertEqual(result.continuation, "deed")
        self.assertEqual(result.char_count, 4)
        self.assertEqual(result.unique_char_count, 2)

    def test_build_sampling_report_requires_results(self) -> None:
        with self.assertRaises(ValueError):
            build_sampling_report("prompt", 4, [])

    def test_default_sampling_cases(self) -> None:
        cases = default_sampling_cases()

        self.assertEqual([case.name for case in cases], ["conservative", "balanced", "creative"])

    def test_write_sampling_csv_and_svg(self) -> None:
        case = SamplingCase("balanced", temperature=0.8, top_k=30, seed=1)
        result = build_sampling_result(case, prompt="abc", max_new_tokens=4, generated="abcdef")
        report = build_sampling_report("abc", 4, [result])

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "sample_lab.csv"
            svg_path = Path(tmp) / "sample_lab.svg"

            write_sampling_csv(report, csv_path)
            write_sampling_svg(report, svg_path)

            self.assertIn("temperature", csv_path.read_text(encoding="utf-8"))
            self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))

    def test_write_sampling_outputs(self) -> None:
        case = SamplingCase("balanced", temperature=0.8, top_k=30, seed=1)
        result = build_sampling_result(case, prompt="abc", max_new_tokens=4, generated="abcdef")
        report = build_sampling_report("abc", 4, [result])

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_sampling_outputs(report, tmp)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["svg"]).exists())


if __name__ == "__main__":
    unittest.main()
