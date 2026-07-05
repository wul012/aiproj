# MiniGPT Public API Policy

This policy keeps the root `minigpt` package facade small while preserving
legacy exports. It defines which imports should be treated as stable, which
imports are compatibility-only, and which modules should stay internal or
historical.

## Current Facade State

`src/minigpt/__init__.py` is a thin lazy facade:

- `src/minigpt/_root_exports.py` owns the large compatibility export tables.
  It aggregates smaller `_root_*exports*.py` table modules so the facade cleanup
  does not create another monolithic file.
- `__init__.py` imports those tables, exposes `__all__`, and lazy-loads names
  through `__getattr__`.
- Tests still use both direct module imports and broad `from minigpt import ...`
  facade imports.

That facade should be preserved until callers have a migration path. New code
should prefer the owner package imports listed in Tier 1.

### Root Facade Export Budget

The root package facade is now treated as a compatibility budget, not an open
place to add new symbols. The current upper bounds are 80 lines in
`src/minigpt/__init__.py`, 500 lines per `_root_*exports*.py` table module, 278
names in `__all__`, and 308 lazy entries in the root export table. Future
cleanup may shrink these numbers, but a change that grows the root facade must
first update this policy and justify why an owner package import is not enough.

`tests/test_public_api_policy.py` enforces this budget, checks that `__all__`
does not contain duplicate names, and verifies every public `__all__` name is
backed by a lazy root export entry.

The import contract is guarded by focused tests:

- `tests/test_public_api_policy.py` checks Tier 1 stable imports and legacy
  facade compatibility, including the root facade export budget.
- `tests/test_foundation_package_reexports.py` checks `core`, `training`,
  `evaluation`, and `serving` owner-package re-exports.
- `tests/test_evidence_package_reexports.py` checks `reports` and
  `governance` owner-package re-exports.

## API Tiers

### Tier 1: Stable Owner Package Imports

These imports are the preferred public API for active code, tests, and scripts.
The owner packages are the current normalized namespace for new code; the
historical flat modules remain available as compatibility paths.

Core model and tokenizer:

```python
from minigpt.core.model import GPTConfig, MiniGPT
from minigpt.core.tokenizer import CharTokenizer, BPETokenizer, load_tokenizer
from minigpt.core.dataset import load_text, split_token_ids, get_batch
```

Data preparation and training history:

```python
from minigpt.training.data_prep import (
    PreparedDataset,
    SourceFileSummary,
    build_prepared_dataset,
    write_prepared_dataset,
)
from minigpt.training.history import (
    TrainingRecord,
    append_record,
    load_records,
    summarize_records,
    write_loss_curve_svg,
)
```

Evaluation:

```python
from minigpt.evaluation.suite import (
    PromptCase,
    PromptSuite,
    build_eval_suite_report,
    build_prompt_result,
    load_builtin_prompt_suite,
    load_prompt_suite,
)
from minigpt.evaluation.suites import standard_zh_prompt_suite
from minigpt.evaluation.comparison import build_comparison_report
from minigpt.evaluation.prediction import (
    TokenPrediction,
    perplexity_from_loss,
    top_k_predictions,
    write_predictions_svg,
)
```

Serving contracts and generation:

```python
from minigpt.serving.contracts import (
    GenerationRequest,
    GenerationResponse,
    GenerationStreamChunk,
    CheckpointOption,
    InferenceSafetyProfile,
)
from minigpt.serving.generator import MiniGPTGenerator
from minigpt.serving.checkpoints import discover_checkpoint_options
from minigpt.serving.chat import ChatTurn, build_chat_prompt, prepare_chat_prompt
from minigpt.serving.profiles import GenerationProfile, generation_profile_ids
```

Reports and evidence artifacts:

```python
from minigpt.reports.model import build_model_report, write_model_report_svg
from minigpt.reports.cards import build_dataset_card, build_experiment_card
from minigpt.reports.dashboard import build_dashboard_payload, write_dashboard
from minigpt.reports.manifest import build_run_manifest, write_run_manifest_json
from minigpt.reports.artifact_map import build_artifact_map_report
from minigpt.reports.utils import write_output_bundle
```

Governance entrypoints that operate on already-produced evidence can use the
`minigpt.governance` package:

```python
from minigpt.governance.release import build_release_gate, build_release_readiness_dashboard
from minigpt.governance.maturity import build_maturity_summary, build_maturity_narrative
from minigpt.governance.registry import build_run_registry, render_registry_html
```

This package is intentionally limited to active release, maturity, and registry
facades. Route-specific chains such as `randomized_holdout_*`,
`model_capability_*`, and `bounded_objective_*` remain Tier 3 unless a future
refactor promotes a small stable owner-level surface for them.

### Tier 2: Compatibility Flat Module And Facade Imports

These imports may continue to work for existing tests, notebooks, historical
scripts, and compatibility checks, but new code should not add more of them:

