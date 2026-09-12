from __future__ import annotations

import contextlib
import io
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from minigpt.evaluation.corpora import aggregate_corpora, load_corpora, render_corpora
from minigpt.evaluation.paired import loss_summary
from scripts import evaluate

ensure_src_path()


class EvalCorporaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)
        self.demo = Path(__file__).resolve().parents[1] / "f/1320/解释/demo"

    def args(self, manifest: Path, out: Path) -> list[str]:
        return [
            "--checkpoint",
            str(self.demo / "baseline.pt"),
            "--compare-with",
            str(self.demo / "candidate.pt"),
            "--corpora",
            str(manifest),
            "--split",
            "all",
            "--windows",
            "16",
            "--batch-size",
            "4",
            "--device",
            "cpu",
            "--out",
            str(out),
        ]

    def make_manifest(self, root: Path) -> Path:
        (root / "forward.txt").write_text("abc " * 30, encoding="utf-8")
        (root / "reverse.txt").write_text("cba " * 30, encoding="utf-8")
        path = root / "corpora.json"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "corpora": [
                        {"name": "forward", "path": "forward.txt", "weight": 9},
                        {"name": "reverse", "path": "reverse.txt", "weight": 1},
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_total_gain_retains_group_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            manifest = self.make_manifest(root)
            out = root / "report.json"
            self.assertEqual(evaluate.main(self.args(manifest, out)), 0)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertLess(report["weighted"]["delta_loss"], 0)
            self.assertGreater(report["macro"]["delta_loss"], 0)
            self.assertEqual(report["regressed_corpora"], ["reverse"])
            self.assertTrue(report["weighted_gain_with_regressions"])

    def test_grouped_matches_single_and_reorder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            manifest = self.make_manifest(root)
            output = root / "grouped.json"
            with patch.object(evaluate, "_load_model", wraps=evaluate._load_model) as loader:
                self.assertEqual(evaluate.main(self.args(manifest, output)), 0)
                self.assertEqual(loader.call_count, 2)
            grouped = json.loads(output.read_text(encoding="utf-8"))
            args = self.args(manifest, root / "single.json")
            index = args.index("--corpora")
            del args[index : index + 2]
            for group in grouped["corpora"]:
                self.assertEqual(evaluate.main(args + ["--data", group["report"]["data"]]), 0)
                single = json.loads((root / "single.json").read_text(encoding="utf-8"))
                self.assertEqual(single, group["report"])
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["corpora"].reverse()
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(evaluate.main(self.args(manifest, output)), 0)
            reversed_report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                {g["name"]: g["report"] for g in grouped["corpora"]},
                {g["name"]: g["report"] for g in reversed_report["corpora"]},
            )
            self.assertEqual(grouped["macro"], reversed_report["macro"])
            self.assertEqual(grouped["weighted"], reversed_report["weighted"])

    def test_aggregation_uses_nll_not_ppl(self) -> None:
        groups = []
        for name, before, after, weight in (("a", 2.0, 1.0, 9), ("b", 1.0, 4.0, 1)):
            groups.append(
                {
                    "name": name,
                    "weight": weight,
                    "report": {
                        "comparison": {
                            "baseline": loss_summary([before]),
                            "candidate": loss_summary([after]),
                            "delta_loss": after - before,
                        }
                    },
                }
            )
        report = aggregate_corpora(groups)
        self.assertAlmostEqual(report["macro"]["baseline"]["loss"], 1.5)
        self.assertAlmostEqual(report["macro"]["candidate"]["loss"], 2.5)
        self.assertAlmostEqual(report["weighted"]["baseline"]["loss"], 1.9)
        self.assertAlmostEqual(report["weighted"]["candidate"]["loss"], 1.3)
        self.assertAlmostEqual(report["weighted"]["candidate"]["perplexity"], math.exp(1.3))
        self.assertNotAlmostEqual(report["weighted"]["candidate"]["perplexity"], (9 * math.exp(1) + math.exp(4)) / 10)
        self.assertEqual(report["regressed_corpora"], ["b"])
        groups[0]["weight"], groups[1]["weight"] = 9e307, 1e307
        scaled = aggregate_corpora(groups)
        self.assertAlmostEqual(scaled["weighted"]["delta_loss"], report["weighted"]["delta_loss"])
        groups[0]["weight"] = 0
        with self.assertRaises(ValueError):
            aggregate_corpora(groups)
        with self.assertRaises(ValueError):
            aggregate_corpora([])

    def test_manifest_resolves_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_manifest(root)
            entries = load_corpora(manifest)
            self.assertEqual(entries[0].path, (root / "forward.txt").resolve())
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["corpora"][0].pop("weight")
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(load_corpora(manifest)[0].weight, 1.0)

    def test_invalid_manifest_rejected(self) -> None:
        good = {"name": "one", "path": "one.txt", "weight": 1}
        rows = [[], [None], [good | {"name": " "}], [good | {"path": 1}], [good | {"typo": 1}]]
        rows += [[good | {"weight": weight}] for weight in (True, 0, -1, "1", float("inf"), float("nan"), 10**400)]
        rows += [[good, good | {"path": "two.txt"}], [good, good | {"name": "two", "path": "./one.txt"}]]
        payloads = [None, [], {}, {"version": True, "corpora": [good]}, {"version": 1.0, "corpora": [good]}]
        payloads += [{"version": 1, "corpora": values} for values in rows]
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "corpora.json"
            for index, payload in enumerate(payloads):
                manifest.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(index=index), self.assertRaises(ValueError):
                    load_corpora(manifest)

    def test_failed_corpus_does_not_publish(self) -> None:
        for failure in ("short", "missing", "output_alias"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                manifest = self.make_manifest(root)
                if failure == "short":
                    (root / "reverse.txt").write_text("ab", encoding="utf-8")
                elif failure == "missing":
                    (root / "reverse.txt").unlink()
                output = root / "report.json" if failure != "output_alias" else manifest
                if failure != "output_alias":
                    output.write_bytes(b"keep original report")
                before = {p.name: p.read_bytes() for p in root.iterdir()}
                with self.assertRaises((ValueError, FileNotFoundError)):
                    evaluate.main(self.args(manifest, output))
                self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, before)

    def test_pair_required_and_labels_escaped(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --compare-with"):
            evaluate.main(["--corpora", "missing.json", "--device", "cpu"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            evaluate.parse_args(["--corpora", "groups.json", "--data", "data.txt"])
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            manifest = self.make_manifest(root)
            output = root / "grouped.json"
            self.assertEqual(evaluate.main(self.args(manifest, output)), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            report["corpora"][0]["name"] = "a|<b>`\nx"
            rendered = render_corpora(report)
            self.assertIn("a&#124;&lt;b&gt;&#96; x", rendered)
            self.assertIn("Weighted total improves", rendered)
            self.assertIn("reverse", rendered)
            self.assertIn("#### Largest regressions", rendered)

    def test_demo_replays_without_training(self) -> None:
        demo = self.demo.parents[2] / "1321/解释/demo"
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            output = Path(tmp) / "comparison.json"
            self.assertEqual(evaluate.main(self.args(demo / "corpora.json", output)), 0)
            actual = json.loads(output.read_text(encoding="utf-8"))
            expected = json.loads((demo / "comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(actual["regressed_corpora"], ["reverse"])
            self.assertTrue(actual["weighted_gain_with_regressions"])
            for mode in ("macro", "weighted"):
                for model in ("baseline", "candidate"):
                    self.assertAlmostEqual(actual[mode][model]["loss"], expected[mode][model]["loss"], delta=1e-5)
            for a, b in zip(actual["corpora"], expected["corpora"]):
                self.assertEqual(a["report"]["sampling"], b["report"]["sampling"])
                self.assertEqual(a["report"]["text_sha256"], b["report"]["text_sha256"])


if __name__ == "__main__":
    unittest.main()
