# aiproj Excellence Brief (A-track) — the fourth project joins the program

Executor: Codex session in `D:\aiproj` (the engineering/governance line; the ML capability
version cadence is a separate lane and this brief must not alter it). Parent program:
`D:\nodeproj\orderops-node\docs\plans\production-excellence-final-acceptance.md` (read-only).
Standard: same spirit as E1–E10, adapted to a Python research/governance repo. Same letter:
a gate counts only when a committed mechanical check fails on regression; waivers must be
written and reviewer-checkable. Existing AGENTS.md conventions bind (cleanup gate,
walkthrough rules, 500–800 line split threshold, no-promotion boundary, honest evaluation
language). All archive roots `a/`–`f/` and `代码讲解记录*` are path-stable: measure, never move.

## Verified starting facts (2026-07-06; re-verify at session start)

- CI exists (`.github/workflows/ci.yml`) — confirm what it actually runs and that it is green.
- `pyproject.toml` has pytest config but NO lint/format/type tooling (no ruff/black/mypy).
- 726 test files under `tests/`; coverage measurement/enforcement state unknown.
- `runs/` is 12M (fine today; budget it anyway). Archive roots measured 2026-07-06:
  `a/` 13M, `b/` 17M, `c/` 87M, `d/` 45M, `e/` 245M, `f/` 17M (~424M total). The `e/`
  growth curve is the same pattern that reached 1.1GB in mini-kv — the A0 inventory and
  forward budget exist to stop that here while it is still cheap.
- Docs set is rich (`docs/*.md`, `文档分流说明.md` governs placement); freshness vs the
  current tree (v1259+) unverified.

## A0 — census and quick wins (1 version)

1. Record what ci.yml runs; confirm green on HEAD. Fix trivial staleness only.
2. Archive + runs inventory (mirror mini-kv K5: stdlib-only script, warning-only, indexed
   in a committed doc). No relocation, ever.
3. START_HERE/README freshness check against the current version line; fix stale version
   pointers and capability claims (the "model quality is educational" boundary stays).

## A1 — static analysis (1–2 versions)

1. Adopt ruff (lint + format) with the program's mechanical-change rule: new-and-touched
   files only, or directory batches within line budgets; committed baseline for the rest;
   CI step fails on new violations. Zero-error end state on `src/` and `scripts/`.
2. mypy on the most load-bearing `src/` modules (public API, artifact/report builders,
   gates). Full-repo mypy is NOT required; the scope line is written down and ratcheted,
   not silently shrunk.

## A2 — coverage (1 version)

Measure pytest coverage in CI; floor = observed baseline − 2 points; ratchet up, never
down. If the suite is slow, a fast-lane/full-lane split is acceptable only if the full
lane still runs in CI on every push.

## A3 — reproducibility and honest-measurement gates (1–2 versions; the aiproj-specific core)

1. Mechanize the house rules that are currently discipline-only:
   - A committed contract test per capability-version family proving its decide()/verdict
     re-derives byte-stably from cached artifacts (the "reuse cached training, don't
     re-run" rule as a failing check).
   - Seed policy doc + test: any pass/fail claim gated on multi-seed evidence where the
     underlying metric is stochastic; single-seed verdicts must be labeled exploratory in
     the artifact itself.
2. Artifact schema guard: experiment/model/data cards and publication receipts validate
   against a committed schema (fail-closed), so governance outputs cannot silently drift.

## A4 — code health (1 version)

File-size census against the AGENTS 500–800 line rule; split or waiver each offender;
commit a size-ratchet test. Contract-preserving splits only; report/renderer outputs
byte-identical, proven by existing tests.

## A5 — docs honesty + closeout (1 version)

1. Every capability claim in `docs/` re-verified against the final tree; claims without a
   file/test citation are fixed or deleted. `no-promotion-boundary.md` re-asserted.
2. Produce `docs/aiproj-track-final-evidence.md`: gate-by-gate table (A0–A4), waiver list,
   census numbers, CI links. Request Claude review.

## Capstone tie-in (after A-track closes and the three-repo capstone lands)

The shared four-project threshold requires aiproj artifacts to be *consumed* somewhere,
not only generated. One slice: the Node `readiness:cross` report (capstone C4) validates
one real aiproj artifact — latest publication receipt or release bundle: schema-valid,
digest-stable, `read_only`/no-promotion boundary fields present. Read-only, no execution,
no promotion authority. This is coordinated through the Node session; aiproj's side is
only to guarantee the artifact contract A3.2 already enforces.

## Fail conditions

- Lint/type adoption via repo-wide mechanical sweep in one commit = revert.
- A reproducibility contract test that re-trains instead of re-deriving = wrong; rewrite.
- Coverage or size ratchet loosened = revert.
- Any doc claim upgraded (especially model quality or maturity) without cited evidence = A5 fails.
- Touching the ML capability lane's experiment semantics, cached artifacts, or verdicts = out of scope; stop.

## Claude track review — 2026-07-07 (A0–A5): PASS

- Verified as CI-enforced steps on every push: static analysis gate, scoped type analysis
  gate, honest-measurement gate, artifact schema guard, file size ratchet, the track
  closeout gate, and unit tests with coverage `--fail-under 88.98`; the v1267 closeout
  runs are green on both branch and tag. `docs/aiproj-track-final-evidence.md` keeps the
  no-promotion boundary explicit — the honesty framing is correct.
- Conditions to fully close: (1) commit the untracked
  `docs/stage2-aiproj-operational-brief.md` — it is not part of the repo until committed
  (it stays INACTIVE/gated regardless); (2) optional quick win: every version currently
  triggers CI twice (branch push + tag push) — add a trigger filter to halve CI spend.
- aiproj is the FIRST Stage-1 track complete. Stage-2 remains gated on the program-wide
  capstone; until then the engineering lane takes maintenance-only versions.

## Claude checkpoint review — 2026-07-10 (v1268–v1272): PASS, track fully closed

- Both close conditions verified done: stage2 brief committed (tracked); CI dedupe
  landed at v1268 — one run per version since (v1267 was the last double-run).
- v1269 cut the ruff baseline substantially (baseline file shrank ~4.7k lines) with CI
  green — debt reduction in the correct ratchet direction, not baseline growth.
- Maintenance-only boundary respected; no ML-lane touches. No conditions remain.
  Next review only at the program-wide capstone (C4 consumes one aiproj artifact).
- Update 2026-07-12: the capstone PASSED (C4 validated this repo's registry-listed
  publication receipt). Sanctioned maintenance work while the Java track finishes:
  the bounded elegance program `docs/elegance-hotspot-program-aiproj.md` (≤3 versions,
  engineering lane only, E-A1 commits the pending AGENTS/brief edits + the name-census
  gate).
