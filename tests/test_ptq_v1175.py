"""v1175 post-training quantization tests: quantizer correctness, the tied-embedding
guard (the subtlety that could have invalidated the probe's 'embedding lossless'),
effective-bits accounting, the gate/verdict, and an end-to-end smoke."""
from __future__ import annotations

import unittest

import torch

from minigpt.model import GPTConfig, MiniGPT
from minigpt.ptq_v1175 import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    PtqConfig,
    beats_lower,
    ce_and_kl,
    component_param_names,
    decide,
    effective_bits_per_weight,
    n_scale_groups,
    quantize_tensor,
    quantized_model,
    run_ptq,
    weight_rel_error,
)
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.tokenizer import CharTokenizer

DEVICE = torch.device("cpu")


def _model(vocab=20, nl=2, ne=16):
    return MiniGPT(GPTConfig(vocab_size=vocab, block_size=8, n_layer=nl, n_head=2, n_embd=ne, dropout=0.0, use_rope=True))


class QuantizerTests(unittest.TestCase):
    def test_roundtrip_within_absmax_bound(self):
        torch.manual_seed(0)
        W = torch.randn(8, 16)
        for bits in (8, 4, 2):
            s = W.abs().max() / (2 ** (bits - 1) - 1)
            Wq = quantize_tensor(W, bits, granularity="per_tensor", scheme="absmax_sym")
            self.assertLessEqual(float((W - Wq).abs().max()), float(s) / 2 + 1e-5, f"bits={bits}")

    def test_per_channel_lower_error_than_per_tensor(self):
        torch.manual_seed(1)
        W = torch.randn(16, 32)
        W[0] *= 20.0  # an outlier row that wrecks a single shared scale
        pt = (W - quantize_tensor(W, 4, granularity="per_tensor", scheme="absmax_sym")).norm()
        pc = (W - quantize_tensor(W, 4, granularity="per_channel_row", scheme="absmax_sym")).norm()
        self.assertLess(float(pc), float(pt))

    def test_more_bits_lower_error(self):
        torch.manual_seed(2)
        W = torch.randn(8, 16)
        e8 = (W - quantize_tensor(W, 8, granularity="per_channel_row", scheme="absmax_sym")).norm()
        e2 = (W - quantize_tensor(W, 2, granularity="per_channel_row", scheme="absmax_sym")).norm()
        self.assertLess(float(e8), float(e2))

    def test_clipping_helps_on_outliers(self):
        torch.manual_seed(3)
        W = torch.randn(8, 64)
        W[:, 0] *= 30.0  # heavy outlier column
        absmax = (W - quantize_tensor(W, 3, granularity="per_channel_row", scheme="absmax_sym")).norm()
        mse = (W - quantize_tensor(W, 3, granularity="per_channel_row", scheme="mse_clip")).norm()
        self.assertLessEqual(float(mse), float(absmax) + 1e-6)

    def test_group32_shape_preserved(self):
        W = torch.randn(6, 64)
        self.assertEqual(quantize_tensor(W, 4, granularity="group32", scheme="absmax_sym").shape, (6, 64))


class TiedEmbeddingTests(unittest.TestCase):
    def test_quantizing_embedding_is_not_reverted_by_the_tie(self):
        # the load-bearing correctness guard: lm_head.weight IS token_embedding.weight,
        # so quantization must apply by parameter identity, not silently revert.
        torch.manual_seed(0)
        base = _model()
        qm = quantized_model(base, 2, "embedding", granularity="per_tensor", scheme="absmax_sym")
        self.assertIs(qm.lm_head.weight, qm.token_embedding.weight)         # tie preserved
        self.assertFalse(torch.allclose(qm.token_embedding.weight, base.token_embedding.weight))  # actually quantized
        idx = torch.tensor([[1, 2, 3]])
        with torch.no_grad():
            self.assertFalse(torch.allclose(base(idx)[0], qm(idx)[0]))      # output logits changed

    def test_component_names_dedup_tie_and_exclude_pos_emb(self):
        m = _model()
        emb = component_param_names(m, "embedding")
        self.assertEqual(emb, ["token_embedding.weight"])                   # tied lm_head not listed twice
        alln = component_param_names(m, "all")
        self.assertNotIn("position_embedding.weight", alln)
        self.assertNotIn("lm_head.weight", alln)
        self.assertIn("token_embedding.weight", alln)


