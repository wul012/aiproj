# Elegance Program Closeout (v1290–v1300)

Baseline question (v1289): "Whole-codebase elegance: about /10" → scored **6/10**.
Target set by the user: "+~3 points to about 9". This report is the honest
re-score with reproducible evidence. Every number below regenerates from the
repo state at tag `v1300.0.0` with the commands given.

## Evidence matrix: before → after

| Axis | v1289 (score-6 evidence) | v1300 | Reproduce with |
|---|---|---|---|
| File naming | 282 stems >120 chars, max 202 | **0 stems >120, max 120**; new long names refused in CI | `python -B scripts/check_elegance_ratchet.py` |
| Static debt | 271 baselined ruff issues | **0**; baseline pinned at zero, strict-format paths | `python -B scripts/check_static_analysis.py` |
| Duplication (helpers) | `_median` copy-pasted 12× | single source `grok_arc_common`, identity-tested | `tests/test_grok_arc_common_v1290.py` |
| Duplication (stock) | unmeasured | measured **227** dup bodies, frozen tighten-only (recursive scan, move-proof) | elegance ratchet `dup_def_stock` |
| Namespace | 1,355 flat modules | 1,355 (unchanged **by design**; see "not delivered") | elegance ratchet `flat_dir_file_count` |
| Inner symbols | 7,515 over-budget names baselined | 7,515 (rebased zero-net across renames, never resolved) | `python -B scripts/check_name_budget.py` |
| Compat surface | n/a | 282 module shims + 78 script shims, every one identity-tested (`old is new`) in both runners | `tests/test_forwarding_shims_v1298.py` |
| Coverage | ratchet floor 88.98 | 89.29, gap 0.0, shims inside the net | `python -B scripts/run_test_coverage.py --fail-under 88.98` |
| Stem distribution | dominated by machine-generated chains | ≤40: 590 · 41–80: 503 · 81–120: 262 | scratch script over non-shim `glob("*.py")` |

Program ledger: 10 versions (v1290–v1299), 282 long names cleared in 5 batches
(6+30+146+43+57), zero behavior change, zero compat breaks, name-budget stock
constant at 7,515 through every rebase (provable-neutrality tool, v1295).
Seven hidden-coupling classes catalogued; the last two (script shims must
never be re-renamed; alphabetical re-sort exposes import-order-dependent
tests) found and fixed inside the final batch.

## Re-score: 6 → **7.5 / 10**

Sub-scores (artifact elegance, not process):

- **Reading a file**: 6.5 — imports clean, filenames rational, but ~half the
  corpus still carries 80–120-char inner symbol names (the 7,515 stock).
- **Navigating the repo**: 5 — 1,355 flat modules, 6 owner packages only.
- **Consistency/idiom**: 8 — format-clean, strict paths, re-exports explicit.
- **Duplication**: 5.5 — 227 dup bodies (~17% of modules touched).
- **Safety-net elegance**: 9 — tighten-only ratchets on every measured axis;
  the compat surface is executable and named in failures.
- **Science-arc code**: 8.5 — unchanged; still the repo's best stratum.

## Why not 9, plainly

The original projection (8.5–9) assumed the full ladder including
sub-packaging. Stage 5 (v1294) discovered the owner-package architecture
contract **correctly blocks** wholesale sub-packaging of verbatim historical
modules (facade-only `__init__`, 220-line cap, structural rules) — that work
belongs to the normalization lane, which rebuilds modules to contract rather
than relocating them. The program honestly narrowed to naming surgery +
shims + ratchets and said so at the time. The remaining ~1.5 points have a
named price, none of it cheap:

1. **Normalization-lane migration** of the flat corpus into owner packages
   (`flat_dir_file_count` 1,355 → low hundreds) — the dominant term.
2. **Symbol-level renames** resolving the 7,515 name-budget stock (an
   API-breaking program needing its own deprecation machinery).
3. **Dup burn-down** `dup_def_stock` 227 → double digits.

## Consciously skipped

- Splitting `tests/test_promoted_training_scale_seed_handoff.py` (1,309
  lines): the file-size ratchet governs it, it is one coherent contract
  family, and a split adds import surface for zero metric or readability
  gain. Skipped on judgment, recorded here.

## What CI now refuses (the durable part)

Any new >120-char stem, any flat-directory growth, any max-stem regression,
any new duplicate function body, any new static issue, any name-budget
growth, any file-size growth past baseline, any coverage drop below 88.98,
any silent shim removal (count floor + per-shim identity). The score can
only be defended upward from here.
