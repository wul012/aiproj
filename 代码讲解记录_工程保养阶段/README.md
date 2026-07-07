# MiniGPT 代码讲解记录_工程保养阶段

本目录从 v1130 开始承接 MiniGPT 的工程后期保养讲解，重点覆盖命名止血、README/docs 拆分、scripts 分层、publication receipt 模板化、模型能力回归节奏和 artifact 对照表。

上一阶段 `代码讲解记录_模型治理阶段/` 保留 v1098-v1129 的模型治理和 publication receipt 讲解，不回头迁移旧文件。

## 写入规则

- 编号继续沿用全局序号，从 `1142-v1130-...` 开始。
- 本阶段讲解默认用中文书写，继续写清目标、边界、入口、输出模型、测试覆盖、运行证据和一句话总结。
- 保养版本不追求大规模重构，优先用可运行检查、入口分层、索引和模板降低阅读成本。
- 对历史长命名和历史目录只做止血、索引、说明和低风险桥接，不在没有兼容迁移时强行改名或搬迁。

## 当前索引

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
