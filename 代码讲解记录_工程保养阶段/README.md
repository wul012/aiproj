# MiniGPT 代码讲解记录_工程保养阶段

本目录从 v1130 开始承接 MiniGPT 的工程后期保养讲解，重点覆盖命名止血、README/docs 拆分、scripts 分层、publication receipt 模板化、模型能力回归节奏和 artifact 对照表。

上一阶段 `代码讲解记录_模型治理阶段/` 保留 v1098-v1129 的模型治理和 publication receipt 讲解，不回头迁移旧文件。

## 写入规则

- 编号继续沿用全局序号，从 `1142-v1130-...` 开始。
- 本阶段讲解默认用中文书写，继续写清目标、边界、入口、输出模型、测试覆盖、运行证据和一句话总结。
- 保养版本不追求大规模重构，优先用可运行检查、入口分层、索引和模板降低阅读成本。
- 对历史长命名和历史目录只做止血、索引、说明和低风险桥接，不在没有兼容迁移时强行改名或搬迁。

## 当前索引

1257-v1300-elegance-program-closeout.md
 -> v1300 code explanation: the elegance program's closing audit — a reproducible re-score against the original 6/10 rubric (docs/elegance/program-closeout-v1300.md), every number regenerable by a named command. Honest verdict: 6 -> 7.5, not the projected 8.5-9: the delivered points are the naming axis (282 long names -> 0, CI-refused), static debt 271 -> 0, tested 360-shim compat surface, and four tighten-only elegance ratchets; the undelivered 1.5 points are priced openly (normalization-lane migration of the 1,355-module flat corpus, symbol-level renames resolving the 7,515 name-budget stock, dup burn-down of 227 frozen bodies) — the projection predated v1294's discovery that the owner-package contract correctly blocks verbatim sub-packaging, and the narrowing was recorded when it happened. One planned item consciously skipped with rationale (the 1,309-line test-file split). Docs-only version; the score is now a measurement, not an opinion.

1256-v1299-final-naming-batch5.md
 -> v1299 code explanation: batch 5 closes the naming arc — the final 57 >120-char stems (packet chain v992-v1002, receipt chain v1030-v1041, the registry-ack GEN-1 layer, and 5 stragglers) short-named in one pass; long_name_stock 57 -> **0**, max_stem_length 150 -> 120, and the ratchet now structurally refuses any new long name. The map is hybrid: the two version-keyed families reuse their batches' established mechanical rules (deliberately different per family), the gen-1 registry layer takes a distinct ack_bundle_* prefix because batch 4's registry_ack_* names own gen-2, and two base names are pinned by batch-4's published artifacts pairings (asserted, not eyeballed). Two more hidden-coupling classes surfaced: (6) earlier batches' script SHIMS still carry old long names and mechanical derivation tried to rename them onto batch-4's finished targets — shims are the compat surface, so the planner now skips every forwarding shim by shape (caught at zero writes); (7) the renamed test_ack_bundle_* files jumped to the FRONT of unittest discovery order and their bare `import minigpt` (no tests._bootstrap) had silently relied on an earlier-sorting test having patched sys.path for years — pytest's conftest masks it, CI's unittest runner exposed it; fixed with the canonical ensure_src_path idiom and adversarially reproduced fresh-process green. Five-batch ledger: 282 long names cleared (6+30+146+43+57), zero behavior change, every old import path still importable and test-guarded.

1255-v1298-packet-registry-batch4.md
 -> v1298 code explanation: batch 4 clears the last >150-char names (43 modules: the versioned packet chain + the generational registry-ack facades, where mechanical tail-collapse provably fails — generation depth IS the distinguishing information — so the map went hand-curated, 43 entries with per-entry semantic invariants). Also closes the v1297 CI coverage failure the right way: 189 forwarding shims sat at 0% coverage; instead of omitting them, test_forwarding_shims_v1298 imports every shim (detected by the canonical _is_shim shape) and asserts old-is-new — compat surface tested, coverage restored, shim-count floor asserted. long_name_stock 100 -> 57, max_stem_length 191 -> 150. Fifth local-vs-CI gap (the Unit-tests step embeds the coverage ratchet) added to the close checklist.

1254-v1297-receipt-chain-batch3.md
 -> v1297 code explanation: batch 3 clears the receipt_index-chain family — all remaining 146 modules >150 chars short-named in one pass, and this tier's consumer filenames embed the module stems so 43 scripts + 86 tests renamed in the same batch (329 files' imports rewritten). The v1296 budget lesson moved upstream into the map generator (zero dup/clash/over-budget asserted at generation; zero rework). 473/473 family tests, 15/15 gates, zero-net name-budget rebase, long_name_stock 246 -> 100.

1253-v1296-receipt-chain-batch2.md
 -> v1296 code explanation: the first production rename batch — the 30 longest receipt_index-chain modules (193-186 chars; the family's names accreted one receipt_index_ layer per generation) renamed in place to receipt_chain_<role>_<version>, 30 forwarding shims, 90 consumer files' imports rewritten. The v1295 rebase tool's REFUSAL branch fired in earnest: 10 mechanically-derived short names were themselves over the 40-char filename budget (a doubled token) and the tool blocked the baseline swap until a second-pass de-dup fixed them — then 7,515 -> 7,515 zero-net rebase. 320/320 family tests, all 15 CI gates swept locally, ratchet tightened: long_name_stock 276 -> 246, max_stem_length 193 -> 191.

1252-v1295-name-budget-rename-rebase.md
 -> v1295 code explanation: v1294's push turned CI red — the name-budget gate keys its 7,515-entry baseline by (path, qualname) digest, so the 6 file renames re-keyed 33 historic inner-name violations as "new" (new 33 + resolved 33, stock unchanged). The fix is a provably-neutral rebase: rebase_renamed_paths allows a baseline path-rebase ONLY when the multiset of (kind, qualname, length) of new violations exactly equals the resolved ones (any net growth, length change, or unprovable metadata refuses); the companion script scans the pre-rename tree via git worktree (core.longpaths for the near-MAX_PATH archive). Run: 7,515 -> 7,515, gate pass. Fourth instance of "local gates ⊊ CI gates" upgraded the AGENTS.md rule to a mandatory full-gate sweep before any close (which immediately caught a strict-format failure in this very version's new code).

