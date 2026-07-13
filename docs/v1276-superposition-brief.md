# v1276 capability brief — superposition: how do n features fit in m << n dimensions?

Lane: ML capability (fresh axis — SUPERPOSITION, the Anthropic Toy-Models-of-
Superposition phenomenon; follows v1275's finding that our grokked circuit is
frequency-sparse but magnitude-DENSE, i.e. basis-vs-neuron alignment matters).
Executor: Codex session in `D:\aiproj`. House rules bind in full, PLUS the v1275
upgrade which is now the lane standard: **preregister-commit-then-run** — the module
with decide() thresholds, the tests, and this brief's gates are committed BEFORE the
first Phase-A run; post-run diffs may only touch report fields/artifacts.

## 背景与问题

Toy Models of Superposition (Elhage et al. 2022): when a model must represent n
features in m << n dimensions, dense features force it to DEDICATE dimensions to the
top-m features and drop the rest; sparse features let it pack MORE than m features as
interfering, non-orthogonal directions — superposition. Questions:
(1) Does superposition emerge as feature sparsity increases, on our own substrate?
(2) Is it loss-OPTIMAL (beats the best dedicated solution analytically) rather than
    an optimization artifact?
(3) Does feature importance order who gets a dedicated dimension?

## 起点核对（session start）

- Clean tree, CI green, current version = v1275. This version is expected CPU-ONLY
  (matrices are tiny); GPU use requires a written justification in the version doc.
- Substrate is a NEW tiny ReLU autoencoder (x ≈ ReLU(WᵀWx + b)) — precedent v1199
  (non-MiniGPT substrate when the phenomenon demands it). It lives inside
  `src/minigpt/superposition_v1276.py`; no new package, no new harness.

## 实验设计（固定，先注册后运行）

- Features: n = 20, dims m = 5. Each feature independently active with probability
  (1 − S), magnitude Uniform[0,1]. Sparsity grid S ∈ {0.0, 0.7, 0.9, 0.97, 0.99}.
- Two arms: IMPORTANCE arm (importance_i = 0.7^i, the TMS schedule) and UNIFORM arm
  (all importances 1) — the control for the importance-ordering claim.
- 5 seeds per (arm, S); full-batch or large-batch Adam to convergence with a
  pre-registered plateau gate (loss drift over the last decile below a written bound;
  unconverged cells are excluded and disclosed, not silently kept).
- Metrics per trained W (Phase B, from cache): per-feature norm ‖W_i‖; represented
  count R(τ) = #{i: ‖W_i‖ ≥ τ} with a τ-robustness grid (τ ∈ {0.3, 0.5, 0.7});
  interference ∑_{j≠i}(Ŵ_i·Ŵ_j)²; loss vs the ANALYTIC best-dedicated baseline
  (choose the top-m features by importance, represent them orthonormally, drop the
  rest — its expected loss is computable in closed form and must be implemented with
  its own unit test).

## 预注册判据（decide() 分支，运行前提交）

- G1 convergence: every kept (arm,S,seed) passes the plateau gate; ≥4/5 seeds kept
  per cell, else the cell is invalid and the verdict must route through review.
- G2 emergence: dense end S=0.0 has R(τ) ≤ m (dedicated regime) AND sparse end
  S=0.99 has R(τ) > m (superposition), for ALL τ in the grid, in ≥4/5 seeds, in BOTH
  arms.
- G3 monotone: median R(τ=0.5) is non-decreasing in S (Spearman ≥ 0.9 with exact
  permutation p ≤ 0.05, pooled seeds), both arms.
- G4 optimality: at S=0.99 the trained loss beats the analytic best-dedicated loss
  (median across seeds, margin ≥ written epsilon); at S=0.0 it does NOT beat it
  (dedicated is optimal when dense) — this is what makes superposition a FINDING
  rather than an artifact.
- G5 importance order (IMPORTANCE arm only): among represented features at the dense
  end, the represented set = the top-m by importance in ≥4/5 seeds; the UNIFORM arm
  is exempt (no ordering exists to recover).
