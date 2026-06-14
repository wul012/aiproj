from __future__ import annotations

import math
import unittest

import torch
import torch.nn.functional as F

from minigpt.dpo_preference_v1166 import (
    LOG2,
    PRIMARY_VERDICTS,
    REFERENCE_VERDICTS,
    REVIEW_VERDICTS,
    SFT_CONTROL_VERDICTS,
    DpoPreferenceConfig,
    build_confusable_preferences,
    dpo_loss,
    evaluate_preference,
    logp_completion,
    run_dpo_preference,
    train_dpo,
)
from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_corpus import EOS, PAD, SftExample, build_sft_corpus
from minigpt.sft_training import IGNORE_INDEX, train_sft
from minigpt.tokenizer import CharTokenizer

DEVICE = torch.device("cpu")


def _tiny_model(vocab_size: int = 10, block_size: int = 8) -> MiniGPT:
    torch.manual_seed(0)
    return MiniGPT(
        GPTConfig(vocab_size=vocab_size, block_size=block_size, n_layer=1, n_head=2, n_embd=16, dropout=0.0, use_rope=True)
    )


class LogpCompletionTests(unittest.TestCase):
    def test_equals_manual_gather_and_negative_ce_sum(self) -> None:
        model = _tiny_model()
        model.eval()
        full = [1, 2, 3, 4, 5, 6]  # prompt [1,2,3], completion [4,5,6]
        n_prompt = 3
        pad_id = 0
        got = logp_completion(model, [(full, n_prompt)], pad_id, device=DEVICE)

        with torch.no_grad():
            x = torch.tensor([full[:-1]], dtype=torch.long)
            logits, _ = model(x)
            logp = F.log_softmax(logits, dim=-1)[0]
            tgt = full[1:]
            # supervised iff (t+1) >= n_prompt -> the completion tokens [4,5,6]
            manual = sum(float(logp[t, tgt[t]]) for t in range(len(tgt)) if (t + 1) >= n_prompt)
        self.assertAlmostEqual(float(got.item()), manual, places=5)

        # equals the negative of a reduction='sum' cross-entropy over the same masked targets
        with torch.no_grad():
            x = torch.tensor([full[:-1]], dtype=torch.long)
            logits, _ = model(x)
            labels = torch.tensor([[t if (i + 1) >= n_prompt else IGNORE_INDEX for i, t in enumerate(full[1:])]])
            ce_sum = F.cross_entropy(logits.reshape(-1, logits.size(-1)), labels.reshape(-1),
                                     ignore_index=IGNORE_INDEX, reduction="sum")
        self.assertAlmostEqual(float(got.item()), float(-ce_sum.item()), places=4)

    def test_invariant_to_batch_padding_width(self) -> None:
        model = _tiny_model()
        model.eval()
        short = ([1, 2, 3, 4], 2)        # completion [3,4]
        long = ([1, 2, 3, 4, 5, 6, 7], 2)
        alone = logp_completion(model, [short], 0, device=DEVICE)
        batched = logp_completion(model, [short, long], 0, device=DEVICE)
        # trailing padding is causal-masked, so the short example's logp is identical
        self.assertAlmostEqual(float(alone[0].item()), float(batched[0].item()), places=5)