1251-v1294-receipts-pilot-batch.md
 -> v1294 code explanation: stage 5 pilot batch — the v1012-v1014 receipt-packet-index cluster (6 modules, 185-202-char names) renamed IN PLACE to short canonical names with sys.modules-forwarding shims at every old path (importlib proves `old is new`), 3 scripts renamed with dual-path shims, 3 tests renamed with their 2 consumers rewritten. The pilot's biggest finding: the first-cut sub-packaging into minigpt/receipts/ was correctly BLOCKED by the owner-package architecture contract (facade-only __init__, 220-line module cap, 93 structural rules) — verbatim historical modules don't meet the normalization bar, so sub-packaging belongs to the normalization lane and the elegance program honestly narrows to naming surgery + shims + ratchets. Three further couplings surfaced and fixed (scripts.-package imports, test-to-test helper imports, long names in artifact-filename strings = output contracts). Elegance metric became shim-aware (+recursive dup scan); ratchet's first tightening: long names 282→276, max stem 202→193.

1250-v1293-baseline-zero-elegance-ratchet.md
 -> v1293 code explanation: stage 4 — static baseline reaches ZERO (271→153→1→0) by fixing the last entry, data_prep's latent NameError (the quality=None fallback called an un-imported function; function-local import mirrors the existing cycle-safe pattern; regression test added), and the same version welds the gate shut: a whole-codebase elegance ratchet (flat_dir_file_count 1355, long_name_stock 282, max_stem_length 202, dup_def_stock 227 — byte-identical function bodies across >=3 modules) frozen at current values, tighten-only updates, wired into CI after the file-size ratchet. The zero state and its lock land in one version so the dirty-window is zero.

1249-v1292-f401-audited-sweep.md
 -> v1292 code explanation: stage 3 — the audited F401 sweep. Three audit iterations (naive from-import scan said 146 dead; adding attribute-access consumers said 137; the final multiline-parenthesized + local-alias-aware audit proved 90 KEEP / 62 dead — a naive sweep would have severed 84 live import chains, and one mid-execution break by the public-API `is`-contract tests proved it concretely). Atomic pipeline: 89 keepers formalized as `Y as Y`, 1 noqa'd, 62 removed by ruff --fix only after formalization succeeded. Baseline 153 → 1 (the lone data_prep F821 bug, reserved for v1293). Two honest rollbacks recorded.

1248-v1291-lint-burndown.md
 -> v1291 code explanation: stage 2 of the elegance program — all 118 mechanically-fixable lint issues (92 E702 semicolon lines, 15 E741 ambiguous `l` names, 6 verified-dead F841 assignments, 5 F541) cleared across 20 files, ratchet baseline tightened 271→153. Three-tier verification: AST-identity proof vs HEAD for the 10 split-only files (the parse tree is byte-identical — mathematically zero behavior change), 204/204 focused tests for the rename/deletion files, and the static gate re-read with the corrected pass signal. F401 (re-export risk) and F821 (bug-class) deliberately deferred to their own audited versions.

1247-v1290-grok-arc-common.md
 -> v1290 code explanation: elegance/maintenance version on the AGENTS.md refactoring rhythm — the 12 byte-identical copies of `_median` (9 plain + 2 NaN-guarded) and the 12 identical Agg figure-scaffolding blocks across the grok-arc experiment modules converge into `grok_arc_common.py` (median/median_or_nan/agg_pyplot/save_figure), with the old private names re-imported so decide() bodies stay textually untouched. Verified three ways: identity-guard tests (`module._median is median` — any re-fork fails the suite), byte-for-byte re-derivation of all committed arc artifacts (61/63 identical; the 2 exceptions are v1277/v1279's pre-existing analyze-time `generated_at` timestamps; all 3 regenerated PNGs identical), and the full suite. Net -141 lines of copy-paste.

1246-v1289-spike-microscopy.md
 -> v1289 code explanation: per-step microscopy of the committed v1287 post-grok spikes — the nine spiking trajectories continued with their original Adam moments via a line-for-line faithful reimplementation of the training loop, certified by bit-equality of all ~740 shared coarse rows (G0 9/9). Verdict `spike_preserves_circuit`: 134/134 deep collapses leave the embedding Fourier circuit intact (r median 1.007, worst 0.979) — the wd shove is a 1-3-step gradient impulse (median 240x) that breaks the network middle while share keeps climbing. The post-grok regime is a ~50-step relaxation oscillator (173 episodes where the census saw 24; 150 fully invisible at 100-step resolution); rotation happens AT spikes (13/161, all lr<=4e-3). Completes the arc: phenomenon (v1287) -> cause (v1288) -> mechanism (v1289). Evidence lives under `f/1289`.

1245-v1288-spike-anatomy.md
 -> v1288 code explanation: the causal follow-up to v1287's metastability discovery — paired branch arms (wd=1.0 vs wd=0.0, sharing the optimizer-reset confound) from nine bit-verified healthy v1287 states, plus two un-censoring runs. Verdict `spikes_are_wd_driven` (the arc's first positive causal verdict): wd=1 arms reproduce the post-grok spikes in 8/9 cells while wd=0 arms are spike-free 9/9; both v1287 "deaths" re-grokked within 100 steps. Norm flow reverses without wd; purification freezes where it has headroom — purification and metastability are two faces of one wd process. Evidence lives under `f/1288`.

1244-v1287-post-grok-purification.md
 -> v1287 code explanation: observes directly the post-grok purification v1286 inferred from endpoints — all 11 v1285/v1286 cells extended to 3x t_gen with the early stop disabled via the existing `grok_stop_val` config field (zero training-code modification), purity measured on each cell's committed cache top-5 set. Preregistered `review` (substrate_unsound: the pre-announced post-grok stability guard fired on two 4e-3 cells). What it caught: grokked solutions are METASTABLE — 9/11 cells spike train+val together and self-heal in 100-300 steps; the "dead" cells are censored mid-spike at their horizons. Purification is real and universal (own purity 0.31→0.50-0.63 at 1e-3, →0.88-0.93 at high lr; extended 4e-3 overtakes 8e-3), and canonical purification rotates the frequency set. Evidence lives under `f/1287`.

1243-v1286-lr-compression.md
 -> v1286 code explanation: tests the construction-completion invariant by re-running the eight v1281 d=128 cells (lr 2-8e-3) with snapshot ladders. Preregistered `review` (bar_instability: the 2e-3 median rides the 0.2 bin line; the G2 guard fired on genuinely boundary-riding data). Certain content: the invariant is FALSIFIED — F drops to ~0.25 under 8x compression — yet compressed cells hold MORE absolute structure at grok; high lr keeps purifying after grok (final shares 0.31→0.81 with lr), so lr decouples construction from generalization. Evidence lives under `f/1286`.

1242-v1285-deep-plateau.md
 -> v1285 code explanation: takes v1284's timing question to the canonical d=128 deep plateau. Verdict `deep_plateau_sculpts` (first non-review since v1280): F = 0.56-0.72 — the deep plateau genuinely builds the circuit before val moves, so v1284's "the plateau does not own construction" is formally a boundary effect and slow sculpting survives where it was originally told. All three cells reproduce their v1279 references bit-for-bit; v1188's 0.307 endpoint triple-replicated; the thinnest module of the arc (v1284 machinery imported unchanged). Evidence lives under `f/1285`.

