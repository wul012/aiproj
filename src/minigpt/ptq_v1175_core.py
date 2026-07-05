"""Reusable post-training quantization primitives for v1175."""

from __future__ import annotations

import copy

import torch
import torch.nn.functional as F

from minigpt.experiment_utils import significant
from minigpt.sft_training import IGNORE_INDEX

SCHEMES = ("absmax_sym", "percentile_clip", "mse_clip", "affine_asym")
GRANULARITIES = ("per_tensor", "per_channel_row", "per_channel_col", "group32")
COMPONENTS = ("embedding", "c_attn", "c_proj", "mlp", "attention", "all")
_MSE_RATIOS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5)


def beats_lower(a, sa, b, sb):
    """True iff ``a`` is significantly LOWER (better, for a loss) than ``b``."""
    return significant(b, sb, a, sa)


# --------------------------------------------------------------------------
# quantizer: 2-D weight -> dequantized, by group (granularity) and scheme
# --------------------------------------------------------------------------
def _to_groups(W, granularity):
    out, inn = W.shape
    if granularity == "per_tensor":
        return W.reshape(1, -1), ("pt", (out, inn))
    if granularity == "per_channel_row":
        return W.reshape(out, inn), ("row", (out, inn))
    if granularity == "per_channel_col":
        return W.t().contiguous().reshape(inn, out), ("col", (out, inn))
    if granularity == "group32":
        g = 32 if inn % 32 == 0 else _largest_divisor_leq(inn, 32)
        return W.reshape(out * (inn // g), g), ("grp", (out, inn))
    raise ValueError(f"unknown granularity {granularity}")


def _largest_divisor_leq(n, cap):
    for g in range(min(cap, n), 0, -1):
        if n % g == 0:
            return g
    return 1


def _from_groups(q, meta):
    kind, shape = meta
    out, inn = shape
    if kind == "col":
        return q.reshape(inn, out).t().contiguous()
    return q.reshape(out, inn)


def _quantize_groups(g2d, bits, scheme):
    """Quantize each row of ``g2d`` (G, group_size) independently, return dequantized."""
    qmax = 2 ** (bits - 1) - 1
    qmin = -(2 ** (bits - 1))
    if scheme == "affine_asym":
        wmin = g2d.amin(1, keepdim=True)
        wmax = g2d.amax(1, keepdim=True)
        s = ((wmax - wmin) / (2 ** bits - 1)).clamp_min(1e-12)
        zp = (-(wmin / s)).round()
        q = (g2d / s + zp).round().clamp(0, 2 ** bits - 1)
        return (q - zp) * s
    # symmetric family: choose the clip threshold `amax`, then RTN
    if scheme == "absmax_sym":
        amax = g2d.abs().amax(1, keepdim=True)
    elif scheme == "percentile_clip":
        amax = torch.quantile(g2d.abs(), 0.999, dim=1, keepdim=True)
    elif scheme == "mse_clip":
        base_amax = g2d.abs().amax(1, keepdim=True).clamp_min(1e-12)
        best_amax = base_amax.clone()
        best_mse = None
        for r in _MSE_RATIOS:
            a = (base_amax * r).clamp_min(1e-12)
            s = a / qmax
            mse = (((g2d / s).round().clamp(qmin, qmax) * s - g2d) ** 2).mean(1, keepdim=True)
            if best_mse is None:
                best_mse = mse
            else:
                better = mse < best_mse
                best_amax = torch.where(better, a, best_amax)
                best_mse = torch.where(better, mse, best_mse)
        amax = best_amax
    else:
        raise ValueError(f"unknown scheme {scheme}")
    s = (amax / qmax).clamp_min(1e-12)
    return (g2d / s).round().clamp(qmin, qmax) * s


def quantize_tensor(W, bits, *, granularity="per_channel_row", scheme="absmax_sym"):
    g2d, meta = _to_groups(W, granularity)
    return _from_groups(_quantize_groups(g2d, bits, scheme), meta)


def n_scale_groups(W, granularity):
    out, inn = W.shape
    if granularity == "per_tensor":
        return 1
    if granularity == "per_channel_row":
        return out
    if granularity == "per_channel_col":
        return inn
    g = 32 if inn % 32 == 0 else _largest_divisor_leq(inn, 32)
    return out * (inn // g)


# --------------------------------------------------------------------------
# which 2-D weights belong to each component (named_parameters dedups the tie)
# --------------------------------------------------------------------------
def component_param_names(model, component):
    names = []
    for name, p in model.named_parameters():
        if p.ndim < 2 or name == "position_embedding.weight":
            continue
        is_emb = name == "token_embedding.weight"   # tied: also the lm_head
        is_cattn = ".attn.c_attn.weight" in name
        is_cproj = ".attn.c_proj.weight" in name
        is_mlp = ".mlp.net." in name
        hit = (component == "all"
               or (component == "embedding" and is_emb)
               or (component == "c_attn" and is_cattn)
               or (component == "c_proj" and is_cproj)
               or (component == "mlp" and is_mlp)
               or (component == "attention" and (is_cattn or is_cproj)))
        if hit:
            names.append(name)
    return names


@torch.no_grad()
def quantized_model(base, bits, component, *, granularity="per_channel_row", scheme="absmax_sym"):
    """A deep copy with the ``component`` weights fake-quantized IN PLACE by parameter
    identity — so the tied embedding/lm_head is quantized once and never reverted."""
    m = copy.deepcopy(base)
    targets = set(component_param_names(m, component))
    seen = set()
    for name, p in m.named_parameters():
        if id(p) in seen:
            continue
        seen.add(id(p))
        if name in targets:
            p.data = quantize_tensor(p.data, bits, granularity=granularity, scheme=scheme)
    return m


def effective_bits_per_weight(model, component, bits, granularity, scale_bits=16):
    """Nominal bits plus the per-group fp scale metadata, weighted by matrix size."""
    targets = set(component_param_names(model, component))
    tot_w = tot_bits = 0
    seen = set()
    for name, p in model.named_parameters():
        if id(p) in seen or name not in targets:
            continue
        seen.add(id(p))
        nw = p.numel()
        ns = n_scale_groups(p.data, granularity)
        tot_w += nw
        tot_bits += bits * nw + scale_bits * ns
    return tot_bits / max(tot_w, 1)


@torch.no_grad()
def ce_and_kl(model, X, Y, ref_logits=None):
    """Mean completion-token CE; and KL(softmax(ref)‖softmax(model)) at those positions
    (NaN if no ref). Returns (ce, kl, logits)."""
    model.eval()
    logits, _ = model(X)
    V = logits.size(-1)
    ce = float(F.cross_entropy(logits.reshape(-1, V), Y.reshape(-1), ignore_index=IGNORE_INDEX).item())
    kl = float("nan")
    if ref_logits is not None:
        mask = (Y != IGNORE_INDEX)
        p = F.softmax(ref_logits, dim=-1)
        logq = F.log_softmax(logits, dim=-1)
        logp = F.log_softmax(ref_logits, dim=-1)
        kl_tok = (p * (logp - logq)).sum(-1)
        kl = float((kl_tok[mask]).mean().item())
    return ce, kl, logits


@torch.no_grad()
def weight_rel_error(base, qmodel, component):
    targets = set(component_param_names(base, component))
    bd = dict(base.named_parameters())
    qd = dict(qmodel.named_parameters())
    num = den = 0.0
    for name in targets:
        num += float((bd[name] - qd[name]).norm().item()) ** 2
        den += float(bd[name].norm().item()) ** 2
    return (num ** 0.5) / (den ** 0.5 + 1e-12)




__all__ = [
    "COMPONENTS",
    "GRANULARITIES",
    "SCHEMES",
    "beats_lower",
    "ce_and_kl",
    "component_param_names",
    "effective_bits_per_weight",
    "n_scale_groups",
    "quantize_tensor",
    "quantized_model",
    "weight_rel_error",
]