class EffectiveBitsTests(unittest.TestCase):
    def test_per_channel_costs_more_than_per_tensor(self):
        m = _model(ne=16)
        pt = effective_bits_per_weight(m, "c_attn", 4, "per_tensor")
        pc = effective_bits_per_weight(m, "c_attn", 4, "per_channel_row")
        self.assertAlmostEqual(pt, 4.0, delta=0.05)        # per-tensor: one scale over the matrix ≈ 4
        self.assertGreater(pc, pt)                          # per-channel: a scale per row adds metadata bits

    def test_n_scale_groups(self):
        W = torch.randn(192, 64)
        self.assertEqual(n_scale_groups(W, "per_tensor"), 1)
        self.assertEqual(n_scale_groups(W, "per_channel_row"), 192)
        self.assertEqual(n_scale_groups(W, "per_channel_col"), 64)
        self.assertEqual(n_scale_groups(W, "group32"), 192 * 2)


class MetricTests(unittest.TestCase):
    def test_self_kl_zero(self):
        torch.manual_seed(0)
        m = _model()
        X = torch.tensor([[1, 2, 3, 4], [5, 6, 7, 8]])
        Y = torch.full_like(X, -100); Y[:, -1] = X[:, -1]
        _ce, _kl, logits = ce_and_kl(m, X, Y, None)
        ce2, kl2, _ = ce_and_kl(m, X, Y, logits)
        self.assertLess(abs(kl2), 1e-6)
        self.assertTrue(ce2 == ce2)

    def test_weight_rel_error_zero_at_high_bits(self):
        torch.manual_seed(0)
        base = _model()
        qm = quantized_model(base, 8, "all", granularity="per_channel_row", scheme="absmax_sym")
        self.assertLess(weight_rel_error(base, qm, "all"), 0.05)


class BeatsLowerTests(unittest.TestCase):
    def test_direction(self):
        self.assertTrue(beats_lower(0.1, 0.01, 0.5, 0.02))      # 0.1 lower(better) than 0.5
        self.assertFalse(beats_lower(0.5, 0.02, 0.1, 0.01))


