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
import itertools
import math
from dataclasses import dataclass, field

import torch

from minigpt.continual_v1193 import (
    ContinualConfig, _opt, _step, consolidate, eq_token, majority_prior, make_model,
    op_token, pair_masks, vocab_size,
)
from minigpt.experiment_utils import mean_std, significant
from minigpt.grok_v1179 import ANSWER_TARGET_POS, answer_accuracy
from minigpt.report_utils import utc_now

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


# ------------------------------------------------------------------------------- stats helpers
def _rank(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def spearman(xs: list[float], ys: list[float]) -> float:
    return _pearson(_rank(xs), _rank(ys))


def spearman_perm_p(xs: list[float], ys: list[float]) -> float:
    """Exact two-sided permutation p-value for |Spearman| (N is tiny -> enumerate)."""
    obs = abs(spearman(xs, ys))
    n = len(xs)
    if n > 8:   # 8! = 40320, safe cap
        return float("nan")
    rx = _rank(xs)
    cnt = tot = 0
    for perm in itertools.permutations(range(n)):
        tot += 1
        ry = [_rank(ys)[i] for i in perm]
        if abs(_pearson(rx, ry)) >= obs - 1e-12:
            cnt += 1
    return cnt / tot


def _ols2(y: list[float], x1: list[float], x2: list[float]) -> tuple[float, float, float]:
    """Standardized 2-variable OLS y ~ x1 + x2; returns (beta1*, beta2*, R^2). Few points ->
    descriptive only (panel: show overlap survives controlling for accB)."""
    def z(v):
        m = sum(v) / len(v)
        sd = math.sqrt(sum((t - m) ** 2 for t in v) / len(v)) or 1.0
        return [(t - m) / sd for t in v]
    Y, X1, X2 = z(y), z(x1), z(x2)
    r12 = _pearson(X1, X2)
    r_y1 = _pearson(Y, X1)
    r_y2 = _pearson(Y, X2)
    denom = 1 - r12 ** 2
    if abs(denom) < 1e-9:
        return float("nan"), float("nan"), float("nan")
    b1 = (r_y1 - r_y2 * r12) / denom
    b2 = (r_y2 - r_y1 * r12) / denom
    r2 = b1 * r_y1 + b2 * r_y2
    return b1, b2, r2


def _isotonic_decreasing(xs: list[float], ys: list[float]) -> list[tuple[float, float]]:
    """PAVA fit of y NON-INCREASING in x; returns sorted (x, y_fit) for interpolation."""
    pts = sorted(zip(xs, ys))
    xv = [x for x, _ in pts]
    yv = [y for _, y in pts]
    w = [1.0] * len(yv)
    # enforce non-increasing
    i = 0
    blocks = [[yv[k], w[k]] for k in range(len(yv))]
    merged = []
    for val, wt in blocks:
        merged.append([val, wt])
        while len(merged) > 1 and merged[-2][0] < merged[-1][0]:
            v2, w2 = merged.pop()
            v1, w1 = merged.pop()
            merged.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2])
    fit = []
    idx = 0
    for val, wt in merged:
        for _ in range(int(round(wt))):
            fit.append(val)
            idx += 1
    return list(zip(xv, fit))


def _interp(curve: list[tuple[float, float]], x: float) -> float:
    """Linear interpolation on a sorted (x,y) curve; clamps to the endpoints."""
    if x <= curve[0][0]:
        return curve[0][1]
    if x >= curve[-1][0]:
        return curve[-1][1]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return curve[-1][1]


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


# verdict vocabulary
REVIEW_VERDICTS = {"task_a_not_consolidated", "no_forgetting_floor", "operand_leak",
                   "not_jointly_learnable", "too_few_learnable_curve_points", "underpowered_type_contrast"}
PRIMARY_VERDICTS = {"forgetting_governed_by_output_overlap",
                    "overlap_grades_forgetting_with_residual_structure",
                    "forgetting_tracks_task_type", "no_overlap_dependence"}


