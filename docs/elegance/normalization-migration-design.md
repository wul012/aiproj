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

## 6. Honest expectation

Even a complete `core` migration moves `flat_dir_file_count` by 5 of 1,355.
The score axis this feeds ("navigating the repo", 5/10) only improves
materially once the large generated families are dealt with — and the
cheapest honest lever there is the archive decision in step 4, not migration.
Reaching 9/10 remains a multi-version program; nothing in this pilot changes
that estimate.