class DecideTests(unittest.TestCase):
    def _cell(self, ce, std=0.02, **extra):
        d = {"ce_mean": ce, "ce_std": std, "dce_mean": extra.get("dce", 0.0), "dce_std": std,
             "kl_mean": 0.0, "em_mean": 0.9, "relerr_mean": 0.1, "eff_bits": extra.get("eff", float(extra.get("bits", 4)))}
        return d

    def _grids(self, pt4_ce, pc3_ce):
        s1 = {("all", "per_tensor", 2): self._cell(5.0),
              ("all", "per_tensor", 4): self._cell(pt4_ce, eff=4.0),
              ("all", "per_channel_row", 3): self._cell(pc3_ce, eff=3.25)}
        s2 = {(c, "per_channel_row", 4): self._cell(0.5, dce=dce)
              for c, dce in (("embedding", 0.0), ("c_attn", 0.4), ("c_proj", 0.1), ("mlp", 0.05))}
        s3 = {("c_attn", "absmax_sym", "per_channel_row", 4): self._cell(0.9),
              ("c_attn", "absmax_sym", "per_channel_col", 4): self._cell(0.92),
              ("c_attn", "mse_clip", "per_channel_row", 4): self._cell(0.91)}
        return s1, s2, s3

    def test_per_channel_buys_bit_verdict(self):
        s1, s2, s3 = self._grids(pt4_ce=1.2, pc3_ce=0.5)   # pc 3b CE far below pt 4b CE
        out = decide(0.3, 0.93, s1, s2, s3, PtqConfig())
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["verdict"], "per_channel_holds_3b_per_tensor_collapses")

    def test_attention_most_sensitive_verdict(self):
        s1, s2, s3 = self._grids(pt4_ce=0.5, pc3_ce=0.5)   # no per-channel bit win, no cliff extension
        out = decide(0.3, 0.93, s1, s2, s3, PtqConfig())
        self.assertIn(out["verdict"], {"attention_most_sensitive_per_row_absmax",
                                       "attention_outlier_sensitive_clipping_helps",
                                       "attention_sensitivity_is_per_row_axis_artifact"})

    def test_per_channel_advantage_not_separable_verdict(self):
        # per-channel extends the NOMINAL cliff (per-tensor collapses at 3b, per-channel holds)
        # but pc 3b CE is NOT strictly below pt 4b CE -> a wash at matched effective bits
        s1 = {("all", "per_tensor", 4): self._cell(0.16, dce=0.04, eff=4.0),
              ("all", "per_tensor", 3): self._cell(0.58, dce=0.46, eff=3.0),
              ("all", "per_tensor", 2): self._cell(4.0, dce=3.9, eff=2.0),
              ("all", "per_channel_row", 4): self._cell(0.123, dce=0.003, eff=4.19),
              ("all", "per_channel_row", 3): self._cell(0.188, dce=0.068, eff=3.19),
              ("all", "per_channel_row", 2): self._cell(2.2, dce=2.08, eff=2.19)}
        s2 = {(c, "per_channel_row", 4): self._cell(0.5, dce=d)
              for c, d in (("embedding", 0.0), ("c_attn", 0.001), ("c_proj", 0.002), ("mlp", 0.0))}
        s3 = {("c_attn", "absmax_sym", "per_channel_row", 4): self._cell(0.9)}
        out = decide(0.12, 0.82, s1, s2, s3, PtqConfig())
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["verdict"], "per_channel_advantage_not_separable")

    def test_baseline_saturated_review(self):
        s1, s2, s3 = self._grids(0.5, 0.5)
        out = decide(0.3, 0.999, s1, s2, s3, PtqConfig())   # EM above ceiling
        self.assertEqual(out["status"], "review")
        self.assertEqual(out["verdict"], "baseline_saturated_or_not_learnable")

    def test_verdict_sets(self):
        for v in ("baseline_saturated_or_not_learnable", "grid_incomplete"):
            self.assertIn(v, REVIEW_VERDICTS)
        for v in ("per_channel_holds_3b_per_tensor_collapses", "component_sensitivity_not_separable"):
            self.assertIn(v, PRIMARY_VERDICTS)


class RunSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ops = ("C", "R", "S")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3,), inputs_per_op_length=40, heldout_ratio=0.3)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id, eos_id = tok.encode(PAD)[0], tok.encode(EOS)[0]
        bs = max(16, corpus.max_text_len)
        cls.report = run_ptq(
            vocab_size=tok.vocab_size,
            train_examples=[(tok.encode(e.text), len(e.prompt)) for e in corpus.train],
            heldout_instructions=[(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout],
            ops=ops, pad_id=pad_id, eos_id=eos_id,
            config=PtqConfig(block_size=bs, seeds=(1337, 1338), n_layer=2, n_head=2, n_embd=32, train_steps=60,
                             s1_bits=(8, 4, 2), s1_granularities=("per_tensor", "per_channel_row"),
                             s2_bits=(4,), s2_components=("embedding", "c_attn", "mlp"), s2_granularities=("per_channel_row",),
                             s3_bits=(4,), s3_schemes=("absmax_sym", "mse_clip"), s3_granularities=("per_channel_row", "per_channel_col"),
                             baseline_em_floor=0.0),
            device=DEVICE, corpus_stats={"heldout_prompts": len(corpus.heldout)}, generated_at="2026-06-16T00:00:00Z",
        )

    def test_report_shape(self):
        r = self.report
        self.assertEqual(r["title"], "MiniGPT post-training weight quantization v1175")
        self.assertIn(r["summary"]["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)
        self.assertTrue(any(row["sweep"] == "S1" for row in r["rows"]))
        self.assertIn("cliffs", r)

    def test_status_iff_task_learned(self):
        self.assertIs(self.report["status"] == "pass", self.report["summary"]["task_learned"])


if __name__ == "__main__":
    unittest.main()
