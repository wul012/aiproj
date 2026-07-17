# v1286 capability brief — lr compression: is F invariant when the plateau shrinks 8×?

Lane: ML capability. Executor: **Claude directly** (v1277–v1285 mode). All lane
rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

v1285 established that the canonical d=128 plateau sculpts: F ≈ 0.56–0.72 of
the final circuit-power increment is in place before val leaves its resting
band. v1281 showed the SAME cells grok ~8× faster at higher lr (t_gen 11,400 →
~1,400 at 4e-3). The unified hypothesis this version tests: **construction
rate is set by the effective lr, and generalization fires when construction
completes** — in which case F should be preserved under compression. If
instead the compressed cells build late (F ≈ 0.2, like the v1284 boundary),
compression changes the construction–generalization relationship, not just its
speed.

## P1 calibration (CPU, free, before this preregistration; disclosed)

From the v1281 cache (read-only reference): the eight α=1 d=128 cells at
lr ∈ {2e-3, 4e-3, 8e-3} have t_mem 100–300, t_gen 1,000–2,800, and their
pre-grok val RESTS NEAR ZERO (min 0.000–0.002; unlike the 1e-3 plateau's
0.11–0.21 band) with a steep takeoff sweeping ~0.1→0.9 in the last few hundred
steps. Bar adaptation (the same disclosed semantic rule as v1285: "just above
the resting band"): t_pre bars {0.10, 0.15, 0.20} (primary 0.15). The F
formula, thresholds (0.2/0.5), snapshot machinery, and prefix gate are
v1284/v1285's unchanged.

## 实验设计（固定；预算：≤ 112 runs, ≤ 130k total training steps）

All cells d=128, α=1; lr varies per cell (via the config, no training-code
change). max_steps=60000 with early-stop (~1.2k–3k actual).

- **Cells (8)**: lr=2e-3 × seeds {1337, 1338}; lr=4e-3 × {1337, 1338, 1339};
  lr=8e-3 × {1337, 1338, 1339} — exactly the v1281 α=1 cells, re-run with
  ladders. G0 requires each full run to reproduce its v1281 reference EXACTLY
  (t_mem, t_gen; |heldout| tol 1e-6) and classify `delayed` (v1283 pair).
- **Ladder**: k ∈ {100, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500, 1800,
  2200, 2600} (13 points, dense near the compressed takeoff), k < steps_run
  per cell. Per-cell cost ≈ full (≤3k) + ladder (≤13.2k); 8 cells ≈ 80–100k
  steps.
- **P2 probe**: the full ladder for (4e-3, 1337); stop conditions: prefix gate
  fails or the reference is not reproduced.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

F per cell as in v1284/v1285 (C = final-top-5-set share; C₀ at init; t_pre =
last snapshot with val ≤ bar, primary 0.15; clipped [0,1]).

- **G0 integrity**: every cell passes the prefix gate, reproduces its v1281
  reference exactly, classifies `delayed`, heldout ≥ 0.9. Fail → `review`
  (prefix_nondeterministic / reference_mismatch / phase_mismatch /
  substrate_unsound).
- **G1 completeness**: 8 cells, every ladder k < steps_run present.
- **Bins** (frozen from v1284): sculpt ≥ 0.5, late ≤ 0.2, else partial.
  Per-lr bin = the bin of the median F over that lr's seeds; within-lr
  dispersion guard: one seed ≤ 0.2 AND another ≥ 0.5 → `review` (mixed_seeds).
- **Ladder**:
  - all three lrs bin sculpt → `construction_completion_invariant` (F survives
    8× compression; the unified hypothesis stands).
  - all three bin late → `compression_switches_to_late_construction`
    (compressed cells behave like the v1284 boundary).
  - all three bin partial → `partial_under_compression`.
  - lrs in different bins → `review` (mixed_lrs).
- **G2 robustness**: verdict identical at bars {0.10, 0.15, 0.20}; any flip →
  `review` (bar_instability).
- Descriptive (never verdict-bearing): F versus lr including v1285's 1e-3
  values (0.720/0.556/0.600); C(t) trajectories on relative time t/t_gen
  overlaid across lrs; final shares versus the v1281/v1188 endpoints.

## 测试与证据要求

`src/minigpt/grok_lr_compression_v1286.py` — thin like v1285: v1284's
`run_cell`/`train_snapshot`/`structure_fraction` imported unchanged (lr varied
via `dataclasses.replace`); new code is the config, the v1281
reference-equality G0, and the per-lr-bin ladder.
`tests/test_grok_lr_compression_v1286.py` (config validation, all G0 paths,
all four ladder branches + both dispersion guards + bar instability,
orchestration with injected snapshots + P2 preload, byte-stable contract,
figure smoke); thin scripts. ONE figure: C versus relative time t/t_gen for
all 8 cells colored by lr, with the v1285 1e-3 trajectories in gray — the
compression-invariance picture. Full lane ritual; walkthrough 1243 BEFORE the
final suite.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, d=128, the 8
  preregistered cells. No new lrs/widths; no threshold changes; v1281/v1285
  caches read-only.

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc = fail. Prefix or reference failures
  silently tolerated = fail. Budget beyond 112 runs / 130k steps or silent
  descope = fail.
