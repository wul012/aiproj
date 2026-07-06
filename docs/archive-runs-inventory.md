# Archive And Runs Inventory

This page records the A0 archive-growth inventory rule for aiproj. It is a
warning-only census, not a relocation policy.

## Purpose

The project has path-stable evidence archives:

```text
a/ b/ c/ d/ e/ f/
```

Those directories are historical evidence roots. They must be measured, indexed,
and budgeted, but not moved during production-excellence cleanup. The same rule
applies to `runs/`: it is generated local evidence, and the inventory tracks its
growth so large temporary outputs are visible before they become hard to manage.

## Command

```powershell
python -B scripts/check_archive_runs_inventory.py --out-dir runs/archive-runs-inventory --force
```

The script is stdlib-only and writes:

- `archive_runs_inventory.json`
- `archive_runs_inventory.csv`
- `archive_runs_inventory.txt`
- `archive_runs_inventory.md`
- `archive_runs_inventory.html`

The script exits `0` even when a warning budget is exceeded. That is deliberate:
A0 establishes a baseline. Later tracks may ratchet individual budgets into
failing checks only after the baseline and waiver policy are written.

## Warning Budgets

Current defaults:

- archive total warning budget: `512 MB`
- single archive-root warning budget: `300 MB`
- `runs/` warning budget: `64 MB`

Warnings are reviewer-visible in JSON/Markdown/HTML output, but they do not move
or delete files.

## A0 Baseline

The first committed A0 run is archived under `f/1260` and summarized in
`docs/aiproj-track-a0-census.md`.

The baseline decision was `archive_runs_inventory_recorded`, with no warning
rows. The largest archive root was `e/` at about `224.7105 MB`; `runs/` was about
`11.349 MB`.
