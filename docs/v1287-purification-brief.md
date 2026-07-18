# v1287 preregistration — post-grok purification: does sculpting continue after generalization, and is the equilibrium lr-independent?

**Status: preregistered.** This brief is committed before any GPU run. Phase-A
runs happen only after this commit; any amendment before Phase A is disclosed
in the Amendments section.

## Motivation

v1286 falsified the construction-completion invariant and discovered — from
endpoint differences alone — that high-lr cells keep purifying *after* grok
(final purity monotone in lr: 0.31 @ 1e-3 → 0.55–0.59 @ 2e-3 → 0.62–0.72 @
4e-3 → 0.71–0.81 @ 8e-3). But the P1 audit of the committed caches shows every
cached run has almost **zero post-grok training time**:

| cache | cell | t_gen | steps_run | post-grok steps |
|---|---|---|---|---|
| v1285 | 1e-3 / 1337 | 11400 | 11600 | 200 (0.018×) |
| v1285 | 1e-3 / 1338 | 12700 | 12900 | 200 (0.016×) |
| v1285 | 1e-3 / 1339 | 10500 | 11600 | 1100 (0.105×) |
| v1286 | 2e-3 / 1337, 1338 | 1900, 2800 | +100 | ≤ 0.053× |
| v1286 | 4e-3 / all | 1000–1800 | +0–100 | ≤ 0.100× |
| v1286 | 8e-3 / all | 1000–1500 | +0 | 0.000× |

Five compressed cells early-stopped **exactly at t_gen**. So every purity
number the arc owns is "purity at grok"; nobody has ever watched what the
circuit does afterwards. The v1286 "purification" segment is an inference from
endpoints, not an observed trajectory — and the natural next question is the
banked v1286 candidate: observe it directly.

## Question and the mechanistic fork

Extend all 11 cells past grok (horizon 3× t_gen, early stop disabled) and
watch the purity trajectory.

- **Universal prediction** (AdamW fixed-point argument): at stationarity the
  normalized task gradient balances the decoupled weight-decay force,
  `grad_hat = -wd * w`, and lr cancels — the *equilibrium* is lr-independent,
  only the approach rate scales with lr. Then the canonical 1e-3 cells, given
  post-grok time, climb toward the same purity the compressed cells reach, and
  the v1286 purity-vs-lr gradient was an artifact of *where early stop cut the
  trajectory*. This would also re-scope v1285: F ≈ 0.6 was measured against an
  early-stopped denominator; against the true equilibrium the deep plateau
  builds far less of the final structure, and all three regimes may share one
  picture ("construction never completes at grok").
- **Lr-gated prediction**: the canonical cells stall near 0.31 while the
  compressed cells sit/climb far above — the purity ceiling itself depends on
  lr, contradicting the fixed-point argument (something else, e.g. curvature
  of the reached basin, sets the equilibrium).

Sculpting-dose note (fairness): with a 3× t_gen horizon the canonical cells
receive the **largest** wd·lr·steps dose of any group (≈ 22.8 lr-units of
post-grok sculpting vs 7.6–16 for the compressed groups, because t_gen grows
faster than 1/lr). A flat canonical curve therefore cannot be blamed on an
undersized horizon in dose terms.

## Design

- **Cells (11, preregistered)** — the exact v1285 + v1286 cells, same seeds,
  same recipe (p=97, train_frac=0.2, wd=1.0, d=128, 4 heads); t_gen_ref frozen
  from the committed caches:
  1e-3/1337 (11400), 1e-3/1338 (12700), 1e-3/1339 (10500),
  2e-3/1337 (1900), 2e-3/1338 (2800),
  4e-3/1337 (1400), 4e-3/1338 (1800), 4e-3/1339 (1000),
  8e-3/1337 (1000), 8e-3/1338 (1400), 8e-3/1339 (1500).
- **No early stop, zero training-code modification**: `train_to_grok` stops
  early via the `grok_stop_val` config field (0.95 default); v1287 builds its
  GrokConfig with `grok_stop_val = 2.0` (unreachable), so runs go to the full
  horizon. The training loop itself is untouched.
- **Snapshots** by the v1284 truncated-rerun method at relative multipliers
  m ∈ {1.4, 1.8, 2.4} of t_gen_ref, plus the full run at m = 3.0 (the
  horizon). Absolute steps: `k(m) = int((m * t_gen_ref + 50) // 100) * 100`
  (eval-grid aligned). Snapshots store the full 49-bin embedding power
  spectrum; all shares are derived in Phase B (CPU).
- **Frozen reference sets and anchors**: each cell's purity is measured on the
  **committed cache's top-5 frequency set** for that cell (v1285/v1286
  `top5`), with the cached `final_share` as the purity-at-grok anchor and the
  cached `c0_share` as the init baseline. These are preregistered constants
  living in the repo — not derived from the new runs. The new final model's
  own top-5 share and a set-match flag are the rotation diagnostics.

