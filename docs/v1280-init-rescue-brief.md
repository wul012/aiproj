# v1280 capability brief — the stuck-memorized state: is small-init grokking death an lr artifact?

Lane: ML capability. Executor: **Claude directly** (v1277/v1279 mode). All lane rules
bind: preregister-commit-then-run, CPU probes before GPU, Phase A caches / Phase B
CPU-only, pre-registered decide() ladder, multi-seed, honest scope, elegance gates.

## 背景与问题

v1279 found that shrinking d=128's init norm (α=0.5, and the d=32-matched α\*≈0.493)
prevents grokking entirely (0/6 at a 100k budget). The v1280 P1 probe re-checked the
committed v1279 cache and CORRECTED the v1279 interpretation (disclosed, commit
`784f91c2`): those cells DO memorize — final_train=1.000 at t_mem=200–300, as fast
as healthy cells — then sit fully memorized for 100k steps. The death is of the
**memorize→generalize transition**, not of optimization.

The sharpest deflationary hypothesis: an **lr artifact**. Under AdamW the update
magnitude is ~lr regardless of gradient scale, so the RELATIVE update is lr/|w| ∝ 1/α
— at α=0.5 the frozen lr=1e-3 is effectively ~2× the baseline's relative step. If
grokking's transition needs a matched effective lr, rescaling lr should revive it.
If v1279's headline dies here, we say so prominently; if it survives a 16× lr sweep,
"small init prevents grokking" becomes robust, not recipe luck.

## P1 calibration probe (CPU, free, run BEFORE this preregistration; disclosed)

- Cache forensics (drove the v1279 correction): all 8 censored v1279 cells have
  final_train=1.000, t_mem=200–300 (d=64 α=1 dead seeds included).
- Init geometry at d=128 across α (seed 1337): init loss ≈ ln(99) for α ≤ 1
  (4.596–4.637; 5.06 at α=2); logit std scales ~α² (0.019/0.080/0.256/0.968 at
  α=0.25/0.5/1/2); grad norm scales ~α (0.13/0.32/1.08/5.01). With Adam
  normalization this makes RELATIVE steps ∝ 1/α — motivating a DOWNWARD lr sweep as
  the primary rescue direction, with upward included for honesty.
- d=64 at α=1 shows NO init-geometry anomaly (logit std 0.19, grad norm 0.52 —
  smooth between w=32 and w=128): the v1279 mid-width hole is not visible at init.
  Descriptive note only; d=64 is out of scope for this version.

## 实验设计（固定；GPU 预算上限 18 runs；all cells d=128, max_steps=60000）

One clock for all new cells: 60,000 steps (baseline α=1 median t_gen is 11,400 from
the v1279 cache, so 60k > 5× baseline and > the worst observed grokking cell, 35k).
Claims are scoped "within 60k". Frozen otherwise: p=97, train_frac=0.2, wd=1.0,
1 layer, n_head=4, full-batch AdamW, init via the v1279 `scaled_init` path.

- **Rescue arm**: α=0.5 × lr ∈ {0.25, 0.5, 2.0, 4.0}×1e-3 × seeds {1337, 1338}
  = 8 runs. α=0.5 lr=1e-3 reference cells come from the committed v1279 cache
  (reuse-cached rule; never re-run).
- **Confirm rule (deterministic)**: any lr with exactly 1/2 grokked gets a seed-1339
  confirm run, processed in ascending lr order until the budget cap;
  rescued(lr) = ≥2 grokked among its seeds.
- **Dose-response arm**: α ∈ {0.6, 0.7, 0.85} × lr=1e-3 × seeds {1337, 1338}
  = 6 runs. With the v1279 refs at α ∈ {0.493, 0.5, 1.0, 2.0} this brackets the
  death boundary.
- **P2 probe (GPU, after this commit, before the rest)**: the first rescue cell
  (α=0.5, lr=5e-4, seed 1337) run alone as harness sanity; it counts toward the 8.
  No stop condition expected; any anomaly re-panels before the grid.
