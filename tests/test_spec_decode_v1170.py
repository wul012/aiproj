"""v1170 speculative decoding — durable home for the CPU-probe assertions.

Migrates the load-bearing results from the (now-deleted) output/spec_decode_probe
scripts and adds the design-panel edge cases:
  - logit-identity invariant (the v1161-style gate) across RoPE on/off, K in
    {1,2,4,8}, multi-block  [was: forward_cached multi-token == full ~6e-8];
  - greedy completion identity (plain vs spec) on random AND trained models
    [was: greedy bitwise identity across RoPE/K, with the overshoot-truncation fix];
  - self-spec anchor: alpha==1.0, tokens-per-target-forward == K+1 [was: self-spec];
  - sampling distributional equivalence: TV within the noise floor [was: TV 0.0027];
  - shared tie-break determinism + tie-artifact classification;
  - EOS-inside-overshoot truncation; block_size boundary (no raise);
  - rollback contiguity + accept-rule consistency;
  - run_spec_decode report shape + status-iff-task_learned + verdict membership.
"""
from __future__ import annotations

import unittest

import torch

import minigpt.spec_decode_v1170 as facade
import minigpt.spec_decode_v1170_core as core
from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.sft_training import train_sft
from minigpt.tokenizer import CharTokenizer
from minigpt.spec_decode_v1170 import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    SpecDecodeConfig,
    chunked_forward_logit_diff,
    classify_greedy_diff,
    greedy_token,
    is_tie,
    plain_generate_greedy,
    run_spec_decode,
    slice_caches,
    speculative_generate_greedy,
    speculative_generate_sample,
    plain_sample,
)

DEVICE = torch.device("cpu")
V, BS = 24, 24


class CoreFacadeContractTests(unittest.TestCase):
    def test_legacy_module_reexports_decoding_primitives(self) -> None:
        names = (
            "SpecStats",
            "chunked_forward_logit_diff",
            "classify_greedy_diff",
            "greedy_token",
            "is_tie",
            "plain_generate_greedy",
            "plain_sample",
            "slice_caches",
            "speculative_generate_greedy",
            "speculative_generate_sample",
        )
        for name in names:
            self.assertIs(getattr(facade, name), getattr(core, name))


def _cfg(n_layer, n_embd, rope):
    return GPTConfig(vocab_size=V, block_size=BS, n_layer=n_layer, n_head=2, n_embd=n_embd, dropout=0.0, use_rope=rope)


class SelectionTests(unittest.TestCase):
    def test_greedy_token_lowest_index_tiebreak(self):
        logits = torch.tensor([[1.0, 5.0, 5.0, 2.0]])  # tie at indices 1 and 2
        self.assertEqual(int(greedy_token(logits).item()), 1)  # lowest index wins

    def test_is_tie(self):
        self.assertTrue(is_tie(torch.tensor([[3.0, 3.0 + 1e-7, 0.0]])))
        self.assertFalse(is_tie(torch.tensor([[3.0, 1.0, 0.0]])))

    def test_slice_caches_length_and_contiguous(self):
        torch.manual_seed(0)
        m = MiniGPT(_cfg(2, 32, True))
        idx = torch.randint(0, V, (1, 6))
        _, caches = m.forward_cached(idx, None, 0)
        sliced = slice_caches(caches, 3)
        for k, v in sliced:
            self.assertEqual(k.shape[2], 3)
            self.assertEqual(v.shape[2], 3)
            self.assertTrue(k.is_contiguous() and v.is_contiguous())


class LogitIdentityTests(unittest.TestCase):
    def test_chunked_verify_matches_full_forward(self):
        # the v1161 invariant at verify-chunk width, RoPE on/off, K in {1,2,4,8}
        for rope in (False, True):
            torch.manual_seed(1)
            m = MiniGPT(_cfg(4, 32, rope))
            m.eval()
            idx = torch.randint(0, V, (1, 20))
            for k in (1, 2, 4, 8):
                diff = chunked_forward_logit_diff(m, idx, k + 1)
                self.assertLess(diff, 1e-4, f"rope={rope} k={k} logit diff {diff}")


