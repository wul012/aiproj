"""v1172 knowledge distillation — tests for the KD loss, the disentangling
controls, the independent-init seeding, the gate, and the verdict selection."""
from __future__ import annotations

import math
import unittest

import torch
import torch.nn.functional as F

from minigpt.distill_v1172 import (
    ARM_ORDER,
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    DistillConfig,
    decide,
    kl_term,
    run_distill,
    shuffle_residual_mass,
    teacher_logit_stats,
    train_student,
)
from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.sft_training import IGNORE_INDEX
from minigpt.tokenizer import CharTokenizer

DEVICE = torch.device("cpu")


class KLTermTests(unittest.TestCase):
    def test_self_distillation_is_zero(self):
        torch.manual_seed(0)
        z = torch.randn(2, 5, 12)
        mask = torch.ones(2, 5, dtype=torch.bool)
        for tau in (1.0, 2.0):
            p_T = F.softmax(z / tau, dim=-1)            # teacher probs == student's, same logits
            self.assertLess(abs(float(kl_term(z, p_T, mask, tau))), 1e-6, f"tau={tau}")

    def test_tau_squared_scaling(self):
        torch.manual_seed(1)
        zS, zT = torch.randn(2, 4, 12), torch.randn(2, 4, 12)
        mask = torch.ones(2, 4, dtype=torch.bool)
        # raw (uncorrected) KL at tau=2 vs the tau^2-corrected term
        p2 = F.softmax(zT / 2.0, dim=-1)
        logp2 = F.log_softmax(zS / 2.0, dim=-1)
        raw = ((p2 * (p2.clamp_min(1e-9).log() - logp2)).sum(-1) * mask).sum() / mask.sum()
        self.assertAlmostEqual(float(kl_term(zS, zT_div2_probs := p2, mask, 2.0)), float(raw) * 4.0, places=5)
        # tau=1 is a no-op multiplier
        p1 = F.softmax(zT, dim=-1)
        logp1 = F.log_softmax(zS, dim=-1)
        raw1 = ((p1 * (p1.clamp_min(1e-9).log() - logp1)).sum(-1) * mask).sum() / mask.sum()
        self.assertAlmostEqual(float(kl_term(zS, p1, mask, 1.0)), float(raw1), places=5)

    def test_mask_excludes_positions(self):
        torch.manual_seed(2)
        zS, zT = torch.randn(1, 6, 12), torch.randn(1, 6, 12)
        p_T = F.softmax(zT, dim=-1)
        full = torch.ones(1, 6, dtype=torch.bool)
        part = full.clone(); part[0, 3:] = False
        # masking out positions changes the value (they carried nonzero KL)
        self.assertNotAlmostEqual(float(kl_term(zS, p_T, full, 1.0)), float(kl_term(zS, p_T, part, 1.0)), places=4)


class ShuffledTeacherTests(unittest.TestCase):
    def test_preserves_argmax_maxprob_entropy_destroys_identity(self):
        torch.manual_seed(0)
        p = F.softmax(torch.randn(3, 4, 12), dim=-1)
        perm = torch.randperm(11)
        q = shuffle_residual_mass(p, perm)
        # argmax index + max-prob preserved
        self.assertTrue(torch.equal(p.argmax(-1), q.argmax(-1)))
        self.assertTrue(torch.allclose(p.max(-1).values, q.max(-1).values, atol=1e-6))
        # entropy preserved (same multiset of probs per token)
        ent_p = -(p.clamp_min(1e-9).log() * p).sum(-1)
        ent_q = -(q.clamp_min(1e-9).log() * q).sum(-1)
        self.assertTrue(torch.allclose(ent_p, ent_q, atol=1e-5))
        # sums to 1 and identity actually changed somewhere
        self.assertTrue(torch.allclose(q.sum(-1), torch.ones(3, 4), atol=1e-5))
        self.assertFalse(torch.allclose(p, q, atol=1e-4))


class TrainStudentTests(unittest.TestCase):
    def _data(self):
        corpus = build_sft_corpus(seed=0, ops=("C", "R"), lengths=(3,), inputs_per_op_length=12, heldout_ratio=0.25)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        ex = [(tok.encode(e.text), len(e.prompt)) for e in corpus.train]
        return ex, tok.encode(PAD)[0], tok.vocab_size

    def test_ce_mode_runs_and_returns_loss(self):
        ex, pad_id, V = self._data()
        torch.manual_seed(0)
        m = MiniGPT(GPTConfig(vocab_size=V, block_size=16, n_layer=1, n_head=2, n_embd=16, dropout=0.0, use_rope=True))
        loss = train_student(m, ex, steps=5, lr=3e-3, batch_size=8, block_size=16, pad_id=pad_id,
                             device=DEVICE, loss_mode="ce")
        self.assertTrue(math.isfinite(loss))

    def test_independent_inits(self):
        # different (arm,seed) -> different init; same -> identical (the seeding contract)
        V = 12
        def init(seed):
            torch.manual_seed(seed)
            return MiniGPT(GPTConfig(vocab_size=V, block_size=16, n_layer=1, n_head=2, n_embd=16, use_rope=True))
        base = 1337
        a0 = init(base + 1009 * 0 + 1337)           # scratch_hard, seed 1337
        a3 = init(base + 1009 * 3 + 1337)           # distill_tau1_hw0, seed 1337
        a0b = init(base + 1009 * 0 + 1337)          # same again
        w0 = a0.token_embedding.weight
        self.assertFalse(torch.allclose(w0, a3.token_embedding.weight))
        self.assertTrue(torch.allclose(w0, a0b.token_embedding.weight))


