# MiniGPT 代码讲解记录_工程保养阶段

本目录从 v1130 开始承接 MiniGPT 的工程后期保养讲解，重点覆盖命名止血、README/docs 拆分、scripts 分层、publication receipt 模板化、模型能力回归节奏和 artifact 对照表。

上一阶段 `代码讲解记录_模型治理阶段/` 保留 v1098-v1129 的模型治理和 publication receipt 讲解，不回头迁移旧文件。

## 写入规则

- 编号继续沿用全局序号，从 `1142-v1130-...` 开始。
- 本阶段讲解默认用中文书写，继续写清目标、边界、入口、输出模型、测试覆盖、运行证据和一句话总结。
- 保养版本不追求大规模重构，优先用可运行检查、入口分层、索引和模板降低阅读成本。
- 对历史长命名和历史目录只做止血、索引、说明和低风险桥接，不在没有兼容迁移时强行改名或搬迁。

## 当前索引

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
