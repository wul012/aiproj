# v1283 capability brief — the delayed phase is width-gated: where does grokking switch on?

Lane: ML capability. Executor: **Claude directly** (v1277–v1282 mode). All lane
rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

v1282 banked a new phenomenon: w=16 cells generalize without ever memorizing.
The v1283 P1 forensics (below) established two facts that reshape the question:
(1) at d=128 the delayed phase SURVIVES every stable lr — the delay compresses
~11,100 → ~700 steps but a full memorized-not-generalizing plateau (max
train−val gap 0.85–1.0) exists at lr up to 8e-3, so "grokking is an lr
artifact" is FALSE in its strong form; (2) w=16 is coupled at BOTH lr=1e-3 and
4e-3 (t_mem ≈ t_gen at 1e-3; max_gap 0.29–0.41 at 4e-3) — the coupling is
**width-gated, not lr-induced**. w=16 never grokked at any lr: no delayed
phase exists there at all, while w=32 has a genuine one (delay 1,400–2,600 at
1e-3, max_gap 0.79–0.83 at 4e-3). This version maps the gate: **where between
w=16 and w=32 does the grokking phase structure switch on — sharply or
gradually?**

## P1 calibration (CPU, free, before this preregistration; disclosed)

Full delay+coupling forensics over all 33 train-curve cells in the v1280/81/82
caches plus v1279's t_mem/t_gen fields. Key numbers: d=128 max_gap ∈
[0.85, 1.0] at every lr ∈ {2.5e-4 … 8e-3} incl. all stuck cells; delay at
d=128 α=1: ~11,100 (1e-3, fields) → 1,800/2,700 (2e-3) → 900–1,700 (4e-3) →
700–1,300 (8e-3); w=32 @ 4e-3 max_gap 0.79–0.83; w=16 @ 4e-3 max_gap
0.29/0.41/0.29 with max_train 0.97–0.99; w=16 @ 1e-3 t_mem/t_gen =
None/2800, 2600/2600, 5900/6600. **The max_gap distribution is bimodal with an
empty hole: nothing lies in [0.41, 0.79]** — thresholds are placed inside it.

## 实验设计（固定；GPU 预算上限 16 runs；all cells α=1, lr=1e-3, max_steps=60000）

The canonical recipe throughout — this version varies WIDTH only (all values
divisible by n_head=4; head_dim 5/6/7 is legal).

- **Boundary arm (verdict)**: widths {20, 24, 28} × seeds {1337, 1338, 1339}
  = 9 runs, full train+val curves cached.
- **Anchor arm**: widths {16, 32} × seeds {1337, 1338} = 4 runs — the endpoint
  cells re-run WITH train curves (v1279 cached only val curves; the field-based
  inference must be confirmed at curve level).
- **P2 probe**: w=24, seed 1337 (the middle cell), run alone first; fills its
  Phase-A slot. Stop condition: only if it fails to generalize (heldout < 0.9),
  re-panel. Total 13 ≤ 16.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

Per-cell phase class from the cached curve, at threshold pair (c, d):
generalized = heldout ≥ 0.90; failed = not generalized;
coupled = generalized AND max_gap ≤ c; delayed = generalized AND max_gap ≥ d;
intermediate = generalized AND c < max_gap < d, where max_gap =
max over eval steps of (train_acc − val_acc). Primary pair (c, d) = (0.5, 0.7),
placed inside the P1 hole [0.41, 0.79].

- **G0 anchors**: all four anchor cells generalized; both w=16 anchors coupled
  and both w=32 anchors delayed at the primary pair. Fail → `review`
  (anchor_mismatch — the v1279 field-based inference was wrong).
- **G1 completeness**: 13 cells cached, no silent exclusion.
- **Width class**: a width with ≥2 failed cells is `failed` → `review`
  (substrate_unsound). Otherwise the class is the unanimous class of its
  non-failed cells (≤1 failed tolerated); non-failed cells disagreeing → mixed.
- **Ladder** (classes of w = 20, 24, 28, ordered by width, with the anchors
  fixing coupled at 16 and delayed at 32):
  - all classes ∈ {coupled, delayed} and the sequence is monotone (all coupled
    widths below all delayed widths, no mixed) →
    `delayed_phase_onset_is_sharp`.
  - ≥1 intermediate class and the sequence is monotone
    (coupled ≤ intermediate ≤ delayed by width) →
    `delayed_phase_onset_is_graded`.
  - any mixed width or a non-monotone sequence → `review` (mixed_widths).
- **G2 robustness**: the verdict must be identical at threshold pairs
  {(0.4, 0.8), (0.5, 0.7)} — both inside the P1 hole; any flip → `review`
  (threshold_instability).
- Descriptive (never verdict-bearing): delay length t_gen − t_mem versus
  width; max_train versus width (does full memorization return gradually?);
  t_gen versus width across the boundary.

## 测试与证据要求

`src/minigpt/grok_delay_gate_v1283.py` (training reuses v1280's `train_cell`
via `dataclasses.replace`; the phase classifier is this version's new metric) +
`tests/test_grok_delay_gate_v1283.py` (classifier units incl. failed and the
threshold pairs, config validation, G0 anchor-mismatch, every ladder branch,
orchestration + preloaded probe slot, byte-stable contract, figure smoke);
thin scripts. ONE figure: max_gap versus width (16–32) with the threshold band
and per-cell classes; anchors hollow. Full lane ritual; walkthrough 1240
BEFORE the final suite.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, canonical recipe
  (lr=1e-3), 60k budget. No lr arms (P1 already settled the lr question from
  caches — that finding ships as disclosed calibration, not a verdict); no
  mechanistic probe of WHY the gate exists (banked: Fourier-circuit formation
  vs width at the boundary); v1279–v1282 caches read-only.

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc = fail (they were frozen from P1's
  bimodal hole BEFORE any new run). Censored/failed cells silently dropped
  = fail. Budget beyond 16 runs or silent descope = fail.