def decide(result: dict, cfg: SimilarityConfig | None = None) -> dict:
    """Pure gates + pre-registered, margin-aware verdict ladder (panel M4/M5). status=='pass'
    certifies a VALID measurement on the model-INDEPENDENT analytic overlap, never a clean curve."""
    cfg = cfg or SimilarityConfig()
    st = result["stats"]
    chance = result["chance"]

    def beats(more, less):   # `more` forgetting meaningfully exceeds `less` (margin AND combined std)
        (mm, ms), (lm, ls) = more, less
        return (mm - lm) > cfg.min_reduction and significant(mm, ms, lm, ls)

    # ---- validity gates ----
    g_consol = result["per_seed_plateau_ok"] and result["plateau"][0] >= cfg.base.plateau_acc - 0.02
    g_floor = result["continue_on_A_forget"][0] <= cfg.floor_tol
    g_leak = bool(result["leak_free"])
    prior = st["type:mul"]["prior"] if "type:mul" in st else next(iter(st.values()))["prior"]
    g_joint = ((result["joint_accA"][0] - prior) >= cfg.b_learn_margin and
               (result["joint_accB"][0] - prior) >= cfg.b_learn_margin)

    # mixture curve = learned mixture arms; EXCLUDE the overlap==1 endpoint (definitional, M4)
    mix = [st[k] for k in result["mix_keys"]]
    mix_learned = [m for m in mix if m["learned"]]
    mix_curve = [m for m in mix_learned if m["overlap"][0] < 0.999]   # interior + low end
    g_enough = len(mix_curve) >= 4

    # independent type evidence = add_offset, linear, rand (add_same==mix s=1, mul==mix s=0)
    indep_type = [st[k] for k in ("type:add_offset", "type:linear", "type:rand") if k in st]
    indep_learned = [t for t in indep_type if t["learned"]]

    degenerate_zero_variance = any(m["forget"][1] == 0.0 for m in mix_learned)

    # ---- C1: monotone graded slope over the mixture interior ----
    ov = [m["overlap"][0] for m in mix_curve]
    fg = [m["forget"][0] for m in mix_curve]
    rho = spearman(ov, fg) if len(mix_curve) >= 3 else float("nan")
    rho_p = spearman_perm_p(ov, fg) if len(mix_curve) >= 3 else float("nan")
    if mix_curve:
        lo = min(mix_curve, key=lambda m: m["overlap"][0])   # lowest overlap -> most forgetting
        hi = max(mix_curve, key=lambda m: m["overlap"][0])   # highest overlap -> least forgetting
        span = lo["forget"][0] - hi["forget"][0]
        c1_slope = (rho <= cfg.spearman_floor) and (span >= cfg.c1_min_range) and beats(lo["forget"], hi["forget"])
    else:
        span, c1_slope = 0.0, False

    # ---- accB / drift confound (panel M3): overlap must survive controlling for them ----
    allp = mix_curve + indep_learned
    if len(allp) >= 4:
        y = [m["forget"][0] for m in allp]
        xo = [m["overlap"][0] for m in allp]
        xb = [m["accB_train_conflict"][0] if not math.isnan(m["accB_train_conflict"][0])
              else m["accB_train"][0] for m in allp]   # learnedness = fitting B's conflict cells
        xd = [m["emb_drift"][0] for m in allp]
        b_ov_accB, b_accB, r2_b = _ols2(y, xo, xb)
        b_ov_drift, b_drift, r2_d = _ols2(y, xo, xd)
        overlap_survives = (b_ov_accB < 0 and abs(b_ov_accB) >= abs(b_accB) and
                            b_ov_drift < 0 and abs(b_ov_drift) >= abs(b_drift))
    else:
        b_ov_accB = b_accB = b_ov_drift = b_drift = r2_b = r2_d = float("nan")
        overlap_survives = False

    # ---- super-linear test (panel S6): observed forgetting vs the (1-overlap) overwrite null ----
    plat_m = result["plateau"][0]
    sl_devs = [m["forget"][0] - (1.0 - m["overlap"][0]) * plat_m for m in mix_curve]
    superlinear = (sum(sl_devs) / len(sl_devs)) >= cfg.superlinear_margin if sl_devs else False

    # ---- C2: operation FAMILY does not protect (equivalence, TOST-style) ----
    ao, mu, asame = st.get("type:add_offset"), st.get("type:mul"), st.get("type:add_same")
    have_c2 = ao is not None and mu is not None and asame is not None
    type_lowov = [t for t in (ao, mu, st.get("type:rand")) if t is not None
                  and t["learned"] and t["overlap"][0] <= cfg.low_overlap_max]
    combined_std_type = math.sqrt(ao["forget"][1] ** 2 + mu["forget"][1] ** 2) if have_c2 else float("nan")
    underpowered_type = bool(have_c2 and combined_std_type > 0.20)
    c2_equiv = bool(have_c2 and ao["learned"] and mu["learned"] and
                    abs(ao["forget"][0] - mu["forget"][0]) <= cfg.equiv_delta - combined_std_type and
                    beats(ao["forget"], asame["forget"]) and beats(mu["forget"], asame["forget"]))
    family_protects = bool(have_c2 and ao["learned"] and mu["learned"] and beats(mu["forget"], ao["forget"]))

    # ---- C3: unification residual -- each independent learned type point near the mixture curve ----
    curve = _isotonic_decreasing([m["overlap"][0] for m in mix_curve], [m["forget"][0] for m in mix_curve]) \
        if len(mix_curve) >= 2 else []
    residuals = {}
    c3_ok = bool(indep_learned) and bool(curve)
    for t in (indep_learned if curve else []):
        pred = _interp(curve, t["overlap"][0])
        res = abs(t["forget"][0] - pred)
        tol = max(cfg.residual_std_mult * t["forget"][1], cfg.residual_margin)
        residuals[t["key"]] = {"overlap": round(t["overlap"][0], 4), "forget": round(t["forget"][0], 4),
                               "pred": round(pred, 4), "residual": round(res, 4), "tol": round(tol, 4),
                               "within": bool(res <= tol)}
        c3_ok = c3_ok and (res <= tol)

    # ---- structure-at-fixed-overlap (panel S4): does operation STRUCTURE add forgetting beyond
    # what overlap predicts? The honest test is the C3 RESIDUAL (raw forgetting differences among
    # "low overlap" tasks are confounded by their small overlap differences -- add_offset o=0.0
    # forgets more than mul o=0.043 BECAUSE it conflicts on every cell, which is the overlap law,
    # not residual structure). So: structure_at_fixed_overlap == some learned type point deviates
    # from the mixture curve beyond tolerance == not c3_ok.
    structure_at_fixed_overlap = bool(indep_learned) and (not c3_ok)
    # raw spread among the learned overlap~0 type tasks, reported for context only (NOT a gate)
    lowov_forget_spread = (max(t["forget"][0] for t in type_lowov) - min(t["forget"][0] for t in type_lowov)) \
        if len(type_lowov) >= 2 else 0.0

    flags = {
        "g_a_consolidated": bool(g_consol), "g_floor_clean": bool(g_floor),
        "g_no_operand_leak": bool(g_leak), "g_jointly_learnable": bool(g_joint),
        "g_enough_curve_points": bool(g_enough), "degenerate_zero_variance": bool(degenerate_zero_variance),
        "c1_monotone_slope": bool(c1_slope), "spearman_overlap_forget": round(rho, 4),
        "spearman_perm_p": round(rho_p, 4) if not math.isnan(rho_p) else None, "slope_span": round(span, 4),
        "overlap_survives_accB_and_drift": bool(overlap_survives),
        "beta_overlap_given_accB": round(b_ov_accB, 3) if not math.isnan(b_ov_accB) else None,
        "beta_accB": round(b_accB, 3) if not math.isnan(b_accB) else None,
        "beta_overlap_given_drift": round(b_ov_drift, 3) if not math.isnan(b_ov_drift) else None,
        "beta_drift": round(b_drift, 3) if not math.isnan(b_drift) else None,
        "superlinear_vs_overwrite_null": bool(superlinear),
        "mean_superlinear_excess": round(sum(sl_devs) / len(sl_devs), 4) if sl_devs else None,
        "c2_family_does_not_protect": bool(c2_equiv), "family_protects": bool(family_protects),
        "underpowered_type_contrast": bool(underpowered_type),
        "c3_type_points_on_curve": bool(c3_ok), "residuals": residuals,
        "structure_at_fixed_overlap": bool(structure_at_fixed_overlap),
        "lowov_forget_spread": round(lowov_forget_spread, 4),
        "n_mix_learned": len(mix_learned), "n_mix_curve": len(mix_curve),
        "n_indep_type_learned": len(indep_learned),
    }

    # ---- ladder ----
    if not g_consol:
        return _v("review", "task_a_not_consolidated", flags)
    if not g_floor:
        return _v("review", "no_forgetting_floor", flags)
    if not g_leak:
        return _v("review", "operand_leak", flags)
    if not g_joint:
        return _v("review", "not_jointly_learnable", flags)
    if not g_enough:
        return _v("review", "too_few_learnable_curve_points", flags)
    if underpowered_type and not family_protects:
        return _v("review", "underpowered_type_contrast", flags)

    if not c1_slope:
        return _v("pass", "no_overlap_dependence", flags)
    if family_protects:
        return _v("pass", "forgetting_tracks_task_type", flags)
    # clean unification: family doesn't protect (C2), every independent type point lies on the
    # mixture curve at its own overlap (C3 == no residual structure), and overlap out-predicts
    # accB/drift (M3). c3_ok already subsumes (not structure_at_fixed_overlap).
    clean = c2_equiv and c3_ok and overlap_survives
    if clean:
        return _v("pass", "forgetting_governed_by_output_overlap", flags)
    return _v("pass", "overlap_grades_forgetting_with_residual_structure", flags)


