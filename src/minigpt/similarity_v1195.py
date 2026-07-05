"""v1195: TASK-SIMILARITY -> CATASTROPHIC FORGETTING (continual-learning axis, 3rd version).

The capstone of the continual-learning arc. v1193 showed forgetting is DISTRIBUTION-SHIFT
driven (random-label-B forgets A as much as a real new op); v1194 showed replay beats EWC
because the shift overwrites the SHARED/tied number-embedding. v1195 asks the natural next
question: does task SIMILARITY *grade* the forgetting, and if so, along which axis?

Setup is v1193's: a shared 1-layer transformer, sequences ``[a, OP, b, EQ, c]``; task
A=(a+b) mod p (PLUS op-token) is consolidated to a sustained plateau, then a task B (TIMES
op-token) is trained for a FIXED budget; forgetting = A's held-out accuracy drop. A GLOBAL
held-out (a,b) pair-mask quarantines A's test operands from ALL training (the shared/tied
embedding rows would otherwise leak A-test via B-train).

The single x-axis is the ANALYTIC OUTPUT-TABLE OVERLAP of B with A, model-independent:

    overlap(B) = |{(a,b) : f_B(a,b) == (a+b) mod p}| / p^2     (0..1)

Two manipulations vary it, and the claim is that forgetting is governed by overlap regardless
of HOW it was produced (operation family is a red herring that matters only through overlap):

* MIXTURE (continuous): B_s = (a+b) on a STRATIFIED fraction s of cells, (a*b) on the rest.
* TYPE family (qualitative): add_same(a+b), add_offset(a+b+c0), linear(2a+b), mul(a*b),
  rand(fixed random table). add_offset/mul/rand all sit at overlap ~0 despite spanning
  "same operation + constant" to "structureless".

Hardened by a 5-lens adversarial design panel. The non-obvious decisions it forced:

* x-axis is ANALYTIC overlap from a materialized (p,p) table -- NOT a model-MEASURED overlap
  (which is partly an EFFECT of low forgetting -> circular). Each B-function is one
  deterministic (p,p) table built BEFORE masking (so the SAME (a,b) maps to the same target
  in the train and test streams); the mixture is STRATIFIED so the realized add-fraction is
  exact, not sampled.
* overlap=1 (add_same / mixture s=1) forgets ~0 BY CONSTRUCTION (= v1193's continue-on-A
  floor restated) and is confounded with the op-token -- so it is EXCLUDED from the backing
  statistics; the claim is about the INTERIOR slope (overlap<1) only.
* accB (B-learnedness) and the SHARED-EMBEDDING DRIFT are logged per arm and partialled out:
  forgetting must track overlap with accB/drift held constant, else the slope is a "B was
  barely learned -> less overwrite" artifact. accB is split into CONFLICT cells (f_B!=f_A,
  genuine B-learning) vs OVERLAP cells (where the retained A-circuit answers for free).
* per-arm B-learnedness GATE: arms the net cannot learn forget via generic drift, OFF the
  overlap curve -- they are excluded and reported separately, not silently included.
* C3 (unification) is a pre-registered RESIDUAL test (each independent type point within a
  margin of the mixture curve), not a bare correlation (which the two end-clusters force).
* C2 (operation family does not protect) is an EQUIVALENCE test (TOST-style), never
  failure-to-reject (which low power passes trivially).
* SUPER-LINEAR test: the trivial "overwrite the conflicting cells" null predicts
  forgetting ~= (1-overlap). Observed forgetting FAR EXCEEDS that -> even a small target
  shift collapses the shared representation GLOBALLY, not locally (the non-trivial content,
  tying back to v1193's global-shift finding).

``status=="pass"`` certifies a VALID measurement (A consolidated per-seed, clean floor, no
leak, enough learnable curve points), with the x-axis the model-INDEPENDENT analytic overlap
-- NEVER a flattering collapse. Phase A trains + caches; Phase B is CPU-only and re-derives.

Scope: toy modular arithmetic on a 1-layer transformer; not a claim about LLM forgetting.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

import torch

from minigpt.continual_v1193 import (
    ContinualConfig, _opt, _step, consolidate, eq_token, majority_prior, make_model,
    op_token, pair_masks, vocab_size,
)
from minigpt.experiment_utils import mean_std
from minigpt.grok_v1179 import ANSWER_TARGET_POS, answer_accuracy
from minigpt.similarity_v1195_decision import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    decide_similarity,
)
from minigpt.similarity_v1195_report import build_similarity_report
from minigpt.similarity_v1195_stats import (
    spearman,
    spearman_perm_p,
)

TYPE_FUNCS = ("add_same", "add_offset", "linear", "mul", "rand")
# operation FAMILY of each type function (for the "family is a red herring" framing)
TYPE_FAMILY = {"add_same": "add", "add_offset": "add", "linear": "linear", "mul": "mul", "rand": "none"}


@dataclass
class SimilarityConfig:
    base: ContinualConfig = field(default_factory=lambda: ContinualConfig(
        p=23, task_a="add", task_b="mul", train_frac=0.8, weight_decay=0.5,
        plateau_acc=0.98, plateau_hold=5, consolidate_max_steps=6000, b_budget=1500,
        b_eval_every=100))
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)   # >=5 (panel S2: the headline is a graded slope)
    mixture_ss: tuple[float, ...] = (1.0, 0.875, 0.75, 0.5, 0.25, 0.0)  # s=1==add_same, s=0==mul (endpoints)
    type_funcs: tuple[str, ...] = TYPE_FUNCS
    add_offset_c0: int = 7
    # --- pre-registered decide() thresholds (panel M5: pinned BEFORE Phase B) ---
    b_learn_margin: float = 0.25     # per-arm "B learned": (accB_conflict - majority_prior) >= this
    floor_tol: float = 0.05          # continue-on-A forgetting must be <= this (the floor)
    min_reduction: float = 0.05      # margin for every "A forgets more than B" (guards std==0 knife-edge)
    c1_min_range: float = 0.30       # slope must span at least this much forgetting (low- vs high-overlap)
    spearman_floor: float = -0.80    # monotone-graded: Spearman(overlap, forgetting) <= this
    equiv_delta: float = 0.15        # C2 equivalence band: |forget(add_offset)-forget(mul)| <= delta-std
    residual_margin: float = 0.15    # C3: |type forget - mixture-curve(overlap)| <= max(2*std, this)
    residual_std_mult: float = 2.0
    superlinear_margin: float = 0.10 # forgetting exceeds the (1-overlap) overwrite null by this (interior)
    low_overlap_max: float = 0.15    # "overlap ~ 0" bucket (>= 1/p chance floor) for C2 / structure test

    @property
    def p(self) -> int:
        return self.base.p


# --------------------------------------------------------------------- task tables (analytic)
def _salt(seed: int, tag: str) -> int:
    """A deterministic per-(seed, tag) Generator salt, independent of the global RNG stream."""
    return (seed * 100003 + sum(ord(ch) for ch in tag) * 7 + len(tag)) % (2 ** 31 - 1)


def f_add_table(p: int) -> torch.Tensor:
    """A's full (p,p) answer table, f_A(a,b)=(a+b) mod p (row=a, col=b)."""
    a = torch.arange(p).view(p, 1)
    b = torch.arange(p).view(1, p)
    return (a + b) % p


