# v1282 capability brief — does the width clock collapse to lr? (closing the v1277 question)

Lane: ML capability. Executor: **Claude directly** (v1277–v1281 mode). All lane
rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

The arc's original observation (v1277): narrow models grok ~5× faster than d=128.
v1279 re-measured it in one harness and found the width→t_gen curve non-monotone,
with d=64 a catastrophic slow zone. v1281 then showed the d=128 baseline was
**lr-starved**: at lr=4e-3 its t_gen collapses 11,400 → ~1,400, saturating near
~1k steps. The synthesis hypothesis — "the width and norm effects were largely
effective-lr effects" — makes a sharp width prediction this version tests: **at
adequate lr, all widths should converge to the same ~1k floor**, the narrow
speedup should vanish, and the d=64 hole should close. Each surviving effect
would instead be genuinely width-specific.

## P1 calibration (CPU, free, before this preregistration; disclosed)

Cache bookkeeping only (lr does not change inits). Anchors re-derived exactly:
v1281 d=128 @ 4e-3: 3/3 grokked, t_gen {1400, 1800, 1000}, median **1,400**.
v1279 grid @ 1e-3 (bar 0.90): w16 median 2,800 (0 censored), w32 median 2,700
(0), w64 = {None, 35000, None} (2 censored), w128 median 11,400 (0).

## 实验设计（固定；GPU 预算上限 12 runs；all cells α=1, lr=4e-3, max_steps=60000）

Frozen otherwise (p=97, train_frac=0.2, wd=1.0, 1 layer, n_head=4, full-batch
AdamW, standard init). The d=128 @ 4e-3 cells come from the v1281 cache
(read-only reference; never re-run).

- **Width arm (verdict)**: widths {16, 32, 64} × seeds {1337, 1338, 1339} = 9
  runs. d=64 is the marquee: does the hole close at high lr?
- **Conditional hole probe (descriptive, deterministic rule)**: iff ≥2 of the 3
  d=64 @ 4e-3 cells fail to grok, run d=64 @ 8e-3 × seeds {1337, 1338} = 2 extra
  runs (does a higher dose open the hole?). Never verdict-bearing.
- **P2 probe**: d=64 @ 4e-3 seed 1337 run alone first (the hole cell); it fills
  its Phase-A slot via the v1280 preloaded mechanism. Stop condition: only if it
  comes out `broken` (memorization lost), re-panel before the grid.
- Per-cell cache: both curves, N0, meta, heldout. Total ≤ 9 + 2 = 11 ≤ 12.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

Cell classes as in v1280 (grokked / stuck_memorized / broken). Convergence ratio
per width: ρ(w) = median t_gen(w @ 4e-3) / median t_gen(128 @ 4e-3, from the
v1281 reference), censored = +∞, bar-recomputed. Parity band [0.5, 2] (v1281's).
States: ρ ∈ band → converged; ρ < 0.5 → still_faster; ρ > 2 → still_slower.

- **G0 reference integrity**: v1281 cache d=128 @ 4e-3 is 3/3 grokked with
  median exactly 1,400; v1279 grid medians are exactly {16: 2,800, 32: 2,700,
  128: 11,400} with w64 having ≥2 censored cells. Fail → `review`
  (reference_cache_invalid).
- **G1 completeness**: 9 width cells cached, plus hole-probe cells exactly iff
  the deterministic rule fired.
- **Ladder** (verdict widths {16, 32, 64}):
  - any broken cell among them → `review` (broken_cells; instability ≠ slowness).
  - all three converged → `width_clock_collapses_to_lr` (the narrow speedup and
    the d=64 hole were lr-regime artifacts; closes the v1277 question).
  - (w16 or w32 still_faster) AND w64 not still_slower →
    `narrow_speedup_survives_lr` (a genuine width effect beyond lr).
  - w64 still_slower AND w16 converged AND w32 converged →
    `mid_width_hole_survives_lr` (the hole is width-specific, not lr).
  - anything else → `review` (mixed_widths).
- **G2 robustness**: verdict identical at t_gen bars {0.85, 0.90, 0.95}.

## 测试与证据要求

`src/minigpt/grok_width_lr_v1282.py` (reuses v1280's `classify`/`cell_tgen`/
`train_cell` — width varies via `dataclasses.replace` on the config, no training
code duplication) + `tests/test_grok_width_lr_v1282.py` (config validation, G0
fail paths for both reference caches, every ladder branch incl. broken and mixed,
conditional hole-probe orchestration firing iff ≥2 censored, preloaded probe
slot, byte-stable contract, figure smoke); thin scripts. ONE figure: t_gen vs
width, lr=1e-3 (v1279, gray) versus lr=4e-3 (new + v1281 ref) — the collapse
picture. Full lane ritual as always; walkthrough 1239 BEFORE the final suite.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, frozen recipe except
  lr, 60k budget. No new α arms; no lr beyond the preregistered {4e-3, 8e-3};
  no re-running of reference cells; v1279/v1280/v1281 caches read-only.

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc without the disclosed protocol = fail.
- Censored cells silently dropped = fail. Budget beyond 12 runs or silent
  descope = fail. A `width_clock_collapses_to_lr` verdict without stamping the
  closure note into the v1277 brief (whose descriptive finding started this
  question) = fail — the linked-notice chain continues.
