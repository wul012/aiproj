# v489：model capability required-term prompt-leading corpus

## 本版目标和边界

v489 的目标是修正 v488 定位出的语料形状问题。v488 训练成功但 continuation hit 仍为 `0`，并新增诊断证明 `prompt_alignment_ready=False`、`prompt_leading_line_count=0`。也就是说，v487 的 balanced corpus 虽然平衡、去重，但行首不是后续 generation probe 使用的 scaffold prompt。

本版不训练新模型，不宣称模型能力提升。它只重建一个 prompt-leading corpus candidate，让每个训练行都以 `data:`、`because:` 等 scaffold prompt 开头，保证下一轮训练输入和 probe prefix 形状一致。

## 前置能力

本版承接：

- v487：构造 balanced corpus，`unique_line_rate=1.0`，`term_line_spread=0`。
- v488：用 v487 corpus 训练 tiny checkpoint，但 continuation hit 为 `0/9`。
- v488 诊断：`prompt_alignment_ready=False`，`prompt_leading_line_count=0`。

v489 的核心动作是保留 v487 的平衡和去重，同时修复 prompt-leading alignment。

## 关键新增文件

- `src/minigpt/model_capability_required_term_prompt_leading_corpus.py`
  - 核心语料构造逻辑。
  - 输入可以是 v488 balanced-training report，也可以是 v487 balanced-corpus report。
  - 如果输入 v488，会通过 `source_required_term_balanced_corpus` 回溯 v487。
  - 对每个 required term 生成多种 prompt-leading pattern。
  - 计算 `prompt_alignment_ready`、`prompt_leading_line_count`、`term_line_spread` 和前后 alignment 对比。

- `src/minigpt/model_capability_required_term_prompt_leading_corpus_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 报告展示 prompt alignment、previous alignment、pattern counts 和 term rows。

- `scripts/run_model_capability_required_term_prompt_leading_corpus.py`
  - CLI 入口。
  - 支持 `--repeat`、`--require-pass`、`--force`。

- `tests/test_model_capability_required_term_prompt_leading_corpus.py`
  - 覆盖从 v488 回溯 v487、prompt-leading 行首约束、summary 降级、缺源失败、artifact 输出和路径定位。

## 核心数据结构

最终报告为：

```text
model_capability_required_term_prompt_leading_corpus.json
```

关键字段：

- `settings`
  - `patterns`：本版使用 `direct/spaced/answer/case_tag` 四类 prompt-leading pattern。
  - `selection_strategy`：复用 v487 的 unique required-term rows，并强制每行以 scaffold prompt 开头。

- `corpus`
  - 指向 `required_term_prompt_leading_corpus.txt`。
  - 记录 line count、char count 和 repeat。

- `summary`
  - `prompt_alignment_ready`：每个 term 是否都有 prompt-leading training row。
  - `prompt_leading_line_count`：所有 prompt-leading 行总数。
  - `previous_prompt_alignment_ready` 和 `previous_prompt_leading_line_count`：来自 v488 诊断，用于前后对比。
  - `term_line_spread`：不同 term 的训练行数差。
  - `unique_line_rate`：仍然检查是否回到重复语料。

- `term_rows`
  - 每个 selected required term 一行，记录 case、term、scaffold prompt、line count、pattern count 和 repeat。

## 运行流程

1. CLI 读取 v488 balanced-training report。
2. 从 `source_required_term_balanced_corpus` 回溯 v487 balanced corpus report。
3. 读取 v487 的 9 个 selected term rows。
4. 对每个 term 生成 prompt-leading rows：

```text
data:data|pattern=direct|...
data: data|pattern=spaced|...
data: answer=data|pattern=answer|...
data: case=qa-training-loop; term=data|pattern=case_tag|...
```

5. 统计 prompt-leading 行数、term line spread、pattern counts 和 unique line rate。
6. 输出 JSON/CSV/text/Markdown/HTML 和 corpus txt。

## v489 真实运行结果

真实命令输出：

```text
status=pass
decision=required_term_prompt_leading_corpus_candidate_ready
prompt_leading_corpus_decision=prompt_leading_corpus_candidate_ready
term_count=9
line_count=363
unique_line_rate=1.0
term_line_spread=0
prompt_alignment_ready=True
prompt_leading_line_count=360
previous_prompt_alignment_ready=False
previous_prompt_leading_line_count=0
model_quality_claim=not_claimed
```

解释：

- v488 的 prompt-leading 行数为 `0`。
- v489 变为 `360`，覆盖 9 个 required terms。
- `term_line_spread=0` 表示每个 term 的暴露量一致。
- `unique_line_rate=1.0` 表示没有退回到重复堆叠。

## 测试覆盖

测试覆盖：

- 从 v488 report 能正确回溯 v487 balanced corpus。
- 所有生成 pattern 行都以 scaffold prompt 开头。
- 当 corpus 没有 prompt-leading 行时，summary 会降级为 needs review。
- source balanced corpus 缺失时，报告失败，`--require-pass` 返回非零。
- JSON/CSV/text/Markdown/HTML 五类输出全部可写。
- 输入路径支持 JSON 文件和目录。

这些测试保护了 v489 的核心约束：下一轮训练输入必须和 probe prefix 对齐。

## 运行证据

运行证据位于：

```text
e/489/解释/model-capability-required-term-prompt-leading-corpus/
e/489/解释/model-capability-required-term-prompt-leading-corpus-cli.txt
e/489/解释/model-capability-required-term-prompt-leading-corpus-snapshot.md
e/489/图片/01-model-capability-required-term-prompt-leading-corpus.png
```

`required_term_prompt_leading_corpus.txt` 是下一轮 tiny training 的候选输入。

## 一句话总结

v489 把 v488 发现的 prompt alignment 缺口修成了 prompt-leading corpus candidate，使下一轮训练可以真正测试“prefix 对齐后 required-term continuation 是否改善”。
