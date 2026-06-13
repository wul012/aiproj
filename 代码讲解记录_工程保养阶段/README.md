# MiniGPT 代码讲解记录_工程保养阶段

本目录从 v1130 开始承接 MiniGPT 的工程后期保养讲解，重点覆盖命名止血、README/docs 拆分、scripts 分层、publication receipt 模板化、模型能力回归节奏和 artifact 对照表。

上一阶段 `代码讲解记录_模型治理阶段/` 保留 v1098-v1129 的模型治理和 publication receipt 讲解，不回头迁移旧文件。

## 写入规则

- 编号继续沿用全局序号，从 `1142-v1130-...` 开始。
- 本阶段讲解默认用中文书写，继续写清目标、边界、入口、输出模型、测试覆盖、运行证据和一句话总结。
- 保养版本不追求大规模重构，优先用可运行检查、入口分层、索引和模板降低阅读成本。
- 对历史长命名和历史目录只做止血、索引、说明和低风险桥接，不在没有兼容迁移时强行改名或搬迁。

## 当前索引

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
