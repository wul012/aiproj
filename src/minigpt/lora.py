"""Low-Rank Adaptation (LoRA) for the MiniGPT model.

This is a from-scratch LoRA implementation used to fine-tune a frozen MiniGPT
checkpoint by training only small low-rank update matrices. It targets the
``nn.Linear`` layers inside :class:`minigpt.model.CausalSelfAttention`
(``c_attn`` and ``c_proj`` by default).

Design notes
------------
* :class:`LoRALinear` wraps an existing ``nn.Linear``. The original weight is
  frozen; the trainable update is ``B @ A`` scaled by ``alpha / r``.
* ``A`` is kaiming-initialised and ``B`` starts at zero, so at initialisation the
  adapter contributes nothing and the wrapped layer is numerically identical to
  the base layer. This makes "before" measurements faithful to the base model.
* :func:`merge_lora` folds the update back into the base weight so a fine-tuned
  model can be served with no extra parameters and no forward-pass overhead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn as nn


@dataclass
class LoRAConfig:
    """Configuration for applying LoRA to a model.

    Either name specific ``target_modules`` (e.g. attention projections) or set
    ``target_all_linear=True`` to adapt every ``nn.Linear`` except those in
    ``exclude_modules``. Targeting all linears (attention + MLP) is the realistic
    LoRA setup and matters a lot on small models, where attention-only adaptation
    leaves most of the signal in the untouched MLP/embedding layers.
    """

    r: int = 8
    alpha: float = 16.0
    dropout: float = 0.0
    target_modules: tuple[str, ...] = ("c_attn", "c_proj")
    target_all_linear: bool = False
    exclude_modules: tuple[str, ...] = ("lm_head",)

    def __post_init__(self) -> None:
        if self.r <= 0:
            raise ValueError("LoRA rank r must be a positive integer")
        if self.alpha <= 0:
            raise ValueError("LoRA alpha must be positive")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("LoRA dropout must be in [0, 1)")
        if not self.target_all_linear and not self.target_modules:
            raise ValueError("name at least one target module or set target_all_linear=True")

    def matches(self, child_name: str) -> bool:
        if child_name in self.exclude_modules:
            return False
        if self.target_all_linear:
            return True
        return child_name in self.target_modules


class LoRALinear(nn.Module):
    """An ``nn.Linear`` with a frozen base weight and a trainable low-rank update."""

    def __init__(self, base: nn.Linear, r: int, alpha: float, dropout: float = 0.0) -> None:
        super().__init__()
        if not isinstance(base, nn.Linear):
            raise TypeError("LoRALinear can only wrap an nn.Linear module")
        if r <= 0:
            raise ValueError("LoRA rank r must be a positive integer")

        self.base = base
        for param in self.base.parameters():
            param.requires_grad_(False)

        self.r = r
        self.alpha = float(alpha)
        self.scaling = float(alpha) / r
        self.lora_dropout: nn.Module = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        weight = base.weight
        self.lora_A = nn.Parameter(torch.zeros(r, base.in_features, device=weight.device, dtype=weight.dtype))
        self.lora_B = nn.Parameter(torch.zeros(base.out_features, r, device=weight.device, dtype=weight.dtype))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        # lora_B stays zero so the initial update is exactly zero.
        self.merged = False

    @property
    def in_features(self) -> int:
        return self.base.in_features

    @property
    def out_features(self) -> int:
        return self.base.out_features

    def _delta_weight(self) -> torch.Tensor:
        return (self.lora_B @ self.lora_A) * self.scaling

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result = self.base(x)
        if self.merged:
            return result
        update = (self.lora_dropout(x) @ self.lora_A.t()) @ self.lora_B.t()
        return result + update * self.scaling

    @torch.no_grad()
    def merge(self) -> None:
        """Fold the low-rank update into the base weight."""
        if self.merged:
            return
        self.base.weight.add_(self._delta_weight().to(self.base.weight.dtype))
        self.merged = True

    @torch.no_grad()
    def unmerge(self) -> None:
        """Undo :meth:`merge`."""
        if not self.merged:
            return
        self.base.weight.sub_(self._delta_weight().to(self.base.weight.dtype))
        self.merged = False

    def lora_parameter_count(self) -> int:
        return self.lora_A.numel() + self.lora_B.numel()


def apply_lora(model: nn.Module, config: LoRAConfig) -> list[str]:
    """Replace every targeted ``nn.Linear`` in ``model`` with a :class:`LoRALinear`.

    Returns the dotted names of the replaced modules. Raises ``ValueError`` if no
    target module is found, so a typo in ``target_modules`` fails loudly instead
    of silently fine-tuning nothing.
    """
    replaced: list[str] = []
    for module_name, module in list(model.named_modules()):
        if isinstance(module, LoRALinear):
            continue  # never wrap the frozen base inside an existing adapter
        for child_name, child in list(module.named_children()):
            if isinstance(child, nn.Linear) and config.matches(child_name):
                wrapped = LoRALinear(child, r=config.r, alpha=config.alpha, dropout=config.dropout)
                setattr(module, child_name, wrapped)
                replaced.append(f"{module_name}.{child_name}" if module_name else child_name)
    if not replaced:
        target = "all linear" if config.target_all_linear else repr(config.target_modules)
        raise ValueError(f"apply_lora found no matching Linear submodules ({target}); nothing to fine-tune")
    return replaced


def mark_only_lora_as_trainable(model: nn.Module) -> None:
    """Freeze every parameter except the LoRA update matrices."""
    for name, param in model.named_parameters():
        param.requires_grad_("lora_" in name)


def lora_parameters(model: nn.Module) -> list[nn.Parameter]:
    """Return the trainable LoRA parameters (for handing to an optimizer)."""
    return [param for name, param in model.named_parameters() if "lora_" in name]


def count_parameters(model: nn.Module) -> dict[str, float | int]:
    """Summarise total vs trainable parameter counts."""
    total = sum(param.numel() for param in model.parameters())
    trainable = sum(param.numel() for param in model.parameters() if param.requires_grad)
    ratio = (trainable / total * 100.0) if total else 0.0
    return {
        "total_parameters": int(total),
        "trainable_parameters": int(trainable),
        "trainable_ratio_percent": round(ratio, 4),
    }


def lora_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    """Extract only the LoRA tensors so adapters can be saved compactly."""
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items() if "lora_" in key}


def merge_lora(model: nn.Module) -> int:
    """Merge every :class:`LoRALinear` update into its base weight. Returns the count merged."""
    merged = 0
    for module in model.modules():
        if isinstance(module, LoRALinear):
            module.merge()
            merged += 1
    return merged


__all__ = [
    "LoRAConfig",
    "LoRALinear",
    "apply_lora",
    "count_parameters",
    "lora_parameters",
    "lora_state_dict",
    "mark_only_lora_as_trainable",
    "merge_lora",
]
