from __future__ import annotations

import unittest

import torch

from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.sft_pretrain_transfer_v1165 import SftTransferConfig, run_sft_transfer
from minigpt.tokenizer import CharTokenizer


class RunSftTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base = build_sft_corpus(seed=0, ops=("C", "R"), lengths=(3,), inputs_per_op_length=40)
        downstream = build_sft_corpus(seed=1, ops=("L",), lengths=(3,), inputs_per_op_length=40)
        tok = CharTokenizer.train(
            "".join(e.text for e in base.train + base.heldout + downstream.train + downstream.heldout) + base.alphabet
        )
        base_stream = "".join(e.text for e in base.train)
        cls.report = run_sft_transfer(
            vocab_size=tok.vocab_size,
            base_train_ids=torch.tensor(tok.encode(base_stream), dtype=torch.long),
            downstream_train=[(tok.encode(e.text), len(e.prompt)) for e in downstream.train],
            downstream_heldout=[(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in downstream.heldout],
            downstream_op="L", pad_id=tok.encode(PAD)[0], eos_id=tok.encode(EOS)[0],
            config=SftTransferConfig(
                block_size=16, seeds=(1337,), base_steps=15, sft_schedule=(10, 30),
                base_batch_size=16, sft_batch_size=16, n_layer=1, n_head=2, n_embd=16, max_new_tokens=5,
            ),
            device=torch.device("cpu"),
            corpus_stats={"base_ops": "C,R", "base_train_char_count": len(base_stream),
                          "downstream_train_count": len(downstream.train), "downstream_heldout_count": len(downstream.heldout)},
            generated_at="2026-06-14T00:00:00Z",
        )

    def test_report_shape(self) -> None:
        r = self.report
        # 2 arms x 2 budgets = 4 rows
        self.assertEqual(len(r["rows"]), 4)
        self.assertEqual({row["arm"] for row in r["rows"]}, {"pretrained", "scratch"})
        self.assertEqual({row["sft_steps"] for row in r["rows"]}, {10, 30})
        self.assertEqual(set(r["accuracy_curves"]["pretrained"]), {"10", "30"})

    def test_status_and_verdict_honest(self) -> None:
        s = self.report["summary"]
        self.assertIn(self.report["status"], {"pass", "review"})
        self.assertIs(self.report["status"] == "pass", s["task_learned"])
        if self.report["status"] == "pass":
            self.assertGreaterEqual(s["pretrained_at_max_budget"], s["learnability_gate"])
        self.assertIn(s["verdict"], {
            "downstream_op_not_learned",
            "pretraining_transfers_most_in_low_data_regime",
            "pretraining_improves_downstream_sft",
            "pretraining_benefit_emerges_with_more_sft",
            "no_measurable_transfer_at_this_scale",
        })
        self.assertEqual(s["downstream_op"], "L")


if __name__ == "__main__":
    unittest.main()
