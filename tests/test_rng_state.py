from __future__ import annotations

import io
import random
import unittest
from unittest.mock import patch

import numpy as np
import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.rng_state import capture_rng_state, restore_rng_state

ensure_src_path()


class RngStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = capture_rng_state()

    def tearDown(self) -> None:
        restore_rng_state(self.original)

    def test_restores_all_cpu_generators(self) -> None:
        random.seed(11)
        np.random.seed(12)
        torch.manual_seed(13)
        saved = capture_rng_state()
        expected = (random.random(), np.random.rand(4), torch.rand(4))
        self.assertTrue(restore_rng_state(saved))
        self.assertEqual(random.random(), expected[0])
        np.testing.assert_array_equal(np.random.rand(4), expected[1])
        self.assertTrue(torch.equal(torch.rand(4), expected[2]))

    def test_serialized_state_roundtrips(self) -> None:
        state = capture_rng_state()
        buffer = io.BytesIO()
        torch.save({"rng_state": state}, buffer)
        expected = torch.rand(4)
        buffer.seek(0)
        loaded = torch.load(buffer, map_location="cpu", weights_only=False)
        restore_rng_state(loaded["rng_state"])
        self.assertTrue(torch.equal(torch.rand(4), expected))

    def test_capture_does_not_advance_rng(self) -> None:
        first = capture_rng_state()
        second = capture_rng_state()
        self.assertEqual(first["python"], second["python"])
        self.assertEqual(first["numpy"][0], second["numpy"][0])
        np.testing.assert_array_equal(first["numpy"][1], second["numpy"][1])
        self.assertEqual(first["numpy"][2:], second["numpy"][2:])
        self.assertTrue(torch.equal(first["torch_cpu"], second["torch_cpu"]))

    def test_legacy_is_noop(self) -> None:
        before = capture_rng_state()
        self.assertFalse(restore_rng_state(None))
        after = capture_rng_state()
        self.assertEqual(before["python"], after["python"])
        np.testing.assert_array_equal(before["numpy"][1], after["numpy"][1])
        self.assertTrue(torch.equal(before["torch_cpu"], after["torch_cpu"]))

    def test_rejects_unknown_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "RNG state version"):
            restore_rng_state({"version": 9})

    def test_cpu_snapshot_does_not_init_cuda(self) -> None:
        with patch("torch.cuda.is_initialized", return_value=False), patch("torch.cuda.get_rng_state_all") as get:
            state = capture_rng_state()
        self.assertIsNone(state["cuda"])
        get.assert_not_called()

    def test_initialized_cuda_state_is_restored(self) -> None:
        states = [torch.tensor([1, 2], dtype=torch.uint8)]
        with (
            patch("torch.cuda.is_initialized", return_value=True),
            patch("torch.cuda.get_rng_state_all", return_value=states),
            patch("torch.cuda.set_rng_state_all") as put,
        ):
            state = capture_rng_state()
            self.assertEqual(len(state["cuda"]), 1)
            restore_rng_state(state)
            self.assertTrue(torch.equal(put.call_args.args[0][0], states[0]))

    def test_cuda_snapshot_on_cpu_skips_cuda(self) -> None:
        state = capture_rng_state()
        state["cuda"] = [torch.tensor([1], dtype=torch.uint8)]
        with patch("torch.cuda.is_initialized", return_value=False), patch("torch.cuda.set_rng_state_all") as put:
            self.assertTrue(restore_rng_state(state))
        put.assert_not_called()


if __name__ == "__main__":
    unittest.main()
