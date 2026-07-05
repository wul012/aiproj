# MiniGPT Module Inventory

This inventory turns the architecture map into a maintenance checklist. It is
not a complete listing of every historical file. It identifies the active
owners, high-volume buckets, and refactor posture for the current project.

Update this file when a module is moved, retired, or promoted into a stable
subsystem.

## Inventory Rules

- Assign every active module one owner class from
  [Architecture map](architecture-map.md).
- Prefer explicit module paths over broad imports from `minigpt.__init__`.
- Use the [Public API policy](public-api.md) before adding, removing, or
  migrating facade exports.
- Keep `src/minigpt/__init__.py` as a thin root facade. Compatibility export
  tables live in `_root_exports.py` and smaller `_root_*exports*.py` modules;
  they are API routing tables, not feature implementation modules.
- Treat very long version-chain names as historical evidence unless a current
  script or test proves they are still active.
- Preserve behavior before moving files. A module can be classified before it is
  physically relocated.

## Normalized Owner Packages

These package directories are the current normalized import roots under
`src/minigpt`. They are compatibility packages over historical flat modules
today, but new active scripts and tests should prefer these owner namespaces.
`tests/test_architecture_boundaries.py` recursively scans these package trees
so new submodules inherit the same layer rules instead of bypassing them.

| Package | Owner class | Primary role | Boundary posture |
|---|---|---|---|
| `minigpt.core` | Core Owner | Model, tokenizer, dataset, history, and RoPE primitives. | Inner layer; must not import training, serving, reports, or governance. |
| `minigpt.training` | Training Owner | Dataset preparation, quality checks, history, runtime, and LM training helpers. | May depend on core primitives; must not depend on serving or governance. |
| `minigpt.evaluation` | Evaluation Owner | Prompt suites, run comparisons, suite design, and generation-quality summaries. | Reads core outputs; must not depend on serving or governance. |
| `minigpt.serving` | Serving Owner | Request/response contracts, checkpoint discovery, generation, routes, and local server assembly. | May depend on core model/tokenizer; must not import release-governance chains. |
| `minigpt.reports` | Reports Owner | Model reports, cards, dashboards, manifests, artifact maps, and shared report utilities. | Converts evidence into artifacts; must not make release decisions. |
| `minigpt.governance` | Governance Owner | Release gates, readiness, maturity, drift contracts, and registry facades. | Outer layer; may consume evidence but should not depend back on core/training/evaluation/serving runtime packages. |

## Current Count Snapshot

Approximate counts from `src/minigpt`:

| Owner class | Count | Current interpretation |
|---|---:|---|
| `governance` / capability chains | 1072 | Main source of package sprawl; mostly outer-layer evidence and decision flows. |
| `reports-governance` | 48 | Stable reports, cards, dashboards, registries, release summaries. |
| `research` | 48 | Versioned experiments around adaptation, decoding, interpretability, and training behavior. |
| `evaluation` | 21 | Prompt suites, comparisons, benchmark summaries, generation quality. |
| `core` | 11 | The small GPT learning path. This is the inner layer to protect. |
| `serving` | 9 | Local generation and HTTP/API wrapper modules. |
| `other` | 58 | Needs classification before future moves. |

High-volume governance prefixes:

| Prefix | Count | Posture |
|---|---:|---|
| `randomized_holdout_publication*` | 404 | Freeze by default; identify active readers before touching. |
| `model_capability_required_term_pair*` | 284 | Candidate for future package-level grouping and shared helpers. |
| `model_capability_route_promotion*` | 134 | Keep as governance; shorten future module names. |
| `bounded_objective_loss_signal_bridge*` | 92 | Keep as capability-governance until active flow is isolated. |
| `promoted_training*` | 50 | Governance/training handoff boundary; keep decision/review contract facades, seed/handoff summary builders, next-plan helpers, receipt automation checks, receipt sections, contract/check rendering, seed/handoff/comparison CSV field and row models, seed/handoff HTML stats, CSV/report rendering, assurance rendering, and artifact rendering split by role. |
| `training_scale*` | 19 | Training governance, not model core; keep promotion guards, run-decision summary fields, and artifact rendering split by role. |
| `release*` | 17 | Release/readiness governance. |
| `target_hidden*` | 16 | Holdout/governance experiments. |
| `registry*` | 14 | Registry/report surface with data, ranking, render row, and format helpers split by role. |

## Core Owner

These modules are the inner learning path. They should stay small, stable, and
free of release or receipt dependencies.