- Per-cell cache: BOTH curves this time — rows (step, train_acc, val_acc) — plus
  N0, meta, heldout; Phase B recomputes t_gen at any bar AND t_mem from the cache.
  Total ≤ 8 + 6 + 4 confirms = 18.

## 预注册判据（decide()，本 commit 先于任何 GPU 运行）

Cell classes (from cached curves at bar): grokked = t_gen(bar) present AND heldout
≥ 0.90; stuck_memorized = not grokked AND t_mem present (train ≥ 0.99);
broken = no t_mem. Censored comparisons use t_gen = +∞, never dropped.

- **G0 reference integrity**: the committed v1279 cache loads; its d=128 α=1 cells
  are 3/3 grokked with median t_gen(0.90) = 11,400; its α ∈ {0.5, α\*} cells are
  0/6 grokked and 6/6 have t_mem present. Fail → `review` (reference_cache_invalid).
- **G1 completeness**: all planned cells cached (8 + 6 + exactly the confirms the
  deterministic rule fired); no silent exclusion.
- **Rescue ladder** (α=0.5 arm; at each bar the baseline median is re-derived from
  the reference cache's α=1 val curves, and the rescue statistic is: per rescued lr,
  the median t_gen over its grokked cells; then the MINIMUM across rescued lrs —
  i.e. the best rescue):
  - no lr rescued → `stuck_memorized_robust_to_lr` (with the stuck/broken split per
    lr reported; a broken cell is a failed rescue, not evidence of stuckness).
  - some lr rescued AND best-rescue statistic < baseline median →
    `norm_clock_revived_under_lr_scaling` (v1279's headline is formally downgraded
    to an lr confound; prominent disclosure in all v1280 surfaces AND a linked
    correction note added to the v1279 brief).
  - some lr rescued AND best-rescue statistic ≥ baseline median →
    `lr_rescues_grokking_without_speedup` (death was lr-conditional; the norm clock
    still yields no speedup, v1279's inversion softens to "at the frozen lr").
  - mixed/other → `review`.
- **Dose-response classification (descriptive, preregistered)**: cliff = one
  threshold α_c with all swept cells below it stuck and all above grokked,
  unanimous across seeds; graded = otherwise. Never verdict-bearing.
- **G2 robustness**: the rescue verdict must be identical at t_gen bars
  {0.85, 0.90, 0.95}; any flip → `review`.

## 测试与证据要求

`src/minigpt/grok_init_rescue_v1280.py` (+ imports of `scaled_init` / `t_gen_at`
from the v1279 module — no duplication) + `tests/test_grok_init_rescue_v1280.py`
(cell classification incl. heldout gate and broken class, t_mem-from-train-curve,
config validation, G0 pass/fail on synthetic reference caches, every decide()
branch, confirm-rule orchestration with an injected trainer, byte-stable contract,
figure smoke); thin `scripts/run_grok_init_rescue_v1280.py` /
`scripts/analyze_grok_init_rescue_v1280.py`. ONE figure (two panels: rescue arm
lr→t_gen with the baseline band; dose-response α→t_gen with v1279 refs hollow).
Full lane ritual: 5-format artifacts, `f/1280/图片+解释/说明.md`, walkthrough 1237
BEFORE the final full suite, README version sections + catalog row + Documentation
Map row + f/README + 讲解 README indexes, cleanup, commit, push, tag, CI green.

## 明确不做

- No LLM claims; scope = own grokked substrate, toy scale, frozen recipe, 60k budget.
- No wd sweep, no optimizer swap, no d=64-hole investigation (banked); no v1279
  cache mutation (read-only reference); no training-loop modification (lr and
  max_steps flow through the existing GrokConfig fields).

## 失败条件

- Any GPU run before this brief + module + tests are committed = fail.
- decide() thresholds edited post-hoc without the disclosed protocol = fail
  (14-times-caught bug class; the 14th is this version's own P1 correction).
- Censored cells silently dropped = fail. Budget beyond 18 runs or silent descope
  = fail. A rescued verdict without the v1279-brief correction note = fail.