## Metrics

Per cell (ref = its committed cache cell):
- `climb` = C_ref(H) − anchor, where C_ref = share of cached top-5 set,
  anchor = cached `final_share`.
- `own_final` = share of the extended model's own top-5 set (physical purity,
  set-free); group convergence is compared on this.
- `saturated` = |C_ref(H) − C_ref(k_2.4)| < 0.02.
- `set_match` = extended model's top-5 set equals the cached set.
- **F_ext (secondary, NOT verdict-driving)** = (C_ref(t_pre) − c0) /
  (C_ref(H) − c0), with C_ref(t_pre) read from the *cached* pre-grok
  snapshots at each regime's committed t_pre bars (canonical
  {0.25, 0.30, 0.35}, committed 0.30; compressed {0.10, 0.15, 0.20},
  committed 0.15 — the v1285/v1286 preregistered grids). This is the
  unification readout: if extended denominators pull all groups' F_ext into
  one band, the three-regime split collapses.

## Verdict ladder (preregistered)

Primary quantities: `canon_climb` = median climb of the 1e-3 group;
`purity(lr)` = median own_final per lr group.

- `purification_universal` — canon_climb ≥ climb_bar (0.10) AND
  max(purity) − min(purity) ≤ conv_band (0.15): sculpting continues post-grok
  and the equilibrium is shared; construction does not complete at grok in any
  regime.
- `partial_purification` — canon_climb ≥ climb_bar but the purity band does
  not close within the horizon: purification is universal in direction,
  lr-limited in extent at matched relative time.
- `purification_lr_gated` — canon_climb < climb_bar AND
  max(purity) − purity(1e-3) > conv_band: the canonical ceiling is real.
- `review` — any guard: `purity_regression` (a group's median trajectory
  [anchor, C(1.4), C(1.8), C(2.4), C(3.0)] drops by > 0.05 between
  consecutive points), `mixed_seeds` (within-group climb range ≥ 0.30),
  `climb_bar_instability` (G2: verdict differs across climb_bar ∈
  {0.05, 0.10, 0.15}), `unexpected_geometry` (canonical flat AND band closed),
  or any G0/G1 failure.

G0 (integrity): per cell — truncation prefix-determinism vs the cell's own
full run (1e-9); `steps_run == horizon` (**early_stop_fired** guard: proves
the stop was actually disabled); t_mem and t_gen equal to the committed cache;
the *entire cached curve* is a bit-exact prefix of the new curve (every cached
(step, train, val) row matches, 1e-9); extended heldout ≥ 0.90
(substrate_unsound — this is also the post-grok stability guard: if continued
high-lr training destroys the solution, it fires); v1283 phase classification
still `delayed`.
G1 (completeness): all 11 cells, each with exactly the preregistered ladder.
G2 (robustness): climb-bar grid as above. The F_ext secondary readout carries
its own bar-stability flag but cannot flip the primary verdict (the v1286
bar_instability lesson: keep the primary decision bar-free).

## Budget

44 runs (11 cells × 4), 407,800 total steps — caps `max_runs = 48`,
`max_total_steps = 420,000`. Per-cell ladders (steps): 1e-3/1337
16000/20500/27400/34200; 1e-3/1338 17800/22900/30500/38100; 1e-3/1339
14700/18900/25200/31500; 2e-3/1337 2700/3400/4600/5700; 2e-3/1338
3900/5000/6700/8400; 4e-3/1337 2000/2500/3400/4200; 4e-3/1338
2500/3200/4300/5400; 4e-3/1339 1400/1800/2400/3000; 8e-3/1337
1400/1800/2400/3000; 8e-3/1338 2000/2500/3400/4200; 8e-3/1339
2100/2700/3600/4500.

## P2 probe (GPU, preregistered stop conditions)

One cell: (8e-3, 1337) — 8,600 steps, the cheapest full cell; fills its
Phase-A slot via the preload mechanism. Stop conditions (any → abort Phase A,
fix or re-panel): `steps_run != 3000` (early stop not disabled);
prefix-determinism failure; t_mem ≠ 300 or t_gen ≠ 1000 (reference mismatch);
heldout < 0.90. The probe also previews the science (anchor 0.7117 → C_ref at
3000) — disclosed, single cell.

## Phase plan

Phase A trains once and caches everything (spectra, curves); Phase B is
CPU-only re-derivation from `phase_a_cache.pt` + the two read-only committed
reference caches (f/1285, f/1286). One figure: C_ref vs relative time t/t_gen
for all 11 cells (pre-grok cached trajectory faint, post-grok new segment
bold), colored by lr, vertical line at t_gen.

## Amendments

(none)
