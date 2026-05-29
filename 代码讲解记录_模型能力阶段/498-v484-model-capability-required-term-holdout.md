# v484：model capability required-term holdout

## 本版目标和边界

v484 的目标是复核 v483 的定向微训练信号。v483 在同一批 scaffold-to-term 样本上训练和评估，出现了 `4/20` 个 continuation required-term hit；v484 进一步把 required terms 拆成 train 和 holdout 两部分，检查模型是否能把训练过的 scaffold-to-term 模式迁移到未作为配对样本训练的 required terms。

本版不扩大 benchmark，不宣称模型质量提升，也不把 prompt 中已经出现的 required term 算作续写能力。核心问题只有一个：split 后的 train/holdout continuation 是否还能命中 required terms。

## 前置能力

本版承接四层证据：

- v480
  - required terms 在 suite 和 tiny corpus 中存在。
- v481
  - archived generations 从未把 required terms 写进 continuation。
- v482
  - 显式 scaffold prompt 不能让归档 checkpoint 复现 required term。
- v483
  - 全量 scaffold-to-term 微训练后，同批样本出现少量 required-term continuation hit。

v484 的价值在于给 v483 加一层泛化复核，而不是继续扩大报告格式。

## 关键新增文件

- `src/minigpt/model_capability_required_term_holdout.py`
  - 核心 held-out 实验逻辑。
  - 输入 v483 micro-training report。
  - 按 required term 做 deterministic split。
  - 构造 holdout corpus，训练新 checkpoint，并分别生成 train/holdout prompt。
  - 输出 train/holdout continuation hit 统计和结论。
- `src/minigpt/model_capability_required_term_holdout_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright MCP 截图，CSV 用于逐行核对 split 与命中。
- `scripts/run_model_capability_required_term_holdout.py`
  - CLI 入口。
  - 支持训练参数、生成参数、`--holdout-term`、`--holdout-stride`、`--holdout-offset`、`--require-pass` 和 `--force`。
- `tests/test_model_capability_required_term_holdout.py`
  - 覆盖 held-out 命中、只训练侧命中、缺输入、输出产物、路径定位和语料泄漏边界。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_holdout.json
```

关键字段：

- `settings`
  - 记录训练参数、生成参数和 split 参数。
  - 默认 `holdout_stride=3`、`holdout_offset=2`，因此真实运行中 holdout terms 是 `data/loss/while`。
- `split`
  - 记录 `unique_terms`、`train_terms`、`holdout_terms`、train/holdout example 数量，以及两侧原始 examples。
  - split 按 term 做，不按 row 做，避免同一个 term 同时泄漏到训练和 holdout。
- `corpus`
  - 记录 `required_term_holdout_corpus.txt`。
  - 语料会暴露 holdout prompt vocabulary，例如 `data:`，保证 tokenizer 能编码 prompt。
  - 但不会写入 `data:data` 这种 holdout prompt-to-term 配对。
- `training`
  - 记录训练命令、checkpoint/tokenizer/metrics/train_config 是否存在。
- `generation_rows`
  - 每行记录 `split=train|holdout`、case、term、prompt、生成文本、continuation preview 和命中数。
- `summary`
  - 分别统计 train/holdout generation 数量、continuation hit count、case hit count、hit rate。
  - `holdout_decision` 区分训练失败、split 无效、held-out 命中、只训练侧命中、两侧均无命中。

## 运行流程

1. 读取 v483 micro-training report。
2. 从 `examples` 中抽取 required term 和 scaffold prompt。
3. 按 term 做 split：

```text
train_terms=because, chain, fixed, four, real, text
holdout_terms=data, loss, while
```

4. 构造训练语料：

```text
Prompt vocabulary: because: chain: data: fixed: four: loss: real: text: while:
holdout-prompt-only|qa-training-loop|data:
because:because
because: because
classification-risk-level|because:because
```

holdout prompt 只作为 prompt/vocab 暴露，不作为 `prompt -> term` 重复样本训练。

5. 调用 `scripts/train.py` 训练新 checkpoint。
6. 用新 checkpoint 分别生成 train split 和 holdout split。
7. 输出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## v484 真实运行结果

真实配置：

```text
max_iters=420
eval_iters=2
batch_size=16
block_size=8
n_layer=1
n_head=1
n_embd=32
learning_rate=0.02
term_repeat=24
max_new_tokens=8
temperature=0.2
top_k=1
```

结果：

```text
status=pass
decision=required_term_holdout_no_uptake
holdout_decision=heldout_micro_training_no_required_term_uptake
train_example_count=12
holdout_example_count=8
train_continuation_hit_count=0
holdout_continuation_hit_count=0
train_hit_rate=0.0
holdout_hit_rate=0.0
model_quality_claim=not_claimed
```

解释：v484 没有复现 v483 的 4/20 continuation hit，甚至训练侧 split 也没有命中。这说明 v483 的信号仍然不稳定，不能作为模型能力提升证据。下一步应先改善微训练语料与 split 设计，让训练侧信号稳定，再讨论 held-out 泛化。

## 测试覆盖

新增测试覆盖：

- fake generator 在 holdout term 上命中时，报告必须输出 `heldout_required_term_uptake_observed`。
- fake generator 只在 train term 上命中时，报告必须输出 `training_slice_only_without_holdout_uptake`。
- source micro-training report 没有 examples 时，报告必须 fail，`--require-pass` 返回非零。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。
- 输入路径必须支持文件和目录。
- holdout corpus 不能包含 `data:data` 这种 holdout prompt-to-term 配对。

这些测试保护了 v484 的核心边界：held-out term 不能作为训练目标泄漏，但 prompt vocabulary 可以被暴露给 tokenizer。

## 运行证据

运行证据位于：

```text
e/484/解释/model-capability-required-term-holdout/
e/484/图片/01-model-capability-required-term-holdout.png
e/484/解释/model-capability-required-term-holdout-snapshot.md
```

这些产物包含真实训练出的 `holdout-run/checkpoint.pt`、held-out 语料、逐行 CSV 和 HTML 报告。它们的角色是约束 v483 的解释边界，而不是扩大模型质量宣传。

## 一句话总结

v484 证明 v483 的 required-term continuation 命中还没有稳定到能通过 held-out split 复现，下一步应先让训练侧信号稳定，再谈泛化。
