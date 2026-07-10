# Stage 2 aiproj Brief — serve a real model artifact, standing eval gate, consumed governance

STATUS: INACTIVE — gated on Stage-1 aiproj A-track PASS + capstone PASS.
Executor: Codex session in `D:\aiproj` (engineering/governance lane; the ML capability
research lane stays separate and untouched — this brief deploys and gates EXISTING
artifacts, it does not run new science). Parent: Node repo
`docs/plans/stage2-operational-reality-program.md` (read-only). Stage-1 A-track gates
(ruff/mypy scope, coverage floor, reproducibility contracts, size ratchet) stay enforced.
Boundary carried over: model quality remains educational; no-promotion boundary intact;
serving an artifact grants it no new authority claim.

## Step 0 — re-grounding (mandatory, first version)

1. Confirm Stage-1 PASS records (A-track final evidence + reviewer sign-off + capstone).
   If absent, STOP.
2. Re-verify: the grokking checkpoint (`.pt`, ~835KB) and its CPU-only inference API
   (v1186 line) still load and reproduce heldout accuracy 0.966 from cache; publication
   receipts validate against the A3.2 schema. These are the artifacts Stage 2 deploys.
3. Read Node `docs/ops/vm-census.md`; the inference service is small (CPU, <1GB) and
   should fit every fallback rung, but the census decides.

## Phase 1 — the inference service (2 versions; the real "AI dev" step)

1. Wrap the existing checkpoint inference API in a minimal HTTP service (FastAPI or
   stdlib — smallest dependency footprint that passes the A-track gates): endpoints
   `GET /healthz`, `GET /model-card` (generated from the checkpoint's own metadata +
   cached eval evidence, honest about task scope: a+b mod 97), `POST /predict`
   (validated input, bounded batch size, deterministic output). No training, no
   fine-tuning, no model mutation at runtime — the service is read-only over a frozen
   artifact, stated in the model card.
2. Contract tests: golden predictions committed (the checkpoint is deterministic —
   assert exact outputs); malformed input → 422 not 500; oversized batch → explicit
   rejection; model file digest checked at startup (wrong/corrupt checkpoint =
   fail-fast, never silent fallback).
3. Package: pinned-deps container or venv bundle, built by CI, digest-recorded, same
   discipline as the other services.

## Phase 2 — deploy + integrate (1–2 versions)

1. Deploy on the VM behind the Node reverse proxy (token auth; localhost bind), systemd/
   compose per census. Log rotation; startup after reboot unattended.
2. Dashboard integration (coordinated with the Node brief): the dashboard shows the
   inference service's health, its model-card summary, and the latest publication-receipt
   validation — aiproj becomes a *consumed* service, not just a validated artifact,
   completing the shared-threshold item at depth.
3. Live probe receipt: a scripted client calls `/predict` through the proxy with a known
   pair and asserts the golden answer.

## Phase 3 — standing eval + supply-chain gates (1–2 versions)

1. Standing eval harness: the cached-artifact eval suite becomes a scheduled CI job —
   re-derives the checkpoint's eval verdicts from cache weekly and fails on ANY drift
   (bit-stable expectations where the artifact is deterministic). This is the regression
   gate any future model work must pass through; it exists BEFORE the next science lands.
2. `pip-audit` (or equivalent) CI gate: fail on new known-vulnerable pins; committed
   baseline for unfixable items, shrink-only, each justified.
3. Load sanity for the service: measured p99 for single predictions and max batch at N
   concurrent clients on the VM; committed as an SLO with a rerunnable script. This is a
   toy model — the point is practicing the discipline of serving + measuring, and the
   numbers must still be real.

## Phase 4 — soak participation + closeout (1 version + soak)

1. During the 14-day soak: the inference service stays up; the Node monitoring loop
   probes `/healthz`; one weekly scripted golden-prediction probe receipt.
2. Closeout: `docs/stage2-aiproj-final-evidence.md` (service contract tests, deploy
   receipts, standing-eval CI links, SLO baseline, soak probes). Request Claude review
   (reviewer calls `/predict` live and re-runs the standing eval from cache).

## Fail conditions

- Any endpoint that mutates the model or triggers training = out of scope, revert.
- Golden predictions regenerated to match changed output (instead of investigating the
  drift) = the standing eval is dead; fail.
- Model card overclaiming (anything beyond "educational demonstration model for modular
  addition, heldout 0.966") = docs-honesty fail.
- Serving deps adopted without passing the A-track lint/type/audit gates = version invalid.
- Capability-lane files (experiments, cached verdicts, decide() logic) touched = stop.
