from __future__ import annotations

import random
import unittest
from unittest import mock

import numpy as np
import torch

from minigpt.script_runtime import choose_device, seed_everything


class ChooseDeviceTests(unittest.TestCase):
    def test_cpu_is_returned_verbatim(self) -> None:
        self.assertEqual(choose_device("cpu"), torch.device("cpu"))

    def test_auto_returns_a_valid_device(self) -> None:
        device = choose_device("auto")
        self.assertIsInstance(device, torch.device)
        self.assertIn(device.type, {"cpu", "cuda"})

    def test_auto_picks_cpu_when_cuda_absent(self) -> None:
        with mock.patch.object(torch.cuda, "is_available", return_value=False):
            self.assertEqual(choose_device("auto"), torch.device("cpu"))

    def test_cuda_requested_but_absent_raises_systemexit(self) -> None:
        # Matches the v1156-v1162 contract: a clean CLI error, not a traceback.
        with mock.patch.object(torch.cuda, "is_available", return_value=False):
            with self.assertRaises(SystemExit):
                choose_device("cuda")


class SeedEverythingTests(unittest.TestCase):
    def test_seeds_torch_numpy_and_random_reproducibly(self) -> None:
        seed_everything(1234)
        t1, n1, r1 = torch.rand(4), np.random.rand(4), [random.random() for _ in range(4)]
        seed_everything(1234)
        t2, n2, r2 = torch.rand(4), np.random.rand(4), [random.random() for _ in range(4)]
        self.assertTrue(torch.equal(t1, t2))
        self.assertTrue(np.allclose(n1, n2))
        self.assertEqual(r1, r2)

    def test_different_seeds_differ(self) -> None:
        seed_everything(1)
        a = torch.rand(8)
        seed_everything(2)
        b = torch.rand(8)
        self.assertFalse(torch.equal(a, b))


if __name__ == "__main__":
    unittest.main()
