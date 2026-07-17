# v1285 capability brief — the deep plateau: does canonical grokking sculpt, or wait?

Lane: ML capability. Executor: **Claude directly** (v1277–v1284 mode). All lane
rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

v1284 found that at boundary widths (20–28) both dynamical phases build the
Fourier circuit on the same relative schedule (F ≈ 0.25), so the plateau does
not own construction — but its cells all sit near the v1283 phase gate, where
plateaus are short and leaky. The one place the canonical slow-sculpting story
could still hold is the CLASSIC deep plateau: d=128 at the canonical recipe,
t_mem = 100, t_gen 10,500–12,700 — a ~10k-step gap. This version runs the same
measurement there. If F is again ≈ 0.25 or lower, the v1284 revision extends to
canonical grokking; if F ≥ 0.5, the deep plateau genuinely sculpts and v1284's
finding is a boundary effect.

## P1 calibration (CPU, free, before this preregistration; disclosed)

From the v1279 cache (read-only reference): the three d=128 grid cells have
t_mem = 100 (memorization by the FIRST eval), t_gen = 11,400 / 12,700 / 10,500,
heldout 0.966 / 0.952 / 0.971, steps_run 11,600 / 12,900 / 11,600. Crucially,
the canonical plateau does NOT rest at chance: val sits in a ~0.11–0.21 band
(0.111 at step 100), dips to 0.14 near 6k, then climbs gradually (0.38@8k,
0.52@10k) before the jump. **Bar adaptation (disclosed)**: v1284's t_pre bars
{0.05, 0.1, 0.2} sit BELOW this plateau's resting band and would force F = 0 by
artifact; the semantic constant is "just above the resting band", so this
version's bars are {0.25, 0.30, 0.35} (primary 0.30). The F formula, thresholds
(0.2 / 0.5), ladder machinery, and prefix gate are v1284's unchanged.

## 实验设计（固定；预算：≤ 50 runs, ≤ 240k total training steps）

- **Cells (3)**: d=128, α=1, lr=1e-3, seeds {1337, 1338, 1339} — the exact
  v1279 grid cells, re-run with full ladders. max_steps=60000 (early-stop ends
  them at ~11.6k–12.9k; constant-lr max_steps-invariance was verified across
  v1279/v1283/v1284 reproductions).
- **Ladder**: k ∈ {100, 200, 400, 700, 1000, 1400, 1900, 2600, 3400, 4400,
  5600, 7000, 8600, 10400, 12400}, k < steps_run per cell. Per-cell cost ≈
  full (~12k) + truncations (~46k–60k) ≈ 60–73k steps; 3 cells ≈ 200k.
- **P2 probe**: the full ladder for seed 1337; stop conditions: prefix gate
  fails OR the full run does not reproduce the v1279 reference cell exactly.
- Per-snapshot cache as v1284: (k, train, val, 48-bin spectrum, C(k) = final
  top-5-set share); C₀ at the seeded init.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

F = (C(t_pre) − C₀)/(C_final − C₀) clipped to [0, 1], t_pre = LAST snapshot
with val ≤ bar (primary 0.30). Thresholds f_low = 0.2, f_high = 0.5 (v1284's).

- **G0 integrity**: every cell passes the prefix gate; its full run reproduces
  the v1279 reference EXACTLY (t_mem, t_gen equal; |heldout − ref| < 1e-6); it
  classifies `delayed` under v1283's phase pair (0.5, 0.7); heldout ≥ 0.9.
  Fail → `review` (prefix_nondeterministic / reference_mismatch /
  phase_mismatch / substrate_unsound).
- **G1 completeness**: 3 cells, every ladder k < steps_run present.
- **Ladder** (median F over the 3 cells):
  - F_med ≥ 0.5 → `deep_plateau_sculpts` (the canonical story survives at
    d=128; v1284's revision is a boundary effect).
  - F_med ≤ 0.2 → `construction_is_late_everywhere` (the revision extends to
    canonical grokking).
  - 0.2 < F_med < 0.5 → `partial_early_construction` (the deep plateau builds
    a minority share before takeoff — continuous with v1284's ≈ 0.25).
  - dispersion guard: one cell ≤ 0.2 AND another ≥ 0.5 → `review`
    (mixed_seeds).
- **G2 robustness**: verdict identical at bars {0.25, 0.30, 0.35}; any flip →
  `review` (bar_instability).
- Descriptive (never verdict-bearing): C at fixed fractions of t_gen (25 / 50 /
  75%); C(t_mem); the full C(t) trajectories against the v1284 boundary cells.

## 测试与证据要求

`src/minigpt/grok_deep_plateau_v1285.py` — thin: `run_cell` / `train_snapshot`
/ `structure_fraction` are imported from the v1284 module unchanged; new code
is the config, the reference-equality G0, and the single-population ladder.
`tests/test_grok_deep_plateau_v1285.py` (config validation, all G0 paths incl.
reference mismatch, all four ladder branches + dispersion guard + bar
instability, orchestration with injected snapshots + P2 preload, byte-stable
contract, figure smoke); thin scripts. ONE figure: the three C(t) trajectories
with val curves faint and t_mem/t_gen marked — the deep-plateau timeline. Full
lane ritual; walkthrough 1242 BEFORE the final suite.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, canonical recipe,
  d=128 × 3 seeds. No new widths/lrs; no attention-level analysis; the v1279
  cache is read-only; no F-threshold changes (0.2/0.5 are v1284's, frozen).

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc = fail. Prefix or reference failures
  silently tolerated = fail. Budget beyond 50 runs / 240k steps or silent
  descope = fail.
