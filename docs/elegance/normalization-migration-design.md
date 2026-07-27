# Normalization Migration — Mechanism Proven, Constraint Found (v1307)

The elegance closeout (`program-closeout-v1300.md`) named this the dominant
remaining term for reaching 9/10: `flat_dir_file_count` is 1,355 and the
"navigating the repo" sub-score is the lowest at 5/10. This document records
what a v1307 pilot established, and what it ruled out. The pilot was applied,
measured, and **reverted**; the repo is unchanged at v1306.

## 1. The mechanism works, and is measurable

Owner packages (`core`, `training`, `evaluation`, `serving`, `reports`,
`governance`) are today **pure facades**. `minigpt/core/model.py` is a 4-line
re-export, and the package docstring states the intent plainly: *"The
implementation still lives in the historical flat modules. This package
provides a migration target before the physical module move."*

That is why the flat count has never moved: while every submodule is a
facade, the flat module remains the only home for the code.

Migration = move the implementation into the owner package, and leave a
`sys.modules`-forwarding shim at the flat path. The elegance ratchet excludes
shims from `flat_dir_file_count`, so the metric drops by exactly the number
of modules migrated, while `minigpt.model is minigpt.core.model` still holds.

**Measured in the pilot: 1,355 → 1,351** after migrating four `core`
primitives (`tokenizer`, `dataset`, `history`, `rope`). Architecture tests,
shim identity tests, static and type gates all passed at that point.

## 2. The constraint: a package cannot be half-migrated

The pilot then failed on a circular import, and the cause is structural, not
incidental:

```
flat model.py  ->  imports minigpt.rope   (now a shim)
     shim      ->  imports minigpt.core   (package __init__ runs)
core/__init__  ->  imports minigpt.core.model  (still a FACADE)
core/model.py  ->  imports minigpt.model   <-- partially initialized
```

The owner `__init__` eagerly wires every submodule. So the moment one
submodule is migrated and any flat module imports it, the un-migrated facades
in the same package point back into the flat namespace mid-initialization.

**The migration unit is therefore the whole owner package, atomically.**

## 3. What that costs for `core`, the smallest package

Migrating `core` as a unit requires `model.py` to move too, and it is 299
lines against the owner packages' 220-line cap. So the true first step is
**splitting `model.py`**, and that is not a mechanical job:

- it is the transformer implementation itself, adjacent to the science lane;
- `GPTConfig` / `MiniGPT` class identities may be reachable from saved
  checkpoints (the v1185 canonical grok checkpoint and its loader), so moving
  classes between modules risks breaking artifacts that must stay loadable.
  This needs verifying against the shipped `.pt` before any split.

## 4. Contract change required (and its compensating strictness)

`tests/test_architecture_boundaries.py` currently asserts owner-package
submodules are facade-only — any `FunctionDef` is reported as *"contains
implementation statement"*. Completing the migration necessarily retires that
rule, which is the intended end of the "transitional" phase the test names.

It should not be retired for free. The pilot's replacement kept the guard set
at least as strong:

- facade-shape rules continue to apply to modules that ARE facades
  (detected by shape, not by location);
- implementation submodules stay bound by the unchanged **220-line cap** and
  the unchanged **owner layering prohibitions**;
- a new rule rejects the in-between state: an implementation submodule may
  not import from the flat namespace it was migrated out of, which is what
  would make a move cosmetic.

## 5. Recommended order

1. Verify checkpoint loading does not depend on `minigpt.model` class paths.
2. Split `model.py` into ≤220-line modules (own version, careful review).
3. Migrate `core` atomically: all five primitives + shims, contract change
   as in §4. Expected `flat_dir_file_count` 1,355 → 1,350.
4. Repeat per owner package, largest last. The flat corpus is ~1,355 modules
   but ~500 of them are generated per-version governance artifacts; whether
   those should be migrated or **archived out of `src/`** is a product
   decision worth taking before mass migration, since archiving would move
   the metric far faster than restructuring.

## 5b. Measured cost of the remaining packages (added after v1308)

v1308 migrated `core` and `flat_dir_file_count` moved 1,355 → 1,350. Applying
the eligibility rules to the other five packages shows **every one is
currently blocked**, and why: the migration unit is not just "the package"
but **the package's transitive flat dependency closure**, because an
implementation submodule may not import an un-migrated flat module.

`core` was migratable only because it is the leaf of the dependency graph.

| owner | closure | lines | modules over 220 | extra modules from splits |
|---|---:|---:|---:|---:|
| training | 6 | 964 | 1 | ~2 |
| evaluation | 9 | 2,679 | 6 | ~7 |
| serving | 14 | 2,906 | 6 | ~7 |
| reports | 13 | 3,626 | 9 | ~10 |
| governance | 43 | 10,739 | 23 | ~25 |

**Totals: 85 flat modules, ~20,900 lines, ~45 splits.**

### What that buys, stated plainly

Migrating **all five remaining packages** would take
`flat_dir_file_count` from 1,350 to roughly **1,265** — about 6% of the flat
corpus, for ~45 careful module splits of live production code.