```python
from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import CharTokenizer, BPETokenizer, load_tokenizer
from minigpt.dataset import load_text, split_token_ids, get_batch
from minigpt.data_prep import build_prepared_dataset
from minigpt.eval_suite import build_eval_suite_report
from minigpt.prediction import top_k_predictions
from minigpt.server_contracts import GenerationRequest
from minigpt.chat import ChatTurn
from minigpt.generation_profiles import generation_profile_ids
from minigpt.model_report import build_model_report
from minigpt import GPTConfig, MiniGPT
from minigpt import CharTokenizer, BPETokenizer, load_tokenizer
from minigpt import build_eval_suite_report
from minigpt import server
from minigpt import release_gate
```

Flat module imports and facade exports are compatibility surfaces, not proof
that every exported symbol is a stable public API.

Before removing or renaming a facade export:

1. Confirm no active script imports it from `minigpt`.
2. Update tests to import from the owning module.
3. Keep a compatibility alias when the change would break historical docs or
   artifact-generation scripts.
4. Run the focused tests for that owner class.

### Tier 3: Internal, Historical, Or Route-Specific Modules

These modules should not become new public API unless they are intentionally
promoted:

- Long versioned receipt/index/check chains.
- One-off `_artifacts.py` writers.
- Route-specific governance modules such as `randomized_holdout_*`,
  `model_capability_*`, and `bounded_objective_*`.
- Research modules such as `grok_*`, `induction_*`, `lora_*`, `sft_*`, `dpo_*`,
  and `distill_*`.

Callers should prefer scripts, reports, manifests, or documented stable module
imports instead of reaching into those modules directly.

## Script Entry Points

CLI scripts remain user-facing compatibility wrappers. The script path can stay
stable even when reusable implementation code moves into a better package.

Important active scripts include:

```text
scripts/train.py
scripts/prepare_dataset.py
scripts/eval_suite.py
scripts/evaluate.py
scripts/chat.py
scripts/inspect_model.py
scripts/inspect_tokenizer.py
scripts/build_dashboard.py
```

New scripts should be thin wrappers over package modules. Avoid placing large
business logic only in `scripts/`.

Active scripts should import from the owner packages introduced above. Core
workflow scripts should use `minigpt.core.*`, `minigpt.training.*`,
`minigpt.evaluation.*`, and `minigpt.serving.*`; report and governance scripts
should use `minigpt.reports.*` and `minigpt.governance.*`.
`tests/test_script_import_boundaries.py` guards the first migrated script set.

## Refactor Policy

Use this order when cleaning `minigpt.__init__`:

1. Document the stable import path in this file.
2. Update active callers to use the stable module import.
3. Add or keep a compatibility export if historical callers still need it.
4. Only then shrink `__all__` or the root export table.

Do not remove facade exports in bulk. A safe cleanup is a small batch with a
clear owner class, focused tests, and a short migration note.

## New Code Rule

For new code:

- Import model/data primitives from `minigpt.core.*`.
- Import training dataset, history, runtime, and training helpers from
  `minigpt.training.*`.
- Import evaluation suites, comparisons, and generation-quality helpers from
  `minigpt.evaluation.*`.
- Import server request/response objects and generation helpers from
  `minigpt.serving.*`.
- Import report builders from `minigpt.reports.*`.
- Import release, maturity, and registry governance helpers from
  `minigpt.governance.*`.
- Avoid `from minigpt import ...` unless preserving an existing compatibility
  test.
- Avoid new imports from flat modules such as `minigpt.model`,
  `minigpt.prediction`, `minigpt.chat`, `minigpt.generation_profiles`,
  `minigpt.server_contracts`, or `minigpt.model_report` unless the file is a
  compatibility wrapper or a focused compatibility test.
- Do not add a route-specific governance symbol to `minigpt.__init__` unless it
  is intentionally promoted to stable public API.
- v1255 intentionally promotes
  `build_model_capability_route_promotion_release_readiness_summary` and
  `write_model_capability_route_promotion_release_readiness_summary_outputs`
  as stable route-promotion governance API, raising the root facade all-export
  budget from 278 to 280 and the lazy-export budget from 308 to 310.
- v1256 intentionally promotes the matching
  `build_model_capability_route_promotion_release_readiness_summary_check` and
  `write_model_capability_route_promotion_release_readiness_summary_check_outputs`
  contract-check API, raising the root facade all-export budget from 280 to 282
  and the lazy-export budget from 310 to 312.
- v1257 intentionally promotes
  `build_model_capability_route_promotion_release_readiness_downstream_receipt`
  and
  `write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs`
  as the stable downstream receipt API for checked route-promotion release
  readiness evidence, raising the root facade all-export budget from 282 to
  284 and the lazy-export budget from 312 to 314.
- v1258 intentionally promotes
  `build_model_capability_route_promotion_release_readiness_receipt_index`
  and
  `write_model_capability_route_promotion_release_readiness_receipt_index_outputs`
  as the stable lookup index API for checked route-promotion release readiness
  downstream receipts, raising the root facade all-export budget from 284 to
  286 and the lazy-export budget from 314 to 316.
- v1259 intentionally promotes
  `build_model_capability_route_promotion_release_readiness_receipt_index_review`
  and
  `write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs`
  as the stable review API for checked route-promotion release readiness
  receipt indexes, raising the root facade all-export budget from 286 to 288
  and the lazy-export budget from 316 to 318.
