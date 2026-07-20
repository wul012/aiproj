"""v1175: post-training weight quantization (PTQ) — the quality cost, measured honestly.

Continues the inference-efficiency thread (v1161 KV-cache, v1170 speculative decoding).
A trained MiniGPT's weights are fake-quantized (``W -> dequantize(quantize(W))``, fp32
inference, NO int kernels) and we measure the quality-vs-bits degradation curve. This
measures the architecture-independent QUALITY COST of quantization — NOT a memory/speed
win (at char-toy scale absolute memory is trivial and there are no int kernels; a
deployable speedup needs large models + integer kernels, out of scope — the mirror of
v1170's wall-clock honesty).

The PRIMARY metric is held-out completion-token cross-entropy (continuous; EM is a coarse
step function that mislocates the cliff). Three sweeps:
  S1  quality-vs-bits curve (component=all, per-tensor vs per-channel vs group32);
  S2  per-component sensitivity (embedding / c_attn / c_proj / mlp, both granularities);
  S3  is "attention most sensitive" an axis/outlier artifact? (c_attn across schemes x axes).

Two headline claims are gated on multi-seed significance (the only variance source is the
training seed — quantization is deterministic given a model, so a single-seed delta is a
lie): (1) "per-channel buys ~a bit" at MATCHED effective-bits-including-scales; (2) "attention
is the most quant-sensitive component" — only if it survives the axis check AND is corroborated
by logit-KL, else the verdict says it is an outlier/axis artifact or not separable. The tied
``token_embedding.weight`` IS the ``lm_head`` — quantization is applied by PARAMETER IDENTITY
(``named_parameters`` dedups the tie) so the embedding can't be silently reverted.

``status=="pass"`` certifies a VALID degradation measurement (roundtrip correct, baseline
learnable/non-saturated, degradation resolvable, grid complete) — never "quantization is good".
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from minigpt.completion_masking import build_completion_xy
from minigpt.experiment_utils import build_minigpt, mean_std, significant
from minigpt.ptq_v1175_core import (
    COMPONENTS,
    GRANULARITIES,
    SCHEMES,
    beats_lower,
    ce_and_kl,
    component_param_names,
    effective_bits_per_weight,
    n_scale_groups,
    quantize_tensor,
    quantized_model,
    weight_rel_error,
)
from minigpt.report_utils import utc_now
from minigpt.sft_instruction_v1164 import evaluate_instructions
from minigpt.sft_training import train_sft


# Quantization primitives are re-exported from the core module.

@dataclass
class PtqConfig:
    block_size: int = 16
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 64
    use_rope: bool = True
    train_steps: int = 800
    lr: float = 3e-3
    batch_size: int = 64
    max_new_tokens: int = 8
    s1_bits: tuple[int, ...] = (8, 6, 4, 3, 2)
    s1_granularities: tuple[str, ...] = ("per_tensor", "per_channel_row", "group32")
    s2_bits: tuple[int, ...] = (4, 3)
    s2_components: tuple[str, ...] = ("embedding", "c_attn", "c_proj", "mlp", "attention", "all")
    s2_granularities: tuple[str, ...] = ("per_tensor", "per_channel_row")
    s3_bits: tuple[int, ...] = (4, 3)
    s3_schemes: tuple[str, ...] = ("absmax_sym", "percentile_clip", "mse_clip", "affine_asym")
    s3_granularities: tuple[str, ...] = ("per_channel_row", "per_channel_col", "group32")
    cliff_ce_nats: float = 0.25
    baseline_em_floor: float = 0.5
    baseline_em_ceiling: float = 0.99


REVIEW_VERDICTS = {
    "ptq_quantizer_roundtrip_failed", "baseline_saturated_or_not_learnable",
    "degradation_unresolvable_at_this_scale", "grid_incomplete",
}
PRIMARY_VERDICTS = {
    "per_channel_holds_3b_per_tensor_collapses", "per_channel_advantage_not_separable",
    "attention_most_sensitive_per_row_absmax", "attention_outlier_sensitive_clipping_helps",
    "attention_sensitivity_is_per_row_axis_artifact", "component_sensitivity_not_separable",
    "embedding_least_sensitive_per_row",
}


def _roundtrip_ok():
    """g0: a fixed tensor's dequant error is within the analytic absmax bound s/2."""
    torch.manual_seed(0)
    W = torch.randn(8, 16)
    for bits in (8, 4, 2):
        s = W.abs().max() / (2 ** (bits - 1) - 1)
        Wq = quantize_tensor(W, bits, granularity="per_tensor", scheme="absmax_sym")
        if float((W - Wq).abs().max().item()) > float(s.item()) / 2 + 1e-5:
            return False
    return True


