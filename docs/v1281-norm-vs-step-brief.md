# v1281 capability brief — norm vs relative step: what makes rescued cells fast?

Lane: ML capability. Executor: **Claude directly** (v1277–v1280 mode). All lane
rules bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope,
elegance gates.

## 背景与问题

v1280 rescued small-init grokking with lr: α=0.5 at lr=4e-3 groks in 1,300–2,300
steps versus the α=1, lr=1e-3 baseline's 11,400 — verdict
`norm_clock_revived_under_lr_scaling`. But that verdict deliberately left the causal
attribution open (banked as this version): under AdamW the relative update is
lr/|w| ∝ lr/α, so the rescued cells differ from the baseline in BOTH init norm
(0.5×) and relative step (4–8×). The missing control is **α=1 at lr 2–8×**: if a
full-norm model at the SAME relative step groks just as fast, the speed is the
step's, not the norm's, and no norm-clock story survives; if α=1 at matched
relative step stays near 11,400 (or stalls), the small norm genuinely helps and
the lr-adjusted norm clock stands.

Matched-relative-step pairs (r = lr/(1e-3·α), baseline r=1):
- **r=4×**: (α=0.5, lr=2e-3) [v1280 cache: median t_gen 3,900] vs (α=1, lr=4e-3) NEW
- **r=8×**: (α=0.5, lr=4e-3) [v1280 cache: median 1,800] vs (α=1, lr=8e-3) NEW

## P1 calibration (CPU, free, before this preregistration; disclosed)

Pure cache bookkeeping — all reference anchors re-derived and confirmed:
v1280 (0.5, 2e-3) 2/2 grokked median 3,900 (heldout 0.977/0.981);
(0.5, 4e-3) 2/2 grokked median 1,800 (heldout 0.9992 both);
v1279 α=1 lr=1e-3 baseline 3/3 median 11,400; α=2 lr=1e-3 refs 12.8k–23.2k.
No init-geometry measurement is relevant (lr does not change the init).

## 实验设计（固定；GPU 预算上限 12 runs；all cells d=128, max_steps=60000）

Frozen otherwise (p=97, train_frac=0.2, wd=1.0, 1 layer, n_head=4, full-batch
AdamW, standard init — α=1 cells need no rescaling; the α=2 arm uses the v1279
`scaled_init` path).

- **Verdict arm (α=1)**: lr ∈ {4e-3, 8e-3} × seeds {1337, 1338, 1339} = 6 runs
  (3 seeds because the verdict rests on median comparisons against 2-seed
  references whose spread is ~2×).
- **Dose arm (α=1, descriptive)**: lr=2e-3 × seeds {1337, 1338} = 2 runs —
  completes the α=1 lr-dose curve {1e-3 (ref), 2e-3, 4e-3, 8e-3}.
- **Symmetry arm (α=2, descriptive)**: lr=8e-3 × seeds {1337, 1338} = 2 runs —
  the r=4× point at LARGE norm, giving a three-norm comparison at one relative
  step: (0.5, 2e-3) vs (1, 4e-3) vs (2, 8e-3).
- **P2 probe**: the first verdict cell (α=1, lr=4e-3, seed 1337) run alone; it
  fills its Phase-A slot (the v1280 preloaded mechanism). Stop condition: only if
  it comes out `broken` (memorization lost — optimizer instability), re-panel the
  lr ladder downward before the grid.
- Per-cell cache: both curves (step, train_acc, val_acc), N0, meta, heldout.
  Total = 6 + 2 + 2 = 10 ≤ 12.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

Cell classes as in v1280 (grokked / stuck_memorized / broken; t_gen from the val
curve at bar, censored = +∞, never dropped). Pair map: {4e-3 → ref (0.5, 2e-3),
8e-3 → ref (0.5, 4e-3)}.

- **G0 reference integrity**: v1280 cache loads and its (0.5, 2e-3)/(0.5, 4e-3)
  cells are 2/2 grokked with medians exactly 3,900 / 1,800 at bar 0.90; v1279
  cache α=1 baseline is 3/3 grokked with median exactly 11,400.
  Fail → `review` (reference_cache_invalid).