| Module | Role | Future target |
|---|---|---|
| `model.py` | `GPTConfig`, attention blocks, `MiniGPT`, generation primitives. | `minigpt.core.model` compatibility path exists. |
| `tokenizer.py` | Character and BPE tokenizers plus load/save. | `minigpt.core.tokenizer` compatibility path exists. |
| `dataset.py` | Text loading, train/validation split, batch sampling. | `minigpt.core.dataset` compatibility path exists. |
| `data_prep.py` | Source discovery, normalization, prepared corpus reports. | `minigpt.training.data_prep` or `minigpt.data.prep` |
| `data_quality.py` | Dataset quality checks and SVG/JSON quality reports. | `minigpt.data.quality` |
| `history.py` | Training record JSONL, summaries, loss curve rendering. | `minigpt.core.history` compatibility path exists; later may move under training. |
| `rope.py` | Rotary position embedding helpers. | `minigpt.core.rope` compatibility path exists. |
| `sampling.py` | Sampling support helpers. | `minigpt.core.sampling` |
| `generation_profiles.py` | Named generation profile contracts. | `minigpt.serving.profiles` compatibility path exists. |
| `chat.py` | Chat prompt structure and trimming. | `minigpt.serving.chat` compatibility path exists. |
| `completion_masking.py` | Completion-target masking helpers. | `minigpt.training.objectives` |

## Training Owner

Training modules produce checkpoints, tokenizer files, metrics, manifests, or
run evidence.

| Module or script | Role | Posture |
|---|---|---|
| `scripts/train.py` | Main checkpoint-producing training entrypoint. | Keep stable; later move reusable logic out of script. |
| `scripts/prepare_dataset.py` | Prepared corpus entrypoint. | Keep as CLI wrapper over data-prep modules. |
| `data_prep.py` | Prepared corpus and dataset version artifacts. | `minigpt.training.data_prep` compatibility path exists. |
| `data_quality.py` | Dataset quality checks. | `minigpt.training.data_quality` compatibility path exists. |
| `history.py` | Training metrics history and loss curve helpers. | `minigpt.training.history` compatibility path exists. |
| `lm_training.py` | Reusable language-model training helpers. | `minigpt.training.lm` compatibility path exists. |
| `script_runtime.py` | Shared CLI device and seeding helpers. | `minigpt.training.runtime` compatibility path exists. |
| `script_setup.py` | Shared single-corpus setup helper. | `minigpt.training.corpus_setup` compatibility path exists. |
| `training_run_evidence*` | Evidence wrappers around training outputs. | Reports/training boundary. |
| `training_portfolio*` | End-to-end training portfolio plan, runner, batch, comparison, and artifacts. | Keep plan construction, batch configuration, execution, artifact rendering, batch orchestration, and comparison review split across focused modules. |
| `training_scale*` | Scale plan, gate, handoff, promotion, workflow. | Governance around training, not core model code; keep promotion assembly, guard checks, run-decision summary fields, and artifact rendering split by role. |

## Evaluation Owner

Evaluation modules read checkpoints or generated outputs and summarize behavior.

| Module | Role | Posture |
|---|---|---|
| `eval_suite.py` | Prompt case/result/report contract. | `minigpt.evaluation.suite` compatibility path exists. |
| `eval_suites.py` | Built-in suite registry. | `minigpt.evaluation.suites` compatibility path exists. |
| `eval_suite_design.py` | Prompt suite design summary. | `minigpt.evaluation.design` compatibility path exists. |
| `heldout_eval.py` | Heldout evaluation helpers. | Evaluation, not governance by itself. |
| `generation_quality.py` | Generation quality report logic. | `minigpt.evaluation.generation_quality` compatibility path exists. |
| `comparison.py` and `comparison_artifacts.py` | Run comparison reports. | `minigpt.evaluation.comparison` compatibility path exists. |
| `prediction.py` | Next-token prediction inspection and perplexity helpers. | `minigpt.evaluation.prediction` compatibility path exists. |
| `benchmark_*` | Benchmark scorecards, history, decisions. | Evaluation feeding governance decisions; scorecard component, decision logic, and decision policy modules keep scoring rules separate from public facades. |

## Serving Owner

Serving modules should depend on core model, tokenizer, and server contracts,
but not on release-governance chains.

| Module | Role | Posture |
|---|---|---|
| `server_generator.py` | Loads checkpoint/tokenizer and generates responses. | `minigpt.serving.generator` compatibility path exists. |
| `server_contracts.py` | Request/response models. | `minigpt.serving.contracts` compatibility path exists. |
| `server_routes.py` | Route definitions. | `minigpt.serving.routes` compatibility path exists. |
| `server_post_routes.py` | POST route handling. | `minigpt.serving.post_routes` compatibility path exists. |
| `server_checkpoints.py` | Checkpoint discovery. | `minigpt.serving.checkpoints` compatibility path exists. |
| `server_request_history.py` | Request history storage. | `minigpt.serving.request_history` compatibility path exists. |
| `server_logging.py` | Logging support. | `minigpt.serving.logging` compatibility path exists. |
| `server_http.py` | HTTP wrapper. | `minigpt.serving.http` compatibility path exists. |
| `server.py` | Server assembly. | Serving entrypoint. |

## Reports Owner

Reports transform data into JSON, HTML, SVG, Markdown, CSV, or dashboard
payloads. They should share writer/rendering helpers over time.

