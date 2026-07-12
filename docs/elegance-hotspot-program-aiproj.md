# aiproj Elegance Hotspot Program (E-track, 2–3 versions, bounded)

Executor: Codex session in `D:\aiproj` (engineering/governance lane ONLY — the ML
capability lane's experiments, cached artifacts, and verdicts are out of scope, as
always). Authorized 2026-07-12 as sanctioned maintenance while the Java track finishes.

Model: the Java maintainability program — census, shrink-only baseline, top-N, hard
stop. At most 3 versions; this is expected to be the LIGHTEST of the four programs
(the repo already carries a size ratchet, ruff/mypy gates, and consolidated helpers).

Binding rules: AGENTS.md Elegance Gates section; existing gates unchanged (coverage
floor, size ratchet, schema guard, honest-measurement gate, no ML-lane touches).

Execution status: E-A1 is implemented as v1273 with a 7,515-digest shrink-only
baseline and zero new violations. E-A2 pin analysis remains pending.

## E-A1 — commit the mechanical gate (1 version, first)

1. Sweep the reviewer's uncommitted AGENTS.md Elegance Gates section (and the
   production-excellence brief's pending review edits) into this version.
2. Extend the existing static-analysis tooling with a name census over `src/` and
   `scripts/`: filenames + public identifiers over 40 chars → shrink-only committed
   baseline + CI step failing on new violations (same adoption recipe as the ruff
   baseline).
3. Record baseline numbers in the version doc.

## E-A2 — top-N remediation (1 version, only if the census justifies it)

1. Top 5 name offenders not pinned by any schema, artifact path, or registry entry:
   extract the concept, rename, update references; full pytest suite green.
   PIN-PROTECTED (off limits): anything referenced by
   `docs/artifact-schema-guard-registry.json`, publication receipts, cached run
   artifacts, or decide() contract paths.
2. If the census shows a surviving duplication family in scripts/, consolidate via the
   established shared-module pattern (report_check_common precedent).
3. If the census shows fewer than 5 meaningful offenders, say so and skip to E-A3 —
   an honest "little debt here" is a valid finding, not a failure.

## E-A3 — close (1 version, may merge into E-A2 if small)

Final census, baseline pinned, one-page summary. Request Claude review.

## Fail conditions

- Any ML-lane experiment, cached artifact, verdict, or schema-registry-referenced path
  touched = out of scope, stop.
- Coverage or any existing ratchet loosened = revert.
- Baseline loosened = revert.
- Inventing remediation work the census does not justify (gold-plating) = fail; the
  program budget is a maximum, not a quota.
