from __future__ import annotations

import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from tests._bootstrap import ensure_src_path

from scripts import train

ensure_src_path()


class ResumeRngTests(unittest.TestCase):
    def setUp(self) -> None:
        self.states = (random.getstate(), np.random.get_state(), torch.get_rng_state())
        self.threads = torch.get_num_threads()
        torch.set_num_threads(1)

    def tearDown(self) -> None:
        random.setstate(self.states[0])
        np.random.set_state(self.states[1])
        torch.set_rng_state(self.states[2])
        torch.set_num_threads(self.threads)

    def run_train(self, root: Path, data: Path, steps: int, resume: bool = False) -> dict:
        args = [
            "--data",
            str(data),
            "--out-dir",
            str(root),
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
            "--seed",
            "73",
            "--max-iters",
            str(steps),
            "--eval-interval",
            "2",
            "--eval-iters",
            "2",
            "--sample-prompt",
            "abc",
            "--sample-tokens",
            "3",
            "--sample-top-k",
            "4",
        ]
        if resume:
            args += ["--resume", str(root / "checkpoint.pt")]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(train.main(args), 0)
        return torch.load(root / "checkpoint.pt", map_location="cpu", weights_only=False)

    def assert_nested_equal(self, left: object, right: object) -> None:
        if isinstance(left, torch.Tensor):
            self.assertIsInstance(right, torch.Tensor)
            self.assertTrue(torch.equal(left, right), "tensor mismatch after resumed training")
        elif isinstance(left, dict):
            self.assertEqual(left.keys(), right.keys())
            for key in left:
                self.assert_nested_equal(left[key], right[key])
        elif isinstance(left, (list, tuple)):
            self.assertEqual(len(left), len(right))
            for a, b in zip(left, right):
                self.assert_nested_equal(a, b)
        else:
            self.assertEqual(left, right)

    def test_resumed_training_matches_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdefghijklmnopqrstuvwxyz " * 20, encoding="utf-8")
            full = self.run_train(root / "full", data, 6)
            for stop in (1, 2, 3, 5):
                with self.subTest(stop=stop):
                    split = root / f"split-{stop}"
                    self.run_train(split, data, stop)
                    resumed = self.run_train(split, data, 6, resume=True)
                    self.assertEqual(resumed["step"], 6)
                    self.assert_nested_equal(full["model"], resumed["model"])
                    self.assert_nested_equal(full["optimizer"], resumed["optimizer"])
                    self.assertEqual(full["last_loss"], resumed["last_loss"])
                    self.assertEqual((root / "full/sample.txt").read_bytes(), (split / "sample.txt").read_bytes())

    def test_old_checkpoint_remains_loadable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdefghijklmnopqrstuvwxyz " * 20, encoding="utf-8")
            run = root / "legacy"
            checkpoint = self.run_train(run, data, 2)
            checkpoint.pop("rng_state", None)
            torch.save(checkpoint, run / "checkpoint.pt")
            restored = self.run_train(run, data, 4, resume=True)
            self.assertEqual(restored["step"], 4)
            self.assertEqual(restored["config"], checkpoint["config"])
            self.assertTrue((run / "run_manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
