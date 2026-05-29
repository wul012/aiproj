# v490 model capability required-term prompt-leading training

## 本版目标和边界

v490 的目标是把 v489 的 prompt-leading corpus 真正送进 tiny training，并回答一个很具体的问题：当训练语料每一行都以 probe 使用的 scaffold prompt 开头后，required-term continuation 是否比 v488 的 `0/9` baseline 改善。

本版不新增治理链，也不把“checkpoint 能生成”包装成模型能力提升。判断口径只有一个：`continuation_hit_count` 是否在 prompt 后的新文本中命中 required term。prompt 本身包含 term、generated 全文包含 prompt，不能作为能力提升证据。

## 前置路线

- v487：构造 balanced corpus，去掉 legacy repeat 的高重复问题。
- v488：用 v487 corpus 训练，结果 `continuation_hit_count=0`，并诊断出 `prompt_alignment_ready=False`、`prompt_leading_line_count=0`。
- v489：重建 prompt-leading corpus，把 `prompt_alignment_ready` 修到 `True`，`prompt_leading_line_count=360`。
- v490：训练 v489 corpus，并与 v488 的 no-uptake baseline 对比。

## 关键文件

- `src/minigpt/model_capability_required_term_prompt_leading_training.py`
  - 负责读取 v489 report、解析 corpus 路径、训练 tiny checkpoint、生成 required-term probe rows，并汇总当前结果与 v488 baseline 的 delta。
- `src/minigpt/model_capability_required_term_prompt_leading_training_artifacts.py`
  - 负责把 report 写成 JSON、CSV、text、Markdown 和 HTML。
- `scripts/run_model_capability_required_term_prompt_leading_training.py`
  - 命令行入口，支持 `--force`、`--require-pass` 和训练参数。
- `tests/test_model_capability_required_term_prompt_leading_training.py`
  - 用 fake train / fake generate 覆盖结构通过、命中改善、无命中、输入缺失、alignment 未就绪和产物写出。
- `e/490/`
  - 保存真实训练产物、报告、CLI 输出和运行截图。

## 输入输出和字段语义

输入是 v489 的 `model_capability_required_term_prompt_leading_corpus.json`。核心字段包括：

- `corpus.path`：真实训练语料路径。
- `term_rows`：每个 required term 的 `case`、`term`、`scaffold_prompt` 和 prompt-leading 行数。
- `summary.prompt_alignment_ready`：是否所有 term 都有以 scaffold prompt 开头的训练行。
- `source_report`：回溯到 v488 balanced training report，用于读取 baseline continuation hit。

v490 report 的关键输出：

- `training`：训练命令、checkpoint、tokenizer、metrics、train_config 和日志路径。
- `generation_rows`：每个 term 的 prompt、generated、continuation、prompt hit、generated hit 和 continuation hit。
- `summary.previous_continuation_hit_count`：v488 baseline 的 continuation hit。
- `summary.continuation_hit_count`：v490 当前训练后的 continuation hit。
- `summary.continuation_hit_delta`：当前结果减去 v488 baseline。
- `interpretation.model_quality_claim`：本版是否允许提出模型能力信号。真实结果为 `not_claimed`。

## 运行流程

1. CLI 定位 v489 report 文件。
2. builder 解析 `term_rows` 和 `corpus.path`。
3. 通过 `source_report` 回溯 v488 report，读取 previous baseline。
4. 调用已有 `_train_micro_checkpoint` 训练 tiny checkpoint。
5. 对 9 个 required term prompt 调用已有 `_generation_row`。
6. 统计 continuation hit、baseline delta、checkpoint/tokenizer/metrics 存在性。
7. 写出 JSON/CSV/text/Markdown/HTML，并把真实 checkpoint 保留在 v490 证据目录。

## 真实结果

```text
status=pass
decision=required_term_prompt_leading_training_completed_without_uptake
prompt_leading_training_decision=prompt_leading_training_completed_without_uptake
term_count=9
generation_count=9
continuation_hit_count=0
previous_continuation_hit_count=0
continuation_hit_delta=0
training_status=pass
checkpoint_exists=True
prompt_alignment_ready=True
prompt_leading_line_count=360
model_quality_claim=not_claimed
```

这组结果说明 v490 的训练和报告链路是通的，但模型能力没有提升。v489 修复的是“训练输入和 probe prefix 不一致”的工程问题；v490 证明这个修复单独不足以让 tiny model 在短续写里输出 required terms。

## 测试覆盖

单测保护了几个关键边界：

- fake generation 命中 term 时，决策必须变成 `required_term_prompt_leading_training_improved`。
- fake generation 不命中时，结构仍然 `pass`，但能力决策必须保持 no-uptake。
- corpus 文件缺失时，`--require-pass` 对应的结构失败可返回非零。
- source prompt alignment 未就绪时，训练前必须标记输入问题。
- JSON/CSV/text/Markdown/HTML 都必须真实写出。

这些测试避免 v490 把“训练成功”误判成“能力提升”，也避免把 v489 的 corpus alignment 问题带入下一轮训练。

## 证据角色

- JSON 是后续脚本消费的主证据。
- CSV 用于逐 term 查看生成结果。
- HTML 和截图用于人工复核报告可读性。
- `checkpoint.pt` 是本次真实 tiny training 产物，但它本身不是能力提升证明。
- `说明.md` 和本讲解负责说明边界：v490 是 negative result，不是成功提升模型质量。

## 一句话总结

v490 把 v489 的 prompt-leading corpus 送进真实 tiny training，证明 prefix alignment 已修复但 required-term continuation 仍未改善，下一步应调整训练预算或语料模板，而不是继续堆报告。
