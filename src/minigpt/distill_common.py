"""Shared primitives for the MiniGPT distillation experiments.

The v1172 deterministic distillation run and the v1173 stochastic
dark-knowledge run use the same low-level training contract: completion-token
masking, Hinton KL, residual-mass shuffling, and the small RoPE MiniGPT factory.
Keeping those helpers here prevents later distillation variants from importing a
versioned experiment module just to reach a reusable primitive.
"""

from __future__ import annotations

from collections.abc import Callable

import torch
import torch.nn.functional as F

from minigpt.model import GPTConfig, MiniGPT
from minigpt.sft_training import IGNORE_INDEX


def _build_xy(examples, block_size: int, pad_id: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Return padded ``X`` and completion-masked ``Y`` for SFT/KD training."""
    n = len(examples)
    X = torch.full((n, block_size), pad_id, dtype=torch.long)
    Y = torch.full((n, block_size), IGNORE_INDEX, dtype=torch.long)
    for i, (full, n_prompt) in enumerate(examples):
        inp, tgt = full[:-1], full[1:]
        X[i, : len(inp)] = torch.tensor(inp, dtype=torch.long)
        for t, tok in enumerate(tgt):
            if (t + 1) < n_prompt:
                continue
            Y[i, t] = tok
    return X, Y


def kl_term(student_logits: torch.Tensor, teacher_probs: torch.Tensor, mask: torch.Tensor, tau: float) -> torch.Tensor:
    """Hinton KD KL over masked completion tokens with the ``tau^2`` correction."""
    logp_s = F.log_softmax(student_logits / tau, dim=-1)
    kl_tok = (teacher_probs * (teacher_probs.clamp_min(1e-9).log() - logp_s)).sum(-1)
    return (kl_tok * mask).sum() / mask.sum().clamp_min(1) * (tau * tau)


def shuffle_residual_mass(probs: torch.Tensor, perm: torch.Tensor) -> torch.Tensor:
    """Permute non-argmax probabilities while preserving argmax, max-prob, and entropy."""
    B, T, V = probs.shape
    argmax = probs.argmax(dim=-1)
    order = torch.arange(V, device=probs.device).view(1, 1, V)
    non_argmax = order != argmax.unsqueeze(-1)
    residual = probs[non_argmax].view(B, T, V - 1)
    residual = residual[..., perm]
    out = probs.clone()
    out[non_argmax] = residual.reshape(-1)
    return out


def train_student(
    student: MiniGPT,
    examples,
    *,
    steps: int,
    lr: float,
    batch_size: int,
    block_size: int,
    pad_id: int,
    device,
    loss_mode: str,
    teacher: MiniGPT | None = None,
    tau: float = 1.0,
    hard_weight: float = 1.0,
    label_smoothing: float = 0.0,
    shuffle_perm: torch.Tensor | None = None,
    teacher_probs_fn: Callable[[torch.Tensor], torch.Tensor] | None = None,
) -> float:
    """Train one student arm under hard CE or completion-token distillation."""
    X, Y = _build_xy(examples, block_size, pad_id)
    X, Y = X.to(device), Y.to(device)
    n, V = X.shape[0], student.config.vocab_size
    if teacher is not None:
        teacher.eval()
    opt = torch.optim.AdamW(student.parameters(), lr=lr)
    student.train()
    last = float("nan")
    for _ in range(steps):
        sel = torch.randint(0, n, (batch_size,), device=device)
        x, y = X[sel], Y[sel]
        z_s, _ = student(x)
        if loss_mode == "ce":
            loss = F.cross_entropy(
                z_s.reshape(-1, V), y.reshape(-1),
                ignore_index=IGNORE_INDEX, label_smoothing=label_smoothing,
            )
        else:
            with torch.no_grad():
                if teacher_probs_fn is not None:
                    p_t = teacher_probs_fn(x)
                else:
                    assert teacher is not None
                    z_t, _ = teacher(x)
                    p_t = F.softmax(z_t / tau, dim=-1)
                    if shuffle_perm is not None:
                        p_t = shuffle_residual_mass(p_t, shuffle_perm)
            mask = y != IGNORE_INDEX
            kl = kl_term(z_s, p_t, mask, tau)
            ce = F.cross_entropy(z_s.reshape(-1, V), y.reshape(-1), ignore_index=IGNORE_INDEX)
            loss = hard_weight * ce + (1.0 - hard_weight) * kl
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        last = float(loss.item())
    return last


@torch.no_grad()
def teacher_logit_stats(teacher: MiniGPT, examples, block_size: int, pad_id: int) -> tuple[float, float]:
    """Mean max-prob and entropy at completion-token positions."""
    X, Y = _build_xy(examples, block_size, pad_id)
    device = next(teacher.parameters()).device
    X, Y = X.to(device), Y.to(device)
    teacher.eval()
    logits, _ = teacher(X)
    probs = F.softmax(logits, dim=-1)
    mask = Y != IGNORE_INDEX
    maxp = probs.max(dim=-1).values[mask]
    entropy = (-(probs.clamp_min(1e-9).log() * probs).sum(-1))[mask]
    return float(maxp.mean().item()), float(entropy.mean().item())


def make_distill_model(vocab_size: int, block_size: int, n_layer: int, n_head: int, n_embd: int) -> MiniGPT:
    """Build the zero-dropout RoPE MiniGPT used by distillation experiments."""
    return MiniGPT(
        GPTConfig(
            vocab_size=vocab_size,
            block_size=block_size,
            n_layer=n_layer,
            n_head=n_head,
            n_embd=n_embd,
            dropout=0.0,
            use_rope=True,
        )
    )


__all__ = [
    "_build_xy",
    "kl_term",
    "make_distill_model",
    "shuffle_residual_mass",
    "teacher_logit_stats",
    "train_student",
]
