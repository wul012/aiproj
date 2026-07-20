"""v1192: CALIBRATION under aleatoric uncertainty + temperature scaling (NEW axis).

Every prior version measured *accuracy* or *distributional fidelity* (v1173's
``KL(P_true || P_model)``). None asked the orthogonal calibration question: when the
model says "class x with probability q", does x actually occur with frequency q?
This module measures that — top-1 reliability — on the SAME stochastic Dirichlet
substrate as v1173 (``build_stochastic_task``: K contexts, each a KNOWN categorical
``P_true``, entropy swept), so calibration is measured against an EXACT oracle.

Why exact metrics (not sampled ECE). The plug-in ECE estimator is positively biased
(Jensen): empirical accuracy is a binomial proportion, so even a perfectly-calibrated
model scores ECE>0 on finite sampled outcomes — comparing to an assumed-0 floor would
MANUFACTURE overconfidence (the v1183 single-threshold artifact class). Because we
CONSTRUCT ``P_true`` we compute ECE/NLL/Brier/KL ANALYTICALLY: the oracle's analytic
ECE is exactly 0 (per-context confidence == true accuracy), so "hard_ce ECE > 0" is a
real signal. :func:`sampled_ece` is kept only as a cross-check that *demonstrates* the
positive sampled floor the analytic path avoids.

The headline (pre-registered, confirmed by a CPU probe before any run): a 2L/32
transformer trained with hard CE at a FEW samples/ctx (n=10) is OVERCONFIDENT
(mean confidence >> mean accuracy; analytic ECE >> 0), and a single GLOBAL temperature
scalar T>1 (fit by NLL over all contexts — no fake held-out split on this per-symbol
substrate) SIGNIFICANTLY and SPECIFICALLY reduces ECE toward the floor. Specific:
the ECE-vs-T curve is U-shaped with its minimum at the fitted T, a mismatched T does
worse, and the same T does NOT help an already-calibrated model or the oracle. It is a
FINITE-SAMPLE MLE artifact: overconfidence and the fitted T shrink toward 1 as samples
grow (the v1173 "not magic" mirror).

Honest scope on novelty vs v1173: expected-NLL = entropy + KL, so NLL is KL relabeled;
on this substrate ECE and KL CO-MOVE under temperature (both reflect P_model-vs-P_true
closeness). We do NOT claim an ECE/KL dissociation. What calibration adds beyond KL is
(a) DIRECTION — KL is direction-blind, ECE diagnoses over- vs under-confidence — and
(b) the actionable, validated single-scalar fix, against an exact oracle floor.

``status=="pass"`` certifies a VALID calibration measurement (model learned the task,
real aleatoric uncertainty, identifiable temperature, non-degenerate binning), never a
flattering magnitude. All lower-is-better comparisons route through :func:`beats_lower`;
the before/after temperature test is PAIRED (shared model + contexts), not the unpaired
in-quadrature test which would use the wrong variance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from minigpt.calibration_v1192_report import build_calibration_report
from minigpt.experiment_utils import mean_std, significant

# Bin schemes for the binning-robustness gate (FIX 7 / g4). "mass:" = equal-mass (adaptive).
BIN_SCHEMES = ("width:10", "width:15", "width:20", "mass:15")
EPS = 1e-12


def beats_lower(a: float, sa: float, b: float, sb: float) -> bool:
    """True iff ``a`` is significantly LOWER (better, for a loss/error) than ``b`` --
    the lower-is-better mirror of :func:`significant` (reused from the v1173 idiom)."""
    return significant(b, sb, a, sa)


def paired_beats(deltas: list[float]) -> bool:
    """Paired one-sided test for a positive mean delta: ``mean(d) - std(d) > 0``.

    Use for before/after-temperature reductions where the two measurements share the
    SAME model and contexts (correlated). The unpaired :func:`beats_lower` would add
    variances in quadrature -- the wrong, over-conservative variance (FIX 2)."""
    m, s = mean_std(list(deltas))
    return (m - s) > 0 if m == m else False


# --------------------------------------------------------------------------- metrics
def pmodel(z: np.ndarray, T: float) -> np.ndarray:
    """Conditional over the M output classes: ``softmax(z / T)`` row-wise. ``z`` is the
    raw final-position logits restricted to the output alphabet, shape ``(K, M)``."""
    zz = np.asarray(z, float) / float(T)
    zz = zz - zz.max(axis=1, keepdims=True)
    e = np.exp(zz)
    return e / e.sum(axis=1, keepdims=True)


def expected_nll(p_true: np.ndarray, z: np.ndarray, T: float) -> float:
    """Analytic expected NLL (cross-entropy) ``-E_{y~P_true}[log P_model(y)]`` averaged
    over contexts. Equals ``entropy_floor + kl_to_true`` (so NLL is KL up to a constant)."""
    P = pmodel(z, T)
    return float(-(np.asarray(p_true, float) * np.log(P + EPS)).sum(1).mean())


def entropy_floor(p_true: np.ndarray) -> float:
    """Mean Shannon entropy of ``P_true`` -- the irreducible NLL floor (= NLL when P_model==P_true)."""
    P = np.asarray(p_true, float)
    return float(-(P * np.log(P + EPS)).sum(1).mean())


def kl_to_true(p_true: np.ndarray, z: np.ndarray, T: float) -> float:
    """Mean ``KL(P_true || P_model)`` = expected_nll - entropy_floor (lower=better, floor 0)."""
    return expected_nll(p_true, z, T) - entropy_floor(p_true)


def brier(p_true: np.ndarray, z: np.ndarray, T: float) -> float:
    """Analytic expected Brier score ``E_y sum_j (P_model_j - 1{y=j})^2`` averaged over
    contexts. Closed form: ``sum_j (P_model - P_true)^2 + sum_j P_true(1-P_true)`` (the
    second term is the irreducible uncertainty floor). Proper score, no binning knob."""
    P = pmodel(z, T)
    Pt = np.asarray(p_true, float)
    return float(((P - Pt) ** 2).sum(1).mean() + (Pt * (1 - Pt)).sum(1).mean())


def _bin_edges_or_assign(conf: np.ndarray, scheme: str):
    """Return per-point bin index array for the given scheme string."""
    kind, n = scheme.split(":")
    n = int(n)
    if kind == "width":
        edges = np.linspace(0.0, 1.0, n + 1)
        return np.clip(np.digitize(conf, edges) - 1, 0, n - 1), n
    # equal-mass: rank-based quantile bins
    order = np.argsort(conf, kind="stable")
    idx = np.empty(len(conf), dtype=int)
    for b, chunk in enumerate(np.array_split(order, n)):
        idx[chunk] = b
    return idx, n


def analytic_ece(p_true: np.ndarray, z: np.ndarray, T: float, scheme: str = "width:15"):
    """Analytic top-1 ECE against the known ``P_true`` (NO outcome sampling -> no Jensen
    bias). For each context: confidence = max-prob of P_model; the EXACT accuracy of that
    top-1 prediction is ``P_true[k, argmax]``. Bin by confidence; ECE = sum_bins weight *
    |mean conf - mean exact-acc|. Returns ``(ece, mean_conf, mean_acc, n_nonempty_bins)``.
    The oracle (P_model==P_true) gives ECE==0 exactly under any scheme."""
    P = pmodel(z, T)
    conf = P.max(1)
    pred = P.argmax(1)
    acc = np.asarray(p_true, float)[np.arange(len(P)), pred]
    idx, n = _bin_edges_or_assign(conf, scheme)
    ece = 0.0
    nonempty = 0
    K = len(P)
    for b in range(n):
        m = idx == b
        if m.any():
            nonempty += 1
            ece += (m.sum() / K) * abs(conf[m].mean() - acc[m].mean())
    return float(ece), float(conf.mean()), float(acc.mean()), int(nonempty)


def sampled_ece(p_true: np.ndarray, z: np.ndarray, T: float, *, n_eval: int, seed: int,
                scheme: str = "width:15") -> float:
    """Plug-in ECE with empirical accuracy from ``n_eval`` sampled outcomes/context --
    a CROSS-CHECK kept only to expose the positive Jensen-bias floor the analytic path
    avoids (the oracle scores >0 here even though its analytic ECE is exactly 0)."""
    P = pmodel(z, T)
    conf = P.max(1)
    pred = P.argmax(1)
    rng = np.random.default_rng(seed)
    Pt = np.asarray(p_true, float)
    emp = np.empty(len(P))
    for k in range(len(P)):
        draws = rng.choice(Pt.shape[1], size=n_eval, p=Pt[k])
        emp[k] = float((draws == pred[k]).mean())
    idx, n = _bin_edges_or_assign(conf, scheme)
    ece = 0.0
    K = len(P)
    for b in range(n):
        m = idx == b
        if m.any():
            ece += (m.sum() / K) * abs(conf[m].mean() - emp[m].mean())
    return float(ece)


def reliability_curve(p_true: np.ndarray, z: np.ndarray, T: float, bins: int = 10):
    """Per-bin (mean confidence, mean exact accuracy, weight) for the reliability figure."""
    P = pmodel(z, T)
    conf = P.max(1)
    acc = np.asarray(p_true, float)[np.arange(len(P)), P.argmax(1)]
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(conf, edges) - 1, 0, bins - 1)
    out = []
    K = len(P)
    for b in range(bins):
        m = idx == b
        if m.any():
            out.append((float(conf[m].mean()), float(acc[m].mean()), float(m.sum() / K)))
    return out


def fit_temperature(p_true: np.ndarray, z: np.ndarray, *, lo: float = 0.3, hi: float = 6.0,
                    n_grid: int = 300):
    """Fit a single GLOBAL temperature minimizing analytic expected NLL over ALL contexts
    (no held-out split: on this per-symbol substrate a context split is not i.i.d., FIX 4).
    Returns ``(T, nll_at_T, nll_at_1, interior)`` -- ``interior`` is False if the optimum
    sits at a grid edge (used by g2 to reject an unidentified / boundary fit)."""
    grid = np.geomspace(lo, hi, n_grid)
    vals = np.array([expected_nll(p_true, z, t) for t in grid])
    j = int(np.argmin(vals))
    interior = 0 < j < (n_grid - 1)
    return float(grid[j]), float(vals[j]), float(expected_nll(p_true, z, 1.0)), bool(interior)


def confidence_spread(z: np.ndarray, T: float = 1.0) -> float:
    """Std of the top-1 confidence across contexts -- if ~0, ECE binning is degenerate."""
    return float(pmodel(z, T).max(1).std())


# ------------------------------------------------------------------- per-arm aggregation
@dataclass
class CalibrationConfig:
    headline_n: int = 10
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    bins_primary: str = "width:15"
    n_eval_sampled: int = 2000          # large, fixed, identical for every sampled cross-check
    entropy_floor_min: float = 0.6      # g1 (reuse v1173)
    entropy_spread_min: float = 0.8     # g1 (reuse v1173)
    t_lo: float = 0.5                   # g2 bounds
    t_hi: float = 5.0
    cstd_min: float = 0.03              # g3 confidence-spread floor
    min_nonempty_bins: int = 3          # g3
    comovement_tol: float = 0.15        # |relΔECE - relΔKL| below this => co-move (not dissociated)


def aggregate_arm(p_true: np.ndarray, arm_logits: dict, cfg: CalibrationConfig):
    """Per-seed analytic metrics for one arm; returns a dict of (mean,std) tuples plus the
    paired before/after-T deltas. ``arm_logits`` maps seed -> z (K,M)."""
    ece1, eceT, nll1, nllT, kl1, klT, br1, brT, Ts, conf1, acc1, cstd = ([] for _ in range(12))
    dECE, dNLL = [], []
    interior_all = True
    for seed in cfg.seeds:
        z = np.asarray(arm_logits[seed], float)
        T, nT, n1, interior = fit_temperature(p_true, z)
        interior_all = interior_all and interior and (cfg.t_lo <= T <= cfg.t_hi)
        e1, c1, a1, _ = analytic_ece(p_true, z, 1.0, cfg.bins_primary)
        eT, _, _, _ = analytic_ece(p_true, z, T, cfg.bins_primary)
        ece1.append(e1)
        eceT.append(eT)
        conf1.append(c1)
        acc1.append(a1)
        nll1.append(n1)
        nllT.append(nT)
        kl1.append(kl_to_true(p_true, z, 1.0))
        klT.append(kl_to_true(p_true, z, T))
        br1.append(brier(p_true, z, 1.0))
        brT.append(brier(p_true, z, T))
        Ts.append(T)
        cstd.append(confidence_spread(z))
        dECE.append(e1 - eT)
        dNLL.append(n1 - nT)
    return {
        "ece": mean_std(ece1), "ece_T": mean_std(eceT), "nll": mean_std(nll1), "nll_T": mean_std(nllT),
        "kl": mean_std(kl1), "kl_T": mean_std(klT), "brier": mean_std(br1), "brier_T": mean_std(brT),
        "T": mean_std(Ts), "conf": mean_std(conf1), "acc": mean_std(acc1), "cstd": mean_std(cstd),
        "dECE": dECE, "dNLL": dNLL, "interior": interior_all,
    }


def binning_robust(p_true: np.ndarray, arm_logits: dict, cfg: CalibrationConfig) -> bool:
    """ECE-reduction sign (pre>post) stable across all BIN_SCHEMES, every seed (FIX 7/g4)."""
    for seed in cfg.seeds:
        z = np.asarray(arm_logits[seed], float)
        T, _, _, _ = fit_temperature(p_true, z)
        for scheme in BIN_SCHEMES:
            e1 = analytic_ece(p_true, z, 1.0, scheme)[0]
            eT = analytic_ece(p_true, z, T, scheme)[0]
            if not (e1 - eT > 0):
                return False
    return True


# ------------------------------------------------------------------ specificity controls
def oracle_logits(p_true: np.ndarray) -> np.ndarray:
    """``log P_true`` -- softmax of this is exactly ``P_true`` (the perfectly-calibrated oracle)."""
    return np.log(np.asarray(p_true, float) + EPS)


def specificity_controls(p_true, headline_logits, wrong_T, calibrated_logits, cfg):
    """The decisive falsifiers (FIX 5), all post-hoc on cached logits:

    * oracle_floor_zero : analytic ECE of the oracle is ~0 (the floor is genuinely 0).
    * u_shaped          : ECE(fitted T) < ECE(T=1) AND < ECE(over-flattened) -> interior min.
    * wrong_T_worse     : a MISMATCHED T (fit on a more-overconfident regime) gives higher ECE.
    * t_not_calibrated  : applying the headline T to an already-calibrated model does NOT help.
    Confirms the correction is temperature-SPECIFIC, not "any flattening reduces binned ECE"."""
    oe = analytic_ece(p_true, oracle_logits(p_true), 1.0, cfg.bins_primary)[0]
    u_ok = True
    e_fit, e_wrong = [], []
    for seed in cfg.seeds:
        z = np.asarray(headline_logits[seed], float)
        T, _, _, _ = fit_temperature(p_true, z)
        e1 = analytic_ece(p_true, z, 1.0, cfg.bins_primary)[0]
        eT = analytic_ece(p_true, z, T, cfg.bins_primary)[0]
        e_over = analytic_ece(p_true, z, min(cfg.t_hi, T * 2.5), cfg.bins_primary)[0]
        u_ok = u_ok and (eT < e1) and (eT < e_over)
        e_fit.append(eT)
        e_wrong.append(analytic_ece(p_true, z, wrong_T, cfg.bins_primary)[0])
    # apply each seed's headline T to the calibrated arm; must not reduce its ECE
    cal_pre, cal_post = [], []
    for seed in cfg.seeds:
        zc = np.asarray(calibrated_logits[seed], float)
        zc_pre = analytic_ece(p_true, zc, 1.0, cfg.bins_primary)[0]
        Th, _, _, _ = fit_temperature(p_true, np.asarray(headline_logits[seed], float))
        cal_pre.append(zc_pre)
        cal_post.append(analytic_ece(p_true, zc, Th, cfg.bins_primary)[0])
    fit_m = float(np.mean(e_fit))
    wrong_m = float(np.mean(e_wrong))
    cal_pre_m = float(np.mean(cal_pre))
    cal_post_m = float(np.mean(cal_post))
    return {
        "oracle_floor_zero": bool(oe < 0.02),
        "oracle_ece": round(oe, 6),
        "u_shaped": bool(u_ok),
        "wrong_T_worse": bool(wrong_m > fit_m + 1e-9),
        "wrong_T_value": round(float(wrong_T), 4),
        "ece_fitted_T": round(fit_m, 6),
        "ece_wrong_T": round(wrong_m, 6),
        "t_not_helping_calibrated": bool(cal_post_m >= cal_pre_m - 1e-9),
        "calibrated_ece_pre": round(cal_pre_m, 6),
        "calibrated_ece_post_headlineT": round(cal_post_m, 6),
    }


# ------------------------------------------------------------------------------- analysis
def run_analysis(cache: dict, cfg: CalibrationConfig | None = None) -> dict:
    """Pure post-hoc analysis over the Phase-A logit cache (no training). ``cache`` keys:
    ``p_true`` (K,M), ``H`` (K,), ``arms`` {name: {seed: z}}, ``sweep`` {n: {seed: z}},
    ``boundary`` {seed: z} + ``boundary_p_true``/``boundary_H``, ``teacher_kl``,
    ``uniform_kl_floor``, ``headline_n``."""
    cfg = cfg or CalibrationConfig()
    p_true = np.asarray(cache["p_true"], float)
    H = np.asarray(cache["H"], float)
    mean_H = float(H.mean())
    spread = float(H.max() - H.min())

    arms = {name: aggregate_arm(p_true, logits, cfg) for name, logits in cache["arms"].items()}

    # sweep summary (the "not magic" trend: overconfidence + T -> 1 as n grows)
    sweep = {}
    for n, logits in sorted(cache["sweep"].items()):
        a = aggregate_arm(p_true, logits, cfg)
        sweep[int(n)] = {"T": a["T"], "ece": a["ece"], "conf": a["conf"], "acc": a["acc"], "kl": a["kl"]}
    sweep_ns = sorted(sweep)

    # specificity: wrong T = the T fitted on the most-overconfident sweep regime (smallest n)
    wrong_T = fit_temperature(p_true, np.asarray(cache["sweep"][sweep_ns[0]][cfg.seeds[0]], float))[0]
    calibrated_logits = cache["sweep"][sweep_ns[-1]]      # largest n ~ calibrated reference
    controls = specificity_controls(p_true, cache["arms"]["hard_ce"], wrong_T, calibrated_logits, cfg)

    # boundary low-entropy task instance (expected null: not overconfident, T~=1)
    bp = np.asarray(cache["boundary_p_true"], float)
    bH = np.asarray(cache["boundary_H"], float)
    boundary = aggregate_arm(bp, cache["boundary"], cfg)
    boundary_overconfident = bool(
        significant(boundary["ece"][0], boundary["ece"][1], 0.0, 0.0)
        and boundary["conf"][0] > boundary["acc"][0]
        and significant(boundary["T"][0], boundary["T"][1], 1.0, 0.0)
    )
    # The meaningful "nothing to fix" null for THIS version (a temperature FIX) is that the
    # boundary's ECE is NOT correctable by temperature -- not merely "statistically flat". A
    # low-entropy few-sample model can be marginally overconfident yet have NO global over-
    # confidence a single scalar can touch (the residual is per-context shape).
    boundary_correctable = bool(paired_beats(boundary["dECE"]))
    boundary_gap = float(boundary["conf"][0] - boundary["acc"][0])

    # sampled-ECE cross-check: the oracle's POSITIVE plug-in floor (illustrates the bias)
    oracle_sampled = sampled_ece(p_true, oracle_logits(p_true), 1.0,
                                 n_eval=cfg.n_eval_sampled, seed=cfg.seeds[0], scheme=cfg.bins_primary)
    hard_sampled = sampled_ece(p_true, np.asarray(cache["arms"]["hard_ce"][cfg.seeds[0]], float), 1.0,
                               n_eval=cfg.n_eval_sampled, seed=cfg.seeds[0], scheme=cfg.bins_primary)

    # co-movement of ECE and KL under temperature (honest: NOT a dissociation here)
    h = arms["hard_ce"]
    rel_dECE = (h["ece"][0] - h["ece_T"][0]) / (h["ece"][0] + EPS)
    rel_dKL = (h["kl"][0] - h["kl_T"][0]) / (h["kl"][0] + EPS)
    comove = {"rel_dECE": round(rel_dECE, 4), "rel_dKL": round(rel_dKL, 4),
              "co_move": bool(abs(rel_dECE - rel_dKL) < cfg.comovement_tol)}

    # not-magic trend
    t_head = sweep[cfg.headline_n]["T"][0] if cfg.headline_n in sweep else h["T"][0]
    t_max = sweep[sweep_ns[-1]]["T"][0]
    t_min = sweep[sweep_ns[0]]["T"][0]
    not_magic = bool(t_max < t_head and abs(t_max - 1) < abs(t_min - 1))

    # figure data (computed here while logits are in hand; seed0 of the headline arm)
    z_h0 = np.asarray(cache["arms"]["hard_ce"][cfg.seeds[0]], float)
    T_h0 = fit_temperature(p_true, z_h0)[0]
    ece_vs_T = [[round(float(t), 4), round(analytic_ece(p_true, z_h0, float(t), cfg.bins_primary)[0], 6)]
                for t in np.geomspace(0.5, 5.0, 31)]
    reliability_pre = [[round(c, 5), round(a, 5), round(w, 5)] for c, a, w in reliability_curve(p_true, z_h0, 1.0)]
    reliability_post = [[round(c, 5), round(a, 5), round(w, 5)] for c, a, w in reliability_curve(p_true, z_h0, T_h0)]

    return {
        "headline_n": int(cache["headline_n"]),
        "uniform_kl_floor": round(float(cache["uniform_kl_floor"]), 6),
        "mean_H": round(mean_H, 6), "entropy_spread": round(spread, 6),
        "teacher_kl": round(float(cache.get("teacher_kl", float("nan"))), 6),
        "oracle_ece": controls["oracle_ece"],
        "oracle_sampled_ece": round(oracle_sampled, 6), "hard_ce_sampled_ece": round(hard_sampled, 6),
        "arms": arms, "boundary": boundary, "boundary_overconfident": boundary_overconfident,
        "boundary_correctable": boundary_correctable, "boundary_gap": round(boundary_gap, 4),
        "boundary_mean_H": round(float(bH.mean()), 6), "boundary_spread": round(float(bH.max() - bH.min()), 6),
        "sweep": sweep, "controls": controls, "comovement": comove,
        "binning_robust": binning_robust(p_true, cache["arms"]["hard_ce"], cfg),
        "not_magic_T_to_one": not_magic,
        "fig_ece_vs_T": ece_vs_T, "fig_T_fitted": round(float(T_h0), 4),
        "fig_reliability_pre": reliability_pre, "fig_reliability_post": reliability_post,
        "per_context_entropy": [round(float(x), 4) for x in H],
    }


REVIEW_VERDICTS = {"task_not_learned", "no_entropy_structure", "temperature_unidentified",
                   "ece_estimator_degenerate"}
PRIMARY_VERDICTS = {
    "overconfidence_specifically_corrected_by_temperature",
    "any_flattening_helps_not_temperature_specific",
    "ece_reduction_binning_fragile",
    "overconfidence_not_correctable_by_temperature",
    "already_calibrated_no_overconfidence",
}


def decide(result: dict, cfg: CalibrationConfig | None = None) -> dict:
    """Pure gates + honest verdict ladder. Gates certify a VALID calibration measurement;
    the ladder (with real data-reachable nulls) carries the finding. No single absolute
    cutoff decides the headline -- overconfidence needs ECE>floor AND direction AND T>1,
    correction is a PAIRED test, and specificity needs all three falsifiers (the v1183/v1191
    artifact guards)."""
    cfg = cfg or CalibrationConfig()
    h = result["arms"]["hard_ce"]
    ctl = result["controls"]
    ece_m, ece_s = h["ece"]
    T_m, T_s = h["T"]

    g0 = h["kl"][0] < result["uniform_kl_floor"]
    g1 = (result["mean_H"] > cfg.entropy_floor_min) and (result["entropy_spread"] >= cfg.entropy_spread_min)
    g2 = h["interior"]   # temperature IDENTIFIED (interior optimum within [t_lo, t_hi]); a calibrated
                         # model legitimately fits T~=1 (no NLL decrease) and must reach the null branch,
                         # so "NLL decreased" is a FINDING signal (below), not a validity gate.
    g3 = (h["cstd"][0] >= cfg.cstd_min) and ctl["oracle_floor_zero"]

    overconfident = (significant(ece_m, ece_s, 0.0, 0.0)
                     and (h["conf"][0] > h["acc"][0])
                     and significant(T_m, T_s, 1.0, 0.0))
    correction = paired_beats(h["dECE"]) and paired_beats(h["dNLL"])
    specific = ctl["u_shaped"] and ctl["wrong_T_worse"] and ctl["t_not_helping_calibrated"]

    flags = {
        "g0_task_learned": g0, "g1_entropy_structure": g1, "g2_temperature_identified": g2,
        "g3_ece_estimator_valid": g3, "direction_overconfident": bool(h["conf"][0] > h["acc"][0]),
        "T_significantly_gt_1": bool(significant(T_m, T_s, 1.0, 0.0)),
        "ece_above_oracle_floor": bool(significant(ece_m, ece_s, 0.0, 0.0)),
        "correction_paired_significant": bool(correction),
        "u_shaped": ctl["u_shaped"], "wrong_T_worse": ctl["wrong_T_worse"],
        "t_not_helping_calibrated": ctl["t_not_helping_calibrated"],
        "binning_robust": result["binning_robust"], "not_magic_T_to_one": result["not_magic_T_to_one"],
        "calibration_kl_co_move": result["comovement"]["co_move"],
        "boundary_not_correctable_null": bool(not result["boundary_correctable"]),
        "soft_distill_calibrated": bool(not significant(result["arms"]["soft_distill"]["T"][0],
                                                        result["arms"]["soft_distill"]["T"][1], 1.0, 0.0)),
    }

    if not g0:
        return _verdict("review", "task_not_learned", flags)
    if not g1:
        return _verdict("review", "no_entropy_structure", flags)
    if not g2:
        return _verdict("review", "temperature_unidentified", flags)
    if not g3:
        return _verdict("review", "ece_estimator_degenerate", flags)
    if not overconfident:
        return _verdict("pass", "already_calibrated_no_overconfidence", flags)
    if not correction:
        return _verdict("pass", "overconfidence_not_correctable_by_temperature", flags)
    if not result["binning_robust"]:
        return _verdict("pass", "ece_reduction_binning_fragile", flags)
    if not specific:
        return _verdict("pass", "any_flattening_helps_not_temperature_specific", flags)
    return _verdict("pass", "overconfidence_specifically_corrected_by_temperature", flags)


def _verdict(status: str, verdict: str, flags: dict) -> dict:
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}


# Report assembly lives in a focused pure module.
def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    """Assemble the stable v1192 report contract."""
    return build_calibration_report(
        result,
        info,
        source,
        generated_at=generated_at,
        seed_count=len(CalibrationConfig().seeds),
    )


__all__ = [
    "CalibrationConfig", "BIN_SCHEMES", "beats_lower", "paired_beats", "pmodel", "expected_nll",
    "entropy_floor", "kl_to_true", "brier", "analytic_ece", "sampled_ece", "reliability_curve",
    "fit_temperature", "confidence_spread", "oracle_logits", "aggregate_arm", "binning_robust",
    "specificity_controls", "run_analysis", "decide", "build_report",
    "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