- Verdict ladder: `superposition_emerges_with_sparsity` (G1–G4 pass; G5 states the
  importance result separately) / `no_superposition_dedicated_only` (G2 sparse end
  fails — an honest null) / `superposition_not_optimal` (G2 passes, G4 fails —
  packing happens but is an optimization artifact) / anything non-monotone or
  mixed-τ → `review`. Every branch is publishable; no post-hoc branches.

## 测试与证据要求

- `src/minigpt/superposition_v1276.py` + `tests/test_superposition_v1276.py`:
  decide() contract test (byte-stable re-derivation from the Phase-A cache), a unit
  test for the analytic dedicated-baseline formula against a brute-force numerical
  check at tiny size, gate tests for every threshold above. Full suite green.
- Thin `scripts/run_superposition_v1276.py` / `scripts/analyze_superposition_v1276.py`
  (run_/analyze_ pattern); Phase A caches every (arm,S,seed) W, b, loss trajectory.
- Lane ritual: 5-format readability artifacts; ONE figure — per-feature norm bars (or
  R(τ) curve) vs S with the m=5 line marked, both arms; `f/1276/图片` + `解释/说明.md`;
  ~3000-char Chinese walkthrough in the active `代码讲解记录*` volume BEFORE the final
  full-suite run; README/index updates; cleanup gate; preregister commit + final
  commit `v1276 <summary>`; push; CI green.
- CPU probes: one probe per arm at (S=0.0, S=0.99) single-seed BEFORE the full grid,
  results recorded in the version doc; if the sparse-end probe shows no packing at
  all, stop and re-panel rather than burning the grid.

## 明确不做

- No claims about superposition in LLMs or in MiniGPT itself; scope label =
  "toy autoencoder, own substrate". (Probing MiniGPT activations for superposition is
  a possible FUTURE version — out of scope here.)
- No phase-diagram sweep over importance ratios (the full TMS heatmap) — the two
  fixed arms only; a diagram version can follow if this one passes.
- No touching any prior version's artifacts; elegance gates apply (identifiers ≤40
  chars, one module + one test file + two thin scripts).

## 失败条件

- decide() thresholds edited after seeing Phase-A data without a disclosed,
  cache-re-derived fix = fail (the lane's 11-times-caught bug class — self-audit
  explicitly in the version doc).
- The analytic baseline implemented without its own correctness test = G4 is
  unsupported = fail.
- Unconverged cells silently kept, a τ value dropped post hoc, or seeds cherry-picked
  = fail.
- GPU used without written justification = fail (this version is CPU-sized).

## Claude review — 2026-07-13 (v1276): review branch ADJUDICATED — superposition demonstrated; G2's metric, not the phenomenon, failed

- Verified: verdict re-derives from the committed cache; the dedicated-baseline
  correction (E[x] variance fix) was disclosed per protocol and recomputed from the
  UNCHANGED probe cache; the executor refused to modify gates post hoc — correct.
  One red run (unittest discovery, infra not science) fixed in the next commit.
- Adjudication of the mixed-τ: the failure is confined to the UNIFORM-arm dense cell
  (R(0.3)/R(0.5)/R(0.7) = 15/6/4). That cell's ground state is DEGENERATE — with
  uniform importance, any 5-of-20 dedicated solution is equally optimal, so norms smear
  and "represented set" is ill-posed there; no τ can fix a definition whose uniqueness
  assumption doesn't hold. Everywhere the concept IS well-posed, the phenomenon is
  unambiguous: importance arm passes G2 at ALL τ (dense R=5 = exactly the top-5 in 5/5
  seeds; sparse R=11–13), uniform sparse end R=20 at all τ, monotone rho=1.0/0.97 with
  exact p≤0.017, and G4 optimality is decisive (sparse loss ratios 0.19/0.16 vs the
  analytic dedicated best; dense ~1.000).
- RULING: **superposition_emerges_with_sparsity holds** (external adjudication of the
  pre-registered review branch). The residual finding is real and worth keeping:
  norm-threshold representedness requires symmetry-breaking (importance) to be
  well-defined at the dense end. A degeneracy-robust metric (participation-ratio-style)
  is a legitimate FUTURE version — not a retrofit to this one.
- Lane status: superposition axis opened and closed honestly in one version. Next
  candidates: degeneracy-robust representedness, the TMS phase heatmap, or probing
  MiniGPT's own activations for superposition.
