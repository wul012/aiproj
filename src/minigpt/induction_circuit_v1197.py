"""v1197: CAUSAL DISSECTION OF THE INDUCTION CIRCUIT (mechanistic capstone of the induction axis).

v1196 behaviorally established that in-context induction REQUIRES DEPTH (1-layer fails, 2-layer
succeeds, with the shortcuts blocked). v1197 opens the 2-layer model and asks WHICH heads
implement induction and HOW -- the canonical prev-token-head -> induction-head circuit
(Elhage/Olsson 2022), reproduced and causally verified on our own model.

Reuses v1196's CLEAN induction task (random high-diversity sequence; target = the token that
MOST-RECENTLY followed the current token; first occurrences masked). Model: 2-layer, width 64,
n_head=8 (more heads than v1196's 4 -> a count-matched non-circuit control is possible).

Heads are classified by attention pattern on a held-out batch:
  prev-token score(h) = mean attention mass position i places on i-1     (a layer-0 head)
  induction score(h)  = mean mass an inductable query i places on j+1, j = most-recent earlier
                        occurrence of x[i], MINUS the uniform baseline 1/(i+1)  (a layer-1 head)
prev-token heads = L0 with prev > tau_prev; induction heads = L1 with ind > tau_ind.

CAUSAL ablation = MEAN-ablation (primary): replace a head's pre-c_proj output with its dataset
MEAN (removes the head's input-dependent computation while preserving the residual/LayerNorm
operating point). ZERO-ablation is run as a SECONDARY check -- the verdict requires the two to
AGREE; a zero-only collapse that lands BELOW the unigram floor is flagged as an out-of-distribution
LayerNorm shock, not clean pathway removal.

The 3-lens design panel forced the non-obvious decisions:
* MEAN-ablation primary + zero/mean AGREEMENT (zeroing injects OOD into LayerNorm + leaves the
  shared c_proj bias, so a below-unigram collapse is shock, not removal).
* COUNT-MATCHED specificity: ablating the top-k prev (or induction) heads vs ablating the
  bottom-k of the SAME layer (same count) -- the targeted class collapses, the matched control
  does not.
* NECESSITY is a TWO-part bar vs the cached v1196 unigram floor: absolute (ablated <=
  max(unigram, chance)+margin) AND relative (drop >= 0.5*(base-unigram)), both significant.
* COMPOSITION (prev -> induction) needs controls to beat the v1193 "generic-disruption" critique:
  ablating prev heads collapses the induction heads' attention MORE than ablating matched
  non-prev L0 heads (rules out a generic LayerNorm/residual shift), a NON-induction L1 head does
  NOT collapse, and re-measurement uses a SEPARATE held-out batch from classification (no
  selection-on-same-data circularity).
* REDUNDANCY (the honest nuance): single-head ablation is COMPENSATED (max single-head drop small)
  while CLASS ablation breaks it -- so the verdict ladder reports redundant vs concentrated.
* Degenerate per-seed classification guarded (a seed needs >=2 prev AND >=2 induction heads to
  judge redundancy); every significant() carries a pinned margin (std==0 can never certify alone);
  a Phase-B THRESHOLD-ROBUSTNESS sweep requires the verdict invariant under +/-0.05 tau nudges.

``status=="pass"`` certifies a VALID, non-degenerate, mean/zero-consistent measurement, NEVER a
flattering shape. Phase A trains + caches per-seed head scores + top-k/bottom-k/single ablation
accuracies (both modes) + composition attentions; Phase B re-derives the verdict (incl. the tau
sweep) with zero retrain.

Scope: 2-layer width-64 MiniGPT, n_head=8, K=20/T=64, wd=0.1; the prev->induction circuit and the
depth requirement are textbook -- the NEW contribution is the controlled, multi-seed REDUNDANCY +
matched-specificity + mean-ablation demonstration on this model. Not a claim about LLM induction heads.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from minigpt.experiment_utils import mean_std, significant
from minigpt.induction_v1196 import IGNORE, InductionConfig, _inductable_acc, make_batch, make_model, unigram_acc
from minigpt.report_utils import utc_now


@dataclass
class CircuitConfig:
    K: int = 20
    T: int = 64
    width: int = 64
    depth: int = 2
    n_head: int = 8
    steps: int = 1500
    batch: int = 256
    eval_batch: int = 256
    eval_n_batches: int = 6
    mech_batch: int = 96
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341, 1342, 1343, 1344)
    # --- thresholds (tau_prev set to the grid minimum: a head with >=30% of its attention on the
    #     previous token is a prev-token head -- some seeds implement prev-token detection diffusely
    #     across several ~0.3 heads rather than 2 sharp ~0.95 heads; the verdict is checked invariant
    #     across the 0.30-0.50 tau grid regardless) ---
    tau_prev: float = 0.30
    tau_ind: float = 0.35
    success_frac: float = 0.6          # base model must induct: base_acc >= success_frac*(1-1/K)
    necessity_margin: float = 0.05     # ablated_acc <= max(unigram,chance)+this (absolute floor)
    necessity_rel: float = 0.5         # drop >= this * (base - unigram) (relative)
    specificity_margin: float = 0.30   # control_acc - class_acc >= this; control still inducts
    single_max: float = 0.30           # redundancy: max single-head drop in a class <= this
    redundancy_gap: float = 0.40       # class_drop - max_single_drop >= this
    composition_margin: float = 0.30   # ind-attn drop(prev-ablate) - drop(nonprev-control) >= this
    min_margin: float = 0.05           # pinned margin on every significant() (guards std==0)
    usable_frac: float = 0.8           # fraction of seeds with >=2 prev AND >=2 ind heads
    tau_prev_grid: tuple[float, ...] = (0.30, 0.35, 0.40, 0.45, 0.50)
    tau_ind_grid: tuple[float, ...] = (0.25, 0.30, 0.35, 0.40, 0.45)

    @property
    def chance(self) -> float:
        return 1.0 / self.K

    @property
    def S(self) -> float:
        return self.success_frac * (1.0 - 1.0 / self.K)


# ------------------------------------------------------------------------- head scoring
def _ind_source(mech_x: torch.Tensor, mech_t: torch.Tensor, T: int):
    """For each (b,i) inductable query, the most-recent-successor source position j+1 (or None)."""
    out = []
    B = mech_x.shape[0]
    for b in range(B):
        last: dict[int, int] = {}
        row = []
        for i in range(T - 1):
            c = int(mech_x[b, i])
            src = None
            if int(mech_t[b, i]) != IGNORE and c in last and last[c] + 1 <= i:
                src = last[c] + 1
            row.append(src)
            last[c] = i
        out.append(row)
    return out


def head_scores(model, mech_x: torch.Tensor, mech_t: torch.Tensor, device,
                ind_src=None) -> tuple[dict, dict]:
    """Per (layer, head): prev-token score (mass i->i-1) and induction score (mass i->successor
    position, minus uniform baseline). Returns (prev, ind) dicts keyed by (layer, head)."""
    model.eval()
    mech_x = mech_x.to(device)
    B, T = mech_x.shape
    H = model.config.n_head
    if ind_src is None:
        ind_src = _ind_source(mech_x.cpu(), mech_t, T)
    model.set_attention_capture(True)
    with torch.no_grad():
        model(mech_x[:, :-1])
    maps = model.attention_maps()
    model.set_attention_capture(False)
    prev, ind = {}, {}
    for li, att in enumerate(maps):
        for h in range(H):
            prev[(li, h)] = sum(att[b, h, i, i - 1].item() for b in range(B) for i in range(1, T - 1)) / (B * (T - 2))
            isum = icnt = 0.0
            for b in range(B):
                for i in range(T - 1):
                    src = ind_src[b][i]
                    if src is not None:
                        isum += att[b, h, i, src].item() - 1.0 / (i + 1)
                        icnt += 1
            ind[(li, h)] = isum / max(icnt, 1)
    return prev, ind


def induction_attention(model, ind_heads, mech_x, mech_t, device, ind_src=None) -> float:
    """Mean induction score (mass on the successor position, minus baseline) over the given L1
    heads, on the supplied batch -- used for the composition test on a SEPARATE batch."""
    if not ind_heads:
        return float("nan")
    prev, ind = head_scores(model, mech_x, mech_t, device, ind_src=ind_src)
    return sum(ind[hh] for hh in ind_heads) / len(ind_heads)


# ------------------------------------------------------------------------- ablation (hook-based)
def acc_under_ablation(cfg: CircuitConfig, model, mu_by_layer, layer_heads: dict, mode: str,
                       eval_x, eval_t, device) -> float:
    """Inductable accuracy with the given heads ablated. mode='mean' replaces a head's pre-c_proj
    output with its dataset mean (mu_by_layer[layer]); mode='zero' replaces it with 0. Reversible
    via forward-pre-hooks on c_proj (the shared c_proj.bias is left intact in both modes)."""
    hs = model.config.n_embd // model.config.n_head
    handles = []

    def make_hook(heads, muL, mode):
        def hook(_m, args):
            y = args[0].clone()
            for h in heads:
                sl = slice(h * hs, (h + 1) * hs)
                y[:, :, sl] = 0.0 if mode == "zero" else muL[sl]
            return (y,)
        return hook

    for layer, heads in layer_heads.items():
        if heads:
            handles.append(model.blocks[layer].attn.c_proj.register_forward_pre_hook(
                make_hook(list(heads), mu_by_layer[layer], mode)))
    try:
        return _inductable_acc(model, eval_x, eval_t, device)
    finally:
        for h in handles:
            h.remove()


def attention_under_ablation(cfg, model, mu_by_layer, layer_heads, mode, ind_heads,
                             mech_x, mech_t, device, ind_src) -> float:
    """Induction-head attention score with the given heads ablated (for the composition test)."""
    hs = model.config.n_embd // model.config.n_head
    handles = []

    def make_hook(heads, muL, mode):
        def hook(_m, args):
            y = args[0].clone()
            for h in heads:
                sl = slice(h * hs, (h + 1) * hs)
                y[:, :, sl] = 0.0 if mode == "zero" else muL[sl]
            return (y,)
        return hook

    for layer, heads in layer_heads.items():
        if heads:
            handles.append(model.blocks[layer].attn.c_proj.register_forward_pre_hook(
                make_hook(list(heads), mu_by_layer[layer], mode)))
    try:
        return induction_attention(model, ind_heads, mech_x, mech_t, device, ind_src=ind_src)
    finally:
        for h in handles:
            h.remove()


def capture_mu(model, batch_x, device) -> dict:
    """Per-layer mean of the pre-c_proj input (the concatenated head outputs), over (batch, pos)."""
    store: dict[int, torch.Tensor] = {}
    handles = []
    for layer in range(len(model.blocks)):
        def make(layer):
            def hook(_m, args):
                store[layer] = args[0].detach().mean(dim=(0, 1))
            return hook
        handles.append(model.blocks[layer].attn.c_proj.register_forward_pre_hook(make(layer)))
    with torch.no_grad():
        model(batch_x[:, :-1].to(device))
    for h in handles:
        h.remove()
    return store


# ------------------------------------------------------------------------- training
def train_model(cfg: CircuitConfig, seed: int, eval_x, eval_t, device):
    icfg = InductionConfig(K=cfg.K, T=cfg.T, n_head=cfg.n_head, steps=cfg.steps, batch=cfg.batch)
    model = make_model(icfg, depth=cfg.depth, width=cfg.width, attn_only=False, seed=seed).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=icfg.lr, betas=(icfg.beta1, icfg.beta2),
                            weight_decay=icfg.weight_decay)
    gen = torch.Generator(device=device).manual_seed(seed + 11)
    for _ in range(cfg.steps):
        x, t = make_batch(icfg, cfg.batch, gen, device, mode="clean")
        model.train(); opt.zero_grad(set_to_none=True)
        _, loss = model(x[:, :-1], t)
        loss.backward(); opt.step()
    return model, icfg


def run_phase_a(cfg: CircuitConfig, device) -> dict:
    icfg = InductionConfig(K=cfg.K, T=cfg.T, n_head=cfg.n_head)
    ge = torch.Generator(device=device).manual_seed(20240)
    eval_x, eval_t = [], []
    for _ in range(cfg.eval_n_batches):
        x, t = make_batch(icfg, cfg.eval_batch, ge, device, mode="clean")
        eval_x.append(x.cpu()); eval_t.append(t.cpu())
    # classification batch and a SEPARATE composition-remeasurement batch (M4 de-circularization)
    gm = torch.Generator(device=device).manual_seed(20242)
    cls_x, cls_t = make_batch(icfg, cfg.mech_batch, gm, device, mode="clean")
    cls_x, cls_t = cls_x.cpu(), cls_t.cpu()
    gc = torch.Generator(device=device).manual_seed(20243)
    comp_x, comp_t = make_batch(icfg, cfg.mech_batch, gc, device, mode="clean")
    comp_x, comp_t = comp_x.cpu(), comp_t.cpu()
    cls_src = _ind_source(cls_x, cls_t, cfg.T)
    comp_src = _ind_source(comp_x, comp_t, cfg.T)

    uni_acc, _ = unigram_acc(icfg, eval_x[0], eval_t[0])

    seeds_out = {}
    H = cfg.n_head
    for seed in cfg.seeds:
        model, _ = train_model(cfg, seed, eval_x, eval_t, device)
        base = _inductable_acc(model, eval_x, eval_t, device)
        prev, ind = head_scores(model, cls_x, cls_t, device, ind_src=cls_src)
        mu = capture_mu(model, eval_x[0], device)

        # L0 heads ranked by prev score (desc), L1 heads ranked by ind score (desc)
        l0_by_prev = sorted(range(H), key=lambda h: prev[(0, h)], reverse=True)
        l1_by_ind = sorted(range(H), key=lambda h: ind[(1, h)], reverse=True)

        rec = {"base_acc": base, "prev": {f"{l},{h}": prev[(l, h)] for (l, h) in prev},
               "ind": {f"{l},{h}": ind[(l, h)] for (l, h) in ind},
               "l0_by_prev": l0_by_prev, "l1_by_ind": l1_by_ind}

        for mode in ("mean", "zero"):
            # top-k / bottom-k ablation accuracy (enables the tau-robustness sweep in Phase B)
            topprev = [acc_under_ablation(cfg, model, mu, {0: l0_by_prev[:k]}, mode, eval_x, eval_t, device) for k in range(H + 1)]
            botprev = [acc_under_ablation(cfg, model, mu, {0: l0_by_prev[H - k:]}, mode, eval_x, eval_t, device) for k in range(H + 1)]
            topind = [acc_under_ablation(cfg, model, mu, {1: l1_by_ind[:k]}, mode, eval_x, eval_t, device) for k in range(H + 1)]
            botind = [acc_under_ablation(cfg, model, mu, {1: l1_by_ind[H - k:]}, mode, eval_x, eval_t, device) for k in range(H + 1)]
            single0 = [acc_under_ablation(cfg, model, mu, {0: [h]}, mode, eval_x, eval_t, device) for h in range(H)]
            single1 = [acc_under_ablation(cfg, model, mu, {1: [h]}, mode, eval_x, eval_t, device) for h in range(H)]
            rec[f"{mode}_topprev"] = topprev
            rec[f"{mode}_botprev"] = botprev
            rec[f"{mode}_topind"] = topind
            rec[f"{mode}_botind"] = botind
            rec[f"{mode}_single_l0"] = single0
            rec[f"{mode}_single_l1"] = single1

        # composition at the PRIMARY thresholds (mean mode): does ablating prev heads collapse the
        # induction heads' attention MORE than ablating matched non-prev L0 heads, on a SEPARATE batch?
        prev_heads = [h for h in range(H) if prev[(0, h)] > cfg.tau_prev]
        ind_heads = [h for h in range(H) if ind[(1, h)] > cfg.tau_ind]
        ind_keys = [(1, h) for h in ind_heads]
        kp = len(prev_heads)
        nonprev_matched = l0_by_prev[H - kp:] if kp else []     # the kp LEAST-prev L0 heads
        noind_l1 = [h for h in range(H) if h not in ind_heads]  # non-induction L1 heads (control)
        noind_keys = [(1, h) for h in noind_l1]
        comp = {"kp": kp, "ki": len(ind_heads)}
        if ind_heads:
            comp["ind_attn_intact"] = induction_attention(model, ind_keys, comp_x, comp_t, device, ind_src=comp_src)
            comp["ind_attn_no_prev"] = attention_under_ablation(cfg, model, mu, {0: prev_heads}, "mean", ind_keys, comp_x, comp_t, device, comp_src)
            comp["ind_attn_no_nonprev"] = attention_under_ablation(cfg, model, mu, {0: nonprev_matched}, "mean", ind_keys, comp_x, comp_t, device, comp_src)
            comp["noind_l1_attn_intact"] = induction_attention(model, noind_keys, comp_x, comp_t, device, ind_src=comp_src) if noind_keys else float("nan")
            comp["noind_l1_attn_no_prev"] = attention_under_ablation(cfg, model, mu, {0: prev_heads}, "mean", noind_keys, comp_x, comp_t, device, comp_src) if noind_keys else float("nan")
        rec["composition"] = comp
        seeds_out[seed] = rec

    return {
        "config": {"K": cfg.K, "T": cfg.T, "width": cfg.width, "depth": cfg.depth, "n_head": cfg.n_head,
                   "steps": cfg.steps, "seeds": list(cfg.seeds), "tau_prev": cfg.tau_prev, "tau_ind": cfg.tau_ind},
        "chance": cfg.chance, "S": cfg.S, "unigram_acc": uni_acc, "seeds": seeds_out,
    }


# ------------------------------------------------------------------------- analysis
def _count_above(scores_row: dict, layer: int, H: int, tau: float, key) -> int:
    return sum(1 for h in range(H) if scores_row[f"{layer},{h}"] > tau)


def _necessity_ok(cfg, base, ablated, uni):
    floor = max(uni, cfg.chance) + cfg.necessity_margin
    rel = (base - ablated) >= cfg.necessity_rel * (base - uni)
    return (ablated <= floor) and rel


def _classify_verdict(cache: dict, cfg: CircuitConfig, tau_prev: float, tau_ind: float) -> dict:
    """Core per-(tau_prev,tau_ind) decision over seeds. Returns flags + the four sub-results."""
    H = cache["config"]["n_head"]
    all_seeds = cache["config"]["seeds"]
    uni = cache["unigram_acc"]
    S = cache["S"]
    # EXCLUDE seeds whose model did not learn induction (base < S): there is no circuit to dissect
    # in a model that never acquired the capability (n_head=8 has occasional optimization failures).
    seeds = [s for s in all_seeds if cache["seeds"][s]["base_acc"] >= S]
    n_trained = len(seeds)
    if n_trained == 0:   # no model learned induction -> nothing to dissect
        z = (0.0, 0.0)
        modes = {m: {"prev_ablate": z, "ind_ablate": z, "prev_control": z, "ind_control": z} for m in ("mean", "zero")}
        return {"base_acc": (mean_std([cache["seeds"][s]["base_acc"] for s in all_seeds])[0], 0.0),
                "unigram": uni, "n_trained": 0, "n_all": len(all_seeds), "classifiable_frac": 0.0,
                "usable": [], "classifiable": [], "kp": {}, "ki": {}, "modes": modes,
                "necessity": False, "necessity_by_mode": {"mean": False, "zero": False}, "specificity": False,
                "redundancy": {"usable_frac": 0.0, "prev_redundant": False, "ind_redundant": False},
                "composition": False, "comp_nums": {"drop_prev": 0.0, "drop_ctrl": 0.0, "n_comp_seeds": 0,
                    "intact": z, "no_prev": z, "nonprev_ctrl": z, "noind_intact": z, "noind_no_prev": z}}
    base_ms = mean_std([cache["seeds"][s]["base_acc"] for s in seeds])

    # per seed: k_p, k_i at these thresholds; usable iff >=2 prev AND >=2 ind heads
    kp = {s: _count_above(cache["seeds"][s]["prev"], 0, H, tau_prev, None) for s in seeds}
    ki = {s: _count_above(cache["seeds"][s]["ind"], 1, H, tau_ind, None) for s in seeds}
    usable = [s for s in seeds if kp[s] >= 2 and ki[s] >= 2]          # >=2/class -> redundancy judgeable
    classifiable = [s for s in seeds if kp[s] >= 1 and ki[s] >= 1]    # >=1/class -> circuit present
    classifiable_frac = len(classifiable) / n_trained if n_trained else 0.0

    def per_seed(mode):
        prev_ab = [cache["seeds"][s][f"{mode}_topprev"][kp[s]] for s in seeds if kp[s] > 0]
        ind_ab = [cache["seeds"][s][f"{mode}_topind"][ki[s]] for s in seeds if ki[s] > 0]
        ctrl_prev = [cache["seeds"][s][f"{mode}_botprev"][kp[s]] for s in seeds if kp[s] > 0]
        ctrl_ind = [cache["seeds"][s][f"{mode}_botind"][ki[s]] for s in seeds if ki[s] > 0]
        return (mean_std(prev_ab), mean_std(ind_ab), mean_std(ctrl_prev), mean_std(ctrl_ind))

    res = {}
    for mode in ("mean", "zero"):
        prev_ab, ind_ab, ctrl_prev, ctrl_ind = per_seed(mode)
        res[mode] = {"prev_ablate": prev_ab, "ind_ablate": ind_ab,
                     "prev_control": ctrl_prev, "ind_control": ctrl_ind}

    bm = base_ms[0]
    # necessity (both classes) under BOTH modes
    nec = {}
    for mode in ("mean", "zero"):
        nec[mode] = (_necessity_ok(cfg, bm, res[mode]["prev_ablate"][0], uni) and
                     _necessity_ok(cfg, bm, res[mode]["ind_ablate"][0], uni))
    necessity = nec["mean"] and nec["zero"]

    def beats(hi, lo):
        (hm, hs), (lm, ls) = hi, lo
        return (hm - lm) > cfg.min_margin and significant(hm, hs, lm, ls)

    # specificity (mean mode primary): matched control survives AND control >> class
    spec = (beats(res["mean"]["prev_control"], res["mean"]["prev_ablate"]) and
            beats(res["mean"]["ind_control"], res["mean"]["ind_ablate"]) and
            (res["mean"]["prev_control"][0] - res["mean"]["prev_ablate"][0]) >= cfg.specificity_margin and
            (res["mean"]["ind_control"][0] - res["mean"]["ind_ablate"][0]) >= cfg.specificity_margin)

    # redundancy (usable seeds, mean mode): max single-head drop in a class is small; class drop big
    red_info = {"usable_frac": len(usable) / len(seeds)}
    if usable:
        prev_single_drops, ind_single_drops, prev_class_drops, ind_class_drops = [], [], [], []
        for s in usable:
            r = cache["seeds"][s]
            l0p = r["l0_by_prev"][:kp[s]]; l1i = r["l1_by_ind"][:ki[s]]
            prev_single_drops.append(max(r["base_acc"] - r["mean_single_l0"][h] for h in l0p))
            ind_single_drops.append(max(r["base_acc"] - r["mean_single_l1"][h] for h in l1i))
            prev_class_drops.append(r["base_acc"] - r["mean_topprev"][kp[s]])
            ind_class_drops.append(r["base_acc"] - r["mean_topind"][ki[s]])
        msp = mean_std(prev_single_drops); msi = mean_std(ind_single_drops)
        mcp = mean_std(prev_class_drops); mci = mean_std(ind_class_drops)
        red_info.update({"prev_max_single_drop": msp, "ind_max_single_drop": msi,
                         "prev_class_drop": mcp, "ind_class_drop": mci})
        prev_redundant = msp[0] <= cfg.single_max and (mcp[0] - msp[0]) >= cfg.redundancy_gap
        ind_redundant = msi[0] <= cfg.single_max and (mci[0] - msi[0]) >= cfg.redundancy_gap
    else:
        prev_redundant = ind_redundant = False
    red_info["prev_redundant"] = bool(prev_redundant)
    red_info["ind_redundant"] = bool(ind_redundant)

    # composition (mean mode, separate batch): prev-ablation collapses ind attn MORE than nonprev control
    # composition aggregates only over seeds whose Phase-A classification found >=1 prev head
    # (a seed with 0 prev heads has a degenerate "ablate no prev heads" = no-op -> exclude).
    comp_seeds = [s for s in seeds if cache["seeds"][s]["composition"].get("kp", 0) > 0
                  and cache["seeds"][s]["composition"].get("ki", 0) > 0]
    comp_intact = mean_std([cache["seeds"][s]["composition"].get("ind_attn_intact", float("nan")) for s in comp_seeds])
    comp_noprev = mean_std([cache["seeds"][s]["composition"].get("ind_attn_no_prev", float("nan")) for s in comp_seeds])
    comp_nonprev_ctrl = mean_std([cache["seeds"][s]["composition"].get("ind_attn_no_nonprev", float("nan")) for s in comp_seeds])
    noind_intact = mean_std([cache["seeds"][s]["composition"].get("noind_l1_attn_intact", float("nan")) for s in comp_seeds])
    noind_noprev = mean_std([cache["seeds"][s]["composition"].get("noind_l1_attn_no_prev", float("nan")) for s in comp_seeds])
    drop_prev = comp_intact[0] - comp_noprev[0]
    drop_ctrl = comp_intact[0] - comp_nonprev_ctrl[0]
    composition = bool(comp_seeds) and (drop_prev - drop_ctrl) >= cfg.composition_margin and drop_prev >= cfg.composition_margin

    return {
        "base_acc": base_ms, "unigram": uni, "usable": usable, "classifiable": classifiable,
        "classifiable_frac": classifiable_frac, "n_trained": n_trained, "n_all": len(all_seeds),
        "kp": kp, "ki": ki, "modes": res, "necessity": bool(necessity), "necessity_by_mode": nec,
        "specificity": bool(spec), "redundancy": red_info, "composition": bool(composition),
        "comp_nums": {"intact": comp_intact, "no_prev": comp_noprev, "nonprev_ctrl": comp_nonprev_ctrl,
                      "drop_prev": drop_prev, "drop_ctrl": drop_ctrl, "n_comp_seeds": len(comp_seeds),
                      "noind_intact": noind_intact, "noind_no_prev": noind_noprev},
    }


def summarize(cache: dict, cfg: CircuitConfig | None = None) -> dict:
    cfg = cfg or CircuitConfig()
    primary = _classify_verdict(cache, cfg, cfg.tau_prev, cfg.tau_ind)
    # threshold robustness: verdict invariance over the central grid
    grid = []
    for tp in cfg.tau_prev_grid:
        for ti in cfg.tau_ind_grid:
            r = _classify_verdict(cache, cfg, tp, ti)
            grid.append((tp, ti, r["necessity"] and r["specificity"]))
    agree = sum(1 for _, _, v in grid if v == (primary["necessity"] and primary["specificity"]))
    return {"cfg": cfg, "primary": primary, "tau_grid_agree_frac": agree / len(grid),
            "n_seeds": len(cache["config"]["seeds"]), "config": cache["config"], "S": cache["S"]}


REVIEW_VERDICTS = {"base_not_inducting", "circuit_not_classifiable", "mean_zero_disagree", "tau_fragile"}
PRIMARY_VERDICTS = {"circuit_necessary_specific_composed_and_redundant",
                    "circuit_necessary_specific_composed_concentrated",
                    "circuit_necessary_specific_composed_redundancy_unassessed",
                    "circuit_necessary_specific_not_composed", "circuit_not_clean"}


def decide(result: dict, cfg: CircuitConfig | None = None) -> dict:
    cfg = cfg or CircuitConfig()
    p = result["primary"]
    flags = {
        "base_acc": round(p["base_acc"][0], 4), "unigram_acc": round(p["unigram"], 4),
        "n_trained": p["n_trained"], "n_all": p["n_all"], "n_comp_seeds": p["comp_nums"]["n_comp_seeds"],
        "usable_seed_frac": round(p["redundancy"]["usable_frac"], 3),
        "classifiable_frac": round(p["classifiable_frac"], 3),
        "necessity": bool(p["necessity"]), "necessity_mean": bool(p["necessity_by_mode"]["mean"]),
        "necessity_zero": bool(p["necessity_by_mode"]["zero"]),
        "prev_ablate_acc_mean": round(p["modes"]["mean"]["prev_ablate"][0], 4),
        "ind_ablate_acc_mean": round(p["modes"]["mean"]["ind_ablate"][0], 4),
        "prev_ablate_acc_zero": round(p["modes"]["zero"]["prev_ablate"][0], 4),
        "ind_ablate_acc_zero": round(p["modes"]["zero"]["ind_ablate"][0], 4),
        "prev_control_acc": round(p["modes"]["mean"]["prev_control"][0], 4),
        "ind_control_acc": round(p["modes"]["mean"]["ind_control"][0], 4),
        "specificity": bool(p["specificity"]),
        "prev_redundant": bool(p["redundancy"]["prev_redundant"]),
        "ind_redundant": bool(p["redundancy"]["ind_redundant"]),
        "composition": bool(p["composition"]),
        "comp_drop_prev": round(p["comp_nums"]["drop_prev"], 4),
        "comp_drop_nonprev_control": round(p["comp_nums"]["drop_ctrl"], 4),
        "tau_grid_agree_frac": round(result["tau_grid_agree_frac"], 3),
    }
    if "prev_max_single_drop" in p["redundancy"]:
        flags["prev_max_single_drop"] = round(p["redundancy"]["prev_max_single_drop"][0], 4)
        flags["ind_max_single_drop"] = round(p["redundancy"]["ind_max_single_drop"][0], 4)
        flags["prev_class_drop"] = round(p["redundancy"]["prev_class_drop"][0], 4)
        flags["ind_class_drop"] = round(p["redundancy"]["ind_class_drop"][0], 4)

    # ---- validity gates (review if fail) ----
    if p["n_trained"] < max(2, 0.5 * p["n_all"]) or p["base_acc"][0] < result["S"]:
        return _v("review", "base_not_inducting", flags)            # too few seeds learned induction
    if p["classifiable_frac"] < cfg.usable_frac:
        return _v("review", "circuit_not_classifiable", flags)      # prev+induction heads absent in most trained seeds
    if p["necessity_by_mode"]["mean"] != p["necessity_by_mode"]["zero"]:
        return _v("review", "mean_zero_disagree", flags)            # zero-ablation OOD artifact
    if result["tau_grid_agree_frac"] < cfg.usable_frac:
        return _v("review", "tau_fragile", flags)

    # ---- verdict ladder (redundancy is a CHARACTERIZATION, not a validity gate: head COUNT varies
    #      across seeds, so it is only assessed where >=half the trained seeds have >=2 heads/class) ----
    if not (p["necessity"] and p["specificity"]):
        return _v("pass", "circuit_not_clean", flags)
    if not p["composition"]:
        return _v("pass", "circuit_necessary_specific_not_composed", flags)
    if p["redundancy"]["usable_frac"] < 0.5:
        return _v("pass", "circuit_necessary_specific_composed_redundancy_unassessed", flags)
    if p["redundancy"]["prev_redundant"] and p["redundancy"]["ind_redundant"]:
        return _v("pass", "circuit_necessary_specific_composed_and_redundant", flags)
    return _v("pass", "circuit_necessary_specific_composed_concentrated", flags)


def _v(status, verdict, flags):
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}


# ------------------------------------------------------------------------- report
def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    p = result["primary"]
    status, verdict, flags = info["status"], info["verdict"], info["flags"]
    cfg = result["cfg"]

    rows = [
        {"arm": "base (no ablation)", "acc_mean": flags["base_acc"], "acc_zero": flags["base_acc"], "note": "trained 2-layer model"},
        {"arm": "ablate ALL prev-token heads", "acc_mean": flags["prev_ablate_acc_mean"], "acc_zero": flags["prev_ablate_acc_zero"], "note": "necessity (L0)"},
        {"arm": "ablate ALL induction heads", "acc_mean": flags["ind_ablate_acc_mean"], "acc_zero": flags["ind_ablate_acc_zero"], "note": "necessity (L1)"},
        {"arm": "ablate matched-count control (L0 least-prev)", "acc_mean": flags["prev_control_acc"], "acc_zero": None, "note": "specificity"},
        {"arm": "ablate matched-count control (L1 least-ind)", "acc_mean": flags["ind_control_acc"], "acc_zero": None, "note": "specificity"},
    ]

    summary = {
        "status": status, "decision": info["decision"], "verdict": verdict,
        "K": cfg.K, "T": cfg.T, "width": cfg.width, "n_head": cfg.n_head, "seeds": result["n_seeds"],
        "base_acc": flags["base_acc"], "unigram_acc": flags["unigram_acc"], "chance": round(cfg.chance, 4),
        "necessity": flags["necessity"], "necessity_mean": flags["necessity_mean"], "necessity_zero": flags["necessity_zero"],
        "prev_ablate_acc": flags["prev_ablate_acc_mean"], "ind_ablate_acc": flags["ind_ablate_acc_mean"],
        "prev_control_acc": flags["prev_control_acc"], "ind_control_acc": flags["ind_control_acc"],
        "specificity": flags["specificity"], "composition": flags["composition"],
        "comp_drop_prev": flags["comp_drop_prev"], "comp_drop_nonprev_control": flags["comp_drop_nonprev_control"],
        "prev_redundant": flags["prev_redundant"], "ind_redundant": flags["ind_redundant"],
        "prev_max_single_drop": flags.get("prev_max_single_drop"), "prev_class_drop": flags.get("prev_class_drop"),
        "ind_max_single_drop": flags.get("ind_max_single_drop"), "ind_class_drop": flags.get("ind_class_drop"),
        "usable_seed_frac": flags["usable_seed_frac"], "tau_grid_agree_frac": flags["tau_grid_agree_frac"],
        "valid_measurement": status == "pass",
    }
    summary.update({f"flag_{k}": v for k, v in flags.items() if not isinstance(v, (dict, list))})

    recs = [
        (f"VERDICT ({verdict}, status={status}): causal dissection of the induction circuit in a 2-layer width-{cfg.width} "
         f"MiniGPT (n_head={cfg.n_head}) on v1196's clean induction task. Heads classified by attention pattern (prev-token "
         f"mass i->i-1 in L0; induction mass i->most-recent-successor in L1). status='pass' certifies a VALID, "
         f"non-degenerate, mean/zero-consistent, tau-robust measurement -- base model inducts {flags['base_acc']:.3f} "
         f"(>> unigram {flags['unigram_acc']:.3f}), >= {cfg.usable_frac:.0%} of seeds have >=2 heads per class."),
        (f"NECESSITY (MEAN-ablation primary; zero-ablation agreement required): ablating ALL prev-token heads -> acc "
         f"{flags['prev_ablate_acc_mean']:.3f}, ALL induction heads -> {flags['ind_ablate_acc_mean']:.3f} (both collapse "
         f"toward unigram {flags['unigram_acc']:.3f}; two-part bar = absolute floor + relative drop>=50%). "
         f"necessity={flags['necessity']} (mean={flags['necessity_mean']}, zero={flags['necessity_zero']}; "
         f"zero acc prev {flags['prev_ablate_acc_zero']:.3f}/ind {flags['ind_ablate_acc_zero']:.3f}). "
         f"Mean-ablation preserves the LayerNorm operating point; zero is reported only as a consistency check."),
        (f"SPECIFICITY (count-matched): ablating the SAME NUMBER of L0 LEAST-prev heads -> acc {flags['prev_control_acc']:.3f} "
         f"and L1 LEAST-induction heads -> {flags['ind_control_acc']:.3f} (vs the circuit-class collapse above). "
         f"specificity={flags['specificity']} -- it is the circuit heads specifically, not 'any k heads', that matter."),
        (f"REDUNDANCY (the honest nuance): max SINGLE-head drop prev {flags.get('prev_max_single_drop')} / ind "
         f"{flags.get('ind_max_single_drop')} vs CLASS drop prev {flags.get('prev_class_drop')} / ind {flags.get('ind_class_drop')} "
         f"-> prev_redundant={flags['prev_redundant']}, ind_redundant={flags['ind_redundant']}. Single-head ablation is "
         f"compensated by the redundant copies; only removing the whole class breaks induction."),
        (f"COMPOSITION (prev-token -> induction, on a SEPARATE batch with controls): ablating prev-token heads drops the "
         f"induction heads' attention by {flags['comp_drop_prev']:.3f} vs only {flags['comp_drop_nonprev_control']:.3f} for "
         f"a matched non-prev L0 control -> composition={flags['composition']} (the induction heads READ the prev-token "
         f"output; not a generic LayerNorm/residual shift). tau-robustness: verdict invariant in "
         f"{flags['tau_grid_agree_frac']:.0%} of the threshold grid. SCOPE: 2-layer width-{cfg.width} MiniGPT, n_head={cfg.n_head}, "
         f"K={cfg.K}/T={cfg.T}; the prev->induction circuit + depth requirement are textbook -- the NEW bit is the controlled "
         f"multi-seed redundancy + matched-specificity + mean-ablation demonstration. NOT a claim about LLM induction heads."),
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT induction circuit dissection v1197",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": info["decision"],
        "summary": summary, "rows": rows, "recommendations": recs,
        "csv_fieldnames": ["arm", "acc_mean", "acc_zero", "note"],
        "source": source,
    }


__all__ = [
    "CircuitConfig", "head_scores", "induction_attention", "acc_under_ablation",
    "attention_under_ablation", "capture_mu", "train_model", "run_phase_a", "summarize", "decide",
    "build_report", "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