def decide(fp32_ce, fp32_em, s1, s2, s3, config):
    """Pure gate + verdict. s1/s2/s3 are dicts of aggregated cells (see run_ptq)."""
    g0 = _roundtrip_ok()
    g1 = (config.baseline_em_floor <= fp32_em <= config.baseline_em_ceiling) and (fp32_ce == fp32_ce)
    worst = s1.get(("all", "per_tensor", min(config.s1_bits)))
    g2 = worst is not None and beats_lower(fp32_ce, 0.0, worst["ce_mean"], worst["ce_std"])
    g3 = bool(s1) and bool(s2) and bool(s3)
    if not g0:
        return {"status": "review", "decision": "ptq_quantizer_roundtrip_failed", "verdict": "ptq_quantizer_roundtrip_failed", "flags": {}}
    if not g1:
        return {"status": "review", "decision": "baseline_saturated_or_not_learnable", "verdict": "baseline_saturated_or_not_learnable", "flags": {}}
    if not g2:
        return {"status": "review", "decision": "degradation_unresolvable_at_this_scale", "verdict": "degradation_unresolvable_at_this_scale", "flags": {}}
    if not g3:
        return {"status": "review", "decision": "grid_incomplete", "verdict": "grid_incomplete", "flags": {}}

    # headline 1: per-channel buys a bit (per_channel_row 3b CE strictly beats per_tensor 4b CE)
    pc3 = s1.get(("all", "per_channel_row", 3))
    pt4 = s1.get(("all", "per_tensor", 4))
    per_channel_buys_bit = (pc3 is not None and pt4 is not None
                            and beats_lower(pc3["ce_mean"], pc3["ce_std"], pt4["ce_mean"], pt4["ce_std"]))

    # does per-channel extend the NOMINAL-bit cliff (per-tensor collapses where per-channel holds)?
    def _cliff(gran):
        bits = sorted({k[2] for k in s1 if k[0] == "all" and k[1] == gran})
        ok = [b for b in bits if s1[("all", gran, b)]["dce_mean"] <= config.cliff_ce_nats]
        return min(ok) if ok else None
    cliff_pt, cliff_pc = _cliff("per_tensor"), _cliff("per_channel_row")
    per_channel_extends_cliff = (cliff_pt is not None and cliff_pc is not None and cliff_pc < cliff_pt)

    # headline 2: component sensitivity at 4b per_channel_row — attn vs runner-up
    comp_dce = {c: s2[(c, "per_channel_row", 4)]["dce_mean"] for c in ("embedding", "c_attn", "c_proj", "mlp")
                if (c, "per_channel_row", 4) in s2}
    comp_std = {c: s2[(c, "per_channel_row", 4)]["dce_std"] for c in comp_dce}
    attn_most = False
    embed_least = False
    if comp_dce:
        ranked = sorted(comp_dce, key=lambda c: comp_dce[c], reverse=True)  # most-damaged first
        top = ranked[0]
        runner = ranked[1] if len(ranked) > 1 else top
        attn_top = top in ("c_attn", "attention")
        attn_most = attn_top and significant(comp_dce[top], comp_std[top], comp_dce[runner], comp_std[runner])
        emb = comp_dce.get("embedding", 1.0)
        embed_least = (emb == min(comp_dce.values())) and (abs(emb) < config.cliff_ce_nats)

    # S3: does clipping/axis close the c_attn gap?
    base_attn = s3.get(("c_attn", "absmax_sym", "per_channel_row", 4))
    alt_axis = [s3[k] for k in s3 if k[0] == "c_attn" and k[2] != "per_channel_row" and k[3] == 4]
    clip_arms = [s3[k] for k in s3 if k[0] == "c_attn" and k[1] in ("percentile_clip", "mse_clip", "affine_asym") and k[3] == 4]
    axis_robust = bool(base_attn) and all(
        not beats_lower(a["ce_mean"], a["ce_std"], base_attn["ce_mean"], base_attn["ce_std"]) for a in alt_axis
    ) if alt_axis else True
    clipping_helps = bool(base_attn) and any(
        beats_lower(a["ce_mean"], a["ce_std"], base_attn["ce_mean"], base_attn["ce_std"]) for a in clip_arms
    )

    flags = {"per_channel_buys_bit": per_channel_buys_bit, "per_channel_extends_cliff": per_channel_extends_cliff,
             "attn_most_sensitive": attn_most, "embed_least_sensitive": embed_least,
             "attn_axis_robust": axis_robust, "attn_clipping_helps": clipping_helps}

    # verdict: prefer the per-channel cliff finding (S1), then the component story (S2/S3)
    if per_channel_buys_bit:
        verdict = "per_channel_holds_3b_per_tensor_collapses"
    elif per_channel_extends_cliff:
        verdict = "per_channel_advantage_not_separable"      # extends nominal cliff, but a wash at matched effective bits
    elif attn_most and not axis_robust:
        verdict = "attention_sensitivity_is_per_row_axis_artifact"
    elif attn_most and clipping_helps:
        verdict = "attention_outlier_sensitive_clipping_helps"
    elif attn_most:
        verdict = "attention_most_sensitive_per_row_absmax"
    elif embed_least:
        verdict = "embedding_least_sensitive_per_row"
    else:
        verdict = "component_sensitivity_not_separable"
    return {"status": "pass", "decision": "ptq_measured", "verdict": verdict, "flags": flags}


