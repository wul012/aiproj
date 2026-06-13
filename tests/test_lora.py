from __future__ import annotations

import unittest

import torch

from minigpt.lora import (
    LoRAConfig,
    LoRALinear,
    apply_lora,
    count_parameters,
    lora_parameters,
    lora_state_dict,
    mark_only_lora_as_trainable,
    merge_lora,
)
from minigpt.model import GPTConfig, MiniGPT


def _tiny_model() -> MiniGPT:
    torch.manual_seed(0)
    config = GPTConfig(vocab_size=24, block_size=16, n_layer=2, n_head=2, n_embd=16, dropout=0.0)
    return MiniGPT(config)


class LoRALinearTests(unittest.TestCase):
    def test_zero_initialised_update_is_identity(self) -> None:
        torch.manual_seed(1)
        base = torch.nn.Linear(8, 12)
        wrapped = LoRALinear(base, r=4, alpha=8.0)
        x = torch.randn(3, 5, 8)
        # lora_B starts at zero, so the wrapped layer must match the base exactly.
        self.assertTrue(torch.allclose(wrapped(x), base(x), atol=1e-6))

    def test_forward_shape_and_nonzero_update(self) -> None:
        torch.manual_seed(2)
        base = torch.nn.Linear(8, 12)
        wrapped = LoRALinear(base, r=4, alpha=8.0)
        torch.nn.init.normal_(wrapped.lora_B, std=0.1)  # break the zero init
        x = torch.randn(3, 5, 8)
        out = wrapped(x)
        self.assertEqual(out.shape, (3, 5, 12))
        self.assertFalse(torch.allclose(out, base(x), atol=1e-6))

    def test_base_weight_is_frozen(self) -> None:
        base = torch.nn.Linear(8, 12)
        wrapped = LoRALinear(base, r=2, alpha=4.0)
        self.assertFalse(wrapped.base.weight.requires_grad)
        self.assertTrue(wrapped.lora_A.requires_grad)
        self.assertTrue(wrapped.lora_B.requires_grad)

    def test_merge_matches_unmerged_forward(self) -> None:
        torch.manual_seed(3)
        base = torch.nn.Linear(8, 12)
        wrapped = LoRALinear(base, r=4, alpha=8.0)
        torch.nn.init.normal_(wrapped.lora_B, std=0.2)
        x = torch.randn(2, 4, 8)
        before = wrapped(x)
        wrapped.merge()
        after = wrapped(x)
        self.assertTrue(wrapped.merged)
        self.assertTrue(torch.allclose(before, after, atol=1e-5))
        wrapped.unmerge()
        self.assertFalse(wrapped.merged)
        self.assertTrue(torch.allclose(wrapped(x), before, atol=1e-5))

    def test_rejects_non_linear(self) -> None:
        with self.assertRaises(TypeError):
            LoRALinear(torch.nn.ReLU(), r=2, alpha=4.0)  # type: ignore[arg-type]


class ApplyLoraTests(unittest.TestCase):
    def test_replaces_targeted_modules(self) -> None:
        model = _tiny_model()
        replaced = apply_lora(model, LoRAConfig(r=4, alpha=8.0, target_modules=("c_attn", "c_proj")))
        # 2 layers x {c_attn, c_proj} = 4 adapters.
        self.assertEqual(len(replaced), 4)
        for block in model.blocks:
            self.assertIsInstance(block.attn.c_attn, LoRALinear)
            self.assertIsInstance(block.attn.c_proj, LoRALinear)

    def test_raises_when_no_target_found(self) -> None:
        model = _tiny_model()
        with self.assertRaises(ValueError):
            apply_lora(model, LoRAConfig(target_modules=("does_not_exist",)))

    def test_only_lora_is_trainable(self) -> None:
        model = _tiny_model()
        apply_lora(model, LoRAConfig(r=4, alpha=8.0))
        mark_only_lora_as_trainable(model)
        for name, param in model.named_parameters():
            self.assertEqual(param.requires_grad, "lora_" in name, name)
        trainable = lora_parameters(model)
        self.assertTrue(trainable)
        self.assertTrue(all(p.requires_grad for p in trainable))

    def test_count_parameters_ratio_is_small(self) -> None:
        model = _tiny_model()
        apply_lora(model, LoRAConfig(r=4, alpha=8.0))
        mark_only_lora_as_trainable(model)
        counts = count_parameters(model)
        self.assertLess(counts["trainable_parameters"], counts["total_parameters"])
        self.assertGreater(counts["trainable_ratio_percent"], 0.0)
        self.assertLess(counts["trainable_ratio_percent"], 50.0)

    def test_lora_state_dict_only_has_adapters(self) -> None:
        model = _tiny_model()
        apply_lora(model, LoRAConfig(r=4, alpha=8.0))
        state = lora_state_dict(model)
        self.assertTrue(state)
        self.assertTrue(all("lora_" in key for key in state))

    def test_merge_lora_counts_all_adapters(self) -> None:
        model = _tiny_model()
        apply_lora(model, LoRAConfig(r=4, alpha=8.0))
        self.assertEqual(merge_lora(model), 4)


class ConfigValidationTests(unittest.TestCase):
    def test_invalid_rank(self) -> None:
        with self.assertRaises(ValueError):
            LoRAConfig(r=0)

    def test_invalid_dropout(self) -> None:
        with self.assertRaises(ValueError):
            LoRAConfig(dropout=1.0)

    def test_empty_targets(self) -> None:
        with self.assertRaises(ValueError):
            LoRAConfig(target_modules=())


if __name__ == "__main__":
    unittest.main()
