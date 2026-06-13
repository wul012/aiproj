from __future__ import annotations

import unittest

import torch

from minigpt.lora_domain_adaptation_v1158 import DomainAdaptationConfig, run_lora_domain_adaptation
from minigpt.model import GPTConfig, MiniGPT
from minigpt.templated_corpus import build_templated_corpus
from minigpt.tokenizer import CharTokenizer


class StructureVocabTests(unittest.TestCase):
    def test_structures_share_identical_vocabulary(self) -> None:
        a = build_templated_corpus(seed=0, structure="declarative", max_sentences=200)
        b = build_templated_corpus(seed=0, structure="reordered", max_sentences=200)
        # Same term pools + same punctuation -> identical character vocabulary.
        self.assertEqual(set(a.full_text), set(b.full_text))
        # ...but different word order -> different text.
        self.assertNotEqual(a.train_sentences[0], b.train_sentences[0])

    def test_unknown_structure_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_templated_corpus(structure="nope")


def _setup():
    torch.manual_seed(0)
    src = build_templated_corpus(seed=0, heldout_ratio=0.2, max_sentences=200, structure="declarative")
    tgt = build_templated_corpus(seed=0, heldout_ratio=0.2, max_sentences=200, structure="reordered")
    tok = CharTokenizer.train(src.full_text + tgt.full_text)
    enc = lambda t: torch.tensor(tok.encode(t), dtype=torch.long)  # noqa: E731
    cfg = GPTConfig(vocab_size=tok.vocab_size, block_size=24, n_layer=2, n_head=2, n_embd=32, dropout=0.0)
    model = MiniGPT(cfg)
    return model, enc(src.train_text), enc(src.heldout_text), enc(tgt.train_text), enc(tgt.heldout_text)


class DomainAdaptationTests(unittest.TestCase):
    def test_lora_adapts_to_target_domain(self) -> None:
        model, s_train, s_hold, t_train, t_hold = _setup()
        cfg = DomainAdaptationConfig(
            base_steps=300, base_lr=3e-4, adapt_steps=300, adapt_lr=3e-3,
            block_size=24, batch_size=16, r=8, alpha=16.0, seed=0,
        )
        report = run_lora_domain_adaptation(
            model, s_train, s_hold, t_train, t_hold, config=cfg, device=torch.device("cpu"),
            generated_at="2026-06-13T00:00:00Z",
        )
        s = report["summary"]
        # A real structural domain gap exists: base is worse on B than on A.
        self.assertGreater(s["domain_gap"], 0.1, s)
        # LoRA closes much of it on B's held-out, training only a small fraction of params.
        self.assertLess(s["lora_target_loss_delta"], -0.05, s)
        self.assertTrue(s["domain_adaptation_succeeded"], s)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "lora_domain_adaptation_succeeded")
        self.assertLess(s["trainable_ratio_percent"], 50.0)

    def test_report_shape(self) -> None:
        model, s_train, s_hold, t_train, t_hold = _setup()
        cfg = DomainAdaptationConfig(base_steps=5, adapt_steps=5, block_size=24, batch_size=8, seed=0)
        report = run_lora_domain_adaptation(
            model, s_train, s_hold, t_train, t_hold, config=cfg, device=torch.device("cpu")
        )
        self.assertEqual(len(report["rows"]), 5)
        for key in ("domain_gap", "lora_target_heldout_loss", "lora_vs_full_capture_ratio", "adapter_forgetting_on_source"):
            self.assertIn(key, report["summary"])
        self.assertEqual(report["csv_fieldnames"], ["arm", "domain", "heldout_loss", "heldout_token_accuracy"])


if __name__ == "__main__":
    unittest.main()
