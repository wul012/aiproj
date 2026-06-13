# 1169 · v1157 · MiniGPT LoRA held-out 泛化评估

## 本版目标与不做什么

v1156 给 MiniGPT 加上了从零实现的 LoRA，并用真实 GPU 训练证明 adapter 能降低训练损失。但 v1156 留了一个诚实的缺口：bundled 语料只有 507 字符，验证集被过拟合主导，验证损失不是可靠的泛化信号，所以那一版只敢用训练损失下结论。v1157 的目标就是把这个缺口补上——构造一个更大的、带真实 held-out 切分的语料，建立一个可信的泛化评估工具，并用“基座 / 全参微调 / LoRA”三臂对照，在不相交的 held-out 集上测量损失与下一字符准确率。

本版明确不做的事：不声称“LoRA 一定赢”，不去调参把一个噪声级别的改善包装成成功，不修改 `model.py` 的基座结构，不引入自然语言大语料（那是更后面的步骤）。本版优先把“评估这件事本身”做对、做可信，再诚实报告 LoRA 的真实表现。这是一次刻意的取舍：一个可信的评估工具，比一个被精心挑选出来的“好看数字”更有价值。

## 本版来自哪条路线

本版直接承接 [[1168-v1156-minigpt-lora-finetune]] 写下的下一步：引入更大真实数据集与 held-out 评估，让 LoRA 的泛化收益可被真实衡量。它复用 v1156 的 `minigpt.lora`（`apply_lora`、`mark_only_lora_as_trainable`、`count_parameters`、`lora_parameters`）和 `LoRAFinetuneConfig`，复用统一的 `readability_report_artifacts.write_readability_outputs` 产物写出器，并新建语料与评估两块基础设施。

## 关键新增 / 修改文件与链路角色

- `src/minigpt/templated_corpus.py`：确定性模板化语料生成器。用“时间、主语、动词、宾语”四个轴的小语法组合出句子，按句子切分成 train / held-out 两半。同一 seed 永远得到同一切分，便于复现与测试。
- `src/minigpt/heldout_eval.py`：held-out 指标计算。在不重叠窗口上算 per-token 交叉熵损失与 next-token top-1 准确率。
- `src/minigpt/lora_heldout_eval_v1157.py`：三臂对照编排。训练欠拟合基座 → 评估基座 → 从同一基座的副本分别做全参微调和 LoRA 微调 → 各自评估 → 组装报告。
- `src/minigpt/lora.py`（修改）：给 `LoRAConfig` 增加 `target_all_linear` 与 `exclude_modules`，并把匹配逻辑收敛到 `LoRAConfig.matches`；`apply_lora` 改为可适配全部 `nn.Linear`（默认排除与 embedding 绑定的 `lm_head`），并跳过已包裹的 `LoRALinear` 以防二次包裹。
- `scripts/run_lora_heldout_eval_v1157.py`：真实运行入口，默认适配全部线性层，可用 `--attention-only` 退回 v1156 的注意力-only 行为。
- 测试：`tests/test_templated_corpus.py`、`tests/test_heldout_eval.py`、`tests/test_lora_heldout_eval_v1157.py`，以及对 `target_all_linear` 的新增断言。

## 核心数据结构与字段语义

`TemplatedCorpus` 持有 `train_text` / `heldout_text` 与对应的句子列表。关键在于“按句子切分”：held-out 句子与训练句子是不相交的组合，但共享同一套字符词表与语法，因此 held-out 是“同分布但未见过”的序列，held-out 损失才真正反映泛化而非记忆。`stats()` 报告训练/保留字符数与词表大小。

`evaluate_heldout` 在长度为 `block_size` 的不重叠窗口上前向，累加 `loss * token 数` 求加权平均得到 `heldout_loss`，用 `argmax(logits) == y` 统计 `heldout_token_accuracy`，并返回 `heldout_token_count` / `heldout_window_count` 便于核对覆盖。

