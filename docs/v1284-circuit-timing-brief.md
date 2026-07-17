# v1284 capability brief — circuit timing: does the plateau build the circuit, or wait?

Lane: ML capability. Executor: **Claude directly** (v1277–v1283 mode). All lane
rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

v1283 established two dynamical phases at the canonical recipe: coupled (w ≤ 20
and one w=24 seed — train/val rise together, delay exactly 0, never a memorized
plateau) and delayed/grokking (w ≥ 28 and the other w=24 seeds). The v1284 P1
probe settled the ENDPOINT question from the v1277 cache: coupled-phase models
end in the SAME solution type — Fourier frequency circuits — with even higher
concentration (w=16 top-5 power share 0.85–0.92 vs w=32's 0.68–0.72). What
remains is the TIMING question, which discriminates two mechanistic stories of
the grokking plateau:

- **Slow sculpting** (the canonical account): the plateau is gradual circuit
  construction — Fourier structure accumulates during memorization and
  generalization arrives when the circuit completes. Prediction: most of the
  final circuit's power is already present BEFORE validation accuracy moves.
- **Wait-then-build**: the plateau is idle; the circuit forms rapidly at the
  end, on the same schedule as in the coupled phase. Prediction: little circuit
  power before val moves, in BOTH phases.

## 方法：确定性截断重训 = 零改动的权重快照

Training is seed-deterministic (verified across sessions in v1279). Re-running
`train_to_grok` with a smaller `max_steps` therefore reproduces the SAME
trajectory prefix — the returned model IS the step-k snapshot, with zero
modification of the canonical training code. The method self-verifies: each
truncated run's last curve row must equal the full run's curve row at that step
(the **prefix-determinism gate**; failure invalidates the method → review).

## P1 calibration (CPU, free, before this preregistration; disclosed)

From the v1277 committed cache: endpoint top-5 power shares — w=16:
0.924/0.854/0.883, w=32: 0.719/0.678/0.711 (all grokked, heldout 0.95–0.97).
The coupled phase ends MORE concentrated; the
`coupled_phase_uses_different_solution` branch is expected NOT to fire but
remains preregistered. v1188's `number_embedding`/`embedding_spectrum` are the
measurement functions (read structure off weights, CPU).

## 实验设计（固定；预算：≤ 76 truncated runs, ≤ 260k total training steps）

All cells α=1, lr=1e-3 (canonical recipe), d per cell below; full runs capped
at 60k with early-stop.

- **Trajectory cells (6)**: (w=20, seeds 1337/1338) and (w=24, seed 1337)
  expected coupled; (w=24, seed 1338) and (w=28, seeds 1337/1338) expected
  delayed — the w=24 pair is the width-matched cross-phase comparison.
- **Per cell**: one full run (defines steps_run, the final spectrum and its
  top-5 frequency set), then truncated runs at every ladder step
  k ∈ {100, 200, 400, 700, 1000, 1400, 1900, 2600, 3400, 4400, 5600} with
  k < steps_run. Per snapshot cache: (k, train_acc, val_acc, 48-bin power
  spectrum, C(k) = power share of the FINAL model's top-5 set).
- **C₀** = the final-set share at the seeded init (CPU, deterministic).
- **P2 probe**: the full ladder for ONE cell (w=28, seed 1337 — the clearest
  delayed cell, delay 3,200), prefix gate checked. Stop condition: prefix
  determinism fails → stop and re-panel the method.
- Expected cost: ≈ 6 full runs (~2.4k–6.2k steps each) + ≈ 60 truncations
  (≈ 26k steps per cell ladder) ≈ 200k steps total.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

Definitions: phase of each cell re-derived from its full-run curve with
v1283's classifier (thresholds (0.5, 0.7), heldout bar 0.9); t_pre(bar) = the
LAST ladder snapshot with val ≤ bar (primary bar 0.1); the **pre-generalization
structure fraction** F = (C(t_pre) − C₀) / (C_final − C₀), clipped to [0, 1].

- **G0 integrity**: every cell's full run generalizes (heldout ≥ 0.9) AND its
  phase matches the preregistered expectation (v1283's observations) AND every
  truncated run passes the prefix-determinism check (last curve row equals the
  full run's row at that step). Fail → `review`
  (prefix_nondeterministic / phase_mismatch / substrate_unsound).
- **G1 completeness**: all 6 cells with their full ladders (every k <
  steps_run present), no silent exclusion.
- **Endpoint gate**: median final top-5 share of coupled cells < 0.5 →
  `coupled_phase_uses_different_solution` (overrides the timing ladder).
- **Timing ladder** (medians of F over the 3 coupled and 3 delayed cells):
  - F_delayed ≥ 0.5 AND F_coupled ≤ 0.2 → `plateau_is_circuit_construction`
    (slow sculpting: structure precedes generalization only where the plateau
    exists).
  - F_delayed ≤ 0.2 AND F_coupled ≤ 0.2 → `construction_is_rapid_in_both`
    (the plateau waits; the canonical slow-sculpting story is falsified here).
  - F_delayed ≥ 0.5 AND F_coupled ≥ 0.5 → `structure_precedes_in_both`.
  - anything else → `review` (mixed_fractions).
- **G2 robustness**: the verdict identical at t_pre bars {0.05, 0.1, 0.2};
  any flip → `review` (bar_instability).
- Descriptive (never verdict-bearing): full C(t) trajectories; the w=24
  cross-phase pair's curves overlaid; C₀ values; generic top-5 share.

## 测试与证据要求

`src/minigpt/grok_circuit_timing_v1284.py` (training via v1280's `train_cell`
with `dataclasses.replace`; spectra via v1188's `number_embedding` /
`embedding_spectrum`; phase via v1283's classifier — no duplication) +
`tests/test_grok_circuit_timing_v1284.py` (F computation incl. clipping and
missing-t_pre, prefix-gate pass/fail, config validation, every ladder branch
incl. the endpoint override, orchestration with an injected trainer + preloaded
P2 ladder, byte-stable contract, figure smoke); thin scripts. ONE figure:
C(t) trajectories for all 6 cells (coupled green / delayed blue), val curves
faint, the w=24 pair highlighted. Full lane ritual; walkthrough 1241 BEFORE
the final suite.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, canonical recipe,
  the 6 preregistered cells. No training-loop modification (truncation only);
  no logit/attention-level circuit analysis (embedding spectra only — the
  v1188 measurement); no new phases; v1277–v1283 caches read-only.

## Closeout (post-run; zero code changes after preregistration)

- Budget 49/76 runs, 60,600/260,000 steps. Phase B CPU-only; G0 (prefix
  determinism 43/43 snapshots, phases 6/6 matching v1283, heldout ≥0.963),
  G1, G2 all pass. The truncated-rerun snapshot method is validated.
- Preregistered verdict: **`review` (mixed_fractions)**, bar-stable. F medians:
  coupled 0.275, delayed 0.240 — both inside the (0.2, 0.5) middle band, so no
  preregistered separation pattern fires. The endpoint override did not fire
  (coupled final median 0.883 ≫ 0.5).
- The uniformity is the finding: **both phases build the circuit on the same
  relative schedule** — ~¼ of the final circuit power is in place when val
  crosses 0.1 in BOTH phases, and the C(t) curves share one shape, merely
  time-stretched (the width-matched w=24 pair: F 0.251 vs 0.240, the delayed
  seed's curve dilated ~3×). The plateau does not own construction; the
  canonical slow-sculpting story needs revision here — structure grows at the
  same slope before, during, and outside the plateau.
- Endpoint gradient (descriptive): final top-5 share falls smoothly with width
  — 0.88–0.91 (w=20) → 0.81–0.85 (24) → 0.76 (28), joining v1277's 0.85–0.92
  (16) and 0.68–0.72 (32). Near-boundary plateaus are LEAKY (w=28/1337 val
  creeps 0.08→0.53 during the plateau; t_mem 1600–2300 vs d=128's 100–300).
- Banked: the same trajectory measurement on d=128's classic DEEP plateau
  (val pinned at chance for thousands of steps; ladder cost ~40k+ steps/cell)
  — is F there also ≈0.25, or genuinely higher?

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc = fail. Prefix-gate failures silently
  tolerated = fail (they invalidate the snapshot method). Budget beyond 76
  truncated runs / 260k total steps or silent descope = fail.
