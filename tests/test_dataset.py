from __future__ import annotations

import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset import get_batch, split_token_ids


class DatasetTests(unittest.TestCase):
    def test_split_token_ids_keeps_validation_non_empty(self) -> None:
        train_data, val_data = split_token_ids([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], train_ratio=0.8)

        self.assertEqual(train_data.tolist(), [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(val_data.tolist(), [9, 10])

    def test_get_batch_returns_shifted_targets(self) -> None:
        torch.manual_seed(1)
        data = torch.arange(20, dtype=torch.long)

        x, y = get_batch(data, block_size=4, batch_size=3, device=torch.device("cpu"))

        self.assertEqual(tuple(x.shape), (3, 4))
        self.assertEqual(tuple(y.shape), (3, 4))
        self.assertTrue(torch.equal(y[:, :-1], x[:, 1:]))

    def test_get_batch_rejects_too_short_data(self) -> None:
        with self.assertRaises(ValueError):
            get_batch(torch.tensor([1, 2, 3]), block_size=3, batch_size=1, device=torch.device("cpu"))


if __name__ == "__main__":
    unittest.main()
