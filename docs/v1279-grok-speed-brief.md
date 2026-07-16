# v1279 capability brief — why do narrow models grok faster? The norm-clock test

> **Downgrade notice (v1280, 2026-07-13).** Two v1279 conclusions were revised by
> the preregistered follow-up ([v1280 brief](v1280-init-rescue-brief.md), verdict
> `norm_clock_revived_under_lr_scaling`): (1) the censored small-init cells DO
> memorize (t_mem≈300; the death is of the memorize→generalize transition — the
> "not even memorization" wording below was corrected in `784f91c2`); (2) the
> headline "shrinking init norm prevents grokking" is **lr-conditional**: at 2–4×
> the frozen lr, α=0.5 groks in 1,300–4,000 steps — faster than the α=1 baseline's
> 11,400. What v1279 measured is real at the frozen lr; it does not generalize
> across lr.

Lane: ML capability. Executor: **Claude directly** (continuing the v1277/v1278 mode).
All lane rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A
caches / Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

v1277's most striking descriptive finding: at the frozen grok recipe, narrow models
grok ~5× FASTER (t_gen ≈ 2,600–3,400 at widths 16–32 versus ~15,000 at the canonical
d=128 from v1183/v1185). Why? The sharpest candidate is the **weight-norm clock**
(the Omnigrok-style account): grokking waits for weight decay to shrink the
init-scale solution down to the small-norm generalizing regime, so time-to-grok is
governed by how much norm must be burned — and wider models start with more norm.
This is causally testable by INTERVENING on init scale at fixed width.

## P1 calibration probe (CPU, free, run BEFORE this preregistration; disclosed)

Standard init total parameter norm N0 scales cleanly with width and is essentially
seed-invariant: d=16 → 7.06, d=32 → 10.11, d=64 → 14.64, d=128 → 21.63
(≈ √params). The per-seed rescale that gives a d=128 model the total init norm of a
d=32 model is **α\* ≈ 0.467** (0.4673/0.4675/0.4676 across seeds 1337–1339).

## 实验设计（固定；GPU 预算上限 28 runs）

Frozen recipe throughout (p=97, train_frac=0.2, wd=1.0, 1 layer, n_head=4,
full-batch AdamW, max_steps=100000 — re-paneled from 40000 after the P2 probe, see
the disclosed section below — early-stop on stable grok). Init rescaling uses
the v1275-era `init_state` hook: build the seeded standard init, multiply every
tensor by α, train from that state (same seed ⇒ same data split).

- **Grid arm (phenomenon, α=1)**: widths {16, 32, 64, 128} × seeds {1337, 1338,
  1339} = 12 runs. This re-measures the width→t_gen curve in ONE harness — the v1277
  observation compared fresh runs against historical d=128 numbers, so
  `phenomenon_not_robust` is a live branch, not a formality.
- **α arm at d=128 (the causal test)**: α ∈ {0.5, 2.0} × 3 seeds = 6 runs (α=1 comes
  from the grid; α=2 cells may censor at the step budget — censoring counts as
  t_gen = +∞, which is evidence in the predicted direction, handled explicitly).
- **Matched-norm arm**: d=128 with per-seed α\* = N0(32,seed)/N0(128,seed) × 3 seeds
  = 3 runs — a wide model whose init norm equals a narrow model's.
- **Symmetry arm (descriptive only)**: d=32 with α=2.0 × 3 seeds = 3 runs — does
  inflating a narrow init slow it toward wide-model times?
- P2 probe (GPU, before the full grid): one d=64, α=1, seed 1337 run; if it fails to
  grok, stop and re-panel. Total ≤ 12+6+3+3+1(+1 validity check, see below) = 26 ≤ 28.
- Per-cell cache: N0, N_final, meta (t_mem/t_gen/steps/final accs), heldout acc, and
  the full (step, val_acc) curve so Phase B can recompute t_gen at any bar.

## P2 probe result & re-panel (disclosed; amended BEFORE any Phase-A grid run)

