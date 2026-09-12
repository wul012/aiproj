from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from minigpt.training.preflight import validate_options, validate_splits
from scripts import train
from tests.model_cli_fixtures import make_tiny_checkpoint, tiny_resume_args

ensure_src_path()


def inventory(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class TrainPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)

    def fresh_args(self, data: Path, out: Path) -> list[str]:
        return [
            "--data",
            str(data),
            "--out-dir",
            str(out),
            "--device",
            "cpu",
            "--batch-size",
            "2",
            "--block-size",
            "8",
            "--n-layer",
            "1",
            "--n-head",
            "2",
            "--n-embd",
            "8",
            "--dropout",
            "0.2",
            "--max-iters",
            "2",
            "--eval-iters",
            "1",
            "--eval-interval",
            "1",
            "--train-ratio",
            "0.5",
            "--sample-prompt",
            "abc",
            "--sample-tokens",
            "1",
        ]

    def test_bad_eval_preserves_old_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdef " * 20, encoding="utf-8")
            out = root / "run"
            out.mkdir()
            (out / "metrics.jsonl").write_bytes(b"keep original metrics\n")
            (out / "checkpoint.pt").write_bytes(b"keep original checkpoint")
            before = inventory(root)
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                train.main(self.fresh_args(data, out) + ["--eval-iters", "0", "--no-sample"])
            self.assertEqual(inventory(root), before)

    def test_small_split_preserves_old_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdefghij" * 2, encoding="utf-8")
            out = root / "run"
            out.mkdir()
            (out / "metrics.jsonl").write_bytes(b"keep history\n")
            before = inventory(root)
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                train.main(self.fresh_args(data, out) + ["--train-ratio", "0.9", "--no-sample"])
            self.assertEqual(inventory(root), before)

    def test_option_errors_before_read_or_seed(self) -> None:
        cases = [
            ("batch-size", "0"),
            ("batch-size", "-2"),
            ("max-iters", "0"),
            ("eval-interval", "0"),
            ("eval-iters", "-1"),
            ("learning-rate", "-1"),
            ("train-ratio", "0"),
            ("train-ratio", "1"),
            ("seed", "-1"),
            ("seed", "4294967296"),
            ("block-size", "0"),
            ("n-layer", "-1"),
            ("n-head", "0"),
            ("n-embd", "0"),
            ("n-embd", "7"),
            ("dropout", "-0.1"),
            ("dropout", "1.1"),
            ("sample-tokens", "-1"),
            ("sample-temperature", "0"),
            ("sample-top-k", "0"),
            ("sample-prompt", ""),
        ]
        cases += [
            (name, value)
            for name in ("learning-rate", "train-ratio", "dropout", "sample-temperature")
            for value in ("nan", "inf", "-inf")
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, value in cases:
                with self.subTest(option=name, value=value), patch.object(train, "load_training_text") as read:
                    with patch.object(train.torch, "manual_seed") as seed:
                        with self.assertRaisesRegex(ValueError, "--" + name):
                            train.main(self.fresh_args(root / "missing.txt", root / "out") + [f"--{name}={value}"])
                        read.assert_not_called()
                        seed.assert_not_called()
                    self.assertEqual(inventory(root), {})

    def test_late_sample_errors_are_now_early(self) -> None:
        for option in (["--sample-temperature", "0"], ["--sample-top-k", "0"], ["--sample-prompt", ""]):
            with self.subTest(option=option), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                data = root / "data.txt"
                data.write_text("abcdef " * 20, encoding="utf-8")
                out = root / "run"
                out.mkdir()
                (out / "metrics.jsonl").write_bytes(b"original metrics")
                before = inventory(root)
                with self.assertRaises(ValueError):
                    train.main(self.fresh_args(data, out) + option)
                self.assertEqual(inventory(root), before)

    def test_invalid_resume_leaves_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            with (root / "metrics.jsonl").open("ab") as stream:
                stream.write(b"uncommitted suffix")
            for option in (["--eval-iters", "0"], ["--train-ratio", "0.9"]):
                before = inventory(root)
                with self.subTest(option=option), self.assertRaises(ValueError):
                    train.main(tiny_resume_args(checkpoint, data, 3) + option)
                self.assertEqual(inventory(root), before)

    def test_resume_uses_effective_model_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            args = tiny_resume_args(checkpoint, data, 2) + [
                "--block-size",
                "1000000",
                "--n-head",
                "0",
                "--dropout",
                "nan",
                "--tokenizer",
                "bpe",
                "--bpe-vocab-size",
                "0",
                "--sample-temperature",
                "nan",
                "--sample-tokens",
                "-1",
                "--sample-top-k",
                "-1",
                "--sample-prompt",
                "",
            ]
            self.assertEqual(train.main(args), 0)
            loaded, _, config = train.load_resume_state(checkpoint, torch.device("cpu"))
            self.assertEqual(config.block_size, 8)
            self.assertEqual(loaded["step"], 2)

    def test_active_bpe_settings_only(self) -> None:
        for option in (["--bpe-vocab-size", "1"], ["--bpe-min-frequency", "0"]):
            with self.subTest(option=option), self.assertRaisesRegex(ValueError, "--bpe"):
                validate_options(train.parse_args(["--tokenizer", "bpe", *option]))
            validate_options(train.parse_args(["--tokenizer", "char", *option]))

    def test_existing_zero_boundaries_still_work(self) -> None:
        validate_options(train.parse_args(["--learning-rate", "0", "--n-layer", "0", "--dropout", "1"]))
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdef " * 20, encoding="utf-8")
            args = self.fresh_args(data, root / "run") + [
                "--learning-rate",
                "0",
                "--sample-tokens",
                "0",
                "--sample-top-k",
                "0",
                "--sample-prompt",
                "",
            ]
            self.assertEqual(train.main(args), 0)
            self.assertTrue((root / "run/sample.txt").exists())
            config = json.loads((root / "run/train_config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["learning_rate"], 0)

    def test_split_minimum_does_not_consume_rng(self) -> None:
        state = torch.get_rng_state()
        for train_size, val_size, block_size in ((9, 10, 8), (10, 9, 8), (10, 10, 0)):
            with self.subTest(sizes=(train_size, val_size, block_size)), self.assertRaises(ValueError):
                validate_splits(train_size, val_size, block_size)
        validate_splits(10, 10, 8)
        self.assertTrue(torch.equal(state, torch.get_rng_state()))


if __name__ == "__main__":
    unittest.main()