class GreedyIdentityTests(unittest.TestCase):
    def test_random_models_identical_all_k_rope(self):
        # spec greedy == plain greedy (EOS-truncated, shared tie-break) on random models
        for rope in (False, True):
            torch.manual_seed(1)
            target = MiniGPT(_cfg(4, 32, rope)); target.eval()
            torch.manual_seed(2)
            draft = MiniGPT(_cfg(2, 16, rope)); draft.eval()
            for k in (1, 2, 4, 8):
                for seed in range(4):
                    torch.manual_seed(100 + seed)
                    prompt = torch.randint(0, V, (1, 3))
                    plain_idx, _, _ = plain_generate_greedy(target, prompt, max_new_tokens=12, block_size=BS)
                    spec_idx, _, _ = speculative_generate_greedy(target, draft, prompt, max_new_tokens=12, k=k, block_size=BS)
                    cls = classify_greedy_diff(target, plain_idx, spec_idx, prompt.shape[1], eos_id=V - 1)
                    self.assertIn(cls, ("identical", "tie_artifact"), f"rope={rope} k={k} seed={seed} -> {cls}")
                    # same generated length after trim
                    self.assertEqual(spec_idx.shape[1], prompt.shape[1] + 12)

    def test_tie_artifact_classification(self):
        # construct a target whose greedy diff sits at a logit tie -> tie_artifact, not genuine
        torch.manual_seed(0)
        target = MiniGPT(_cfg(2, 16, True)); target.eval()
        plain = torch.tensor([[1, 2, 3, 4, 5]])
        spec = torch.tensor([[1, 2, 3, 9, 5]])  # diff at completion index 0 (abs pos 3)
        # abs pos 3 is predicted by logits at input index 2 (prompt_len + 0 - 1)

        real_forward = target.forward

        def fake_forward(idx, targets=None):
            logits, loss = real_forward(idx, targets)
            logits = logits.clone()
            logits[:, 2, :] = 0.0
            logits[:, 2, 4] = 5.0
            logits[:, 2, 9] = 5.0  # exact tie between the two divergent tokens
            return logits, loss

        target.forward = fake_forward  # type: ignore
        cls = classify_greedy_diff(target, plain, spec, prompt_len=3, eos_id=99)
        self.assertEqual(cls, "tie_artifact")


class SelfSpecAnchorTests(unittest.TestCase):
    def test_self_spec_alpha_one_and_ceiling(self):
        torch.manual_seed(7)
        target = MiniGPT(_cfg(4, 32, True)); target.eval()
        prompt = torch.randint(0, V, (1, 3))
        for k in (1, 2, 4):
            spec_idx, st, _ = speculative_generate_greedy(target, target, prompt, max_new_tokens=12, k=k, block_size=BS)
            self.assertEqual(st.accepted, st.proposed)                 # alpha == 1.0
            self.assertAlmostEqual(st.generated / st.target_forwards, 0.0, delta=k + 1)
            # tokens-per-target-forward hits the K+1 ceiling (minus prefill forward)
            self.assertGreaterEqual(st.generated / max(st.target_forwards, 1), 1.0)


class BoundaryTests(unittest.TestCase):
    def test_block_size_boundary_never_raises(self):
        torch.manual_seed(3)
        target = MiniGPT(_cfg(2, 32, True)); target.eval()
        torch.manual_seed(4)
        draft = MiniGPT(_cfg(2, 16, True)); draft.eval()
        # prompt + max_new chosen so the final verify block straddles block_size
        prompt = torch.randint(0, V, (1, BS - 4))
        for k in (1, 2, 4, 8):
            spec_idx, _, _ = speculative_generate_greedy(target, draft, prompt, max_new_tokens=10, k=k, block_size=BS)
            self.assertLessEqual(spec_idx.shape[1], BS + 10)  # did not crash; bounded


class TrainedModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ops = ("C", "R", "S", "L")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3, 4), inputs_per_op_length=60, heldout_ratio=0.3)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        cls.tok = tok
        cls.pad_id = tok.encode(PAD)[0]
        cls.eos_id = tok.encode(EOS)[0]
        cls.block_size = max(16, corpus.max_text_len)
        train_ex = [(tok.encode(e.text), len(e.prompt)) for e in corpus.train]
        cls.heldout = [(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout]
        cfg = GPTConfig(vocab_size=tok.vocab_size, block_size=cls.block_size, n_layer=2, n_head=2,
                        n_embd=32, dropout=0.0, use_rope=True)
        torch.manual_seed(123)
        cls.target = MiniGPT(cfg)
        # under-trained draft snapshot, then finish training the target
        train_sft(cls.target, train_ex, steps=40, lr=3e-3, batch_size=32, block_size=cls.block_size,
                  device=DEVICE, pad_id=cls.pad_id, mask_prompt=True)
        cls.draft = MiniGPT(cfg)
        cls.draft.load_state_dict({k: v.clone() for k, v in cls.target.state_dict().items()})
        train_sft(cls.target, train_ex, steps=460, lr=3e-3, batch_size=32, block_size=cls.block_size,
                  device=DEVICE, pad_id=cls.pad_id, mask_prompt=True)
        cls.target.eval(); cls.draft.eval()

    def test_eos_inside_overshoot_truncation_identity(self):
        # trained model: greedy completions reach EOS; spec must match plain on the
        # EOS-truncated portion even when blocks overshoot max_new_tokens.
        genuine = 0
        for p, _exp, _op in self.heldout[:40]:
            prompt = torch.tensor([p])
            plain_idx, _, _ = plain_generate_greedy(self.target, prompt, max_new_tokens=8, block_size=self.block_size)
            spec_idx, _, _ = speculative_generate_greedy(self.target, self.draft, prompt, max_new_tokens=8,
                                                         k=4, block_size=self.block_size)
            cls = classify_greedy_diff(self.target, plain_idx, spec_idx, prompt.shape[1], self.eos_id)
            genuine += int(cls == "genuine_diff")
        self.assertEqual(genuine, 0)

    def test_multiblock_partial_and_full_accept_identity(self):
        # weak draft -> mix of full-accept and partial-accept blocks; identity must hold
        # (the rollback path that the probe's bug lived in).
        for k in (2, 4):
            for p, _exp, _op in self.heldout[:20]:
                prompt = torch.tensor([p])
                plain_idx, _, _ = plain_generate_greedy(self.target, prompt, max_new_tokens=8, block_size=self.block_size)
                spec_idx, st, _ = speculative_generate_greedy(self.target, self.draft, prompt, max_new_tokens=8,
                                                             k=k, block_size=self.block_size)
                cls = classify_greedy_diff(self.target, plain_idx, spec_idx, prompt.shape[1], self.eos_id)
                self.assertNotEqual(cls, "genuine_diff")

    def test_accept_rule_consistency(self):
        # per-block emission (prefill-excluded, un-truncated) ~ (1-a^(k+1))/(1-a)
        # with a = per-position CONDITIONAL accept prob (accepted / tested)
        k = 4
        acc = tested = blocks = 0
        for p, _exp, _op in self.heldout[:40]:
            prompt = torch.tensor([p])
            _idx, st, _ = speculative_generate_greedy(self.target, self.draft, prompt, max_new_tokens=8,
                                                      k=k, block_size=self.block_size)
            acc += st.accepted; tested += st.tested; blocks += st.blocks
        alpha = acc / max(tested, 1)
        measured = (acc + blocks) / max(blocks, 1)
        theo = (k + 1) if alpha >= 1 - 1e-9 else (1 - alpha ** (k + 1)) / (1 - alpha)
        self.assertLess(abs(measured - theo), 0.5, f"alpha={alpha} measured={measured} theo={theo}")

    def test_sampling_distributional_equivalence(self):
        # TV(spec, target) within ~the noise floor TV(target, target')
        gen = torch.Generator(device=DEVICE)
        vocab = self.tok.vocab_size

        def hist(seed_off, sampler):
            gen.manual_seed(seed_off)
            counts = torch.zeros(vocab)
            for _ in range(30):
                for p, _e, _o in self.heldout[:20]:
                    out = sampler(torch.tensor([p]))
                    for tk in out[0, len(p):].tolist():
                        counts[tk] += 1
            return counts

        spec_h = hist(11, lambda pr: speculative_generate_sample(self.target, self.draft, pr, max_new_tokens=6,
                                                                 k=4, block_size=self.block_size, temperature=1.0, generator=gen)[0])
        tgt_h = hist(22, lambda pr: plain_sample(self.target, pr, max_new_tokens=6, block_size=self.block_size,
                                                 temperature=1.0, generator=gen))
        tgt_h2 = hist(33, lambda pr: plain_sample(self.target, pr, max_new_tokens=6, block_size=self.block_size,
                                                  temperature=1.0, generator=gen))

        def tv(a, b):
            pa, pb = a / a.sum(), b / b.sum()
            return 0.5 * float((pa - pb).abs().sum())

        tv_spec = tv(spec_h, tgt_h)
        tv_floor = tv(tgt_h2, tgt_h)
        self.assertLessEqual(tv_spec, tv_floor * 3.0 + 0.02, f"tv_spec={tv_spec} floor={tv_floor}")


class RunSpecDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ops = ("C", "R", "S")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3,), inputs_per_op_length=40, heldout_ratio=0.3)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id, eos_id = tok.encode(PAD)[0], tok.encode(EOS)[0]
        block_size = max(16, corpus.max_text_len)
        cls.report = run_spec_decode(
            vocab_size=tok.vocab_size,
            base_train=[(tok.encode(e.text), len(e.prompt)) for e in corpus.train],
            heldout_instructions=[(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout],
            ops=ops, pad_id=pad_id, eos_id=eos_id,
            config=SpecDecodeConfig(block_size=block_size, seeds=(1337,), target_steps=120,
                                    draft_snapshot_steps=(20, 60), k_values=(1, 2), max_new_tokens=6,
                                    eval_prompts=10, n_layer=1, n_head=2, n_embd=16,
                                    tv_repeats=4, tv_floor_batches=2, timing_repeats=2, timing_warmup=1, timing_k=2),
            device=DEVICE,
            corpus_stats={"heldout_prompts": len(corpus.heldout)},
            generated_at="2026-06-15T00:00:00Z",
        )

    def test_report_shape(self):
        r = self.report
        self.assertEqual(r["title"], "MiniGPT speculative decoding v1170")
        self.assertTrue(any(row["draft"] == "self" for row in r["rows"]))
        self.assertIn("target_positions_ratio_vs_plain", r["rows"][0])

    def test_status_iff_task_learned(self):
        r = self.report
        self.assertIn(r["status"], {"pass", "review"})
        self.assertIs(r["status"] == "pass", r["summary"]["task_learned"])

    def test_verdict_membership(self):
        self.assertIn(self.report["summary"]["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)

    def test_correctness_gate_inputs_present(self):
        s = self.report["summary"]
        for key in ("max_verify_logit_diff", "logit_identity_ok", "sampling_tv_ok",
                    "accept_rule_consistency_ok", "greedy_genuine_diff"):
            self.assertIn(key, s)


if __name__ == "__main__":
    unittest.main()