The P2 probe **triggered its own stop condition**: d=64, α=1, seed 1337 did NOT grok
within the original 40,000-step budget (heldout 0.219, t_gen censored, N0=15.23 —
`total_norm_of` includes buffers, hence slightly above P1's parameter-only 14.64).
A validity check through the identical `init_state` code path (d=32, seed 1337, α=1;
one extra GPU run, disclosed against the budget) reproduced the v1277 reference cell
EXACTLY (heldout 0.97024, t_gen 2600) — the harness is sound, so the d=64 stall is a
real observation: the width→t_gen curve may be slower at mid-width than at d=128,
i.e. possibly non-monotone. Re-panel decision, made before any grid data exists:

- **max_steps 40000 → 100000 for ALL cells** (one clock for the whole design, the
  v1183 precedent for a 100k budget). Early-stop keeps fast cells cheap.
- Nothing else changes: arms, seeds, α values, decide() ladder, G0–G2, and all
  thresholds are untouched. If d=64 still censors in ≥2/3 seeds at 100k, G0 routes
  the verdict to `review` as originally written — that is the honest outcome, and
  the mid-width slow zone itself becomes the reportable finding.
- Runs spent so far: 2 (probe + validity check); 24 remain planned, total 26 ≤ 28.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

Definitions: grokked = meta t_gen present AND heldout ≥ 0.90. t_gen(bar) = first
eval step with val ≥ bar, recomputed from the cached curve; censored cells count as
+∞ in comparisons and are excluded from medians only where stated.

- **G0 substrate**: every grid width groks in ≥2/3 seeds at α=1. Fail → `review`.
- **G1 completeness**: all 24 cells cached, no silent exclusion.
- **Phenomenon** (bar 0.90, grid medians over grokked cells):
  ratio = median t_gen(128) / median t_gen(16); adjacent medians non-increasing as
  width shrinks. ratio ≥ 2 AND non-increasing → confirmed; ratio ≥ 2 with an
  adjacent inversion → `review`; ratio < 2 → `phenomenon_not_robust`.
- **α sign test** (d=128, per seed, adjacent pairs (0.5,1.0) and (1.0,2.0) = 6
  comparisons, censored = +∞): predicted direction is t_gen increasing in α.
  ≥5/6 → alpha_effect true; ≤3/6 → false; 4/6 → `review`.
- **Mediation share**: gap = median t_gen(128, α=1) − median t_gen(32, α=1);
  reduced = median t_gen(128, α\*) − median t_gen(32, α=1);
  share = 1 − reduced/gap.
- **Ladder**: phenomenon fails → `phenomenon_not_robust`; alpha_effect false →
  `norm_clock_rejected`; share ≥ 0.5 → `narrow_speedup_is_norm_clock`;
  0.2 ≤ share < 0.5 → `norm_clock_partial`; share < 0.2 → `norm_clock_rejected`;
  anything mixed/gated → `review`. Every branch is publishable.
- **G2 robustness**: the ladder verdict must be identical when t_gen is recomputed at
  bars {0.85, 0.90, 0.95}; any flip → `review`.
- Symmetry-arm and N0/N_final trajectories are descriptive only, never verdict-bearing.

## 测试与证据要求

`src/minigpt/grok_speed_v1279.py` + `tests/test_grok_speed_v1279.py` (t_gen-from-curve
incl. censoring, sign-test counting, mediation-share math incl. censored α\*, every
decide() branch on synthetic caches, config validation, injected-trainer Phase-A
orchestration, committed-cache byte-stable contract, figure smoke); thin
`scripts/run_grok_speed_v1279.py` / `scripts/analyze_grok_speed_v1279.py`.
Lane ritual in full: 5-format artifacts; ONE figure (t_gen vs width with the α-arms
overlaid at d=128); `f/1279/图片` + `解释/说明.md`; ~3000-char Chinese walkthrough
BEFORE the final full-suite run; README version sections (NOT forgetting them —
the v1277 lesson) + Documentation Map row + f/README + 讲解 README indexes;
cleanup gate; preregister commit + close commit; push; CI green; tag.

## 明确不做

- No LLM claims; scope = "own grokked substrate, toy scale, frozen recipe/budget".
- No second mechanism arm (lr/wd sweeps, memorization-capacity manipulations are
  FUTURE versions); no v1185 artifact mutation; no training-loop modification —
  init rescaling goes through the existing `init_state` parameter only.

## Closeout (post-run; report rendering only, decide() untouched)

- Phase A: 24/24 cells cached in one run; total GPU budget spent 26/28 (P2 probe +
  validity check + 24 grid/arm cells). Phase B re-derived the verdict CPU-only.
- Preregistered verdict: **`review` (reason=`substrate_unsound`)**, identical at
  t_gen bars {0.85, 0.90, 0.95} (G2 pass). G0 failed exactly as written: d=64
  grokked 1/3 seeds (sole success t_gen=35,000; two seeds censored at 100k,
  heldout ≈0.23) — the P2 stall was a systematic mid-width slow zone, not seed luck.
  G1 complete; phenomenon check `review` (ratio 4.07 ≥ 2 with the d=64 adjacent
  inversion); sign test 3/6 ((1,2) pairs all predicted-direction, (0.5,1) pairs all
  counter-direction); mediation share = −∞ (matched-norm cells all censored).
- Headline observation (descriptive; the verdict stays `review`): the norm clock is
  INVERTED on this substrate. d=128 at α=0.5 and at the d=32-matched α\*≈0.493
  never groks (0/6, heldout 0.14–0.29), α=2 groks 3/3 (12.8k–23.2k); same-norm
  contrasts dissociate norm from speed in both directions (α\* d=128 at N0=10.88
  censors while d=32 at the same norm groks in 2,600; d=32 inflated to
  N0=21.77 ≈ d=128's natural 22.09 is fastest overall, 1,200–3,900).
- Post-run code delta: `plot_result` rendering only (censored-cell fan-out, minor
  x-tick suppression). decide(), thresholds, and all gates untouched since
  `37433657`. Artifacts: `f/1279/解释/grok_speed_v1279/` (five formats + Phase-A
  cache), `f/1279/图片/grok-speed-v1279.png`, walkthrough 1236.

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc without the disclosed cache-re-derived
  protocol = fail (13-times-caught bug class; explicit self-audit in the version doc).
- Censored cells silently dropped from the sign test = fail (they are +∞, not
  missing). Budget beyond 28 runs or silent descope = fail.
