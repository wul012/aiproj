from __future__ import annotations

import unittest

import torch

from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.sft_instruction_v1164 import (
    SftInstructionConfig,
    evaluate_instructions,
    run_sft_instruction,
)
from minigpt.tokenizer import CharTokenizer


def _encode(ops, lengths, seed=0, inputs_per_op_length=60):
    corpus = build_sft_corpus(seed=seed, ops=ops, lengths=lengths, inputs_per_op_length=inputs_per_op_length)
    tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    train = [(tok.encode(e.text), len(e.prompt)) for e in corpus.train]
    heldout = [(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout]
    return tok, train, heldout, tok.encode(PAD)[0], tok.encode(EOS)[0], corpus


class EvaluateInstructionsTests(unittest.TestCase):
    def test_returns_accuracy_in_range(self) -> None:
        tok, _, heldout, _, eos_id, _ = _encode(("C", "R"), (3,))
        torch.manual_seed(0)
        model = MiniGPT(GPTConfig(vocab_size=tok.vocab_size, block_size=16, n_layer=1, n_head=2, n_embd=16, dropout=0.0, use_rope=True))
        m = evaluate_instructions(model, heldout, eos_id=eos_id, max_new_tokens=6, device=torch.device("cpu"))
        self.assertGreaterEqual(m["overall_accuracy"], 0.0)
        self.assertLessEqual(m["overall_accuracy"], 1.0)
        self.assertEqual(set(m["accuracy_by_op"]), {"C", "R"})
        self.assertEqual(m["count"], len(heldout))


class RunSftInstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ops = ("C", "R")
        tok, train, heldout, pad_id, eos_id, corpus = _encode(ops, (2, 3), inputs_per_op_length=80)
        cfg = SftInstructionConfig(
            block_size=16, seeds=(1337, 1338), arms=("completion_only", "full_loss"),
            step_schedule=(20, 40), lr=3e-3, batch_size=32, n_layer=1, n_head=2, n_embd=32, max_new_tokens=5,
        )
        cls.report = run_sft_instruction(
            vocab_size=tok.vocab_size, train_examples=train, heldout=heldout, ops=ops,
            pad_id=pad_id, eos_id=eos_id, config=cfg, device=torch.device("cpu"),
            corpus_stats=corpus.stats(), generated_at="2026-06-14T00:00:00Z",
        )

    def test_report_shape(self) -> None:
        r = self.report
        # 2 arms x 2 step-milestones = 4 rows
        self.assertEqual(len(r["rows"]), 4)
        self.assertEqual({row["arm"] for row in r["rows"]}, {"completion_only", "full_loss"})
        self.assertEqual({row["steps"] for row in r["rows"]}, {20, 40})
        self.assertEqual(set(r["accuracy_curves"]["completion_only"]), {"20", "40"})
        self.assertEqual(set(r["per_op_at_max_steps"]["completion_only"]), {"C", "R"})

    def test_status_matches_gate_and_verdict_honest(self) -> None:
        s = self.report["summary"]
        self.assertIn(self.report["status"], {"pass", "review"})
        # Invariant: pass iff the gate (copy learned at max budget) passed.
        self.assertIs(self.report["status"] == "pass", s["task_learned"])
        if self.report["status"] == "pass":
            self.assertGreaterEqual(s["completion_only_copy_accuracy_at_max"], s["learnability_gate"])
        self.assertIn(s["verdict"], {
            "instruction_following_not_learned",
            "completion_only_helps_early_benefit_shrinks_with_training",
            "completion_only_loss_improves_instruction_following",
            "completion_only_benefit_emerges_with_training",
            "masking_no_measurable_effect_at_this_scale",
            "completion_only_only_no_ablation",
        })


if __name__ == "__main__":
    unittest.main()
