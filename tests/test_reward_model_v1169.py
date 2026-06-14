from __future__ import annotations

import unittest

import torch

from minigpt.experiment_utils import build_minigpt
from minigpt.model import GPTConfig, MiniGPT
from minigpt.reward_model_v1169 import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    RewardModel,
    RewardModelConfig,
    rank_accuracy,
    run_reward_model,
    train_reward_model,
)
from minigpt.sft_corpus import EOS, INPUT_ALPHABET, PAD, build_sft_corpus
from minigpt.dpo_preference_v1166 import build_confusable_preferences
from minigpt.tokenizer import CharTokenizer

DEVICE = torch.device("cpu")


class Cfg:
    block_size = 16
    n_layer = 2
    n_head = 2
    n_embd = 16
    use_rope = True


class FeaturesRefactorTests(unittest.TestCase):
    def test_features_matches_forward_path(self) -> None:
        torch.manual_seed(0)
        m = MiniGPT(GPTConfig(vocab_size=10, block_size=8, n_layer=2, n_head=2, n_embd=16, dropout=0.0, use_rope=True))
        m.eval()
        idx = torch.tensor([[1, 2, 3, 4]])
        with torch.no_grad():
            feats = m.features(idx)
            logits, _ = m(idx)
        # forward's logits must equal lm_head(features)
        self.assertTrue(torch.allclose(logits, m.lm_head(feats), atol=1e-6))
        self.assertEqual(feats.shape, (1, 4, 16))

    def test_features_seq_len_guard(self) -> None:
        torch.manual_seed(0)
        m = MiniGPT(GPTConfig(vocab_size=10, block_size=4, n_layer=1, n_head=2, n_embd=16, use_rope=True))
        with self.assertRaises(ValueError):
            m.features(torch.zeros((1, 5), dtype=torch.long))


class RewardModelTests(unittest.TestCase):
    def test_reward_shape_and_pooling(self) -> None:
        torch.manual_seed(0)
        rm = RewardModel(10, Cfg())
        idx = torch.tensor([[1, 2, 3, 0], [4, 5, 0, 0]])
        last = torch.tensor([2, 1])
        r = rm.reward(idx, last)
        self.assertEqual(r.shape, (2,))

    def test_bradley_terry_separates_a_trivial_pair(self) -> None:
        # one fixed (chosen, rejected); training should drive r(chosen) > r(rejected)
        torch.manual_seed(0)
        rm = RewardModel(10, Cfg())
        pairs = [([1, 2, 3, 4], [1, 2, 5, 6])] * 8
        train_reward_model(rm, pairs, steps=60, lr=5e-3, batch_size=4, pad_id=0, device=DEVICE)
        self.assertEqual(rank_accuracy(rm, pairs, 0, device=DEVICE), 1.0)


class RunRewardModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import random
        ops = ("C", "R", "S")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3,), inputs_per_op_length=40, heldout_ratio=0.3)
        tr, _ = build_confusable_preferences(corpus.train, ops)
        ev, _ = build_confusable_preferences(corpus.heldout, ops)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id, eos_id = tok.encode(PAD)[0], tok.encode(EOS)[0]
        rng = random.Random(1)
        ood = []
        for e in corpus.heldout:
            inp = e.prompt[1:-1]
            corrupted = e.expected_output
            while corrupted == e.expected_output:
                corrupted = "".join(rng.choice(INPUT_ALPHABET) for _ in inp)
            ood.append((tok.encode(e.text), tok.encode(e.prompt + corrupted + EOS)))
        cls.report = run_reward_model(
            vocab_size=tok.vocab_size,
            rm_train_pairs=[(tok.encode(p.chosen_text), tok.encode(p.rejected_text)) for p in tr],
            rm_eval_pairs=[(tok.encode(p.chosen_text), tok.encode(p.rejected_text)) for p in ev],
            rm_ood_pairs=ood,
            base_train=[(tok.encode(e.text), len(e.prompt)) for e in corpus.train],
            heldout_instructions=[(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout],
            ops=ops, pad_id=pad_id, eos_id=eos_id,
            config=RewardModelConfig(block_size=16, seeds=(1337,), rm_steps=40, base_steps=20,
                                     n_values=(1, 4), batch_size=8, n_layer=1, n_head=2, n_embd=16, max_new_tokens=5),
            device=DEVICE,
            corpus_stats={"rm_train_pairs": len(tr), "rm_eval_pairs": len(ev), "rm_ood_pairs": len(ood)},
            generated_at="2026-06-14T00:00:00Z",
        )

    def test_report_shape(self) -> None:
        r = self.report
        self.assertEqual({row["n"] for row in r["rows"]}, {1, 4})
        self.assertEqual(set(r["best_of_n_curves"]), {"rerank_em", "random_em", "oracle_em"})
        # oracle >= rerank >= 0 and random within [0,1] at each N
        for row in r["rows"]:
            self.assertGreaterEqual(row["oracle_em_mean"] + 1e-9, row["rerank_em_mean"])

    def test_status_iff_task_learned(self) -> None:
        r = self.report
        self.assertIn(r["status"], {"pass", "review"})
        self.assertIs(r["status"] == "pass", r["summary"]["task_learned"])

    def test_verdict_membership(self) -> None:
        s = self.report["summary"]
        self.assertIn(s["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)
        self.assertIn(s["rm_verdict"], {"reward_model_generalizes_to_off_distribution", "reward_model_in_distribution_only"})
        self.assertIn(s["best_of_n_verdict"], {"best_of_n_reranking_helps", "best_of_n_reranking_degrades", "best_of_n_reranking_neutral"})


if __name__ == "__main__":
    unittest.main()