`LoRAConfig.matches(child_name)` 是本版新增的匹配中枢：先按 `exclude_modules` 排除（默认排除 `lm_head`），再根据 `target_all_linear` 决定是“匹配全部线性层”还是“只匹配 `target_modules` 里点名的层”。这样既保留 v1156 的注意力-only 默认，又开放“适配全部 attention+MLP 线性层”这一更接近真实实践的选项。

报告 dict 的字段语义：`harness_valid` 表示“全参微调把 held-out 损失压低到了远超噪声的程度”，是本版判定 `status=pass`/`decision=heldout_eval_harness_validated` 的依据；`lora_vs_full_capture_ratio = (lora_delta / full_delta)` 表示 LoRA 拿到了全参微调泛化收益的几成；`lora_verdict` 把 LoRA 结果分成 `lora_matches_full_finetune`（≥50%）、`lora_partial_gain`（>0）、`lora_no_gain` 三档。`rows` 给出 base / full_finetune / lora 三行的 held-out 损失、准确率、可训练参数数。

## 运行流程与真实结果

入口脚本先用确定性语料生成器写出 `data/templated_corpus_v1157.txt`，在全文上训练 `CharTokenizer`（保证 held-out 字符全部在词表内、不出 `<unk>`），把 train/held-out 文本各自编码成 token 张量。编排函数先把基座欠拟合训练（默认 30 步），评估其 held-out；再用 `copy.deepcopy` 复制出两份起点相同的基座，一份做全参微调、一份套全线性层 LoRA，各训练相同步数后分别评估。

真实 GPU 结果：基座 held-out loss 2.0589；全参微调降到 1.2284（delta −0.8305，acc 0.6843）；LoRA 适配全部 16 个 attention+MLP 线性层、7.5% 可训练参数，降到 2.0160（delta −0.0428，acc 0.6820）；capture 比例约 5.1%，`lora_verdict=lora_partial_gain`，`harness_valid=True`。

## 关键检查项与诚实结论

本版最重要的判断是把 `status=pass` 的含义钉死为“评估工具可信”，而不是“LoRA 赢了”。全参微调把 held-out 损失压低 0.83，这一步本身证明 held-out 指标会对真实学习作出明显反应，从根上修掉了 v1156 的噪声问题。

而 LoRA 的诚实结论是：即使适配了全部 attention+MLP 线性层，它也只拿到全参微调泛化收益的约 5%。原因是结构性的——MiniGPT 的 token embedding 与输出头是权重绑定的，LoRA 把它冻结了，而字符级模型的大部分可学信号恰好落在 embedding/输出头上，LoRA 够不到。这不是实现 bug，而是“LoRA 该适配哪些层”的真实工程教训，也指明了 v1158 的方向：在 LoRA 真正擅长的领域自适应场景里验证它，或把适配范围扩展到 embedding/输出头。

## 测试如何真实覆盖链路

`test_templated_corpus` 钉死确定性（同 seed 同输出）、不同 seed 改变切分、train/held-out 句子集合不相交、held-out 字符被全文与训练文本覆盖、规模合理、非法比例报错。`test_heldout_eval` 用一个“永远预测对”的桩模型验证准确率为 1.0、损失趋近 0，用已知长度的流验证 `heldout_token_count`，并用真实小模型验证指标落在合理区间、对过短流报错。`test_lora_heldout_eval_v1157` 在 CPU 小配置上验证：全参微调把 held-out 损失压低到阈值以下从而 `harness_valid=True`、`status=pass`，三行 stage 顺序正确，`lora_verdict` 落在三档之一，适配层数为 8（2 层 × 4 线性）。`test_lora` 新增断言验证 `target_all_linear` 覆盖的模块严格多于注意力-only，且始终排除与 embedding 绑定的 `lm_head`。

## 一句话总结

v1157 交付了一个被全参微调验证为可信的 held-out 泛化评估工具，并用三臂对照诚实量化出“在权重绑定的微型字符模型上，attention+MLP 的 LoRA 只拿到全参微调约 5% 的泛化收益”——把评估做对，把结论说实话，为 v1158 指明了让 LoRA 真正发挥价值的方向。
