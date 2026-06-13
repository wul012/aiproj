# 1170 · v1158 · MiniGPT LoRA 领域自适应

## 本版目标与不做什么

[[1169-v1157-minigpt-lora-heldout-eval]] 用一个被验证为可信的 held-out 评估工具得出一个诚实但不好看的结论：在 MiniGPT 这种 token embedding 与输出头权重绑定的微型字符模型上，即使适配全部 attention+MLP 线性层，LoRA 也只拿到全参微调约 5% 的泛化收益——因为需要改动的信号大量落在被 LoRA 冻结的 embedding 上。v1157 因此明确把下一步指向“在 LoRA 真正擅长的场景里验证它”。

v1158 就做这件事：构造一个**纯结构性**的领域差距——源域 A 和目标域 B 使用完全相同的字符词表，只是语序不同。这样基座在 A 上训练得到的（绑定）embedding 能原样迁移到 B，A 与 B 之间唯一的差距是“词序/结构”，而这正是注意力与 MLP（也就是 LoRA 能触达的层）负责的部分。于是本版要回答的问题是：当 embedding 不再是瓶颈时，LoRA 能不能用很小的参数代价把一个冻结的通用模型自适应到新领域。

本版明确不做：不修改基座结构、不向 B 引入 A 没有的新字符（否则又退回 v1157 的冻结-embedding 困境）、不把全参微调精调成上界后再比较、不靠调参制造胜负。先确认真实存在领域差距，再诚实比较 base / 全参微调 / LoRA。

## 本版来自哪条路线

直接承接 v1157 写下的 v1158 方向，复用 v1157 建立的基础设施：`templated_corpus.py` 的模板化语料与 held-out 切分、`heldout_eval.py` 的 held-out 损失与下一字符准确率、`lora.py` 的 `target_all_linear` 全线性层适配，以及统一的 `write_readability_outputs` 产物写出器。

## 关键新增 / 修改文件与链路角色

- `src/minigpt/templated_corpus.py`（修改）：抽出 `STRUCTURES` 模板字典，新增 `reordered` 结构，并给 `build_templated_corpus` 增加 `structure` 参数。`declarative` 模板与 v1157 逐字节一致，保证 v1157 的语料和测试不受影响；`reordered` 用相同的词池与标点、不同的语序，从而与 `declarative` 拥有完全相同的字符集合。
- `src/minigpt/lora_domain_adaptation_v1158.py`：领域自适应编排。训练基座于 A → 在 A、B 两个 held-out 上评估基座（确认领域差距）→ 从冻结基座的两份副本分别做全参微调和 LoRA 适配到 B → 在 B held-out 上比较，并测量 LoRA 适配后在 A 上的“可逆遗忘”。
- `scripts/run_lora_domain_adaptation_v1158.py`：真实运行入口，用同一个在 A+B 全文上训练的 tokenizer（词表本来就相同），把两域的 train/held-out 文本编码后交给编排函数。
- `tests/test_lora_domain_adaptation_v1158.py`：覆盖“两结构共享词表但文本不同”“未知结构报错”，以及领域自适应的核心断言。

## 核心数据结构与字段语义

两个结构模板共享词池与标点，因此 `set(A.full_text) == set(B.full_text)`——这是本版设计的关键，它把 embedding 这个变量从实验里消掉，只留下结构这一个变量。

编排函数返回的报告 summary 中：`domain_gap = base_target_loss - base_source_loss` 衡量“基座在 B 上比在 A 上差多少”，是“领域差距是否真实存在”的前置条件；`lora_target_loss_delta = lora_target_loss - base_target_loss`（应为较大负值）是 LoRA 自适应的收益；`full_target_loss_delta` 是全参微调参考的收益；`lora_vs_full_capture_ratio = lora_delta / full_delta` 表示 LoRA 拿到了参考收益的几成；`adapter_forgetting_on_source = lora_source_loss_after - base_source_loss` 衡量带 adapter 时源域退化了多少——但因为基座冻结，这个退化是可逆的：摘掉 adapter 即恢复原模型。

判定逻辑：`gap_present = domain_gap > 0.1`（必须有真实差距才算有效演示），`lora_adapted = lora_target_loss_delta < -0.05`（LoRA 必须实质性降低目标域损失），两者都满足才 `status=pass`、`decision=lora_domain_adaptation_succeeded`。

## 运行流程与真实结果

脚本用 `declarative` 建源域、`reordered` 建目标域，在两域全文上训练共享 tokenizer（词表 64），把四段文本（A-train/A-held/B-train/B-held）编码成 token 张量。编排函数先在 A-train 上训练基座 400 步，分别在 A、B held-out 上评估；再用 `copy.deepcopy` 复制两份起点相同的冻结基座，一份全参微调、一份套全线性层 LoRA，各在 B-train 上训练 400 步，最后在 B held-out（以及 LoRA 在 A held-out）上评估。

真实 GPU 结果：基座 A held-out loss 0.883，B held-out loss 3.988（domain_gap 3.105，B 准确率仅 0.462）；全参微调把 B 降到 1.182；LoRA（16 个线性层，7.5% 可训练参数）把 B 降到 0.892（准确率 0.700），capture 比例 1.10。LoRA 在目标域 held-out 上达到甚至略优于全参微调参考。带 adapter 时 A held-out 升到 3.756，但摘掉 adapter 可精确恢复原 A 模型。

## 关键检查项与诚实边界

需要诚实说明：这里的全参微调是“参考”而不是精调到收敛的上界（lr 3e-4、400 步），因此“LoRA ≥ 全参微调”不能被过度解读为“LoRA 永远更强”。诚实的表述是：在这个结构性领域差距上，LoRA 用 7.5% 的可训练参数达到了与全参微调参考相当甚至略好的目标域泛化，并且保持可逆。把 v1157（LoRA 因冻结 embedding 而吃亏）和 v1158（embedding 可迁移、差距结构化、LoRA 取胜）放在一起，正好讲清了 LoRA 价值的真实边界：它解决的是“在保留通用能力的前提下，用极小代价适配到结构性新任务/新域”的问题。

另需记下一笔工程债：训练循环 `_train` 现在在 v1156 脚本、v1157 模块、v1158 模块里重复了三次。按 AGENTS.md 的节奏，v1159 适合做一次小的去重/保养版本，把它抽成共享的 `train_lm` 工具。

## 测试如何真实覆盖链路

`test_lora_domain_adaptation_v1158` 在 CPU 小配置上验证：两结构共享完全相同的字符词表但首句文本不同；未知结构名报错；基座在 B 上确实比 A 差（`domain_gap > 0.1`），LoRA 实质性降低目标域 held-out loss（delta `< -0.05`）从而 `domain_adaptation_succeeded=True`、`status=pass`、`decision=lora_domain_adaptation_succeeded`，可训练占比 < 50%；以及报告含 5 行 arm×domain、关键字段齐全、csv 字段名固定。这些断言把“领域差距真实存在”和“LoRA 真的把差距补上了”这两件事钉死，而不是只看一个可能被噪声左右的数字。

## 一句话总结

v1158 兑现了 v1157 的预测：当领域差距是结构性的、embedding 可原样迁移时，LoRA 用 7.5% 的参数把目标域 held-out loss 从 3.99 降到 0.89、准确率从 0.46 提到 0.70，达到全参微调参考水平且保持可逆——干净、诚实地证明了 LoRA 的真实价值与边界。