def type_table(name: str, p: int, seed: int, c0: int) -> torch.Tensor:
    """A B-type function's full deterministic (p,p) answer table (materialized before masking)."""
    a = torch.arange(p).view(p, 1)
    b = torch.arange(p).view(1, p)
    if name == "add_same":
        return (a + b) % p
    if name == "add_offset":
        return (a + b + c0) % p
    if name == "linear":
        return (2 * a + b) % p
    if name == "mul":
        return (a * b) % p
    if name == "rand":
        g = torch.Generator().manual_seed(_salt(seed, "rand"))
        return torch.randint(p, (p, p), generator=g)
    raise ValueError(f"unknown type function {name!r}")


def mixture_table(s: float, p: int, seed: int, train_cells: torch.Tensor,
                  test_cells: torch.Tensor) -> torch.Tensor:
    """B_s table: (a+b) on a fraction s of cells (STRATIFIED separately within the train and
    test cell sets so the realized add-fraction is EXACT in each), (a*b) elsewhere."""
    add = f_add_table(p)
    mul = (torch.arange(p).view(p, 1) * torch.arange(p).view(1, p)) % p
    use_add = torch.zeros(p, p, dtype=torch.bool)
    g = torch.Generator().manual_seed(_salt(seed, f"mix{s:.4f}"))
    for cells in (train_cells, test_cells):
        flat = cells.reshape(-1).nonzero(as_tuple=False).flatten()
        k = int(round(s * flat.numel()))
        if k > 0:
            pick = flat[torch.randperm(flat.numel(), generator=g)[:k]]
            use_add[pick // p, pick % p] = True
    return torch.where(use_add, add, mul)


def analytic_overlap(table_b: torch.Tensor, p: int, cell_mask: torch.Tensor | None = None) -> float:
    """Fraction of cells (all p^2, or those selected by cell_mask) where f_B == f_A=(a+b) mod p.
    Exact, model-INDEPENDENT (includes accidental a*b==a+b collisions)."""
    agree = table_b == f_add_table(p)
    if cell_mask is not None:
        agree = agree[cell_mask]
    return float(agree.float().mean().item())


def build_rows(cfg: SimilarityConfig, table: torch.Tensor, which: str,
               cells: torch.Tensor) -> torch.Tensor:
    """Rows ``[a, op, b, EQ, c]`` for op ``which`` over the (a,b) cells (a (p,p) bool) selected,
    with answers read from ``table[a,b]`` (so train and test draw the SAME function)."""
    p = cfg.p
    a = torch.arange(p).repeat_interleave(p)
    b = torch.arange(p).repeat(p)
    m = cells.reshape(-1)
    a, b = a[m], b[m]
    c = table[a, b]
    opid = torch.full_like(a, op_token(cfg.base, which))
    eq = torch.full_like(a, eq_token(cfg.base))
    return torch.stack([a, opid, b, eq, c], dim=1)


def conflict_overlap_masks(table_b: torch.Tensor, p: int, cells: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Split selected cells into (conflict = f_B!=f_A, overlap = f_B==f_A) (p,p) bool masks."""
    agree = (table_b == f_add_table(p)) & cells
    conflict = (~(table_b == f_add_table(p))) & cells
    return conflict, agree


# ----------------------------------------------------------------------------- training (B phase)
def train_b(cfg: SimilarityConfig, init_state: dict, b_train: torch.Tensor, *,
            a_test: torch.Tensor, b_test_conflict: torch.Tensor | None,
            b_test_overlap: torch.Tensor | None, b_train_acc: torch.Tensor,
            b_train_conflict: torch.Tensor | None = None, b_train_overlap: torch.Tensor | None = None,
            seed: int = 0, device=None) -> dict:
    """From the consolidated A-init, train the fixed B-budget on ``b_train``; log A's trajectory,
    accB split into conflict/overlap cells (on TEST cells for generalization AND on TRAIN cells
    -- the latter is the honest learnedness signal, since the random-partition mixture cannot
    generalize a per-cell add/mul split to held-out cells but CAN fit it on the train cells, and
    fitting B-train is what causes the interference), B-train memorization, and the displacement
    of the SHARED number-embedding rows (the v1194 overwrite locus) + total parameter drift."""
    base = cfg.base
    model = make_model(base).to(device)
    model.load_state_dict(init_state)
    opt = _opt(model, base)
    p = cfg.p
    b_train = b_train.to(device); a_test = a_test.to(device); b_train_acc = b_train_acc.to(device)

    num_rows0 = model.token_embedding.weight.detach()[:p].clone()
    theta0 = [q.detach().clone() for q in model.parameters()]

    traj = []
    for st in range(base.b_budget):
        _step(model, opt, b_train)
        if st % base.b_eval_every == 0:
            traj.append(round(answer_accuracy(model, a_test), 6))

    num_rows1 = model.token_embedding.weight.detach()[:p]
    emb_drift = float((num_rows1 - num_rows0).norm().item())
    total_drift = float(math.sqrt(sum((q.detach() - t0).pow(2).sum().item()
                                      for q, t0 in zip(model.parameters(), theta0))))

    def acc_or_none(rows):
        if rows is None or rows.shape[0] == 0:
            return None
        return answer_accuracy(model, rows.to(device))

    return {
        "accA_after_B": answer_accuracy(model, a_test),
        "accB_conflict": acc_or_none(b_test_conflict),
        "accB_overlap": acc_or_none(b_test_overlap),
        "accB_train": answer_accuracy(model, b_train_acc),
        "accB_train_conflict": acc_or_none(b_train_conflict),
        "accB_train_overlap": acc_or_none(b_train_overlap),
        "emb_drift": emb_drift, "total_drift": total_drift, "trajA": traj,
    }


def _consolidate_joint(cfg: SimilarityConfig, A_tr, B_tr, A_te, B_te, seed, device):
    """Multitask-joint upper bound (fresh model on A_tr+B_tr) for the v1193 interference-not-
    incapacity anchor; run for the canonical add+mul only."""
    base = cfg.base
    torch.manual_seed(seed)
    jm = make_model(base).to(device)
    jopt = _opt(jm, base)
    both = torch.cat([A_tr, B_tr], dim=0).to(device)
    A_te_d, B_te_d = A_te.to(device), B_te.to(device)
    js, hold = 0, 0
    while js < base.joint_max_steps:
        for _ in range(base.eval_every):
            _step(jm, jopt, both); js += 1
        hold = hold + 1 if (answer_accuracy(jm, A_te_d) >= base.plateau_acc and
                            answer_accuracy(jm, B_te_d) >= base.plateau_acc) else 0
        if hold >= base.plateau_hold:
            break
    return {"accA": answer_accuracy(jm, A_te_d), "accB": answer_accuracy(jm, B_te_d)}


def run_phase_a(cfg: SimilarityConfig, device) -> dict:
    """Single training pass -> cache. Per seed: consolidate A once (reused); for every B-arm
    (type funcs + mixture s) train B from that init logging forgetting/accB-split/drift/overlap;
    continue-on-A floor; canonical add+mul joint bound. No verdict logic (Phase B re-derives)."""
    base = cfg.base
    p = cfg.p
    chance = 1.0 / p
    seeds = cfg.seeds
    arms: dict[str, dict] = {}          # arm_key -> {seed -> record}
    overlaps: dict[str, dict] = {}      # arm_key -> {seed -> (global, train, test)}
    plateau: dict[int, float] = {}
    cont: dict[int, dict] = {}
    joint: dict[int, dict] = {}
    b_majority: dict[str, float] = {}
    leak_ok = True

    f_add = f_add_table(p)

    for seed in seeds:
        tr_flat, te_flat = pair_masks(base, seed)
        train_cells = tr_flat.reshape(p, p)
        test_cells = te_flat.reshape(p, p)
        A_tr = build_rows(cfg, f_add, "A", train_cells)
        A_te = build_rows(cfg, f_add, "A", test_cells)

        # leak: A-test operands never appear in ANY B-train stream (shared global mask -> true)
        tr_pairs = {(int(r[0]), int(r[2])) for r in A_tr}
        te_pairs = {(int(r[0]), int(r[2])) for r in A_te}
        leak_ok = leak_ok and tr_pairs.isdisjoint(te_pairs)

        state, plat, _ = consolidate(base, A_tr, A_te, seed, device)
        plateau[seed] = plat

        def run_arm(key, table):
            B_tr = build_rows(cfg, table, "B", train_cells)
            conf, ovl = conflict_overlap_masks(table, p, test_cells)
            tconf, tovl = conflict_overlap_masks(table, p, train_cells)
            B_te_conf = build_rows(cfg, table, "B", conf) if conf.any() else None
            B_te_ovl = build_rows(cfg, table, "B", ovl) if ovl.any() else None
            B_tr_conf = build_rows(cfg, table, "B", tconf) if tconf.any() else None
            B_tr_ovl = build_rows(cfg, table, "B", tovl) if tovl.any() else None
            rec = train_b(cfg, state, B_tr, a_test=A_te, b_test_conflict=B_te_conf,
                          b_test_overlap=B_te_ovl, b_train_acc=B_tr, b_train_conflict=B_tr_conf,
                          b_train_overlap=B_tr_ovl, seed=seed, device=device)
            arms.setdefault(key, {})[seed] = rec
            overlaps.setdefault(key, {})[seed] = (
                analytic_overlap(table, p), analytic_overlap(table, p, train_cells),
                analytic_overlap(table, p, test_cells))
            if key not in b_majority:
                b_majority[key] = majority_prior(B_tr, p)

        for name in cfg.type_funcs:
            run_arm(f"type:{name}", type_table(name, p, seed, cfg.add_offset_c0))
        for s in cfg.mixture_ss:
            run_arm(f"mix:{s:.3f}", mixture_table(s, p, seed, train_cells, test_cells))

        # continue-on-A floor (more A under the A op-token -> ~0 forgetting)
        cont[seed] = {"accA_after_B": train_b(
            cfg, state, A_tr, a_test=A_te, b_test_conflict=None, b_test_overlap=None,
            b_train_acc=A_tr, seed=seed, device=device)["accA_after_B"]}

        # canonical add+mul joint upper bound (interference, not incapacity)
        B_mul = build_rows(cfg, type_table("mul", p, seed, cfg.add_offset_c0), "B", train_cells)
        B_mul_te = build_rows(cfg, type_table("mul", p, seed, cfg.add_offset_c0), "B", test_cells)
        joint[seed] = _consolidate_joint(cfg, A_tr, B_mul, A_te, B_mul_te, seed, device)

    return {
        "config": {"p": p, "train_frac": base.train_frac, "b_budget": base.b_budget,
                   "weight_decay": base.weight_decay, "seeds": list(seeds),
                   "mixture_ss": list(cfg.mixture_ss), "type_funcs": list(cfg.type_funcs),
                   "add_offset_c0": cfg.add_offset_c0},
        "chance": chance, "leak_free": leak_ok, "b_majority": b_majority,
        "plateau": plateau, "arms": arms, "overlaps": overlaps,
        "continue_on_A": cont, "joint": joint,
    }


# ------------------------------------------------------------------------------- analysis
def _arm_stats(cache: dict, key: str, cfg: SimilarityConfig) -> dict:
    seeds = cache["config"]["seeds"]
    plat = cache["plateau"]
    recs = cache["arms"][key]
    forget = mean_std([plat[s] - recs[s]["accA_after_B"] for s in seeds])
    accA = mean_std([recs[s]["accA_after_B"] for s in seeds])
    accB_conf = mean_std([recs[s]["accB_conflict"] for s in seeds if recs[s]["accB_conflict"] is not None])
    accB_tr_conf = mean_std([recs[s].get("accB_train_conflict") for s in seeds
                             if recs[s].get("accB_train_conflict") is not None])
    accB_train = mean_std([recs[s]["accB_train"] for s in seeds])
    emb = mean_std([recs[s]["emb_drift"] for s in seeds])
    tot = mean_std([recs[s]["total_drift"] for s in seeds])
    ov = cache["overlaps"][key]
    overlap_test = mean_std([ov[s][2] for s in seeds])      # held-out cells (where forgetting is read)
    overlap_glob = mean_std([ov[s][0] for s in seeds])
    prior = cache["b_majority"][key]
    # "Learned" == the model FIT B's CONFLICT cells (those whose target differs from A) DURING
    # TRAINING -- that fitting is what overwrites the shared weights and causes forgetting. The
    # held-out conflict accuracy cannot be the signal: a random per-cell add/mul partition has NO
    # held-out generalization (the model can't know an unseen cell's assignment), so a learnedness
    # gate on TEST conflict would wrongly mark the mid-overlap mixtures unlearned. An overlap==1
    # arm has no conflict cells -> trivially learned (it is just A).
    has_conflict = not math.isnan(accB_tr_conf[0])
    learn_signal = accB_tr_conf[0] if has_conflict else accB_train[0]
    learned = (learn_signal - prior) >= cfg.b_learn_margin if has_conflict else True
    return {"key": key, "forget": forget, "accA_after": accA, "accB_conflict": accB_conf,
            "accB_train_conflict": accB_tr_conf, "accB_train": accB_train,
            "emb_drift": emb, "total_drift": tot, "overlap": overlap_test, "overlap_global": overlap_glob,
            "prior": prior, "learned": bool(learned), "has_conflict": has_conflict}


def summarize(cache: dict, cfg: SimilarityConfig | None = None) -> dict:
    cfg = cfg or SimilarityConfig()
    seeds = cache["config"]["seeds"]
    plat = cache["plateau"]

    mix_keys = [f"mix:{s:.3f}" for s in cache["config"]["mixture_ss"]]
    type_keys = [f"type:{n}" for n in cache["config"]["type_funcs"]]
    stats = {k: _arm_stats(cache, k, cfg) for k in mix_keys + type_keys}

    plateau_ms = mean_std([plat[s] for s in seeds])
    per_seed_plateau_ok = all(plat[s] >= cfg.base.plateau_acc - 0.02 for s in seeds)
    cont_forget = mean_std([plat[s] - cache["continue_on_A"][s]["accA_after_B"] for s in seeds])
    joint_accA = mean_std([cache["joint"][s]["accA"] for s in seeds])
    joint_accB = mean_std([cache["joint"][s]["accB"] for s in seeds])

    return {
        "config": cache["config"], "chance": cache["chance"], "leak_free": cache["leak_free"],
        "plateau": plateau_ms, "per_seed_plateau_ok": per_seed_plateau_ok,
        "continue_on_A_forget": cont_forget, "joint_accA": joint_accA, "joint_accB": joint_accB,
        "mix_keys": mix_keys, "type_keys": type_keys, "stats": stats, "seeds": seeds,
    }


# verdict vocabulary and report assembly live in focused pure modules.
def decide(result: dict, cfg: SimilarityConfig | None = None) -> dict:
    """Apply the pre-registered v1195 verdict ladder."""
    return decide_similarity(result, cfg or SimilarityConfig())


def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    """Assemble the stable v1195 report contract."""
    defaults = SimilarityConfig()
    return build_similarity_report(
        result,
        info,
        source,
        generated_at=generated_at,
        c1_min_range=defaults.c1_min_range,
        equiv_delta=defaults.equiv_delta,
    )


__all__ = [
    "SimilarityConfig", "TYPE_FUNCS", "TYPE_FAMILY", "f_add_table", "type_table", "mixture_table",
    "analytic_overlap", "build_rows", "conflict_overlap_masks", "train_b", "run_phase_a",
    "spearman", "spearman_perm_p", "summarize", "decide", "build_report",
    "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
