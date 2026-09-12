from __future__ import annotations

import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.rng_state import capture_rng_state, restore_rng_state, validate_rng_state
from scripts import train
from tests.model_cli_fixtures import make_tiny_checkpoint, tiny_resume_args

ensure_src_path()


class RngValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = capture_rng_state()
        self.addCleanup(restore_rng_state, self.original)

    def assert_cpu_equal(self, expected: dict) -> None:
        actual = capture_rng_state()
        self.assertEqual(expected["python"], actual["python"])
        self.assertEqual(expected["numpy"][0], actual["numpy"][0])
        np.testing.assert_array_equal(expected["numpy"][1], actual["numpy"][1])
        self.assertEqual(expected["numpy"][2:], actual["numpy"][2:])
        self.assertTrue(torch.equal(expected["torch_cpu"], actual["torch_cpu"]))

    def test_bad_numpy_leaves_globals_unchanged(self) -> None:
        state = capture_rng_state()
        state["python"] = random.Random(789).getstate()
        state["numpy"] = ("broken",)
        with self.assertRaises((ValueError, TypeError)):
            restore_rng_state(state)
        self.assert_cpu_equal(self.original)

    def test_bad_snapshot_preserves_run_files(self) -> None:
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            state = torch.load(checkpoint, map_location="cpu", weights_only=False)
            state["rng_state"]["version"] = 9
            torch.save(state, checkpoint)
            with (root / "metrics.jsonl").open("ab") as stream:
                stream.write(b"uncommitted suffix")
            before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            with self.assertRaisesRegex(ValueError, "RNG state version"):
                train.main(tiny_resume_args(checkpoint, data, 3))
            self.assertEqual({p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}, before)

    def test_invalid_matrix_preserves_globals(self) -> None:
        base = capture_rng_state()
        base["python"] = random.Random(987).getstate()
        base["numpy"] = np.random.RandomState(654).get_state()
        base["torch_cpu"] = torch.Generator().manual_seed(321).get_state()
        cases = [[], "bad", {}, base | {"version": True}, base | {"version": 1.0}]
        for field in ("python", "numpy", "torch_cpu", "cuda"):
            cases.append({key: value for key, value in base.items() if key != field})
        cases += [base | {"python": ()}, base | {"numpy": ("bad",)}]
        tensors = [
            None,
            [],
            torch.ones(5),
            torch.ones((2, 2), dtype=torch.uint8),
            torch.empty(0, dtype=torch.uint8),
            torch.zeros(2, dtype=torch.uint8),
        ]
        cases += [base | {"torch_cpu": value} for value in tensors]
        cases += [base | {"cuda": value} for value in ("bad", {}, [None], [torch.ones(3)])]
        for index, state in enumerate(cases):
            with self.subTest(case=index), self.assertRaisesRegex(ValueError, "RNG state"):
                restore_rng_state(state)
            self.assert_cpu_equal(self.original)

    def test_validation_is_pure_and_normalizes(self) -> None:
        state = capture_rng_state()
        before_cpu = state["torch_cpu"].clone()
        cuda_tensor = torch.tensor([1, 2], dtype=torch.uint8)
        state["cuda"] = (cuda_tensor,)
        with patch("torch.cuda.init") as init, patch("torch.cuda.is_initialized") as initialized:
            prepared = validate_rng_state(state)
        init.assert_not_called()
        initialized.assert_not_called()
        self.assertIsNot(prepared, state)
        self.assertIsInstance(state["cuda"], tuple)
        self.assertIsInstance(prepared["cuda"], list)
        self.assertEqual(prepared["torch_cpu"].device.type, "cpu")
        self.assertTrue(torch.equal(state["torch_cpu"], before_cpu))
        self.assertTrue(torch.equal(prepared["cuda"][0], cuda_tensor))
        self.assert_cpu_equal(self.original)
        self.assertIsNone(validate_rng_state(None))

    def test_cpu_probe_accepts_replayable_state(self) -> None:
        state = capture_rng_state()
        prepared = validate_rng_state(state)
        self.assertEqual(set(prepared), set(state))
        expected = (random.random(), np.random.rand(3), torch.rand(3))
        self.assertTrue(restore_rng_state(prepared))
        self.assertEqual(random.random(), expected[0])
        np.testing.assert_array_equal(np.random.rand(3), expected[1])
        self.assertTrue(torch.equal(torch.rand(3), expected[2]))

    def test_bad_rng_does_not_create_new_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
            saved["rng_state"] = capture_rng_state() | {"torch_cpu": torch.zeros(2, dtype=torch.uint8)}
            torch.save(saved, checkpoint)
            before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            with patch.object(train, "MiniGPT") as model, self.assertRaisesRegex(ValueError, "RNG state"):
                train.main(tiny_resume_args(checkpoint, data, 2) + ["--out-dir", str(root / "new")])
            model.assert_not_called()
            self.assertFalse((root / "new").exists())
            self.assertEqual({p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
