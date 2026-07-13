# v1277 capability brief — capacity squeeze: drop, superpose, or fail?

Lane: ML capability. Executor: **Claude directly** (user: "entirely in your hands,
independently without codex") — the lane's rules bind the reviewer-as-executor
unchanged: preregister-commit-then-run, CPU probes before GPU, Phase A caches /
Phase B CPU-only, pre-registered decide() ladder, multi-seed, honest scope.

## 背景与问题

Three closed arcs meet here. The grokked mod-97 model computes addition through a
small set of Fourier frequencies (v1188/v1191, causal); that circuit is
frequency-sparse but magnitude-dense (v1275); and when features outnumber
dimensions, packing beats dedicating on a toy autoencoder (v1276). Each frequency
feature needs 2 embedding dimensions (cos+sin). **Squeeze `n_embd` below the
circuit's orthogonal footprint and the model must choose**: keep its frequencies
and pack them non-orthogonally (superposition in a real transformer), economize
to fewer frequencies that still fit, solve the task some non-Fourier way, or fail
to grok. All four outcomes are pre-registered verdicts.

## P1 calibration probe (CPU, read-only, run BEFORE this preregistration; disclosed)

On the shipped v1185 checkpoint (d=128, heldout 0.9660):
- **k_func = 4**: min k with keep-top-k-frequency ablation ≥ 0.9 × model acc
  (k=3 → 0.838 fails; k=4 → 0.943 passes; the v1191 top-5 was sufficient but not
  minimal). Baseline orthogonal footprint = **2·k_func = 8 dimensions**.
- Spectral participation ratio n_eff = 27.3 — the raw spectrum is long-tailed, so
  spectral counts are NOT a valid feature count; k_func (causal, via the v1191
  keep-ablation) is the primary metric. n_eff is descriptive only.
- Baseline interference at d=128 over the top-4 cos/sin directions:
  max |off-diag cos| = 0.066 (near-orthogonal), mean-square 0.0009.

## 实验设计（固定）

- Recipe: frozen v1183/v1185 grok recipe (p=97, train_frac=0.2, wd=1.0, 1 layer,
  n_head=4, full-batch AdamW, max_steps=40000, early-stop on stable grok) with ONE
  knob: `n_embd` ∈ **{32, 16, 12, 8, 4}** (all divisible by n_head; the squeeze
  region {8, 4} sits at/below the baseline forcing dimension 8). Seeds
  {1337, 1338, 1339} per width → 15 training runs; GPU cap 20 incl. the P2 probe.
- P2 probe (GPU, before the grid): one run at width 16, seed 1337. If it fails to
  grok within budget, STOP and re-panel the grid upward rather than burning runs.
- Per-cell Phase-A cache (all Phase-B inputs, no model retained): meta (t_mem,
  t_gen, final accs, steps), heldout acc, normalized 48-bin spectrum, top-8
  frequencies, keep-top-k ablation acc for k=1..8 (v1191 mechanics, tied lm_head),
  Gram stats (max |off-diag cos|, mean-square) of the top-k cos/sin direction
  images in embedding space for k=1..8, and n_eff.

## 预注册判据（decide()，本 commit 先于任何 Phase-A 运行）

Definitions: grokked = heldout ≥ 0.90. Per grokked cell, k_func(ratio) = min k ≤ 8
with keep_acc[k] ≥ ratio × heldout; none → the cell is `off_mechanism`.
Cell class at width w: `forced_packing` if 2·k_func > w; `economized` if
2·k_func ≤ w.

- **G0 substrate**: baseline width 32 has ≥2/3 grokked AND median k_func ∈ [2,8]
  AND median top-k_func gram max|cos| ≤ 0.30. Fail → `review` (substrate_unsound).
- **G1 completeness**: all 15 cells attempted and cached; no silent exclusion.
- **Verdict over squeeze-region ({8,4}) grokked cells**, at keep_ratio 0.90:
  - fewer than 2 such cells → `squeeze_hits_capacity_floor` (smallest grokking
    width reported);
  - ≥70% `forced_packing` → `squeeze_forces_superposition`;
  - ≥70% `economized` → `squeeze_drops_features`;
  - ≥30% `off_mechanism` → `review` (non-Fourier strategy suspected);
  - otherwise → `review` (mixed strategies).
- **G2 robustness**: the verdict must be identical across keep_ratio
  ∈ {0.85, 0.90, 0.95}; any flip → `review`.
- Every branch, including floor and review, is publishable. No post-hoc branches;
  threshold edits after Phase A only via the disclosed cache-re-derived protocol.

## 测试与证据要求

- `src/minigpt/capacity_squeeze_v1277.py` + `tests/test_capacity_squeeze_v1277.py`
  (metric unit tests incl. analytically-constructed embeddings with known
  frequencies; every decide() branch on synthetic caches; contract test = decide
  re-derives byte-stably from the committed cache); thin
  `scripts/run_capacity_squeeze_v1277.py` / `scripts/analyze_capacity_squeeze_v1277.py`.
- Lane ritual in full: 5-format artifacts, ONE figure (k_func & interference vs
  width with the forcing line at 8), `f/1277/图片` + `解释/说明.md`, ~3000-char
  Chinese walkthrough BEFORE the final full-suite run, README/index updates,
  cleanup gate, preregister commit + close commit, push, CI green.

## 明确不做

- No claims about LLM superposition; scope = "own grokked substrate, toy scale".
- No second knob (n_head, train_frac, wd all frozen); no v1185 artifact mutation.
- No spectral-count verdicts (P1 showed spectral n_eff is invalid for counting).

## 失败条件

- Phase A run before this brief + module + tests are committed = fail.
- decide() thresholds edited after Phase-A data without disclosed cache-re-derived
  fix = fail (12-times-caught bug class; explicit self-audit in the version doc).
- GPU budget beyond 20 runs, or a silent descope = fail.
- A verdict claimed from cells whose keep-ablation was not computed = fail.

## Execution status (2026-07-13, executed directly by Claude)

- Preregister commit `644dd535` (module + tests + this brief) landed BEFORE any
  Phase-A run. P2 probe: w=16 grokked (0.952, t_gen 2,800). Phase A: 15 runs,
  budget 16/20, v1185 checkpoint untouched.
- **Verdict: `squeeze_hits_capacity_floor`** — squeeze region {8,4} grokked 0/6;
  smallest grokking width 12 (1/3 seeds; the other two stall at ~0.78); G0/G1/G2
  all pass; verdict identical across keep_ratio {0.85, 0.90, 0.95}. decide()
  thresholds unchanged after Phase A (threshold-bug self-audit: clean — the floor
  branch sits far from every threshold boundary).
- Descriptive findings recorded (not verdict-bearing): narrow widths grok ~5x
  FASTER than d=128 (t_gen 2,600–3,400 vs ~15,000); w=8 failures show top-freq
  direction interference 0.74–0.77 at chance-level accuracy = attempted-but-failed
  packing; the lone w=12 success uses 5 freqs at interference 0.564.
- Evidence: `f/1277/解释/capacity_squeeze_v1277/` (5 formats + cache),
  `f/1277/图片/capacity-squeeze-v1277.png`, walkthrough
  `代码讲解记录_工程保养阶段/1234-v1277-capacity-squeeze.md`.
- Follow-up candidates: locate the floor precisely (widths between 12 and 8,
  longer budget arm); or the new question this version surfaced — why do NARROW
  models grok so much faster?
