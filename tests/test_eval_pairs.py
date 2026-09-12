from __future__ import annotations

import contextlib
import io
import json
import math
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from tests._bootstrap import ensure_src_path

from minigpt.core.model import GPTConfig, MiniGPT
from minigpt.core.tokenizer import CharTokenizer
from minigpt.evaluation.windows import make_plan, score_windows, select_split
from minigpt.evaluation.paired import loss_summary, pair_results
from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from scripts import evaluate
from tests.model_cli_fixtures import make_tiny_checkpoint

ensure_src_path()


class EvalPairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)

    def test_windows_do_not_depend_on_width(self) -> None:
        traces = []
        for width in (8, 16):
            torch.manual_seed(1337)
            model = MiniGPT(GPTConfig(vocab_size=40, block_size=8, n_layer=1, n_head=2, n_embd=width))
            inputs = []
            forward = model.forward

            def trace(x, targets=None):
                inputs.extend(x.tolist())
                return forward(x, targets)

            with patch.object(model, "forward", side_effect=trace):
                evaluate.estimate_loss(model, torch.arange(40), 8, 4, 2, torch.device("cpu"))
            traces.append(inputs)
        self.assertEqual(traces[0], traces[1])

    def test_plan_is_unique_pure_and_replayable(self) -> None:
        torch_state, python_state = torch.get_rng_state(), random.getstate()
        plan = make_plan(20, 8, 100, 42)
        self.assertEqual(set(plan.starts), set(range(12)))
        self.assertEqual(len(plan.starts), 12)
        self.assertEqual(plan, make_plan(20, 8, 100, 42))
        self.assertNotEqual(plan.starts, make_plan(20, 8, 100, 43).starts)
        self.assertTrue(torch.equal(torch_state, torch.get_rng_state()))
        self.assertEqual(python_state, random.getstate())
        self.assertEqual(make_plan(9, 8, 3, 0).starts, (0,))
        for sizes in ((8, 8, 1), (9, 0, 1), (9, 8, 0)):
            with self.subTest(sizes=sizes), self.assertRaises(ValueError):
                make_plan(*sizes, 1)

    def test_metric_matches_manual_oracle(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=9, block_size=4, n_layer=1, n_head=1, n_embd=8, dropout=0.5))
        data = torch.arange(13) % 9
        plan = make_plan(len(data), 4, 7, 11)
        model.eval()
        manual = []
        with torch.no_grad():
            for start in plan.starts:
                x, y = data[start : start + 4], data[start + 1 : start + 5]
                logits, _ = model(x.unsqueeze(0))
                terms = [-torch.log_softmax(logits[0, i], dim=-1)[target].item() for i, target in enumerate(y)]
                manual.append(sum(terms) / 4)
        model.train()
        before = torch.get_rng_state()
        actual = score_windows(model, data, plan, 3, torch.device("cpu"))
        self.assertTrue(model.training)
        self.assertTrue(torch.equal(before, torch.get_rng_state()))
        for expected, value in zip(manual, actual):
            self.assertAlmostEqual(expected, value, places=6)
        regrouped = score_windows(model, data, plan, 1, torch.device("cpu"))
        torch.testing.assert_close(torch.tensor(actual), torch.tensor(regrouped), atol=1e-6, rtol=1e-6)

    def test_uniform_logits_have_known_loss(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=5, block_size=3, n_layer=1, n_head=1, n_embd=4))
        for parameter in model.parameters():
            parameter.data.zero_()
        data = torch.arange(9) % 5
        losses = score_windows(model, data, make_plan(9, 3, 4, 1), 3, torch.device("cpu"))
        self.assertAlmostEqual(loss_summary(losses)["loss"], math.log(5), places=6)
        self.assertAlmostEqual(loss_summary(losses)["perplexity"], 5, places=5)
        self.assertIsNone(loss_summary([1000.0])["perplexity"])
        for values in ([], [float("nan")], [float("inf")]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                loss_summary(values)

    def test_pair_sign_ranking_and_self_tie(self) -> None:
        tokenizer = CharTokenizer.train("abcdef")
        data = torch.tensor(tokenizer.encode("abcdefabcdef"))
        plan = make_plan(len(data), 3, 3, 1)
        a, b = [1.0, 2.0, 3.0], [0.5, 2.0, 4.0]
        report = pair_results(a, b, plan, data, tokenizer, 7)
        swapped = pair_results(b, a, plan, data, tokenizer, 7)
        self.assertAlmostEqual(report["delta_loss"], -swapped["delta_loss"])
        self.assertEqual((report["improved_windows"], report["regressed_windows"], report["tied_windows"]), (1, 1, 1))
        self.assertEqual(report["largest_improvements"][0]["start_token"], plan.starts[0] + 7)
        self.assertEqual(report["largest_regressions"][0]["delta"], 1.0)
        self.assertEqual(
            report["windows"][0]["target_preview"],
            tokenizer.decode(data[plan.starts[0] + 1 : plan.starts[0] + 4].tolist()),
        )
        self.assertEqual(pair_results(a, a, plan, data, tokenizer, 0)["delta_loss"], 0)
        with self.assertRaises(ValueError):
            pair_results(a, b[:1], plan, data, tokenizer, 0)

    def test_real_cli_self_pair_and_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            output = root / "pair.json"
            args = [
                "--checkpoint",
                str(checkpoint),
                "--compare-with",
                str(checkpoint),
                "--data",
                str(data),
                "--split",
                "all",
                "--windows",
                "7",
                "--batch-size",
                "3",
                "--device",
                "cpu",
                "--out",
                str(output),
            ]
            before = checkpoint.read_bytes()
            self.assertEqual(evaluate.main(args), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["comparison"]["delta_loss"], 0)
            self.assertEqual(report["comparison"]["tied_windows"], 7)
            self.assertEqual(report["checkpoint_sha256"], report["candidate_sha256"])
            self.assertEqual(report["evaluated_tokens"], 56)
            self.assertIn("Largest regressions", output.with_suffix(".md").read_text(encoding="utf-8"))
            original = output.read_bytes()
            torch.rand(100)
            self.assertEqual(evaluate.main(args), 0)
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(checkpoint.read_bytes(), before)

    def test_cli_common_context_and_tokenizer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, tokenizer_path, data, _ = make_tiny_checkpoint(root)
            candidate = root / "candidate.pt"
            saved = torch.load(checkpoint, weights_only=False)
            config = GPTConfig(**saved["config"])
            config.n_embd, config.block_size = 16, 12
            model = MiniGPT(config)
            torch.save({"config": config.__dict__, "model": model.state_dict()}, candidate)
            output = root / "pair.json"
            args = [
                "--checkpoint",
                str(checkpoint),
                "--compare-with",
                str(candidate),
                "--data",
                str(data),
                "--split",
                "all",
                "--windows",
                "5",
                "--device",
                "cpu",
                "--out",
                str(output),
            ]
            traces = {8: [], 16: []}
            forward = MiniGPT.forward

            def trace(instance, x, targets=None):
                traces[instance.config.n_embd].extend(x.tolist())
                return forward(instance, x, targets)

            with patch.object(MiniGPT, "forward", new=trace):
                self.assertEqual(evaluate.main(args), 0)
            self.assertEqual(traces[8], traces[16])
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["block_size"], 8)
            self.assertEqual(len(report["comparison"]["windows"]), 5)
            with self.assertRaisesRegex(ValueError, "Context size"):
                evaluate.main(args + ["--context-size", "9"])
            payload = json.loads(tokenizer_path.read_text(encoding="utf-8"))
            payload["itos"][1:3] = reversed(payload["itos"][1:3])
            wrong = root / "wrong.json"
            wrong.write_text(json.dumps(payload), encoding="utf-8")
            previous = output.read_bytes()
            with self.assertRaisesRegex(ValueError, "identical tokenizer"):
                evaluate.main(args + ["--candidate-tokenizer", str(wrong)])
            self.assertEqual(output.read_bytes(), previous)

    def test_no_validation_training_fallback(self) -> None:
        data, offset = select_split(list(range(20)), "val", 0.99)
        self.assertEqual(offset, 19)
        self.assertEqual(data.tolist(), [19])
        with self.assertRaisesRegex(ValueError, "Evaluation split"):
            make_plan(len(data), 8, 3, 0)
        with self.assertRaises(ValueError):
            select_split([1, 2], "val", float("nan"))

    def test_nonfinite_restores_model_mode(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=4, block_size=3, n_layer=1, n_head=1, n_embd=4))
        plan = make_plan(8, 3, 2, 0)
        with patch.object(model, "forward", return_value=(torch.full((2, 3, 4), float("nan")), None)):
            with self.assertRaisesRegex(ValueError, "Non-finite"):
                score_windows(model, torch.arange(8) % 4, plan, 2, torch.device("cpu"))
        self.assertTrue(model.training)

    def test_invalid_cli_leaves_inputs_intact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            args = [
                "--checkpoint",
                str(checkpoint),
                "--compare-with",
                str(checkpoint),
                "--data",
                str(data),
                "--device",
                "cpu",
                "--windows",
                "4",
                "--out",
                str(root / "new/pair.json"),
            ]
            before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            cases = [
                ["--windows", "0"],
                ["--batch-size", "0"],
                ["--context-size", "0"],
                ["--train-ratio", "0.999"],
                ["--out", str(checkpoint)],
                ["--out", str(root / "same.md")],
            ]
            for extra in cases:
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    evaluate.main(args + extra)
                self.assertEqual({p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}, before)
                self.assertFalse((root / "new").exists())

    def test_demo_replays_both_directions(self) -> None:
        demo = Path(__file__).resolve().parents[1] / "f/1320/解释/demo"
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            output = Path(tmp) / "comparison.json"
            args = [
                "--checkpoint",
                str(demo / "baseline.pt"),
                "--compare-with",
                str(demo / "candidate.pt"),
                "--data",
                str(demo / "eval.txt"),
                "--split",
                "all",
                "--windows",
                "64",
                "--batch-size",
                "8",
                "--device",
                "cpu",
                "--out",
                str(output),
            ]
            self.assertEqual(evaluate.main(args), 0)
            actual = json.loads(output.read_text(encoding="utf-8"))
            expected = json.loads((demo / "comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(actual["sampling"], expected["sampling"])
            result = actual["comparison"]
            self.assertEqual(result["improved_windows"], 28)
            self.assertEqual(result["regressed_windows"], 36)
            self.assertGreater(result["delta_loss"], 0)
            for name in ("baseline", "candidate"):
                self.assertAlmostEqual(result[name]["loss"], expected["comparison"][name]["loss"], delta=1e-5)
            self.assertIn("abc", result["largest_improvements"][0]["target_preview"])
            self.assertIn("cba", result["largest_regressions"][0]["target_preview"])


if __name__ == "__main__":
    unittest.main()
