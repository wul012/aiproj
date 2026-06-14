from __future__ import annotations

import math
import unittest
from dataclasses import dataclass

import torch

from minigpt.experiment_utils import build_minigpt, clone_state, mean_std
from minigpt.model import MiniGPT


@dataclass
class _Cfg:
    block_size: int = 16
    n_layer: int = 2
    n_head: int = 2
    n_embd: int = 16
    use_rope: bool = True


class MeanStdTests(unittest.TestCase):
    def test_basic_mean_and_sample_std(self) -> None:
        m, s = mean_std([1.0, 2.0, 3.0])
        self.assertAlmostEqual(m, 2.0)
        self.assertAlmostEqual(s, 1.0)  # sample stdev of 1,2,3

    def test_single_value_zero_std(self) -> None:
        m, s = mean_std([5.0])
        self.assertEqual((m, s), (5.0, 0.0))

    def test_empty_is_nan_zero(self) -> None:
        m, s = mean_std([])
        self.assertTrue(math.isnan(m))
        self.assertEqual(s, 0.0)

    def test_ignores_none_and_nan(self) -> None:
        m, s = mean_std([1.0, None, float("nan"), 3.0])
        self.assertAlmostEqual(m, 2.0)  # only 1.0 and 3.0 survive
        self.assertAlmostEqual(s, math.sqrt(2.0))


class BuildMiniGptTests(unittest.TestCase):
    def test_builds_with_config_fields(self) -> None:
        model = build_minigpt(13, _Cfg())
        self.assertIsInstance(model, MiniGPT)
        self.assertEqual(model.config.vocab_size, 13)
        self.assertEqual(model.config.block_size, 16)
        self.assertEqual(model.config.n_layer, 2)
        self.assertTrue(model.config.use_rope)
        self.assertEqual(model.config.dropout, 0.0)

    def test_deterministic_given_seed(self) -> None:
        torch.manual_seed(123)
        a = build_minigpt(13, _Cfg())
        torch.manual_seed(123)
        b = build_minigpt(13, _Cfg())
        for ka, va in a.state_dict().items():
            self.assertTrue(torch.equal(va, b.state_dict()[ka]), ka)


class CloneStateTests(unittest.TestCase):
    def test_independent_equal_copy(self) -> None:
        model = build_minigpt(13, _Cfg())
        snap = clone_state(model)
        # equal values now
        for k, v in model.state_dict().items():
            self.assertTrue(torch.equal(v, snap[k]))
        # but an independent copy: mutating the live weights does not change the snapshot
        with torch.no_grad():
            for p in model.parameters():
                p.add_(1.0)
        changed = any(not torch.equal(v, snap[k]) for k, v in model.state_dict().items())
        self.assertTrue(changed)


if __name__ == "__main__":
    unittest.main()