1241-v1284-circuit-timing.md
 -> v1284 code explanation: measures WHEN the Fourier circuit forms relative to generalization in each of v1283's phases, using deterministic truncated re-runs as weight snapshots (zero training-code modification, prefix-determinism gate 43/43). Preregistered `review` (mixed_fractions) — the uniformity is the finding: both phases build the circuit on the same relative schedule (F~0.25 everywhere; the width-matched w=24 pair differs only by ~3x time dilation), so the plateau does not own construction and the slow-sculpting account needs revision. Coupled endpoints are the most concentrated circuits measured. Evidence lives under `f/1284`.

1240-v1283-delay-gate.md
 -> v1283 code explanation: locates the gate behind v1282's banked no-memorization phenomenon. P1 forensics over four committed caches (free) establish the delayed phase is width-gated, not lr-induced, with a bimodal max-gap distribution whose empty hole [0.41,0.79] freezes the thresholds. The boundary experiment (widths 20/24/28 + re-run anchors) lands preregistered `review` (mixed_widths) — the finding itself: a sharp bimodal jump at critical width ~24 where seeds split between phases; no intermediate cells exist, coupled cells have delay exactly 0, and the `graded` branch is cleanly excluded. Evidence lives under `f/1283`.

1239-v1282-width-lr.md
 -> v1282 code explanation: the width version of the v1281 control — widths {16,32,64} at lr=4e-3 against the v1281 d=128 floor. Preregistered `review` (broken_cells: w=16 exceeds its stability window, the instability guard's first real firing). Descriptively: v1279's d=64 hole CLOSES at 4x lr (2,400 steps vs censored-at-100k), the narrow speedup inverts (w=32 ~3x slower), the usable lr window shifts upward with width, and two w=16 seeds grok WITHOUT ever memorizing (banked). Evidence lives under `f/1282`.

1238-v1281-norm-vs-step.md
 -> v1281 code explanation: the control v1280 banked — alpha=1 at matched relative step (lr/alpha) against the committed v1280 cells. Preregistered `review` (mixed_pairs: rho 0.359/0.778), but both pairs exclude the small-norm branch; descriptively the ABSOLUTE lr dominates (alpha=1 dose 11,400 -> ~1,400, saturating ~1k at lr>=4e-3), larger norm is mildly faster at adequate lr (alpha=2 @ 8e-3: 900 steps, heldout 1.0), and the v1277-v1280 width/norm story collapses into "the canonical baseline is lr-starved". Evidence lives under `f/1281`.

1237-v1280-init-rescue.md
 -> v1280 code explanation: stress-tests v1279's headline with the lr-artifact hypothesis. P1 corrects v1279's record from the committed cache (dead cells memorize instantly; the death is of the transition), then a preregistered 16x lr sweep at alpha=0.5 lands `norm_clock_revived_under_lr_scaling`: lr-down rescues nothing, lr-up at 2-4x groks in 1,300-4,000 steps vs baseline 11,400 (heldout up to 0.9992) — v1279's headline is formally downgraded to lr-conditional with linked notices. Dose arm: a cliff in (0.7, 0.85] at the frozen lr. Evidence lives under `f/1280`.

1236-v1279-grok-speed.md
 -> v1279 code explanation: preregisters (commit `0f5f77a3`) the norm-clock causal test of WHY narrow models grok faster, survives its own P2 stop condition (d=64 stalls at 40k; harness exonerated by a bit-exact v1277 cell reproduction; budget re-paneled to 100k BEFORE any grid data, commit `37433657`), and lands the preregistered `review` (substrate_unsound): d=64 is a real mid-width slow zone, and the norm clock is INVERTED — shrinking the wide init norm prevents grokking (0/6) while doubling it still groks. Evidence lives under `f/1279`.

1235-v1278-readme-exhibition.md
 -> v1278 code explanation: reconnoiters the README's machine-read surfaces first (cadence regex, doc-link contracts, honesty gate), then prepend-only installs the exhibition layer — badges, bilingual hero, a 13-row science catalog with verdicts quoted exactly, how-to-trust, boundaries — and repairs the missed v1277 README version sections with disclosure. Documentation-only; all focused gates green. Evidence lives under `f/1278`.

1234-v1277-capacity-squeeze.md
 -> v1277 code explanation: preregisters (commit `644dd535`, before any training) and runs the capacity-squeeze grid — n_embd {32,16,12,8,4} × 3 seeds on the frozen grok recipe — and finds the preregistered `squeeze_hits_capacity_floor` verdict: the squeeze region {8,4} never groks, so the model hits its floor (smallest grokking width 12) before the drop-vs-superpose choice is ever forced. Descriptive extras: narrow models grok ~5× faster than d=128, and w=8 failures show 0.74+ direction interference ("attempted packing"). Evidence lives under `f/1277`.

1233-v1276-superposition.md
 -> v1276 code explanation: preregisters and runs a CPU-only 20-feature/5-dimension ReLU autoencoder with importance and uniform controls, corrects the best-dedicated analytic baseline from the untouched probe cache, and finds converged monotone loss-optimal sparse packing while preserving the formal `review` verdict because the uniform dense control is mixed across τ. Evidence lives under `f/1276`.

1232-v1275-fourier-ticket.md
 -> v1275 code explanation: preregisters a toy-scale Fourier lottery-ticket test, runs exact per-tensor/global magnitude pruning plus matched random controls on the frozen v1185 checkpoint, and honestly stops Arm L when 50% sparsity drops heldout accuracy to 0.407/0.487 despite the known-frequency power share remaining visible. Evidence lives under `f/1275`.

1231-v1273-elegance-name-gate.md
 -> v1273 code explanation: turns the 40-character filename/public-identifier rule into an AST census, line-stable digest baseline, fail-closed shrink-only update contract, CI ordering guard, engineering-health step, and strict ruff/mypy scope. It records 7,515 legacy violations without claiming they are fixed and uses the top-offender report to gate E-A2 pin analysis. Evidence lives under `f/1273`.

1230-v1272-deep-maintenance-closeout.md
 -> v1272 code explanation: closes the v1268-v1271 maintenance batch with 3,747 full pytest passes, 3,538 CI-style unittest cases, 91.06% coverage against the unchanged 88.98% floor, and three in-process tests that raise the active assurance contract from 0/63 to 59/63 covered statements. It records the remaining 271/21/496 debt rather than continuing version-count-driven cleanup. Evidence lives under `f/1272`.

1229-v1271-governance-report-loader-consolidation.md
 -> v1271 code explanation: consolidates nine active governance JSON object loaders into strict and optional-empty shared contracts, preserves exact public errors and path behavior, evolves the existing dedup checker to fourteen protected modules, and extracts handoff guard construction into a 113-line strict typed component so the active facade returns below the file-size warning threshold. It leaves 496 historical copies visible rather than bulk-rewriting frozen experiments. Evidence lives under `f/1271`.

1228-v1270-ci-workflow-hygiene-responsibility-split.md
 -> v1270 code explanation: splits the 523-line CI workflow hygiene module into typed checks, summary, contract, and public orchestration layers; preserves a byte-identical canonical report; expands strict mypy scope to 19; and promotes zero-console-error HTML evidence into a repository rule. Evidence lives under `f/1270`.

1227-v1269-static-analysis-baseline-debt-reduction.md
 -> v1269 code explanation: reduces the committed ruff baseline from 545 to 271, makes reviewed bootstrap and facade re-exports explicit at line scope, removes real unused/redefined bindings, and makes baseline updates fail-closed and shrink-only. Evidence lives under `f/1269`.

1226-v1268-ci-execution-economy-and-review-reconciliation.md
 -> v1268 code explanation: closes the Stage-1 review follow-up, tracks the inactive Stage-2 brief, removes duplicate tag CI runs, enables pip caching and same-ref cancellation, and protects all execution-economy choices with positive and negative contract tests. Evidence lives under `f/1268`.

1225-v1267-production-excellence-a5-final-evidence-closeout.md
 -> v1267 code explanation: completes production-excellence A5 with a final evidence closeout gate. It validates the A0-A4 evidence docs, final evidence matrix, no-promotion wording, README/docs indexes, and CI closeout wiring, then archives proof under `f/1267`.

1224-v1266-production-excellence-a4-file-size-ratchet.md
 -> v1266 code explanation: completes production-excellence A4 with a CI-backed file-size ratchet. It scans Python files under `src`, `scripts`, and `tests`, records eight no-growth waivers for legacy oversize tests, and fails on new unwaived oversize files or waiver growth. Evidence lives under `f/1266`.

1223-v1265-production-excellence-a3-artifact-schema-guard.md
 -> v1265 code explanation: continues production-excellence A3 with a fail-closed artifact schema guard for current experiment cards, dataset cards, model cards, and publication receipts. It validates required fields, expected values, simple types, and no-promotion receipt fields. Evidence lives under `f/1265`.

1222-v1264-production-excellence-a3-honest-measurement-gate.md
 -> v1264 code explanation: starts production-excellence A3 by adding a CI-backed honest-measurement registry gate for bounded model-capability governance claims. It validates source artifacts, no-training/no-promotion boundaries, seed-policy labels, and positive plus negative contract-test markers. Evidence lives under `f/1264`.

1221-v1263-production-excellence-a2-coverage-ratchet.md
 -> v1263 code explanation: completes production-excellence A2 by raising the coverage gate to the measured baseline minus two points, committing a coverage-floor manifest, locking CI/workflow-hygiene/project-configuration agreement, and keeping the science lane unchanged. Evidence lives under `f/1263`.

1220-v1262-production-excellence-a1-scoped-type-analysis.md
 -> v1262 code explanation: completes production-excellence A1 with strict mypy over eight committed load-bearing targets in four groups, protects the scope with a floor and ownership validation, integrates the gate into CI/engineering health/workflow hygiene, and keeps the science lane unchanged. Evidence lives under `f/1262`.

1219-v1261-production-excellence-a1-static-analysis.md
 -> v1261 code explanation: production-excellence A1 staged static analysis. Adds ruff as a committed CI gate without a repo-wide mechanical sweep, records the 545-finding historical `src/`/`scripts/` baseline, keeps strict maintained paths lint-clean and format-clean, and extends CI workflow hygiene plus engineering health to protect the new gate. Evidence lives under `f/1261`.

1218-v1260-production-excellence-a0-census.md
 -> v1260 code explanation: production-excellence A0 census for aiproj. Adds a stdlib-only warning-only archive/runs inventory, records CI/test/archive baseline facts, refreshes stale START_HERE pointers, and preserves the no-promotion/model-quality boundary. Evidence lives under `f/1260`.

1212-v1200-minigpt-weight-decay-rescues-under-label-noise.md
 -> v1200 code explanation: weight decay on v1199's noisy halfspace. It shows wd improves converged generalization by selectively rejecting flipped labels (`fit_to_noise` drops while clean-row accuracy stays high), but does not significantly beat the wd=0 early-stopping optimum, so the honest verdict is `wd_equals_early_stopping`. Evidence lives under `f/1200`.

1211-v1199-minigpt-double-descent-absent-at-toy-scale.md
 -> v1199 code explanation: double descent check at toy MiniGPT scale. It uses noisy halfspace model-size and epoch-wise arms with eta=0 controls, finds no second descent, and records the conservative `no_double_descent_monotone` verdict. Evidence lives under `f/1199`.

1210-v1198-minigpt-induction-ov-copying-circuit.md
 -> v1198 code explanation: induction head OV copying mechanism. It pairs weight-level OV copying scores with activation Direct Logit Attribution while defending against the tied-embedding Gram confound. Evidence lives under `f/1198`.

1209-v1197-minigpt-induction-circuit-dissection.md
 -> v1197 code explanation: causal dissection of the induction circuit. It classifies prev-token and induction heads, then uses mean ablation, count-matched controls, composition checks, and tau robustness to show the two-part circuit is necessary and specific. Evidence lives under `f/1197`.

1208-v1196-minigpt-induction-requires-depth.md
 -> v1196 code explanation: in-context induction depth experiment. It blocks positional and frequency shortcuts, shows a 2-layer model learns the most-recent-successor task while a 1-layer model fails, and includes shortcut plus attention-only controls. Evidence lives under `f/1196`.

1207-v1195-minigpt-similarity-forgetting.md
 -> v1195 code explanation: task-similarity grading of catastrophic forgetting. It uses analytic output-table overlap to show forgetting is monotone-graded by overlap and that operation family is a red herring. Evidence lives under `f/1195`.

1206-v1194-minigpt-ewc-vs-replay.md
 -> v1194 code explanation: EWC versus replay on the v1193 continual-learning substrate. It compares stability-plasticity frontiers and finds replay dominates EWC under the toy modular tasks. Evidence lives under `f/1194`.

1205-v1193-minigpt-continual-learning-catastrophic-forgetting.md
 -> v1193 code explanation: continual-learning and catastrophic forgetting axis. It trains task A then task B, shows A collapses toward chance, and demonstrates replay mitigation with held-out operand-pair quarantine. Evidence lives under `f/1193`.

1204-v1192-minigpt-calibration-temperature-scaling.md
 -> v1192 code explanation: calibration under aleatoric uncertainty. It uses the known-P_true stochastic task to measure overconfidence analytically and shows temperature scaling reduces ECE. Evidence lives under `f/1192`.

1203-v1191-minigpt-grokking-causal-frequency-ablation.md
 -> v1191 code explanation: causal frequency ablation for the grokking Fourier mechanism. It keeps or removes top embedding frequencies to move v1188/v1190 from correlation toward causal evidence. Evidence lives under `f/1191`.

1202-v1190-minigpt-grokking-logit-frequency-alignment.md
 -> v1190 code explanation: output-logit frequency alignment for the shipped grokking checkpoint. Builds the full `L[a,b,y]` logit cube, uses 2D FFT over `(a,b)` to measure diagonal frequency power expected by `a+b=y`, compares against random-init and ideal addition controls, and verifies the logit top frequencies match the v1188 embedding dominant frequencies. Evidence lives under `f/1190`.

1201-v1189-ci-unittest-portability.md
 -> v1189 code explanation: CI portability repair for the v1186 checkpoint inference test. GitHub Actions uses stdlib `unittest discover`, but `tests/test_grok_predict_v1186.py` imported `pytest` only for a skip marker, causing `ModuleNotFoundError` in CI from v1186 through v1188. v1189 replaces it with `unittest.skipIf`, adds local `src/` path injection, and keeps the boundary to test portability plus index repair only. Evidence lives under `f/1189`.

1200-v1188-minigpt-grokking-interpretability.md
 -> v1188 code explanation: mechanistic interpretability for grokking. Reads learned number embeddings, applies FFT over the number axis, and compares grokked wd=1, memorized-not-grokked wd=0, and random-init arms. The real result links generalization to modest Fourier concentration, while explicitly avoiding the stronger attention-only ultra-sparse claim. Evidence lives under `f/1188`.

1199-v1187-minigpt-report-check-common-dedup.md
 -> v1187 code explanation: contract-preserving maintenance dedup for grokking audit modules. Extracts shared check-row construction, failure collection, and exit-code resolution into `report_check_common.py`, then migrates v1180/v1181/v1182/v1184 audit modules without changing their public behavior. Evidence lives under `f/1187`.

1198-v1186-minigpt-grokking-checkpoint-inference.md
 -> v1186 code explanation: turns the v1185 canonical checkpoint into a usable inference/demo artifact. Adds load/predict APIs, table evaluation over train/held-out modular-addition pairs, and a demo report proving the shipped checkpoint computes `a+b mod 97` on held-out pairs. Evidence lives under `f/1186`.

1197-v1185-minigpt-grokking-checkpoint.md
 -> v1185 code explanation: productizes the chosen grokking recipe into a self-contained checkpoint. Freezes `weight_decay=1.0`, trains one canonical model, saves weights plus metadata, verifies save/load logits, and archives the reusable checkpoint under `f/1185`. Evidence lives under `f/1185`.

1196-v1184-minigpt-grokking-wd-law-check.md
 -> v1184 code explanation: contract check over the v1183 grokking weight-decay dose-response artifact. Adds `grok_wd_law_check_v1184.py` and `scripts/check_grok_wd_law_v1184.py` to reload `grok_wd_law_v1183.json`, re-derive threshold wd, fastest interior wd, low/high-end censoring, strongest-dose memorization-vs-grok behavior, and the toy-scale boundary from the rows. It is artifact reconstruction only, not a training rerun; the purpose is to prevent the earlier monotone-acceleration over-claim from returning. Evidence lives under `f/1184`.

1195-v1183-minigpt-grokking-wd-dose-response.md
 -> v1183 code explanation: real weight-decay dose-response sweep over the v1179 modular-addition grokking primitive. It scans `weight_decay ∈ {0.0,0.1,0.3,1.0,3.0}` across paired init+split seeds, catches and repairs an initial monotone-acceleration over-claim, and records the honest verdict `wd_dose_response_interior_optimum`: fastest grokking at wd=1.0, threshold wd=0.3, and high-end wd=3.0 memorizing without grokking. Evidence lives under `f/1183`.

1194-v1182-minigpt-grokking-paired-contrast.md
 -> v1182 code explanation: paired seed counterfactual report over the v1181 phase rows. Adds `grok_paired_contrast_v1182.py` and `scripts/analyze_grok_paired_contrast_v1182.py` to collapse each seed's `weight_decay_on` / `weight_decay_off` rows into one contrast row, checking matched memorization, delayed grok only in the weight-decay arm, no-decay censoring, large final validation gain, and the no-rerun boundary. Evidence lives under `f/1182`.

1193-v1181-minigpt-grokking-trajectory-phases.md
 -> v1181 code explanation: grokking trajectory phase report over the v1179 real experiment curves. Adds `grok_trajectory_phases_v1181.py` and `scripts/analyze_grok_trajectory_v1181.py` to align rows with curves, classify each seed/arm as `delayed_grok` or `memorized_only_censored`, compute plateau low-validation rates, max validation jumps, curve endpoint/mempoint consistency, and paired phase separation. It explains the curve process behind v1179 rather than rerunning training or expanding the model-quality claim. Evidence lives under `f/1181`.

1192-v1180-minigpt-grokking-evidence-check.md
 -> v1180 code explanation: grokking evidence check over the v1179 real experiment artifact. Adds `grok_evidence_check_v1180.py` and `scripts/check_grok_evidence_v1180.py` to rebuild the headline evidence from `grok_v1179.json` rows: paired seed/arm grid, weight-decay memorization and delayed generalization, no-decay non-grokking ablation, low validation accuracy at memorization, summary-rate agreement, and toy-scale boundary. It is artifact reconstruction only, not a training rerun or stronger model-quality claim. Tests cover pass/fail mutations and CLI output wiring; evidence lives under `f/1180`.

1191-v1179-minigpt-grokking.md
 -> v1179 code explanation: the first positive grokking reproduction in this MiniGPT line. Uses modular addition `a + b = c (mod 97)` with a small train split, paired weight-decay vs no-decay arms, five seeds, delayed-generalization metrics, and censoring-aware aggregation. The version proves a toy-scale mechanism claim only: with weight decay, all seeds memorize early and generalize much later; without weight decay, the same memorization does not become grokking within the run budget.

1190-v1178-minigpt-ptq-policy-sensitivity.md
 -> v1178 code explanation: PTQ policy sensitivity over the v1177 candidate selector. Defines strict/default/aggressive `PtqPolicyProfile` values, reuses the v1177 candidate builder rather than duplicating selection logic, and proves the chosen candidate changes with quality tolerance (`per_tensor:4b` / `group32:3b` / `per_channel_row:3b`). Emphasizes that `group32:3b` is the balanced default, not a policy-invariant deployment truth.

1189-v1177-minigpt-ptq-candidate-selector.md
 -> v1177 code explanation: PTQ deployment candidate selector. Consumes the real v1175 PTQ JSON, applies an explicit quality budget (`dCE <= 0.08`, exact-match drop `<= 0.10`, KL `<= 0.10`), records budget pass/fail and reject reasons for each S1 full-model candidate, and selects `group32:3b` as the lowest effective-bits candidate inside the budget. Emphasizes the boundary: quality-cost selection only, not int-kernel runtime speed or memory proof.

1188-v1176-minigpt-completion-mask-dedup.md
 -> v1176 code explanation: extract completion-token X/Y masking into a neutral helper shared by distillation and PTQ, preserve distill_common compatibility, and link the plain-language project guide.

1187-v1175-minigpt-ptq.md
 -> v1175 code explanation: post-training weight quantization (PTQ; the inference-efficiency thread). New ptq_v1175.py: quantize_tensor (per-tensor/per-channel-row/-col/group32 × absmax_sym/percentile_clip/mse_clip/affine_asym RTN), quantized_model (quantizes by PARAMETER IDENTITY so the tied token_embedding/lm_head is quantized once, not silently reverted via state_dict round-trip — guarded by a test), component_param_names, effective_bits_per_weight (charges fp16 scales), ce_and_kl + weight_rel_error metrics, decide, run_ptq. Primary metric = held-out CE (continuous; EM mislocates the cliff). Three sweeps: S1 quality-vs-bits, S2 per-component sensitivity (attention DECOMPOSED into c_attn/c_proj), S3 attention axis+scheme robustness. 5 seeds (the only variance source is the training seed); two headline claims significance-gated via beats_lower. Real RTX 4060 (5 seeds, 4L/64): status=pass, verdict=per_channel_advantage_not_separable — a sharp cliff (lossless ≥6b, usable 3–4b, collapse at 2b); per-channel/group extend the nominal cliff (per-tensor collapses at 3b CE 0.540, per-channel holds 0.168) but it's a wash at matched effective bits (pc 3b 3.19-eff CE 0.168 vs pt 4b 4.0-eff 0.097); no component separably most-sensitive at 4b (all ΔCE < fp32 std 0.027). The probe's "per-channel buys a bit / attention most sensitive / embedding lossless" are single-seed artifacts. Fixed a latent unreachable-verdict bug (per_channel_advantage_not_separable). Tests: tests/test_ptq_v1175.py (19, incl. the tied-embedding revert guard). Weight-only RTN measures the quality cost only — no memory/speed claim at toy scale.

1186-v1174-minigpt-distill-common-dedup.md
 -> v1174 code explanation: extract shared distillation primitives from v1172/v1173 into distill_common while preserving old imports and focused test contracts.

1185-v1173-minigpt-distillation-uncertainty.md
 -> v1173 code explanation: distillation under aleatoric uncertainty — dark knowledge made real (the mirror of v1172). New distill_v1173.py: build_stochastic_task (Dirichlet P_true, entropy swept), student_P (per-context categorical readout, NOT exact-match), kl_fwd/kl_full (latter charges off-alphabet leakage), beats_lower (KL is lower-is-better → inverts the project's higher-is-better significant), eps_for_entropy, ols_slope_se, decide, run_distill_uncertainty. Reuses distill_v1172 train_student/kl_term/shuffle_residual_mass (train_student extended with a backward-compatible teacher_probs_fn for the oracle arm; v1172's 14 tests stay green). EOS-free completions so the trained/measured KL lives only at the stochastic position. Three-way decomposition: data-efficiency = KL(scratch_hard)−KL(teacher_argmax_hard); DARK KNOWLEDGE = KL(teacher_argmax_hard)−KL(teacher_soft) (same teacher, same 400-sample budget, mode vs soft shape) + controls (label_smooth, shuffled_teacher, oracle_true_P) + a scratch_many sample sweep. Independent inits per (arm,seed); samples re-drawn per seed. Real RTX 4060 (5 seeds, K=32): status=pass, verdict=dark_knowledge_is_data_efficiency_under_uncertainty. teacher KL 0.041; arms: oracle 0.002 / soft 0.050 / label_smooth 1.30 / shuffled 2.42 (HURTS) / argmax 3.52 / scratch_hard 4.48; dark-knowledge term 3.47, grows with entropy (slope lb 3.05>0, confound slope 0.30); scratch_many n=400→0.047≈soft (recovers P = not magic); entropy bias hard/argmax −1.12 (one-hot collapse) vs soft/oracle ≈0. Tests: tests/test_distill_v1173.py (17, incl. the beats_lower direction-bug guard, single-position mask, kl_full leakage, decide verdicts). v1172↔v1173 answer when distillation helps.

1184-v1172-minigpt-distillation.md
 -> v1172 code explanation: knowledge distillation (new capability-transfer axis). A trained teacher (4L/64) distills into a smaller student via per-token Hinton τ² KL (kl_term), vs hard-label SFT, with two disentangling controls — label_smooth (ε matched to teacher confidence) and shuffle_residual_mass (shuffled-teacher: preserve argmax+max-prob+entropy, destroy class identity) — plus a matched-FLOPs scratch_long arm. Each (arm,seed) gets an INDEPENDENT init (seed_base+1009*arm_index+seed) so the unpaired significant() test is valid. On this DETERMINISTIC task the teacher is near-one-hot (max-prob 0.989, entropy 0.037) so dark knowledge is absent by construction. Real RTX 4060 (5 seeds): status=pass (comparison valid), verdict=no_distill_benefit — the CPU probe's single-seed/shared-init +0.058 EVAPORATES and reverses (distill τ1 0.757 < scratch 0.773; τ2 0.803 > τ1, τ ordering flipped → τ is a coupled step-size knob), both controls ≈ baseline, Δ(distill−scratch) negative at every size; and scratch_long (2485 steps) hits 0.949, crushing all distillation arms. The design panel + multi-seed + controls + matched-compute caught the flattering single-seed artifact. Tests: tests/test_distill_v1172.py (KL self-distill=0, τ² scaling, shuffled invariants, independent-init contract, decide() verdicts, smoke). Device fix: teacher_logit_stats moves the batch to the teacher's device.

1183-v1171-minigpt-script-setup-dedup.md
 -> v1171 code explanation: contract-preserving maintenance dedup (the v1159/v1163/v1167 cadence). Extract the single-corpus script setup (build_sft_corpus → CharTokenizer.train → pad/eos → block_size=max(16,…)), repeated byte-identically in 5 of 6 capability-pivot run-scripts, into a new minigpt.script_setup.setup_single_corpus; migrate v1164/v1166/v1168/v1169/v1170 (one call + one import each; drop dead imports, v1169 keeps EOS/INPUT_ALPHABET; reorder build_confusable_preferences after the helper in v1166/68/69, value-neutral). v1165 (dual-corpus/dual-seed) and all *_v11xx.py module bodies left in place (RNG-coupled / duck-typed / below the 3+ rule). RNG-free helper → model-init seeds unchanged; module signatures untouched → existing tests unchanged & green = behavior preserved; adds tests/test_script_setup.py regression guard. The user's proposed large relocations (archive/rename/re-layer 1000+ legacy files, split model.py) were JUDGED and DECLINED on verified facts (src/minigpt=1226 .py not 2467, tests=665 not 1336, model.py=346 lines, sampled legacy module imported by 237 files) — they would break imports at collection, violate the freeze rule, and erase git/forensic history.

1182-v1170-minigpt-spec-decode.md
 -> v1170 code explanation: speculative decoding (resumes the v1161 inference-efficiency thread; not alignment). A small draft proposes K tokens, the target verifies all K in ONE (K+1)-wide forward (re-feeding the block anchor), and an accept/reject rule keeps the output distributed exactly as target-only decoding; on rejection both KV-caches roll back to the accepted prefix. An adversarial design panel re-keyed the GATE off greedy-bitwise-identity (unsound — v1161 already learned ~1e-6 drift flips argmax ties) onto the LOGIT invariant (verify == full forward < 1e-4) + sampling-TV within the noise floor + accept-rule consistency ((1−α^(K+1))/(1−α)), with a shared lowest-index tie-break and a tie-artifact classifier. Real RTX 4060 (3 seeds): status=pass, correctness verified on all four clauses (logit 1.96e-05, greedy 3600/3600 identical, TV within floor, consistency residual 0.22), graded acceptance α 0.58→0.88→1.0 by draft quality. But the PRIMARY FLOPs-honest metric (target_positions_processed) is 1.28× plain, total forwards/token ≈2.1, and wall-clock 0.55× — verified-identical, fewer target CALLS, but a FLOPs/wall-clock LOSS at char-toy scale (the expected honest result far below GPU saturation). Tests migrated from the deleted output/spec_decode_probe/* into tests/test_spec_decode_v1170.py.

1181-v1169-minigpt-reward-model.md
 -> v1169 code explanation: reward modeling + best-of-N (the RLHF component DPO skips). MiniGPT backbone + scalar head, Bradley-Terry loss; exposes a new MiniGPT.features(). HH-RLHF is infeasible on a char-level model, so the same controllable synthetic setting is used. Real RTX 4060 (3 seeds): the RM ranks held-out pairs (in-dist 0.82, off-dist random-reject 0.64 > chance) but in best-of-N the oracle climbs to 0.54 while RM rerank ≈ 0.10 ≈ a random pick — it can't rank a policy's own off-distribution samples. The oracle baseline separates "RM is a bad ranker" from "no correct answer in the pool". Reward models are reliable only on-distribution.

1180-v1168-minigpt-dpo-sft-aux.md
 -> v1168 code explanation: NLL-regularized DPO (DPO+SFT-aux), the upside follow-up to v1166. L = L_DPO + λ·SFT_CE_mean(chosen), with the aux computed as train_sft's token-mean CE fused into the SAME single chosen forward as the DPO summed-logp (so λ=0 reproduces vanilla DPO bit-for-bit and λ→∞ converges to SFT-on-chosen). Design panel was session-limited; the feasibility probe was run on the main thread instead. Real RTX 4060 (3 seeds): the aux RECOVERS the generation vanilla DPO destroys (0.14→0.68, Δlogp(chosen) −23→0) but only MATCHES plain SFT-on-chosen — no capability gain from the preference term at this scale. Promotes `significant` into experiment_utils (its second user).

1179-v1167-minigpt-experiment-utils-dedup.md
 -> v1167 code explanation: contract-preserving maintenance dedup (refactor cadence after v1164/v1165/v1166). Extract the three primitives the multi-seed experiment drivers repeated — mean_std, build_minigpt, clone_state — into a shared minigpt.experiment_utils; migrate v1164/v1165/v1166. Deliberately leaves _significant local to v1166 (single user) and argues build_minigpt's RNG-identity (same constructor wrapped = identical init weights). Existing module tests unchanged and green = behavior preserved.

1178-v1166-minigpt-dpo-preference.md
 -> v1166 code explanation: DPO-lite preference tuning (the loss), on a synthetic correctness signal with confusable hard-negatives. An adversarial design panel (with a real CPU probe) ran before the GPU experiment and falsified the flattering framings. Real RTX 4060 (3 seeds): from a weak SFT init, DPO grows the chosen-vs-rejected margin ~6x but, because it optimizes a RELATIVE margin, log p(chosen) falls and held-out exact-match REGRESSES 0.59->0.10; a matched-compute (forward-pass axis) SFT-on-chosen control rises to 0.76, and the reference/KL term shows no measurable effect at this scale. The margin (not the near-ceiling preference accuracy) is the faithful "did the objective move" gate. Preference accuracy up != capability up.

1177-v1165-minigpt-sft-pretrain-transfer.md
 -> v1165 code explanation: the real two-stage SFT recipe. Pretrain a base LM on {copy,reverse,sort}, then SFT on a HELD-OUT new op (shift-left) — comparing pretrained-base vs from-scratch across an SFT-budget sweep. Pretraining shifts the SFT curve left (data efficiency): 0.31 vs 0.02 at 50 SFT steps, 0.97 vs 0.83 at 1000. Transfer of shared positional-copy primitives + instruction format, not leakage (the new op was never in pretraining).

1176-v1164-minigpt-sft-instruction.md
 -> v1164 code explanation: supervised fine-tuning (SFT) for instruction-following on copy/reverse/sort over UNSEEN inputs, with completion-only loss masking. A training-budget sweep honestly shows the masking advantage is large in the low-compute regime (+0.24 at 150 steps) and shrinks to ~0 by 1500 steps — a low-compute accelerant, not a free lunch. Pivot from the dead-ended RoPE-base recall probe (which honestly hit the predicted learnability risk).

1175-v1163-minigpt-script-runtime-dedup.md
 -> v1163 code explanation: contract-preserving maintenance dedup. Extract the choose_device helper (duplicated 14x) and the torch/numpy/random seed triple into a shared minigpt.script_runtime; migrate the 6 capability-pivot scripts (v1156-v1162), leaving the 8 pre-pivot legacy scripts intentionally out of scope. Existing tests unchanged, full suite 3209 passed.

1174-v1162-minigpt-rope-length-extrapolation.md
 -> v1162 code explanation: honestly measure learned-absolute vs RoPE positions beyond the trained length (5 seeds, length sweep, per-position curves, sliding-window + zeroed-tail diagnostic arms). The true difference is "learned has untrained position rows / RoPE has zero position params and is defined at any index", NOT "RoPE extrapolates longer dependencies" or "learned crashes" — both schemes raise identically beyond block_size, and the realistic sliding-window learned baseline ties RoPE on this no-long-range corpus.

1173-v1161-minigpt-kv-cache.md
 -> v1161 code explanation: add a KV-cache incremental-generation path (forward_cached/generate_cached, RoPE-aware) verified numerically identical to the uncached forward (max logit diff ~1e-6) and ~1.6x faster at scale; correctness gated on logit identity, not argmax-sensitive greedy equality.

1172-v1160-minigpt-rope.md
 -> v1160 code explanation: add RoPE rotary position embeddings to MiniGPT behind a backward-compatible use_rope flag (default off, byte-for-byte old behavior); rope.py primitives, model.py wiring, and an honest held-out comparison where learned positions edge RoPE on short fixed-length sequences (length extrapolation left to a later version).

1171-v1159-minigpt-train-lm-dedup.md
 -> v1159 code explanation: contract-preserving maintenance refactor extracting the training loop duplicated across v1156/v1157/v1158 into a shared minigpt.lm_training.train_lm; existing tests unchanged and green, full suite 3173 passed.

1170-v1158-minigpt-lora-domain-adaptation.md
 -> v1158 code explanation: LoRA domain adaptation across two sentence structures sharing one vocabulary; with the embedding transferable and the gap purely structural, LoRA adapts a frozen base to the target at 7.5% params, matching full fine-tuning and staying reversible — the win v1157 predicted.

1169-v1157-minigpt-lora-heldout-eval.md
 -> v1157 code explanation: a templated corpus with a true held-out split plus a validated held-out generalization eval; three-arm base/full-finetune/LoRA comparison shows all-linear LoRA captures ~5% of full-finetune's held-out gain on the tied-embedding model.

1168-v1156-minigpt-lora-finetune.md
 -> v1156 code explanation: from-scratch LoRA fine-tuning for MiniGPT, freezing the base and training ~2.9% of params to reduce training loss on a real GPU run; starts the real-model-capability direction.

1167-v1155-unassisted-loss-suffix-repair-replay-comparison.md
 -> v1155 code explanation: replay the v1154 checkpoint against v1153 target-free holdout prompts and preserve the partial-signal boundary.

1166-v1154-unassisted-loss-suffix-repair-training-run.md
 -> v1154 code explanation: train the repaired corpus into a bounded checkpoint while keeping the result in the training-artifact-only lane.

1165-v1153-unassisted-loss-suffix-repair-seed.md
 -> v1153 code explanation: materialize the loss-suffix repair seed from the v1152 diagnostic while keeping holdout prompts target-free.

1164-v1152-unassisted-holdout-repair-partial-signal-diagnostic.md
 -> v1152 code explanation: diagnose the v1151 fixed-only partial signal and route the missing loss suffix into the next bounded repair action.

1163-v1151-unassisted-holdout-repair-replay-comparison.md
 -> v1151 code explanation: replay the v1149 target-free holdout prompts against the v1150 checkpoint and classify the result as partial fixed-only signal.

1162-v1150-unassisted-holdout-repair-training-run.md
 -> v1150 code explanation: run bounded CPU training from the v1149 repair seed corpus and hand off the checkpoint for replay comparison without claiming promotion.

1161-v1149-unassisted-holdout-repair-seed-corpus.md
 -> v1149 code explanation: materialize the v1148 repair blueprint into corpus/jsonl/holdout prompt files for the next bounded training run.

1160-v1148-unassisted-holdout-repair-plan.md
 -> v1148 code explanation: turn the v1147 unassisted fixed/loss gap into a repair plan and seed blueprint without claiming promotion.

1159-v1147-decoder-anchor-holdout-comparison.md
 -> v1147 code explanation: compare decoder-anchor fragment evidence against unassisted holdout replay on the same v1145 checkpoint.

1158-v1146-decoder-anchor-probe.md
 -> v1146 code explanation: run a decoder-anchor local fragment probe against the v1145 checkpoint without claiming promotion.

1157-v1145-loss-signal-bridge-decoder-anchor-distribution.md
 -> v1145 code explanation: run bounded loss-signal training and decoder-anchor distribution evidence after the v1144 holdout scorecard smoke.

1156-v1144-holdout-scorecard-smoke.md
 -> v1144 code explanation: run five real MiniGPT holdout smoke generations and feed them into the existing benchmark scorecard.

1155-v1143-required-term-real-execution.md
 -> v1143 code explanation: run the first bounded real required-term coverage execution for capability-regression-01 without claiming promotion.

1154-v1142-model-capability-cadence-watch.md
 -> v1142 code explanation: publish cadence watch due list after v1141 loop closure and stop for roadmap review.

1153-v1141-model-capability-regression-loop-trend.md
 -> v1141 code explanation: verify the v1135-v1139 model capability regression loop as closed read-only evidence.

1152-v1140-report-loader-dedup.md
 -> v1140 code explanation: deduplicate report loader helpers for v1135-v1139 regression modules without changing public contracts.

1151-v1139-model-capability-regression-followup-closeout.md
 -> v1139 code explanation: close the pre-execution model capability regression follow-up chain without claiming model promotion.

1150-v1138-model-capability-regression-suite-readiness.md
 -> v1138 code explanation: check source/test path readiness for the bounded regression suite manifest.

1149-v1137-model-capability-regression-suite-manifest.md
 -> v1137 code explanation: build a bounded suite manifest from model capability regression inventory rows.

1148-v1136-model-capability-regression-inventory.md
 -> v1136 code explanation: inventory existing evidence for the bounded model capability regression plan.

1147-v1135-model-capability-regression-plan.md
 -> v1135 code explanation: turn the v1133 cadence watch into a bounded model capability regression plan.

1146-v1134-artifact-map.md
 -> v1134 code explanation: build an artifact map for recent f/ version evidence folders.

1145-v1133-model-capability-cadence.md
 -> v1133 code explanation: add a cadence check that schedules model capability regression after long governance or maintenance runs.

1144-v1132-publication-receipt-template.md
 -> v1132 code explanation: add a publication receipt template and verify script layer readiness.

1143-v1131-project-docs-readability.md
 -> v1131 code explanation: split stable reader docs and verify README navigation links.

1142-v1130-publication-naming-readability.md
 -> v1130 code explanation: stop new publication naming sprawl with a readable scanner and short-alias policy.