class DecideTests(unittest.TestCase):
    def _cell(self, scratch, distill, ls, shuf, t2, long_, std=0.005):
        return {"scratch_hard": (scratch, std), "label_smooth": (ls, std), "shuffled_teacher": (shuf, std),
                "distill_tau1_hw0": (distill, std), "distill_tau2_hw0": (t2, std), "scratch_long": (long_, std)}

    def test_no_headroom_is_review(self):
        cell = self._cell(0.90, 0.90, 0.90, 0.90, 0.90, 0.90)  # scratch already at teacher
        out = decide(cell, teacher_em=0.91, teacher_maxprob=0.99, headroom=0.05)
        self.assertEqual(out["status"], "review")
        self.assertEqual(out["verdict"], "no_valid_distillation_headroom")

    def test_logit_matching_verdict(self):
        # distill beats scratch AND both controls; near-one-hot; tau1>=tau2
        cell = self._cell(0.60, 0.85, 0.70, 0.70, 0.80, 0.85)
        out = decide(cell, teacher_em=0.90, teacher_maxprob=0.986, headroom=0.05)
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["verdict"], "distillation_helps_via_logit_matching_not_dark_knowledge")

    def test_generic_regularization_verdict(self):
        # distill beats scratch but NOT label_smooth (control matches it) -> generic
        cell = self._cell(0.60, 0.85, 0.85, 0.70, 0.80, 0.95)
        out = decide(cell, teacher_em=0.90, teacher_maxprob=0.986, headroom=0.05)
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["verdict"], "gain_is_generic_soft_target_regularization")

    def test_no_benefit_verdict(self):
        cell = self._cell(0.80, 0.80, 0.80, 0.80, 0.80, 0.80)
        out = decide(cell, teacher_em=0.90, teacher_maxprob=0.986, headroom=0.05)
        self.assertEqual(out["verdict"], "no_distill_benefit")

    def test_all_verdicts_in_known_sets(self):
        for v in ("no_valid_distillation_headroom", "controls_missing"):
            self.assertIn(v, REVIEW_VERDICTS)
        for v in ("distillation_helps_via_logit_matching_not_dark_knowledge",
                  "gain_is_generic_soft_target_regularization", "no_distill_benefit"):
            self.assertIn(v, PRIMARY_VERDICTS)


class RunDistillSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ops = ("C", "R", "S")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3,), inputs_per_op_length=40, heldout_ratio=0.3)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id, eos_id = tok.encode(PAD)[0], tok.encode(EOS)[0]
        block_size = max(16, corpus.max_text_len)
        ex = [(tok.encode(e.text), len(e.prompt)) for e in corpus.train]
        held = [(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout]
        train_instr = [(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.train[:20]]
        cls.report = run_distill(
            vocab_size=tok.vocab_size, train_examples=ex, heldout_instructions=held,
            train_instructions=train_instr, ops=ops, pad_id=pad_id, eos_id=eos_id,
            config=DistillConfig(block_size=block_size, seeds=(1337, 1338), seed_base=1337,
                                 teacher_steps=40, steps=30, teacher_layer=2, teacher_head=2, teacher_embd=32,
                                 sizes=((1, 2, 16, "1L/16"), (2, 4, 32, "2L/32")), capable_label="2L/32"),
            device=DEVICE, corpus_stats={"heldout_prompts": len(held)}, generated_at="2026-06-15T00:00:00Z",
        )

    def test_report_shape(self):
        r = self.report
        self.assertEqual(r["title"], "MiniGPT knowledge distillation v1172")
        self.assertIn("2L/32", r["capacity_curve"])
        self.assertTrue(any(row["arm"] == "shuffled_teacher" for row in r["rows"]))
        self.assertIn(r["summary"]["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)

    def test_status_iff_task_learned(self):
        r = self.report
        self.assertIs(r["status"] == "pass", r["summary"]["task_learned"])

    def test_teacher_logit_stats_reported(self):
        s = self.report["summary"]
        self.assertIn("teacher_mean_maxprob", s)
        self.assertIn("teacher_mean_entropy_nats", s)


if __name__ == "__main__":
    unittest.main()