class DpoLossTests(unittest.TestCase):
    def test_zero_margin_is_log2(self) -> None:
        z = torch.zeros(4)
        loss = dpo_loss(z, z, z, z, beta=0.1, use_reference=True)
        self.assertAlmostEqual(float(loss.item()), LOG2, places=6)

    def test_positive_margin_below_log2_no_ref(self) -> None:
        chosen = torch.tensor([0.0, 0.0])
        rejected = torch.tensor([-2.0, -3.0])  # chosen preferred
        loss = dpo_loss(chosen, rejected, torch.zeros(2), torch.zeros(2), beta=0.5, use_reference=False)
        self.assertLess(float(loss.item()), LOG2)

    def test_step0_with_ref_equals_log2_and_zero_relative_margin(self) -> None:
        model = _tiny_model()
        full_c = [1, 2, 3, 4, 5]
        full_r = [1, 2, 3, 6, 7]
        triples_c = [(full_c, 3)]
        triples_r = [(full_r, 3)]
        # ref == policy (same module) -> relative margin is exactly zero
        pol_c = logp_completion(model, triples_c, 0, device=DEVICE)
        pol_r = logp_completion(model, triples_r, 0, device=DEVICE)
        with torch.no_grad():
            ref_c = logp_completion(model, triples_c, 0, device=DEVICE)
            ref_r = logp_completion(model, triples_r, 0, device=DEVICE)
        rel = (pol_c - pol_r) - (ref_c - ref_r)
        self.assertAlmostEqual(float(rel.abs().max().item()), 0.0, places=6)
        loss = dpo_loss(pol_c, pol_r, ref_c, ref_r, beta=0.1, use_reference=True)
        self.assertAlmostEqual(float(loss.item()), LOG2, places=5)


class TrainDpoReferenceTests(unittest.TestCase):
    def test_reference_stays_frozen_and_unchanged(self) -> None:
        policy = _tiny_model()
        ref = _tiny_model()  # same seed -> identical init
        ref.requires_grad_(False)
        before = {k: v.detach().clone() for k, v in ref.state_dict().items()}
        triples = [([1, 2, 3, 4, 5], 3, [1, 2, 3, 6, 7], 3)] * 8
        train_dpo(policy, ref, triples, steps=5, lr=1e-2, beta=0.1, batch_size=4, device=DEVICE, pad_id=0)
        self.assertTrue(all(not p.requires_grad for p in ref.parameters()))
        for key, value in ref.state_dict().items():
            self.assertTrue(torch.allclose(value, before[key]), f"ref param {key} changed")

    def test_no_ref_runs_without_reference(self) -> None:
        policy = _tiny_model()
        triples = [([1, 2, 3, 4, 5], 3, [1, 2, 3, 6, 7], 3)] * 8
        last = train_dpo(policy, None, triples, steps=5, lr=1e-2, beta=0.1, batch_size=4,
                         device=DEVICE, pad_id=0, use_reference=False)
        self.assertTrue(math.isfinite(last))


class ConfusablePreferenceTests(unittest.TestCase):
    def test_drops_degenerate_pairs(self) -> None:
        # For op C (copy) the cyclically-next op is R (reverse); reverse of a
        # palindrome equals copy -> degenerate, must be dropped.
        examples = [
            SftExample(op="C", prompt="Caba=", completion="aba" + EOS),  # reverse("aba")=="aba" -> drop
            SftExample(op="C", prompt="Cabc=", completion="abc" + EOS),  # reverse("abc")=="cba" -> keep
        ]
        pairs, dropped = build_confusable_preferences(examples, ("C", "R"))
        self.assertEqual(dropped, 1)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].op, "C")
        self.assertEqual(pairs[0].reject_op, "R")
        self.assertEqual(pairs[0].chosen, "abc" + EOS)
        self.assertEqual(pairs[0].rejected, "cba" + EOS)
        self.assertNotEqual(pairs[0].chosen, pairs[0].rejected)

    def test_pair_text_helpers(self) -> None:
        pairs, _ = build_confusable_preferences([SftExample(op="R", prompt="Rabc=", completion="cba" + EOS)], ("C", "R", "S"))
        p = pairs[0]
        self.assertEqual(p.chosen_text, "Rabc=cba" + EOS)
        self.assertEqual(p.n_prompt, len("Rabc="))
        self.assertEqual(p.chosen_output, "cba")


class EvaluatePreferenceTests(unittest.TestCase):
    def test_metrics_present_and_bounded(self) -> None:
        model = _tiny_model()
        triples = [([1, 2, 3, 4, 5], 3, [1, 2, 3, 6, 7], 3), ([1, 2, 3, 5, 4], 3, [1, 2, 3, 7, 6], 3)]
        out = evaluate_preference(model, triples, 0, device=DEVICE)
        self.assertIn("preference_accuracy", out)
        self.assertTrue(0.0 <= out["preference_accuracy"] <= 1.0)
        self.assertAlmostEqual(out["mean_margin"], out["mean_logp_chosen"] - out["mean_logp_rejected"], places=5)


class RunDpoPreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ops = ("C", "R")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3,), inputs_per_op_length=24, heldout_ratio=0.25)
        train_pairs, dropped_train = build_confusable_preferences(corpus.train, ops)
        eval_pairs, dropped_eval = build_confusable_preferences(corpus.heldout, ops)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id, eos_id = tok.encode(PAD)[0], tok.encode(EOS)[0]

        def triple(p):
            return (tok.encode(p.chosen_text), p.n_prompt, tok.encode(p.rejected_text), p.n_prompt)

        cls.report = run_dpo_preference(
            vocab_size=tok.vocab_size,
            sft_init_train=[(tok.encode(e.text), len(e.prompt)) for e in corpus.train],
            pref_train_triples=[triple(p) for p in train_pairs],
            eval_triples=[triple(p) for p in eval_pairs],
            eval_heldout_instructions=[(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout],
            eval_confusable=[(tok.encode(p.prompt), tok.encode(p.chosen_output), tok.encode(p.rejected_output), p.op) for p in eval_pairs],
            ops=ops, pad_id=pad_id, eos_id=eos_id,
            config=DpoPreferenceConfig(
                block_size=16, seeds=(1337,), sft_init_steps=10, budget_sweep=(8, 16),
                beta=0.1, lr=1e-2, batch_size=8, n_layer=1, n_head=2, n_embd=16, max_new_tokens=5,
                scaling_betas=(0.1,), scaling_lrs=(1e-2,),
            ),
            device=DEVICE,
            corpus_stats={"pref_train_pairs": len(train_pairs), "pref_eval_pairs": len(eval_pairs),
                          "dropped_degenerate_pairs": dropped_train + dropped_eval},
            generated_at="2026-06-14T00:00:00Z",
        )

    def test_report_shape(self) -> None:
        r = self.report
        # sft_init row + 3 arms x 2 budgets
        self.assertEqual(len(r["rows"]), 1 + 3 * 2)
        arms = {row["arm"] for row in r["rows"]}
        self.assertEqual(arms, {"sft_init", "dpo_with_ref", "dpo_no_ref", "sft_on_chosen"})
        self.assertEqual(set(r["accuracy_curves"]["dpo_with_ref"]), {"8", "16"})
        self.assertEqual(set(r["pref_acc_curves"]["dpo_with_ref"]), {"8", "16"})
        self.assertEqual(len(r["scaling_grid_rows"]), 1)  # 1 beta x 1 lr

    def test_status_iff_task_learned(self) -> None:
        r = self.report
        s = r["summary"]
        self.assertIn(r["status"], {"pass", "review"})
        self.assertIs(r["status"] == "pass", s["task_learned"])

    def test_verdict_membership(self) -> None:
        s = self.report["summary"]
        self.assertIn(s["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)
        self.assertIn(s["reference_verdict"], REFERENCE_VERDICTS)
        self.assertIn(s["sft_control_verdict"], SFT_CONTROL_VERDICTS)
        if self.report["status"] == "pass":
            self.assertIn(s["verdict"], PRIMARY_VERDICTS)
            self.assertTrue(s["gate_lower"] <= s["sft_init_exact_match"] <= s["gate_upper"])
        else:
            self.assertIn(s["verdict"], REVIEW_VERDICTS)

    def test_compute_axis_documented(self) -> None:
        s = self.report["summary"]
        self.assertIn("forward_passes", s["compute_axis"])
        # dpo arms run budget//2 optimizer steps; sft_on_chosen runs budget
        dpo_row = next(row for row in self.report["rows"] if row["arm"] == "dpo_with_ref" and row["budget_forward_passes"] == 16)
        sft_row = next(row for row in self.report["rows"] if row["arm"] == "sft_on_chosen" and row["budget_forward_passes"] == 16)
        self.assertEqual(dpo_row["opt_steps"], 8)
        self.assertEqual(sft_row["opt_steps"], 16)


if __name__ == "__main__":
    unittest.main()