The reason is structural: the ~1,200 modules that dominate the flat namespace
are **not faced by any owner package at all**. They are the generated
per-version governance artifacts (`receipt_chain_*`, `packet_chain_*`,
`model_capability_*`, …). No amount of owner-package migration touches them.

### Revised recommendation

Owner-package migration is **not** the path to a materially better
"navigating the repo" score. It is worth doing incrementally for the
packages that are cheap (`training` next, at 6 modules and one split), but it
should not be sold as the route to 9/10.

The decision that actually moves this axis is what to do with the ~1,200
generated artifact modules: **archive them out of `src/`** (they are records
of completed versions, not code under maintenance) versus keep and migrate
them. That is a product decision about what belongs in the source tree, and
it is worth taking before any further migration work is funded.

## 5c. The archive question, made decidable (added after v1309)

The ~1,000 generated per-version modules dominate the flat namespace and no
owner package faces them. Before anything can be archived, one question has
to be answered with evidence rather than intuition: **are they inert records,
or load-bearing infrastructure?**

Measured by consumer analysis — a module counts as inert when nothing outside
its own family imports it (its own test, its own `build_/check_/review_`
script and its family siblings do not count as outside):

| family | modules | inert | load-bearing |
|---|---:|---:|---:|
| model_capability | 483 | 425 | 58 |
| receipt_chain | 192 | 94 | 98 |
| randomized_holdout | 145 | 130 | 15 |
| bounded_objective | 93 | 66 | 27 |
| packet_chain | 38 | 16 | 22 |
| registry_ack | 24 | 22 | 2 |
| ack_bundle | 17 | 12 | 5 |
| packet_index | 6 | 0 | 6 |
| **total** | **998** | **765** | **233** |

**765 of 998 are inert.** They are closed records of completed versions: the
module, its script and its test refer only to each other.

### But the unit is a family cluster, not a module

233 modules are genuinely load-bearing, and the dependencies cross family
lines (`ack_bundle_packet_index` is imported by `registry_ack_review`, which
couples those two families). So the archivable unit is a set of families
closed under cross-family dependency, moved with their scripts and tests
together — the same atomicity lesson as v1307/v1308, one level up.

### Why this is not an engineering decision

Archiving on this scale would take `flat_dir_file_count` from 1,350 to
roughly **585** — an order of magnitude more than every owner-package
migration combined (which buys ~85). It would also remove those modules'
tests from the suite, which moves the coverage denominator, and shrink the
name-budget and duplication baselines substantially.

That is not a refactor; it changes what the project **is**. These modules are
the accumulated governance record of ~1,000 versions of deliberate work. The
engineering evidence says they are archivable; whether they *should* be
archived is the author's call, and it should be made explicitly rather than
arrived at as a side effect of chasing a score.

**Recommendation:** take this decision before funding further migration work.
If the answer is "archive", the flat namespace problem is largely solved in
one deliberate move. If the answer is "keep", then `flat_dir_file_count` is
measuring something the project has consciously chosen, the "navigating the
repo" sub-score should be re-framed to exclude generated records, and the
9/10 target should be restated against a corpus that excludes them.

## 5d. Executing the archive — verified recipe and the one open question

The archive was executed and reverted three times on 2026-07-25. It works;
what follows is the exact recipe, including the two mistakes that cost a run
each, so the next attempt is a single pass.

### The closure must be seeded with non-import anchors

A fixpoint over Python imports is **not sufficient**. Some consumers never
import: CI names scripts by path in `ci.yml`, and gate baselines name paths
in JSON. A set can be perfectly closed under imports and still contain live
infrastructure. The first run swept in
`model_capability_honest_measurement` — a **CI gate** — because its name
begins with `model_capability`, and nothing *imported* it.

Seed the "outside" set before iterating:

