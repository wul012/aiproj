# v1275 capability brief — sparsity: is the winning ticket the Fourier circuit?

Lane: ML capability (fresh axis — SPARSITY/PRUNING; follows the closed arcs: grokking+
interp v1179–91, calibration v1192, continual learning v1193–95, induction mechanism
v1196–98, double-descent/noise v1199–1200). Executor: Codex session in `D:\aiproj`.
House rules bind in full: adversarial design-panel premortem documented BEFORE Phase A,
CPU probes before any GPU, Phase A trains once + caches / Phase B CPU-only re-derives,
pre-registered decide() gates, multi-seed for stochastic claims, honest scope labels,
name budget ≤40 chars for all new identifiers, no ML-lane artifact of a prior version
may be modified.

## 背景与问题

The lottery ticket hypothesis (Frankle & Carlin 2019) claims a sparse subnetwork,
found by magnitude pruning and rewound to init, trains to full accuracy. We are in a
rare position to test WHAT the ticket IS: v1188/v1191 proved our grokked mod-97 model
generalizes via a 5-frequency Fourier circuit (freqs [43,3,48,26,44]; keep-only-top-5
retains 0.972, remove-them drops to 0.578). Question, two halves:
(P) Does magnitude pruning of the SHIPPED checkpoint preserve the Fourier circuit —
    i.e., do the surviving weights concentrate on the known frequencies?
(L) Does a sparse ticket found by iterative magnitude pruning + rewind re-TRAIN to
    grokking, and does the trained ticket land on the SAME circuit?

## 起点核对（session start）

- `git log --oneline -3`; confirm clean tree, CI green on HEAD, current version = v1274.
- The shipped checkpoint from v1185 loads read-only (the v1186 inference API is the
  entry point); its bytes are frozen — copying is allowed, mutation is a fail condition.
- Reuse existing modules (grok task/model/train from v1179/v1183/v1185, FFT tooling from
  v1188/v1191). New training harness = scope violation.

## Arm P — prune the artifact (CPU-only; run FIRST, as probe and as result)

1. Global magnitude pruning sweep on the v1185 checkpoint (embedding/unembed and MLP
   treated per-tensor AND globally; both reported): heldout accuracy vs sparsity
   ∈ {0.5, 0.7, 0.8, 0.9, 0.95}, on the SAME 7527-pair heldout set as v1185.
2. Fourier alignment: at each sparsity, the kept embedding/unembed weights' top-5
   frequency power share (v1188 metric) vs the full model and vs a random-mask control
   at matched sparsity. Pre-registered: alignment = kept top-5 share exceeds the
   random-mask control's by ≥0.05 at the highest sparsity where acc ≥ 0.9.
3. This arm is pure CPU (~minutes). It doubles as the mandatory pre-GPU probe: if
   pruning at 0.5 already destroys accuracy, STOP and re-panel before Arm L.

## Arm L — lottery ticket proper (GPU, budget-capped)

1. 3 seeds. Per seed: train to grok with the frozen v1183 recipe (wd=1.0, known
   t_gen≈15k); IMP with rewind-to-init at prune levels {0.5, 0.75, 0.875} (3 rounds
   max); controls per level: random mask (same sparsity, same init) and reinit ticket
   (same mask, fresh init). GPU budget cap: ≤ 3 seeds × 5 training runs; if the cap
   cannot cover 3 prune levels, drop 0.875 first and record the descope.
2. Pre-registered outcomes per level: ticket groks (heldout ≥ 0.9 within ≤ 1.5× the
   dense t_gen) vs controls; trained-ticket Fourier top-5 share vs dense model.
3. Verdict ladder (decide() implements exactly this, committed before Phase A runs):
   `ticket_matches_fourier_circuit` / `ticket_trains_but_unaligned` /
   `ticket_needs_dense_start` (P passes, L controls tie) / `pruning_breaks_circuit`
   (P fails) — every branch including nulls is a publishable outcome; picking the
   verdict AFTER seeing results without a pre-registered branch = fail.

## 测试与证据要求

- `src/minigpt/fourier_ticket_v1275.py` + `tests/test_fourier_ticket_v1275.py`:
  decide() contract test re-derives the verdict byte-stably from the Phase-A cache;
  gate tests for every pre-registered threshold; full suite green.
- The lane's full per-version ritual: 5-format readability artifacts via
  `minigpt.readability_report_artifacts.write_readability_outputs`; ONE figure
  (acc-vs-sparsity with Fourier-alignment overlay, both arms) in `f/1275/图片`;
  `f/1275/解释/说明.md`; the ~3000-char Chinese walkthrough in the active
  `代码讲解记录*` volume (written BEFORE the final full-suite run); README/index
  updates; cleanup gate; one commit `v1275 <summary>`; push; CI green.
- The design-panel premortem (≥3 lenses: circularity risks, control adequacy, budget
  honesty) and every CPU-probe result go in the version doc BEFORE Phase-A numbers.

## 明确不做

- No claims about LLM-scale lottery tickets; scope label = "toy scale, own substrate".
- No modification of any prior version's cached artifacts, checkpoints, or verdicts.
- No second axis (superposition is queued as its own future version — do not fold it in).
- No new abstractions beyond one module + one test file + two thin scripts
  (run_/analyze_ pattern); elegance gates apply.

## 失败条件

- v1185 checkpoint bytes touched = stop, revert.
- Single-seed Arm-L claims, or a verdict branch invented post hoc = fail.
- decide() thresholds edited after seeing Phase-A data (the lane's 8-times-caught bug
  class — self-audit for it explicitly in the version doc) = fail unless re-derived
  with the fix from cache and disclosed.
- GPU budget exceeded silently = fail; descopes are recorded, not hidden.
- Random-mask or reinit control skipped = the corresponding claim is unsupported.

## Claude review — 2026-07-12 (v1275): PASS — an honest negative with a real finding

- Verified: the reviewer re-ran Phase B from the committed cache and the verdict
  re-derives byte-stably (`pruning_breaks_circuit`); CI green; checkpoint sha pinned
  and unchanged; zero GPU runs spent (probe stop honored, descope pre-declared).
- The preregister-commit-then-run pattern (thresholds committed at `f12f8793` BEFORE
  the first probe) is a genuine upgrade to the lane's discipline — keep it as the
  standard for all future capability versions.
- The finding is better than a null: at 50% sparsity accuracy collapses
  (0.966 → 0.41 per-tensor / 0.49 global) while the SURVIVORS' fixed-5-freq Fourier
  share stays ~0.305 (0.314 even at 95%) with the same top-5 — the circuit is
  frequency-sparse but magnitude-DENSE. Magnitude pruning cannot find this ticket
  because the circuit lives in a rotated basis and needs its coordinated small
  weights. This cleanly explains WHY Arm L would have been mis-posed, and is the
  correct scientific closure for the sparsity axis on this substrate.
- Next capability version: superposition (Anthropic toy-models phase diagram) as
  queued — a natural follow-on since basis-vs-neuron alignment is exactly what v1275
  just made concrete.