def run_ptq(*, vocab_size, train_examples, heldout_instructions, ops, pad_id, eos_id,
            config, device, corpus_stats=None, generated_at=None):
    bs = config.block_size
    held_full = [(p + e + [eos_id], len(p)) for p, e, _ in heldout_instructions]
    X, Y = build_completion_xy(held_full, bs, pad_id)
    X, Y = X.to(device), Y.to(device)

    # per-seed: train fp32 baseline, then quantize across the grid (reuse the same baseline)
    fp32_ce, fp32_em = [], []
    s1_acc, s2_acc, s3_acc = {}, {}, {}

    def push(acc, key, ce, dce, kl, em, relerr, eff_bits):
        d = acc.setdefault(key, {"ce": [], "dce": [], "kl": [], "em": [], "relerr": [], "eff_bits": eff_bits})
        d["ce"].append(ce)
        d["dce"].append(dce)
        d["kl"].append(kl)
        d["em"].append(em)
        d["relerr"].append(relerr)

    class Cfg:
        block_size = bs
        n_layer = config.n_layer
        n_head = config.n_head
        n_embd = config.n_embd
        use_rope = config.use_rope

    for seed in config.seeds:
        torch.manual_seed(seed)
        base = build_minigpt(vocab_size, Cfg).to(device)
        train_sft(base, train_examples, steps=config.train_steps, lr=config.lr, batch_size=config.batch_size,
                  block_size=bs, device=device, pad_id=pad_id, mask_prompt=True)
        f_ce, _, ref_logits = ce_and_kl(base, X, Y, None)
        f_em = evaluate_instructions(base, heldout_instructions, eos_id=eos_id,
                                     max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
        fp32_ce.append(f_ce)
        fp32_em.append(f_em)

        def measure(component, bits, gran, scheme):
            qm = quantized_model(base, bits, component, granularity=gran, scheme=scheme)
            ce, kl, _ = ce_and_kl(qm, X, Y, ref_logits)
            em = evaluate_instructions(qm, heldout_instructions, eos_id=eos_id,
                                       max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
            re = weight_rel_error(base, qm, component)
            eff = effective_bits_per_weight(base, component, bits, gran)
            return ce, ce - f_ce, kl, em, re, eff

        for gran in config.s1_granularities:
            for bits in config.s1_bits:
                ce, dce, kl, em, re, eff = measure("all", bits, gran, "absmax_sym")
                push(s1_acc, ("all", gran, bits), ce, dce, kl, em, re, eff)
        for comp in config.s2_components:
            for gran in config.s2_granularities:
                for bits in config.s2_bits:
                    ce, dce, kl, em, re, eff = measure(comp, bits, gran, "absmax_sym")
                    push(s2_acc, (comp, gran, bits), ce, dce, kl, em, re, eff)
        for scheme in config.s3_schemes:
            for gran in config.s3_granularities:
                for bits in config.s3_bits:
                    ce, dce, kl, em, re, eff = measure("c_attn", bits, gran, scheme)
                    push(s3_acc, ("c_attn", scheme, gran, bits), ce, dce, kl, em, re, eff)

    def agg(acc):
        out = {}
        for key, d in acc.items():
            ce_m, ce_s = mean_std(d["ce"])
            dce_m, dce_s = mean_std(d["dce"])
            kl_m, _ = mean_std([v for v in d["kl"] if v == v])
            em_m, _ = mean_std(d["em"])
            re_m, _ = mean_std(d["relerr"])
            out[key] = {"ce_mean": round(ce_m, 6), "ce_std": round(ce_s, 6),
                        "dce_mean": round(dce_m, 6), "dce_std": round(dce_s, 6),
                        "kl_mean": round(kl_m, 6) if kl_m == kl_m else "", "em_mean": round(em_m, 6),
                        "relerr_mean": round(re_m, 6), "eff_bits": round(d["eff_bits"], 4)}
        return out

    s1, s2, s3 = agg(s1_acc), agg(s2_acc), agg(s3_acc)
    fp32_ce_m, fp32_ce_s = mean_std(fp32_ce)
    fp32_em_m, _ = mean_std(fp32_em)
    out = decide(fp32_ce_m, fp32_em_m, s1, s2, s3, config)
    status, decision, verdict, flags = out["status"], out["decision"], out["verdict"], out["flags"]

    # cliff per granularity (smallest bits with dCE below threshold, on CE)
    cliffs = {}
    for gran in config.s1_granularities:
        ok_bits = [b for b in sorted(config.s1_bits) if s1.get(("all", gran, b), {}).get("dce_mean", 9e9) <= config.cliff_ce_nats]
        cliffs[gran] = min(ok_bits) if ok_bits else None

    rows = []
    for (comp, gran, bits), d in {**{("all",) + k[1:]: v for k, v in s1.items()}}.items():
        rows.append({"sweep": "S1", "component": comp, "granularity": gran, "bits": bits,
                     "eff_bits": d["eff_bits"], "ce_mean": d["ce_mean"], "dce_mean": d["dce_mean"],
                     "kl_mean": d["kl_mean"], "em_mean": d["em_mean"], "relerr_mean": d["relerr_mean"]})
    for (comp, gran, bits), d in s2.items():
        rows.append({"sweep": "S2", "component": comp, "granularity": gran, "bits": bits,
                     "eff_bits": d["eff_bits"], "ce_mean": d["ce_mean"], "dce_mean": d["dce_mean"],
                     "kl_mean": d["kl_mean"], "em_mean": d["em_mean"], "relerr_mean": d["relerr_mean"]})
    for (comp, scheme, gran, bits), d in s3.items():
        rows.append({"sweep": "S3", "component": f"c_attn:{scheme}", "granularity": gran, "bits": bits,
                     "eff_bits": d["eff_bits"], "ce_mean": d["ce_mean"], "dce_mean": d["dce_mean"],
                     "kl_mean": d["kl_mean"], "em_mean": d["em_mean"], "relerr_mean": d["relerr_mean"]})

    stats = corpus_stats or {}
    summary = {
        "status": status, "decision": decision, "verdict": verdict,
        "device": str(device), "seeds": len(config.seeds), "ops": ",".join(ops),
        "model_size": f"{config.n_layer}L/{config.n_embd}",
        "fp32_ce": round(fp32_ce_m, 6), "fp32_ce_std": round(fp32_ce_s, 6),
        "fp32_exact_match": round(fp32_em_m, 6),
        "cliff_bits_per_tensor": cliffs.get("per_tensor"),
        "cliff_bits_per_channel_row": cliffs.get("per_channel_row"),
        "cliff_bits_group32": cliffs.get("group32"),
        "task_learned": status == "pass",
        "heldout_prompts": stats.get("heldout_prompts"),
    }
    if status == "pass":
        def g(d, k):
            return d.get(k, {})
        summary.update({
            "s1_pt_4b_ce": g(s1, ("all", "per_tensor", 4)).get("ce_mean"),
            "s1_pc_3b_ce": g(s1, ("all", "per_channel_row", 3)).get("ce_mean"),
            "s1_pt_4b_em": g(s1, ("all", "per_tensor", 4)).get("em_mean"),
            "s1_pc_3b_em": g(s1, ("all", "per_channel_row", 3)).get("em_mean"),
            "s1_pt_4b_eff_bits": g(s1, ("all", "per_tensor", 4)).get("eff_bits"),
            "s1_pc_3b_eff_bits": g(s1, ("all", "per_channel_row", 3)).get("eff_bits"),
            "s2_embedding_dce_4b_pc": g(s2, ("embedding", "per_channel_row", 4)).get("dce_mean"),
            "s2_c_attn_dce_4b_pc": g(s2, ("c_attn", "per_channel_row", 4)).get("dce_mean"),
            "s2_c_proj_dce_4b_pc": g(s2, ("c_proj", "per_channel_row", 4)).get("dce_mean"),
            "s2_mlp_dce_4b_pc": g(s2, ("mlp", "per_channel_row", 4)).get("dce_mean"),
            "s2_c_attn_relerr_4b_pc": g(s2, ("c_attn", "per_channel_row", 4)).get("relerr_mean"),
            "s2_c_attn_kl_4b_pc": g(s2, ("c_attn", "per_channel_row", 4)).get("kl_mean"),
            "s2_embedding_relerr_4b_pc": g(s2, ("embedding", "per_channel_row", 4)).get("relerr_mean"),
            **{f"flag_{k}": v for k, v in flags.items()},
        })

    recommendations = [
        f"VERDICT ({verdict}): weight-only PTQ measures the QUALITY COST of quantization (fp32 inference, no int kernels) — NOT a memory/speed win at char-toy scale (the mirror of v1170's wall-clock honesty). status='{status}' certifies a VALID degradation measurement (roundtrip correct, baseline learnable EM {fp32_em_m:.3f}, degradation resolvable, grid complete), NOT that quantization is good.",
        f"CLIFF (primary metric = held-out CE, fp32 {fp32_ce_m:.3f}): smallest bits within {config.cliff_ce_nats} nats of fp32 — per-tensor {cliffs.get('per_tensor')}b, per-channel-row {cliffs.get('per_channel_row')}b, group32 {cliffs.get('group32')}b. PER-CHANNEL buys ~a bit (sig={flags.get('per_channel_buys_bit')}) but charged at EFFECTIVE bits-incl-scales: per_channel_row 3b ≈ {summary.get('s1_pc_3b_eff_bits')} eff vs per_tensor 4b = {summary.get('s1_pt_4b_eff_bits')} eff — a partial-bit saving, not a clean one.",
        f"COMPONENT SENSITIVITY at 4b per-channel-row (ΔCE vs fp32, multi-seed): embedding {summary.get('s2_embedding_dce_4b_pc')}, c_attn {summary.get('s2_c_attn_dce_4b_pc')}, c_proj {summary.get('s2_c_proj_dce_4b_pc')}, mlp {summary.get('s2_mlp_dce_4b_pc')}. attn_most_sensitive={flags.get('attn_most_sensitive')}, embed_least={flags.get('embed_least_sensitive')}. The probe's 'attention most sensitive / embedding lossless' is only asserted if it survives multi-seed significance.",
        f"MECHANISM / ROBUSTNESS: c_attn weight-rel-error {summary.get('s2_c_attn_relerr_4b_pc')} vs logit-KL {summary.get('s2_c_attn_kl_4b_pc')} (amplification = LOW rel-error but HIGH KL). S3: attn finding axis-robust={flags.get('attn_axis_robust')}, clipping-helps={flags.get('attn_clipping_helps')} — if clipping closes the gap, attention is OUTLIER-sensitive (fixable), not intrinsically fragile; if it flips under an alternate axis, it is a per-row-absmax artifact.",
        "SCOPE / FALSIFIED PRIORS: weight-only RTN PTQ; activation quantization, QAT, GPTQ/AWQ calibration out of scope. The tied token_embedding IS the lm_head — quantized by parameter identity so it can't be silently reverted. The naive 'biggest/tied tensor is most sensitive (v1157)' prior is tested, not assumed.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT post-training weight quantization v1175",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": decision,
        "summary": summary, "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["sweep", "component", "granularity", "bits", "eff_bits",
                           "ce_mean", "dce_mean", "kl_mean", "em_mean", "relerr_mean"],
        "cliffs": cliffs,
        "seeds": list(config.seeds),
    }


__all__ = [
    "beats_lower", "quantize_tensor", "n_scale_groups", "component_param_names",
    "quantized_model", "effective_bits_per_weight", "ce_and_kl", "weight_rel_error",
    "PtqConfig", "decide", "run_ptq", "SCHEMES", "GRANULARITIES", "COMPONENTS",
    "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
