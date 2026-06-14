from __future__ import annotations

import unittest

import torch
import torch.nn.functional as F

from minigpt.dpo_preference_v1166 import build_confusable_preferences, logp_completion, train_dpo
from minigpt.dpo_sft_aux_v1168 import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    DpoSftAuxConfig,
    chosen_logp_and_ce,
    run_dpo_sft_aux,
    train_dpo_sft,
)
from minigpt.experiment_utils import build_minigpt
from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.sft_training import IGNORE_INDEX
from minigpt.tokenizer import CharTokenizer

DEVICE = torch.device("cpu")


def _tiny() -> MiniGPT:
    torch.manual_seed(0)
    return MiniGPT(GPTConfig(vocab_size=10, block_size=8, n_layer=1, n_head=2, n_embd=16, dropout=0.0, use_rope=True))


class ChosenLogpAndCeTests(unittest.TestCase):
    def test_summed_matches_logp_completion_and_ce_matches_cross_entropy(self) -> None:
        model = _tiny()
        model.eval()
        examples = [([1, 2, 3, 4, 5], 3), ([1, 2, 3, 5, 4], 3)]
        with torch.no_grad():
            summed, ce = chosen_logp_and_ce(model, examples, 0, device=DEVICE)
            ref_summed = logp_completion(model, examples, 0, device=DEVICE)
        self.assertTrue(torch.allclose(summed, ref_summed, atol=1e-5))

        # ce equals F.cross_entropy over the same (t+1)>=n_prompt masked labels
        n = len(examples); width = max(len(f) for f, _ in examples) - 1
        X = torch.full((n, width), 0, dtype=torch.long)
        labels = torch.full((n, width), IGNORE_INDEX, dtype=torch.long)
        for i, (full, npr) in enumerate(examples):
            X[i, : len(full[:-1])] = torch.tensor(full[:-1])
            for t, tok in enumerate(full[1:]):
                if (t + 1) >= npr:
                    labels[i, t] = tok
        with torch.no_grad():
            logits, _ = model(X)
            expect = F.cross_entropy(logits.reshape(-1, logits.size(-1)), labels.reshape(-1), ignore_index=IGNORE_INDEX)
        self.assertAlmostEqual(float(ce.item()), float(expect.item()), places=5)


class TrainDpoSftLambdaZeroTests(unittest.TestCase):
    def test_lambda_zero_reproduces_vanilla_dpo(self) -> None:
        triples = [([1, 2, 3, 4, 5], 3, [1, 2, 3, 6, 7], 3)] * 8
        # vanilla DPO via v1166
        pol_a = _tiny(); ref_a = _tiny(); ref_a.requires_grad_(False)
        torch.manual_seed(123)
        train_dpo(pol_a, ref_a, triples, steps=6, lr=1e-2, beta=0.1, batch_size=4, device=DEVICE, pad_id=0)
        # DPO+SFT with λ=0 via v1168
        pol_b = _tiny(); ref_b = _tiny(); ref_b.requires_grad_(False)
        torch.manual_seed(123)
        train_dpo_sft(pol_b, ref_b, triples, steps=6, lr=1e-2, beta=0.1, sft_aux_lambda=0.0,
                      batch_size=4, device=DEVICE, pad_id=0)
        for k, v in pol_a.state_dict().items():
            self.assertTrue(torch.allclose(v, pol_b.state_dict()[k], atol=1e-6), f"param {k} diverged at λ=0")

    def test_positive_lambda_changes_the_update(self) -> None:
        triples = [([1, 2, 3, 4, 5], 3, [1, 2, 3, 6, 7], 3)] * 8
        pol_a = _tiny(); ref_a = _tiny(); ref_a.requires_grad_(False)
        torch.manual_seed(123)
        train_dpo_sft(pol_a, ref_a, triples, steps=6, lr=1e-2, beta=0.1, sft_aux_lambda=0.0,
                      batch_size=4, device=DEVICE, pad_id=0)
        pol_b = _tiny(); ref_b = _tiny(); ref_b.requires_grad_(False)
        torch.manual_seed(123)
        train_dpo_sft(pol_b, ref_b, triples, steps=6, lr=1e-2, beta=0.1, sft_aux_lambda=1.0,
                      batch_size=4, device=DEVICE, pad_id=0)
        diverged = any(not torch.allclose(v, pol_b.state_dict()[k]) for k, v in pol_a.state_dict().items())
        self.assertTrue(diverged, "λ=1 should change the update vs λ=0")


class RunDpoSftAuxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ops = ("C", "R")
        corpus = build_sft_corpus(seed=0, ops=ops, lengths=(3,), inputs_per_op_length=24, heldout_ratio=0.25)
        train_pairs, dt = build_confusable_preferences(corpus.train, ops)
        eval_pairs, de = build_confusable_preferences(corpus.heldout, ops)
        tok = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
        pad_id, eos_id = tok.encode(PAD)[0], tok.encode(EOS)[0]

        def triple(p):
            return (tok.encode(p.chosen_text), p.n_prompt, tok.encode(p.rejected_text), p.n_prompt)

        cls.report = run_dpo_sft_aux(
            vocab_size=tok.vocab_size,
            sft_init_train=[(tok.encode(e.text), len(e.prompt)) for e in corpus.train],
            pref_train_triples=[triple(p) for p in train_pairs],
            eval_triples=[triple(p) for p in eval_pairs],
            eval_heldout_instructions=[(tok.encode(e.prompt), tok.encode(e.expected_output), e.op) for e in corpus.heldout],
            eval_confusable=[(tok.encode(p.prompt), tok.encode(p.chosen_output), tok.encode(p.rejected_output), p.op) for p in eval_pairs],
            ops=ops, pad_id=pad_id, eos_id=eos_id,
            config=DpoSftAuxConfig(block_size=16, seeds=(1337,), sft_init_steps=10, budget=8,
                                   lambda_grid=(0.0, 1.0), beta=0.1, lr=1e-2, batch_size=8,
                                   n_layer=1, n_head=2, n_embd=16, max_new_tokens=5),
            device=DEVICE,
            corpus_stats={"pref_train_pairs": len(train_pairs), "pref_eval_pairs": len(eval_pairs),
                          "dropped_degenerate_pairs": dt + de},
            generated_at="2026-06-14T00:00:00Z",
        )

    def test_report_shape(self) -> None:
        r = self.report
        arms = {row["arm"] for row in r["rows"]}
        self.assertEqual(arms, {"sft_init", "dpo_aux_l0", "dpo_aux_l1", "sft_on_chosen"})
        self.assertEqual(set(r["exact_match_by_lambda"]), {"0", "1"})

    def test_status_iff_task_learned(self) -> None:
        r = self.report
        self.assertIn(r["status"], {"pass", "review"})
        self.assertIs(r["status"] == "pass", r["summary"]["task_learned"])

    def test_verdict_membership(self) -> None:
        s = self.report["summary"]
        self.assertIn(s["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)
        self.assertIn(s["vanilla_dpo_verdict"], {"vanilla_dpo_regresses_generation", "vanilla_dpo_no_regression_at_this_scale"})
        if self.report["status"] == "pass":
            self.assertIn(s["verdict"], PRIMARY_VERDICTS)


if __name__ == "__main__":
    unittest.main()
