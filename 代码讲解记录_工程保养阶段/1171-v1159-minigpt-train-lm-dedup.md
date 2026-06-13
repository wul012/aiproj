# 1171 · v1159 · train_lm 训练循环去重保养

## 本版目标与不做什么

[[1168-v1156-minigpt-lora-finetune]]、[[1169-v1157-minigpt-lora-heldout-eval]] 和 [[1170-v1158-minigpt-lora-domain-adaptation]] 连续三版都各自写了一份几乎一模一样的“语言模型训练循环”：建 AdamW、`model.train()`、循环里 `get_batch` → 前向拿 loss → `zero_grad` → `backward` → `step` → 记录 last loss。v1158 的讲解里已经把这笔重复债记下来了。本版按 AGENTS.md 的节奏（3-4 个功能版本后做 1 个契约保持的重构版本）来还债：把这三份重复抽成一个共享的 `minigpt.lm_training.train_lm`。

本版明确不做：不新增任何模型能力、不改训练超参或随机种子语义、不改动任何报告产物（json/csv/html/md/txt）的结构、不碰 `model.py` 基座。它是一次纯粹的契约保持重构——对外行为必须逐字节等价，唯一的变化是“同一段逻辑只存在一处”。

## 为什么现在做

重复的训练循环有三个现实代价：一是任何一处要修 bug（比如 `set_to_none`、loss 为 None 的处理、日志格式）都要改三处且容易漏；二是后续模型能力版本（SFT、更大规模训练、RoPE/KV-cache 实验）还会继续复制这段，债越滚越大；三是阅读成本——读者在三个文件里看到三段近似代码，会怀疑它们是否真的等价。趁刚好攒满三版、且行为已被各自测试钉死的时机抽出来，是成本最低、风险最小的窗口。

## 关键新增 / 修改文件与链路角色

- `src/minigpt/lm_training.py`（新增）：唯一的训练循环实现。`train_lm(model, params, data, *, steps, lr, batch_size, block_size, device, log_every=None, label="train") -> float`。它训练“传进来的 params”而不自己决定冻结谁——全量训练就传 `model.parameters()`，adapter-only 就传 `lora_parameters(model)`，冻结由调用方（如 `mark_only_lora_as_trainable`）负责。这条边界很重要：训练循环不该越权决定哪些参数可训。
- `scripts/run_lora_finetune_v1156.py`（修改）：删除 `train_base`，main 里改调 `train_lm(model, list(model.parameters()), ..., log_every=max(1, base_steps//5), label="base")`，保留原来的 `[base] step=...` 进度打印。
- `src/minigpt/lora_heldout_eval_v1157.py`（修改）：删除私有 `_train`，base/full/lora 三处调用改用 `train_lm`。
- `src/minigpt/lora_domain_adaptation_v1158.py`（修改）：同样删除 `_train`，base/full/lora 三处调用改用 `train_lm`。
- `tests/test_lm_training.py`（新增）：覆盖共享实现的核心契约。

## 核心设计决策

第一，参数显式传入而非内部固定。三个调用方需求不同：v1156 全量训练基座、v1157 既要全量也要 adapter-only、v1158 三臂都用。把 `params` 作为显式参数，`train_lm` 就能同时服务“全参微调”和“LoRA 微调”，AdamW 也只会更新传入的张量——这正是 LoRA 那条“base 冻结、只更新 adapter”契约的落点。

第二，把日志统一进去。v1156 脚本原先在循环里按 `step % (steps//5)` 打印进度，而 v1157/v1158 静默。如果把打印留在调用方，就又要在调用方复制一段判断。于是给 `train_lm` 加可选的 `log_every` 和 `label`：为 None 时完全静默（v1157/v1158 行为不变），为正数时在首步、末步和每 `log_every` 步打印 `[label] step= loss=`（v1156 行为不变）。这样三个调用方的差异被一个参数吸收，而不是再分叉出两份代码。

第三，加一处防御。原三份循环默认 `model(x, y)` 一定返回 loss；共享实现里显式检查 `loss is None` 并抛 `RuntimeError`，让“忘了传 targets”这类错误在训练循环里就暴露，而不是在更远处以难懂的方式炸开。这是收敛带来的小幅净改善，不改变正常路径行为。

## 契约保持如何被证明

重构版本最重要的不是“新写了什么”，而是“证明行为没变”。本版的证据链是：v1156、v1157、v1158 的既有测试**一行未改**仍全部通过——这些测试断言的是 LoRA 降损、base 逐字节冻结、held-out 工具有效、领域自适应成功等行为，它们绿就说明训练循环替换没有改变任何对外可观察的行为。全量测试 `3173 passed`（相比 v1158 的 3170，净增的 3 条正是 `test_lm_training` 的新增，既有数量未减说明没有删改其它测试来“迁就”重构）。此外 v1156 脚本 smoke 仍打印 `[base] step=...` 进度、输出 `status=pass`、保存 adapter，肉眼可见行为一致。

## 测试如何真实覆盖链路

`test_lm_training` 钉死三件事：在可记忆的重复序列上，`train_lm` 多步训练后的 loss 低于 1 步（确实在学且返回 float）；只把某个注意力块的参数传进去时，未传入的 `token_embedding.weight` 在训练后逐字节不变（验证“只更新传入的 params”这条契约，也正是 LoRA 冻结 base 的底层保证）；带 `log_every` 的日志路径不抛错。前两条尤其关键——它们把“训练循环只动该动的参数”这条容易被悄悄破坏的不变量固定下来。

## 一句话总结

v1159 把 v1156-v1158 三份重复的训练循环收敛成一个 `train_lm`，既有测试零改动全绿、full suite 3173 通过、v1156 脚本行为一致——在不动任何对外行为的前提下还清了重复债，给后续模型能力版本留下一个干净、单一来源的训练底座。
