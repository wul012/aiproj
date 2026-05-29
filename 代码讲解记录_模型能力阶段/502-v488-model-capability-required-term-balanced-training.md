# v488：model capability required-term balanced training

## 本版目标和边界

v488 的目标是把 v487 的 balanced corpus candidate 真正送进 tiny training，再检查 required-term continuation 是否出现。v487 已经把 legacy repeat corpus 的重复问题收束掉，但还没有训练新 checkpoint。v488 补上这一步，并且在报告中记录 prompt-alignment 诊断。

本版不做 held-out claim，不扩大模型规模，也不宣称模型质量提升。它只回答：用 v487 balanced corpus 训练后，短 scaffold prompt 能否续写 required term；如果不能，失败原因是否可定位。

## 前置能力

本版承接：

- v483：legacy scaffold-to-term 微训练出现 `4/20` continuation hit。
- v486：最佳 split 的训练侧 hit 只在 `1/3` seed 上复现。
- v487：构造 balanced corpus，唯一行率从 `0.133` 提升到 `1.0`，term-line spread 为 `0`。

v488 发现 v487 的一个新边界：语料虽然平衡，但 prompt 没有出现在行首。

## 关键新增文件

- `src/minigpt/model_capability_required_term_balanced_training.py`
  - 核心训练和 probe 逻辑。
  - 输入 v487 balanced corpus report。
  - 解析 `corpus.path` 和 `term_rows`。
  - 复用 `_train_micro_checkpoint()` 训练 tiny checkpoint。
  - 复用 `_generation_row()` 对每个 term row 做 generation probe。
  - 计算 continuation hit、prompt alignment、checkpoint/tokenizer/metrics 存在性。

- `src/minigpt/model_capability_required_term_balanced_training_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 报告展示训练证据、prompt alignment、generation rows 和下一步。

- `scripts/run_model_capability_required_term_balanced_training.py`
  - CLI 入口。
  - 支持训练参数、生成参数、`--require-pass` 和 `--force`。

- `tests/test_model_capability_required_term_balanced_training.py`
  - 用 fake train/generate 覆盖命中、未命中、缺 corpus、artifact 输出、路径定位和 prompt alignment 缺失。

## 核心数据结构

最终报告为：

```text
model_capability_required_term_balanced_training.json
```

关键字段：

- `source_required_term_balanced_corpus`
  - 指向 v487 balanced corpus JSON。

- `source_corpus`
  - 记录 corpus path、line count、unique line rate、term line spread。
  - 新增 `prompt_leading_line_count`、`prompt_aligned_term_count`、`prompt_alignment_ready`。

- `training`
  - 训练命令、stdout/stderr、checkpoint、tokenizer、metrics、train config。

- `generation_rows`
  - 每个 required term 一行。
  - 记录 prompt、generated、continuation、prompt hit、generated hit、continuation hit 和预览。

- `summary`
  - `continuation_hit_count`：真正续写命中的 required term 数。
  - `generated_hit_count`：完整 generated 文本命中数，注意这可能来自 prompt 本身。
  - `prompt_alignment_ready`：语料中是否存在每个 scaffold prompt 开头的训练行。

## 运行流程

1. CLI 读取 v487 balanced corpus report。
2. 解析 `required_term_balanced_corpus.txt`。
3. 检查 corpus 中是否有以每个 `scaffold_prompt` 开头的行。
4. 用 v487 corpus 训练 tiny checkpoint。
5. 对 9 个 term row 做短 continuation generation。
6. 汇总 continuation hit 和 prompt alignment。
7. 输出 JSON/CSV/text/Markdown/HTML 证据。

## v488 真实运行结果

真实命令输出：

```text
status=pass
decision=required_term_balanced_training_completed_without_uptake
balanced_training_decision=balanced_training_completed_without_uptake
term_count=9
generation_count=9
continuation_hit_count=0
generated_hit_count=9
continuation_hit_rate=0.0
training_status=pass
checkpoint_exists=True
prompt_alignment_ready=False
prompt_leading_line_count=0
model_quality_claim=not_claimed
next_action=rebuild the balanced corpus with prompt-leading scaffold-to-term rows before increasing training budget
```

解释：

- checkpoint 成功生成，所以不是训练命令失败。
- `generated_hit_count=9` 不是能力提升证据，因为 prompt 本身就是 `data:`、`because:` 这类含 term 的文本。
- `continuation_hit_count=0` 才是关键结果：模型没有在 prompt 后续写目标 term。
- `prompt_leading_line_count=0` 解释了原因：v487 corpus 的行首是 `cycle=...|pattern=...`，不是 scaffold prompt。

## 测试覆盖

测试覆盖：

- fake training 成功且 fake generation 命中时，输出 uptake decision。
- fake generation 不命中时，输出 completed-without-uptake。
- corpus 文件缺失时，报告失败，`--require-pass` 可返回非零。
- JSON/CSV/text/Markdown/HTML 五类 artifact 都能写出。
- 输入路径支持 JSON 文件和目录。
- 当 corpus 只有 prefixed pattern row、没有 prompt-leading row 时，报告 `prompt_alignment_ready=False`，下一步指向重建语料。

这些测试保护了 v488 的重点：不只看训练是否跑完，还要解释为什么 continuation 没有改善。

## 运行证据

运行证据位于：

```text
e/488/解释/model-capability-required-term-balanced-training/
e/488/解释/model-capability-required-term-balanced-training-cli.txt
e/488/解释/model-capability-required-term-balanced-training-snapshot.md
e/488/图片/01-model-capability-required-term-balanced-training.png
```

`balanced-run/` 下保存真实 checkpoint、tokenizer、metrics、train config、loss curve 和训练日志。

## 一句话总结

v488 证明 balanced corpus 可以完成 tiny training，但 continuation 仍为 0，并把原因定位到 prompt-leading alignment 缺失，为下一版重建语料提供了明确目标。
