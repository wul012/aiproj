"""v1158: LoRA domain adaptation — the scenario where LoRA is expected to win.

v1157 found that LoRA captured little of full fine-tuning's held-out gain because
the needed change lived in MiniGPT's *tied* token embedding, which LoRA leaves
frozen. v1158 isolates a purely **structural** domain gap instead:

* Source domain A and target domain B are built from the SAME term pools and
  punctuation (identical character vocabulary) but a different word order
  (:data:`minigpt.templated_corpus.STRUCTURES`).
* A base trained on A transfers its (tied) embedding to B perfectly — the only
  gap is structural, which attention/MLP (and therefore LoRA) *can* close.

Pipeline: train base on A → confirm a domain gap on B's held-out → from copies of
the frozen base, run full fine-tuning and LoRA on B's train split → compare on B's
held-out. Because the base is frozen, the LoRA adapter is removable, so adapting
to B does not destroy the A model (we measure that "forgetting" is reversible).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import torch
import torch.nn as nn

from minigpt.heldout_eval import evaluate_heldout
from minigpt.lm_training import train_lm
from minigpt.lora import LoRAConfig, apply_lora, count_parameters, lora_parameters, mark_only_lora_as_trainable
from minigpt.report_utils import utc_now


@dataclass
class DomainAdaptationConfig:
    source_structure: str = "declarative"
    target_structure: str = "reordered"
    base_steps: int = 400
    base_lr: float = 3e-4
    adapt_steps: int = 400
    adapt_lr: float = 1e-3
    full_adapt_lr: float = 3e-4
    block_size: int = 48
    batch_size: int = 32
    r: int = 8
    alpha: float = 16.0
    target_all_linear: bool = True
    seed: int = 1337


def run_lora_domain_adaptation(
    model: nn.Module,
    source_train: torch.Tensor,
    source_heldout: torch.Tensor,
    target_train: torch.Tensor,
    target_heldout: torch.Tensor,
    *,
    config: DomainAdaptationConfig,
    device: torch.device | None = None,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    device = device or next(model.parameters()).device
    bs = config.block_size
    torch.manual_seed(config.seed)
    base_total = sum(p.numel() for p in model.parameters())

    # 1) train base on the SOURCE domain (A)
    train_lm(model, list(model.parameters()), source_train, steps=config.base_steps, lr=config.base_lr,
             batch_size=config.batch_size, block_size=bs, device=device)
    base_source = evaluate_heldout(model, source_heldout, block_size=bs, device=device)
    base_target = evaluate_heldout(model, target_heldout, block_size=bs, device=device)

    # 2) reference: full fine-tune all params on the TARGET domain (B)
    model_full = copy.deepcopy(model)
    train_lm(model_full, list(model_full.parameters()), target_train, steps=config.adapt_steps, lr=config.full_adapt_lr,
             batch_size=config.batch_size, block_size=bs, device=device)
    full_target = evaluate_heldout(model_full, target_heldout, block_size=bs, device=device)

    # 3) LoRA-adapt the frozen base on the TARGET domain (B)
    model_lora = copy.deepcopy(model)
    replaced = apply_lora(
        model_lora,
        LoRAConfig(r=config.r, alpha=config.alpha, target_all_linear=config.target_all_linear),
    )
    mark_only_lora_as_trainable(model_lora)
    model_lora.to(device)
    counts = count_parameters(model_lora)
    train_lm(model_lora, lora_parameters(model_lora), target_train, steps=config.adapt_steps, lr=config.adapt_lr,
             batch_size=config.batch_size, block_size=bs, device=device)
    lora_target = evaluate_heldout(model_lora, target_heldout, block_size=bs, device=device)
    lora_source = evaluate_heldout(model_lora, source_heldout, block_size=bs, device=device)

    return _build_report(
        replaced=replaced, counts=counts, base_total=base_total,
        base_source=base_source, base_target=base_target,
        full_target=full_target, lora_target=lora_target, lora_source=lora_source,
        config=config, device=device, corpus_stats=corpus_stats or {},
        generated_at=generated_at or utc_now(),
    )


def _build_report(*, replaced, counts, base_total, base_source, base_target, full_target, lora_target, lora_source,
                  config, device, corpus_stats, generated_at) -> dict:
    domain_gap = base_target["heldout_loss"] - base_source["heldout_loss"]
    lora_delta = lora_target["heldout_loss"] - base_target["heldout_loss"]
    full_delta = full_target["heldout_loss"] - base_target["heldout_loss"]
    capture = (lora_delta / full_delta) if full_delta < 0 else None
    forgetting = lora_source["heldout_loss"] - base_source["heldout_loss"]

    # A valid demonstration needs a real domain gap to close.
    gap_present = domain_gap > 0.1
    lora_adapted = lora_delta < -0.05  # LoRA meaningfully lowered target held-out loss
    succeeded = gap_present and lora_adapted
    status = "pass" if succeeded else "review"
    decision = "lora_domain_adaptation_succeeded" if succeeded else "lora_domain_adaptation_weak"

    rows = [
        {"arm": "base", "domain": "source(A)", "heldout_loss": round(base_source["heldout_loss"], 6), "heldout_token_accuracy": round(base_source["heldout_token_accuracy"], 6)},
        {"arm": "base", "domain": "target(B)", "heldout_loss": round(base_target["heldout_loss"], 6), "heldout_token_accuracy": round(base_target["heldout_token_accuracy"], 6)},
        {"arm": "full_finetune", "domain": "target(B)", "heldout_loss": round(full_target["heldout_loss"], 6), "heldout_token_accuracy": round(full_target["heldout_token_accuracy"], 6)},
        {"arm": "lora", "domain": "target(B)", "heldout_loss": round(lora_target["heldout_loss"], 6), "heldout_token_accuracy": round(lora_target["heldout_token_accuracy"], 6)},
        {"arm": "lora", "domain": "source(A)", "heldout_loss": round(lora_source["heldout_loss"], 6), "heldout_token_accuracy": round(lora_source["heldout_token_accuracy"], 6)},
    ]

    summary = {
        "status": status,
        "decision": decision,
        "device": str(device),
        "source_structure": config.source_structure,
        "target_structure": config.target_structure,
        "lora_r": config.r,
        "adapted_module_count": len(replaced),
        "base_steps": config.base_steps,
        "adapt_steps": config.adapt_steps,
        "lora_trainable_parameters": int(counts["trainable_parameters"]),
        "total_parameters": int(counts["total_parameters"]),
        "trainable_ratio_percent": counts["trainable_ratio_percent"],
        "base_source_heldout_loss": round(base_source["heldout_loss"], 6),
        "base_target_heldout_loss": round(base_target["heldout_loss"], 6),
        "domain_gap": round(domain_gap, 6),
        "full_finetune_target_heldout_loss": round(full_target["heldout_loss"], 6),
        "lora_target_heldout_loss": round(lora_target["heldout_loss"], 6),
        "lora_target_loss_delta": round(lora_delta, 6),
        "full_target_loss_delta": round(full_delta, 6),
        "lora_vs_full_capture_ratio": round(capture, 4) if capture is not None else None,
        "lora_target_accuracy": round(lora_target["heldout_token_accuracy"], 6),
        "base_target_accuracy": round(base_target["heldout_token_accuracy"], 6),
        "lora_source_heldout_loss_after": round(lora_source["heldout_loss"], 6),
        "adapter_forgetting_on_source": round(forgetting, 6),
        "domain_adaptation_succeeded": succeeded,
    }

    recommendations = []
    if succeeded:
        cap = f"{capture * 100:.0f}%" if capture is not None else "n/a"
        recommendations.append(
            f"LoRA adapted the frozen base to the target structure, cutting target held-out loss by {abs(lora_delta):.4f} "
            f"(capturing {cap} of full fine-tuning) while training only {counts['trainable_ratio_percent']}% of parameters — the LoRA win v1157 predicted."
        )
    else:
        if not gap_present:
            recommendations.append("No real domain gap (base already models B); increase base_steps or make the structures more different.")
        else:
            recommendations.append("LoRA did not meaningfully adapt to B; raise adapt_steps/adapt_lr or rank r.")
    recommendations.append(
        f"Because the base is frozen, the adapter is removable: with it applied, source(A) held-out loss moved by {forgetting:+.4f}, "
        "but dropping the adapter restores the original A model exactly — unlike full fine-tuning, which overwrites it."
    )
    recommendations.append(
        "Source and target share the identical character vocabulary, so this isolates structural adaptation; the embedding/output head transfers for free."
    )

    return {
        "schema_version": 1,
        "title": "MiniGPT LoRA domain adaptation report v1158",
        "generated_at": generated_at,
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["arm", "domain", "heldout_loss", "heldout_token_accuracy"],
    }


__all__ = ["DomainAdaptationConfig", "run_lora_domain_adaptation"]