1. every `scripts/*.py` named in `.github/workflows/ci.yml`;
2. every path in `docs/static-analysis/ruff-baseline.json` → `strict_paths`;
3. for each anchored `check_/run_/build_/…` script, the module it wraps;
4. **every path in the honest-measurement registry's
   `contract_test_modules`** (and each family's source artifacts). The gate
   reads these from a registry, not a hardcoded list — see
   `model_capability_honest_measurement.py:255,313,321`.

Then run the fixpoint **to proven convergence** — assert it, do not cap the
iteration count. An early run stopped at a 50-iteration cap while still
evicting and was not closed.

### Measured results with steps 1–3 applied

> **Superseded by §5e.** The numbers below came from a set that was **not
> sound**: it archived a live gate's own test, and it archived modules a live
> lazy-export registry loads by name. They are kept here only so the
> correction is legible. The sound figure is **1,350 → 918**, not 724.

| | |
|---|---|
| closed set | 626 src + 456 scripts + 408 tests = 1,490 files |
| `flat_dir_file_count` | 1,350 → ~~724~~ (unsound) |
| `dup_def_stock` | 102 → ~~65~~ (unsound) |
| unresolvable imports | 0 |
| structural tests | pass (architecture, root hygiene, import resolution) |
| `static_analysis`, `type_analysis` | **pass** |

### The open question — deliberately not resolved by an engineer

With steps 1–3, two gates still fail:
`check_model_capability_honest_measurement` (7 checks) and
`normalization_guard`. Both report the same thing:

> **Honest measurement contract is missing or widened.**

They fail because the archive removes the **contract test modules** that
enforce the project's honest-measurement guarantees. That is the gate working
as designed, not staleness. Rebasing its inventory would make the sweep green
by restating what the project asserts about its own measurement honesty —
which is editing an expectation to make the work pass.

Step 4 above is the resolution that costs nothing: anchor those contract
tests and their subjects so they stay live, and archive the remainder. The
win lands somewhat below 724 and **no contract is weakened**. Take that
route unless the author decides, explicitly and on the record, what those
contracts should assert once the artifacts are archived.

### Note

`ruff format --check src scripts` reports ~1,229 files would be reformatted.
That is pre-existing and expected here; only `strict_paths` are format
enforced. It is not caused by the archive and must not be "fixed" as part of
it.

## 5e. The archive is blocked by a coverage subsidy (v1312)

Executing §5d found three more bugs in the closure, corrected the win
downward, and then hit a blocker that is not mechanical at all.

### Three further consumer classes the fixpoint could not see

| # | anchor class | what it missed |
|---|---|---|
| 5 | `_normalization_guard.FOCUSED_TEST_MODULES` | 25 test modules named as strings |
| 6 | **test ↔ subject symmetry** | archived `test_model_capability_honest_measurement.py` while keeping the gate it tests — dropping a guard on LIVE code |
| 7 | **whole-string module identity** | `_root_lazy_exports_*.py` maps names to modules loaded on demand |

Class 6 is not a *reference* at all, it is a **relation**: a module and its
test must move together, or the archive silently retires a live guard. Assert
it both ways — no archived test may have a live subject, and no archived
module may have a live test.

Class 7 needs care in **both** directions. Splitting strings into tokens
evicted 343 modules on a false signal: `"model_capability_ladder.json"` is an
artifact a module *writes*, not a consumer of it. Ignoring strings entirely
archives modules a live registry loads by name. Only **whole-string module
identity** is sound.

Each correction moved the win *against* the archive — 724 → 735 → 833 → 918 —
because each was a bug fixed, not a concession. Corroborating signal that the
corrected set is the sound one: under it, **zero** of the 134 entries in
`test_script_bootstrap.py`'s contract need editing, where the earlier set
required deleting 9. A closure that does not force you to touch a live
contract is evidence the closure is right.

### Sound measured result

| | |
|---|---|
| closed set | 432 src + 325 scripts + 215 tests = **972 files** |
| `flat_dir_file_count` | 1,350 → **918** (−32%) |
| `dup_def_stock` | 102 → **77** |
| elegance ratchet | **pass** on all four metrics |
| surviving suite | **2,584 tests, 0 failures, 0 errors, 0 import failures** |
| surviving files naming an archived file | 500 — **all documentation prose**, no code |

### The blocker: the coverage floor is subsidised by the records

Post-archive line coverage is **87.51%** against a `--fail-under` of
**88.98**. It is not a scoping bug: only 8 live modules lose any coverage at
all, 75 lines total (0.1 points). Splitting the *same* cached full-suite run
into the two populations shows the real cause:

| population | coverage | share of corpus |
|---|---|---|
| generated records | **93.26%** | 29.0% |
| maintained code | **87.61%** | 71.0% |
| headline (both) | 89.25% | floor 88.98 |

**The generated records are 5.65 points better covered than the code under
maintenance, and they are 29% of the corpus.** The project meets its coverage
floor partly because of them. Archiving does not *lower* coverage — it stops
the records from concealing it, and what they conceal is that maintained code
sits 1.37 points below the floor it appears to satisfy.

### What this costs, and the one thing that must not be done

Holding the floor honestly after the archive requires **+974 covered lines**
on maintained code. That debt is real and pre-existing: 62 live modules sit
under 60% coverage, concentrated in the science and training modules that are
expensive to test. It is a program, not a session.

Lowering `fail_under` to fit the new corpus would make the archive pass by
restating what the project claims about its own test coverage. Ratchets only
tighten. **Do not do it** — it is the same move as rebasing the
honest-measurement inventory in §5d, and it is refused for the same reason.

**Status:** the archive is mechanically ready and proven sound; it is blocked
on a priced coverage gap, not on a filing decision. The finding is worth more
than the move: a metric that reads 89.25% describes a corpus that is 29%
closed records, and the number for the code anyone actually maintains
is 87.61%.

## 6. Honest expectation

Even a complete `core` migration moves `flat_dir_file_count` by 5 of 1,355.
The score axis this feeds ("navigating the repo", 5/10) only improves
materially once the large generated families are dealt with — and the
cheapest honest lever there is the archive decision in step 4, not migration.
Reaching 9/10 remains a multi-version program; nothing in this pilot changes
that estimate.

§5e prices that lever exactly: the archive is worth 1,350 → 918 and is proven
sound, but it is gated behind **+974 covered lines** of pre-existing test debt
on maintained code. The generated records were paying that bill.