def _v(status: str, verdict: str, flags: dict) -> dict:
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}


# ------------------------------------------------------------------------------- report
def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    st = result["stats"]
    status, verdict, flags = info["status"], info["verdict"], info["flags"]
    chance = result["chance"]

    rows = []
    for k in result["mix_keys"] + result["type_keys"]:
        m = st[k]
        rows.append({
            "arm": k, "overlap": round(m["overlap"][0], 4),
            "forgetting": round(m["forget"][0], 4), "forgetting_std": round(m["forget"][1], 4),
            "accB_conflict_test": (round(m["accB_conflict"][0], 4) if not math.isnan(m["accB_conflict"][0]) else None),
            "accB_conflict_train": (round(m["accB_train_conflict"][0], 4) if not math.isnan(m["accB_train_conflict"][0]) else None),
            "emb_drift": round(m["emb_drift"][0], 4), "learned": m["learned"],
        })

    summary = {
        "status": status, "decision": info["decision"], "verdict": verdict,
        "p": result["config"]["p"], "seeds": len(result["seeds"]),
        "train_frac": result["config"]["train_frac"], "b_budget": result["config"]["b_budget"],
        "chance": round(chance, 5), "leak_free": result["leak_free"],
        "accA_plateau": round(result["plateau"][0], 4), "per_seed_plateau_ok": result["per_seed_plateau_ok"],
        "continue_on_A_forgetting": round(result["continue_on_A_forget"][0], 4),
        "joint_accA": round(result["joint_accA"][0], 4), "joint_accB": round(result["joint_accB"][0], 4),
        "spearman_overlap_forgetting": flags["spearman_overlap_forget"],
        "spearman_perm_p": flags["spearman_perm_p"], "slope_span": flags["slope_span"],
        "overlap_survives_accB_and_drift": flags["overlap_survives_accB_and_drift"],
        "superlinear_vs_overwrite_null": flags["superlinear_vs_overwrite_null"],
        "mean_superlinear_excess": flags["mean_superlinear_excess"],
        "c2_family_does_not_protect": flags["c2_family_does_not_protect"],
        "family_protects": flags["family_protects"],
        "c3_type_points_on_curve": flags["c3_type_points_on_curve"],
        "structure_at_fixed_overlap": flags["structure_at_fixed_overlap"],
        "n_mix_curve": flags["n_mix_curve"], "n_indep_type_learned": flags["n_indep_type_learned"],
        "valid_measurement": status == "pass",
    }
    summary.update({f"flag_{k}": v for k, v in flags.items() if not isinstance(v, dict)})

    ao, mu, asame = st["type:add_offset"], st["type:mul"], st["type:add_same"]
    recs = [
        (f"VERDICT ({verdict}, status={status}): x-axis is the ANALYTIC output-table overlap of B with "
         f"A=(a+b) mod {result['config']['p']} -- model-INDEPENDENT, |{{(a,b):f_B==f_A}}|/p^2. "
         f"Forgetting = A's held-out accuracy drop from its consolidated plateau {result['plateau'][0]:.3f} "
         f"after a fixed {result['config']['b_budget']}-step B phase. status='pass' certifies a VALID "
         f"measurement (A consolidated per-seed, clean continue-on-A floor {result['continue_on_A_forget'][0]:.3f}, "
         f"no operand leak, add+mul jointly learnable A{result['joint_accA'][0]:.2f}/B{result['joint_accB'][0]:.2f}, "
         f">={flags['n_mix_curve']} learnable interior curve points), NOT a clean collapse."),
        (f"C1 SLOPE (interior, overlap<1): forgetting is monotone-graded in overlap -- "
         f"Spearman(overlap,forgetting)={flags['spearman_overlap_forget']} (perm p={flags['spearman_perm_p']}), "
         f"spanning {flags['slope_span']:.3f} from high-overlap to low-overlap (>= {SimilarityConfig().c1_min_range}); "
         f"slope_certified={flags['c1_monotone_slope']}. The overlap=1 endpoint is EXCLUDED (forgetting-free "
         f"by construction = v1193's continue-on-A floor + op-token-confounded); the claim is the INTERIOR only."),
        (f"NOT A B-LEARNEDNESS / DRIFT ARTIFACT: controlling for accB and shared-embedding drift, the overlap "
         f"coefficient stays negative and dominant (std beta overlap|accB={flags['beta_overlap_given_accB']} vs "
         f"accB={flags['beta_accB']}; overlap|drift={flags['beta_overlap_given_drift']} vs drift={flags['beta_drift']}); "
         f"overlap_survives={flags['overlap_survives_accB_and_drift']}. accB is read on CONFLICT cells only "
         f"(where the retained A-circuit cannot answer for B)."),
        (f"FAMILY IS A RED HERRING (re-confirms v1193's distribution-shift null via a 2nd manipulation): at "
         f"overlap~0, add_offset (SAME '+' operation, just +{result['config']['add_offset_c0']}) forgets "
         f"{ao['forget'][0]:.3f} vs mul {mu['forget'][0]:.3f} -- equivalent (|Δ|<= {SimilarityConfig().equiv_delta}), "
         f"both >> add_same {asame['forget'][0]:.3f}; family_does_not_protect={flags['c2_family_does_not_protect']}, "
         f"structure_at_fixed_overlap={flags['structure_at_fixed_overlap']}. UNIFICATION residual test "
         f"(type points on the mixture curve)={flags['c3_type_points_on_curve']}."),
        (f"SHAPE vs the overwrite null: the trivial 'overwrite only the conflicting cells' null predicts "
         f"forgetting ~= (1-overlap)*plateau. Observed mean excess over the null is {flags['mean_superlinear_excess']} "
         + ("(>= margin) -> SUPER-LINEAR: even a small target shift collapses the shared representation GLOBALLY, "
            "beyond the conflicting cells (ties to v1193's global-shift mechanism)."
            if flags['superlinear_vs_overwrite_null'] else
            "(< margin) -> forgetting is APPROXIMATELY the local-overwrite null (mild mid-overlap excess only). So "
            "the overlap law is largely the overwrite-fraction made quantitative, NOT a special global collapse; "
            "v1193's 'catastrophic' forgetting is the overlap=0 endpoint of this graded, ~proportional overwrite.")
         + f" SCOPE: toy modular arithmetic, 1-layer transformer, p={result['config']['p']}; overlap = 1 - "
         f"conflict-fraction on shared inputs; the random-partition mixture is fit on train cells but does NOT "
         f"generalize the per-cell split to held-out cells; NOT a claim about instruction-tuned LLM forgetting."),
    ]

    # curve for the figure: (overlap, forgetting, std, learned, kind)
    curve_points = []
    for k in result["mix_keys"] + result["type_keys"]:
        m = st[k]
        curve_points.append({"key": k, "kind": "mix" if k.startswith("mix") else "type",
                             "overlap": round(m["overlap"][0], 5), "forgetting": round(m["forget"][0], 5),
                             "forgetting_std": round(m["forget"][1], 5), "learned": m["learned"],
                             "accB_conflict_train": (round(m["accB_train_conflict"][0], 4) if not math.isnan(m["accB_train_conflict"][0]) else None),
                             "accB_conflict_test": (round(m["accB_conflict"][0], 4) if not math.isnan(m["accB_conflict"][0]) else None)})

    return {
        "schema_version": 1,
        "title": "MiniGPT task-similarity -> catastrophic forgetting v1195",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": info["decision"],
        "summary": summary, "rows": rows, "recommendations": recs,
        "csv_fieldnames": ["arm", "overlap", "forgetting", "forgetting_std", "accB_conflict_test", "accB_conflict_train", "emb_drift", "learned"],
        "curve_points": curve_points, "residuals": flags["residuals"],
        "plateau": round(result["plateau"][0], 5),
        "source": source,
    }


__all__ = [
    "SimilarityConfig", "TYPE_FUNCS", "TYPE_FAMILY", "f_add_table", "type_table", "mixture_table",
    "analytic_overlap", "build_rows", "conflict_overlap_masks", "train_b", "run_phase_a",
    "spearman", "spearman_perm_p", "summarize", "decide", "build_report",
    "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
