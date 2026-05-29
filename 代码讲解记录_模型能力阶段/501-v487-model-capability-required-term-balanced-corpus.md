# v487：model capability required-term balanced corpus

## 本版目标和边界

v487 的目标是落实 v486 的下一步建议：先改善 required-term 微训练语料构造，再继续训练或 held-out claim。v486 已经说明，v485 最佳 split 的训练侧信号只在部分 seed 上复现，held-out 始终为 `0`。这意味着继续盲目做更大 held-out 检查意义不大，应该先把语料重复、term 暴露和上下文模板做成可复核的候选输入。

本版不训练新模型，不扩大模型规模，也不宣称模型质量提升。它只生成一个 balanced corpus candidate，并用 JSON/CSV/text/Markdown/HTML 说明这个 corpus 是否比 legacy repeat corpus 更适合进入下一轮 tiny 训练。

## 前置能力

本版承接以下链路：

- v483：从 scaffold-to-term 语料训练 tiny checkpoint，观察到 `4/20` continuation hit。
- v484：引入 train/holdout required-term split，默认 split 未出现 train 或 holdout hit。
- v485：扫描多种 split，发现 `split-4` 有训练侧 hit 但 held-out 为 `0`。
- v486：重复 `split-4` 的多个 seed，发现训练侧 hit 只在 `1/3` seed 上复现。

v487 因此选择不继续扩张评估，而是先让训练语料本身更可控。

## 关键新增文件

- `src/minigpt/model_capability_required_term_balanced_corpus.py`
  - 核心 corpus candidate 构造逻辑。
  - 支持输入 v486 seed-stability report，也支持直接输入 v483 micro-training report。
  - 自动解析 `source_required_term_micro_training`，读取原始 examples。
  - 按 unique required term 选择代表行，生成多模板、多 cycle 的 balanced corpus。
  - 同时计算 legacy repeat corpus 的唯一行率，用来做对比。

- `src/minigpt/model_capability_required_term_balanced_corpus_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - CSV 以 term row 为单位，记录 case、term、prompt、line count、pattern count 和 repeat。
  - HTML 报告展示 summary cards、pattern counts 和 term rows。

- `scripts/run_model_capability_required_term_balanced_corpus.py`
  - CLI 入口。
  - 支持 `--repeat`、`--require-pass`、`--force`。
  - 默认输出到 `runs/model-capability-required-term-balanced-corpus`，本版真实归档输出到 `e/487/解释/model-capability-required-term-balanced-corpus`。

- `tests/test_model_capability_required_term_balanced_corpus.py`
  - 覆盖从 seed-stability source 解析 micro report。
  - 覆盖 corpus pattern 生成、唯一行、summary review 分支、缺 source 失败、artifact 输出和目录定位。

## 核心数据结构

最终报告为：

```text
model_capability_required_term_balanced_corpus.json
```

关键字段：

- `source_report`
  - 本版真实运行时指向 v486 seed-stability JSON。

- `source_required_term_micro_training`
  - 从 v486 report 回溯得到的 v483 micro-training JSON。

- `settings`
  - `repeat`：每个 pattern 对每个 term 重复的 cycle 数。
  - `patterns`：本版使用的六类上下文模板。
  - `selection_strategy`：`one representative row per unique required term`。
  - `training_boundary`：明确说明这只是候选语料，后续 held-out 检查仍要隐藏 held-out prompt-to-term pairs。

- `corpus`
  - `path` 指向 `required_term_balanced_corpus.txt`。
  - `line_count` 和 `char_count` 说明 corpus 规模。
  - `vocab_boundary` 说明本版不是 held-out corpus。

- `summary`
  - `unique_line_rate`：新 corpus 的唯一行率。
  - `legacy_unique_line_rate`：旧 repeat corpus 的唯一行率。
  - `term_line_spread`：不同 term 的训练行数差。
  - `pattern_counts`：各模板生成了多少行。
  - `balanced_corpus_decision`：是否达到 candidate ready。

- `term_rows`
  - 每个 selected required term 一行。
  - 记录 term、case、scaffold prompt、line count、expected line count、pattern count 和 repeat。

## 运行流程

1. CLI 接收 v486 seed-stability 目录。
2. 定位 `model_capability_required_term_split_seed_stability.json`。
3. 从该报告读取 `source_required_term_micro_training`。
4. 读取 v483 micro-training report。
5. 从 `20` 条 source examples 中按 unique required term 收束为 `9` 条 term row。
6. 对每个 term 使用六种 pattern，并按 `repeat=8` 生成训练候选行。
7. 对比新 corpus 与 legacy repeat corpus 的唯一行率。
8. 输出 JSON/CSV/text/Markdown/HTML 和 `required_term_balanced_corpus.txt`。

## v487 真实运行结果

真实命令输出：

```text
status=pass
decision=required_term_balanced_corpus_candidate_ready
balanced_corpus_decision=balanced_corpus_candidate_ready
source_example_count=20
example_count=9
unique_term_count=9
line_count=435
unique_line_count=435
unique_line_rate=1.0
legacy_unique_line_rate=0.133
term_line_spread=0
model_quality_claim=not_claimed
```

解释：

- `unique_line_rate=1.0` 说明新 corpus 没有重复行。
- `legacy_unique_line_rate=0.133` 说明旧 repeat corpus 主要靠重复同样的行堆训练信号。
- `term_line_spread=0` 说明每个 selected term 的暴露量一致。
- `model_quality_claim=not_claimed` 保持边界：这只是输入质量准备，不是模型能力结论。

## 测试覆盖

测试覆盖以下保护点：

- 从 v486 seed-stability report 能正确解析回 v483 micro-training report。
- balanced corpus 的所有 pattern 都会出现，且生成行不重复。
- 当 corpus 出现重复行时，summary 会降级为 `balanced_corpus_candidate_needs_review`。
- 当 micro source 丢失时，报告失败，`--require-pass` 可返回非零退出码。
- JSON/CSV/text/Markdown/HTML 五类输出都能写出，CSV 可读到 term rows。
- 输入路径既可以是 JSON 文件，也可以是目录。

这些测试保证 v487 不是单纯写一个文本文件，而是形成了可重复、可检查、可进入下一轮训练的 corpus construction step。

## 运行证据

运行证据位于：

```text
e/487/解释/model-capability-required-term-balanced-corpus/
e/487/解释/model-capability-required-term-balanced-corpus-cli.txt
e/487/解释/model-capability-required-term-balanced-corpus-snapshot.md
e/487/图片/01-model-capability-required-term-balanced-corpus.png
```

其中 HTML 和截图用于证明报告可读，JSON/CSV 用于后续脚本消费，`required_term_balanced_corpus.txt` 是下一轮真实 tiny 训练的候选输入。

## 一句话总结

v487 把 v486 的“先改善语料构造”落实成了 balanced corpus candidate，让下一版可以真正测试“更好的 required-term 训练输入是否提升 tiny 模型的稳定 continuation 能力”。