- **G1 completeness**: all 10 cells cached; no silent exclusion.
- **Pair validity**: a verdict pair is invalid if any of its α=1 cells is
  `broken` (instability is not slowness); any invalid pair → `review`
  (broken_cells).
- **Pair ratio**: ρ(lr) = median t_gen(α=1 cells at lr) / median t_gen(matched
  reference cells), censored → +∞. Parity band: ρ ∈ [0.5, 2].
- **Ladder**: both pairs in parity → `relative_step_sets_the_clock` (the norm
  contributes nothing at matched step; no norm-clock story survives).
  Both pairs ρ > 2 → `small_norm_speeds_grokking_beyond_lr` (the lr-adjusted
  norm clock stands). Both pairs ρ < 0.5 → `large_norm_speeds_grokking_beyond_lr`
  (inverted direction). Pairs disagree → `review` (mixed_pairs).
- **G2 robustness**: the verdict identical at t_gen bars {0.85, 0.90, 0.95};
  any flip → `review`.
- Dose and symmetry arms are descriptive only, never verdict-bearing.

## 测试与证据要求

`src/minigpt/grok_norm_vs_step_v1281.py` (reuses v1280's `classify`/`cell_tgen`/
`train_cell` and v1279's caches — no duplication) +
`tests/test_grok_norm_vs_step_v1281.py` (config validation, G0 pass/fail on
synthetic references, every ladder branch incl. broken→review and mixed→review,
orchestration with injected trainer + preloaded probe slot, byte-stable contract,
figure smoke); thin `scripts/run_grok_norm_vs_step_v1281.py` /
`scripts/analyze_grok_norm_vs_step_v1281.py`. ONE figure (two panels: the
matched-pair comparison at r=4×/8×; the α=1 lr-dose curve with refs). Full lane
ritual: 5-format artifacts, `f/1281/图片+解释/说明.md`, walkthrough 1238 BEFORE
the final full suite, README version sections + catalog row + Documentation Map
row + f/README + 讲解 README indexes, cleanup, commit, push, tag, CI green.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, frozen recipe except
  the manipulated lr, 60k budget. No wd/optimizer sweeps; no d=64; no re-running
  of any reference cell (v1279/v1280 caches are read-only).

## Closeout (post-run; zero code changes after preregistration ran)

- GPU 10/12 (P2 probe filled its slot); all 10 cells grokked — no stuck, no
  broken, even at lr=8e-3. Phase B CPU-only; G0/G1/G2 pass.
- Preregistered verdict: **`review` (mixed_pairs)**, bar-stable. ρ(r=4×) = 0.359
  (below the parity band: α=1 is ~2.8× FASTER than the matched-step α=0.5);
  ρ(r=8×) = 0.778 (parity). Both pairs exclude the small-norm branch (neither
  ρ > 2) — the certain content inside the review.
- Descriptive resolution of the banked question: the ABSOLUTE lr dominates the
  clock. α=1 lr dose: 11,400 (1e-3) → 1,900/2,800 (2e-3) → median 1,400 (4e-3)
  → median 1,400 (8e-3, saturated ~1k). Three norms at one relative step (r=4×):
  (α=0.5, 1, 2) → (3,900, 1,400, 900). At adequate lr, larger norm is mildly
  FASTER; α=2 @ 8e-3 is the fastest, most accurate cell of the whole arc
  (900/900 steps, heldout 0.9999/1.0).
- Arc synthesis (descriptive): v1277's narrow-5×-faster, v1279's small-init
  death, and v1280's rescue unify as "lr=1e-3 is far below optimal for d=128 —
  the canonical baseline sits in an lr-starved regime"; norm/width effects were
  largely indirect effective-lr effects. Banked: do narrow widths also converge
  to ~1k steps at high lr (the width version of this control)?
- The v1280 brief's banked-question note is resolved with a linked notice (the
  preregistered obligation bound only the `relative_step_sets_the_clock` branch,
  but the resolution is stamped regardless — the chain of notices continues).

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc without the disclosed protocol = fail.
- Censored cells silently dropped = fail. Budget beyond 12 runs or silent
  descope = fail. A `relative_step_sets_the_clock` verdict without updating the
  v1280 brief's banked-question note = fail (the chain of linked notices
  continues).