| Bucket | Examples | Refactor signal |
|---|---|---|
| Model reports and cards | `model_report.py`, `dataset_card*`, `experiment_card*`, `model_card*` | `minigpt.reports.model` and `minigpt.reports.cards` compatibility paths exist; next refactor can share card schema and artifact writers. |
| Project audit | `project_audit.py`, `project_audit_builder.py`, `project_audit_contexts.py`, `project_audit_artifacts.py` | The facade owns input discovery and assembly; builder, context extraction, and artifact rendering stay separate. |
| Dashboards | `dashboard.py`, `dashboard_render.py`, `dashboard_sections.py` | `minigpt.reports.dashboard` compatibility path exists; keep sections split and avoid another monolithic dashboard file. |
| Manifests and artifact maps | `manifest.py`, `artifact_map.py` | `minigpt.reports.manifest` and `minigpt.reports.artifact_map` compatibility paths exist for stable evidence index contracts. |
| Readiness/maturity | `maturity*`, `maturity_capabilities.py`, `maturity_html_sections.py`, `maturity_narrative_summary_helpers.py`, `release_readiness*`, `release_readiness_comparison_html.py` | `minigpt.governance.maturity` and `minigpt.governance.release` compatibility paths exist; keep capability/version inventory, artifact writers, narrative input normalization, and HTML sections separate, and treat them as governance reports, not model quality proof. |
| `_artifacts.py` files | Many modules | Extract common output helpers before adding more one-off writers. |

## Engineering Owner

Engineering modules define local and CI quality gates rather than product
runtime behavior.

| Bucket | Role | Posture |
|---|---|---|
| `ci_workflow_hygiene*` | CI action, command, and ordering policy plus the report model. | `ci_workflow_hygiene_policy.py` owns the policy constants; `ci_workflow_hygiene.py` owns report assembly. |
| `source_encoding_hygiene.py` and `test_coverage_report.py` | Source hygiene and coverage gate reports. | Active engineering gates used by local health and CI. |

## Governance Owner

Governance modules make decisions, enforce contracts, create receipt chains, or
decide whether evidence can be consumed downstream.

| Bucket | Role | Posture |
|---|---|---|
| `model_capability_*` | Capability gates, diagnostics, route decisions. | Active governance; group by route before moving. |
| `randomized_holdout_*` | Holdout suites, publication receipts, registry consumers. | Mostly historical/outer-layer evidence; freeze unless active. |
| `bounded_objective_*` | Loss-signal and bounded-objective route work. | Capability-governance. |
| `baseline_candidate_*` | Baseline/candidate comparisons, eval loops, artifacts, and handoff gates. | Evaluation-to-governance boundary; keep report construction, rendering/writing, threshold matrices, and handoff checks split by role. |
| `release_*` | Release gates, bundles, readiness, drift contracts. | `release_gate_policy.py` owns named gate profiles; `minigpt.governance.release` compatibility path exists for active release governance facades. |
| `registry_*` | Registry render, ranking, release-readiness. | `minigpt.governance.registry` compatibility path exists for the active registry facade; run summary extraction, data aggregation, render helpers, row/cell formatting, rankings, release-readiness delta collection, and delta summary stats stay separate. |
| `maintenance_*` | Maintenance policy, batching, pressure, governance. | Engineering governance. |

## Research Owner

Research modules are useful, but they should not silently become core
dependencies.

| Bucket | Examples | Posture |
|---|---|---|
| Adaptation | `lora_*`, `sft_*`, `dpo_*`, `distill_*` | Keep isolated until promoted by tests and docs; split reusable DPO primitives from experiment orchestration. |
| Decoding/runtime | `spec_decode*`, `kv_cache*`, `rope_eval*` | Promote only stable primitives into core; keep speculative algorithms separate from experiment orchestration. |
| Interpretability/behavior | `grok_*`, `induction_*`, `similarity*` | Research/evaluation boundary; keep statistical, verdict, and report helpers split from long experiment modules and training paths. |
| Training dynamics | `calibration*`, `continual*`, `ewc*`, `double_descent*`, `wd_noise*` | Research, not production proof; keep evidence reports separate from analysis kernels. |

## Scripts Inventory

Approximate counts from `scripts/`:

| Script class | Count | Guidance |
|---|---:|---|
| Governance build/check scripts | 231 | Keep as wrappers; move shared logic into package modules. |
| Active entry scripts | 17 | Preserve CLI compatibility before refactors. |
| Analysis scripts | 15 | Keep tied to research modules. |
| Nested grouped scripts | 10 | `evaluation`, `publication`, and `devtools` are good precedents. |
| Other scripts | 375 | Classify before touching. Many may be historical wrappers. |

## Legacy Signals

Treat a file as likely legacy until proven active if it has one or more of
these signals:

- Version suffixes such as `_v981` through later chains.
- Repeated chain words such as `receipt_index_receipt_index`.
- File names longer than normal command-line ergonomics.
- A matching artifact directory in `a/` through `f/` but no current script or
  active test path.

Legacy does not mean delete. It means preserve, avoid new dependencies, and
only refactor when an active consumer is identified.

## Next Actions

1. Classify the `other` source modules into this inventory.
2. Pick one active owner class for the first physical package split.
3. Reduce future pressure on `minigpt.__init__` by migrating active callers to
   stable imports documented in the [Public API policy](public-api.md).
4. Extract common artifact writer helpers only after selecting a small group of
   active `_artifacts.py` modules with the same output contract.
