from __future__ import annotations

import unittest

import torch

from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_corpus import PAD, build_sft_corpus
from minigpt.sft_training import IGNORE_INDEX, train_sft
from minigpt.tokenizer import CharTokenizer


def _setup():
    corpus = build_sft_corpus(seed=0, ops=("C", "R"), lengths=(3,), inputs_per_op_length=40)
    tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    examples = [(tok.encode(e.text), len(e.prompt)) for e in corpus.train]
    pad_id = tok.encode(PAD)[0]
    return tok, examples, pad_id


class TrainSftTests(unittest.TestCase):
    def test_reduces_loss_completion_only(self) -> None:
        tok, examples, pad_id = _setup()
        torch.manual_seed(0)
        model = MiniGPT(GPTConfig(vocab_size=tok.vocab_size, block_size=16, n_layer=2, n_head=2, n_embd=32, dropout=0.0))
        before = train_sft(model, examples, steps=1, lr=3e-3, batch_size=16, block_size=16,
                           device=torch.device("cpu"), pad_id=pad_id, mask_prompt=True)
        after = train_sft(model, examples, steps=120, lr=3e-3, batch_size=16, block_size=16,
                          device=torch.device("cpu"), pad_id=pad_id, mask_prompt=True)
        self.assertIsInstance(after, float)
        self.assertLess(after, before)

    def test_both_mask_modes_run(self) -> None:
        tok, examples, pad_id = _setup()
        torch.manual_seed(0)
        model = MiniGPT(GPTConfig(vocab_size=tok.vocab_size, block_size=16, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        full = train_sft(model, examples, steps=5, lr=1e-3, batch_size=8, block_size=16,
                         device=torch.device("cpu"), pad_id=pad_id, mask_prompt=False)
        self.assertIsInstance(full, float)
        self.assertEqual(IGNORE_INDEX, -100)

    def test_rejects_block_size_too_small(self) -> None:
        tok, examples, pad_id = _setup()
        model = MiniGPT(GPTConfig(vocab_size=tok.vocab_size, block_size=4, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        with self.assertRaises(ValueError):
            train_sft(model, examples, steps=1, lr=1e-3, batch_size=4, block_size=4,
                      device=torch.device("cpu"), pad_id=pad_id)


if __name__ == "__main__":
    unittest.main()
