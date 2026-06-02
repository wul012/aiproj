# v737 direct-completion surface corpus materialization

## 本版目标和边界

v737 的目标是把 v736 的 `pair_readiness_direct_completion_surface_contract` 变成真实训练输入。

本版不新增 Python 模块，不改变训练逻辑，也不宣称模型能力提升。它只回答一个问题：新 contract 是否能被现有 corpus materializer 接受，并产出下一版训练可直接消费的 corpus 与 heldout fixture。

## 前置链路

```text
v735 bridge closeout plan
 -> proposed direct-completion surface contract
v736 direct-completion surface contract
 -> 16 training rows, 3 evaluation probes
v737 corpus materialization
 -> 5120 training lines, heldout fixture preserved
```

## 输入和输出

输入目录：

```text
e/736/解释/model-capability-required-term-pair-readiness-direct-completion-surface-contract/
```

输出目录：

```text
e/737/解释/model-capability-required-term-pair-readiness-direct-completion-surface-corpus-materialization/
```

主要输出：

- `pair_readiness_training_corpus.txt`
  - v738 训练脚本将读取的真实文本语料。
- `pair_readiness_heldout_eval_fixture.json`
  - 保存 heldout eval probes 和 training rows 摘要。
- `model_capability_required_term_pair_readiness_corpus_materialization.json`
  - materialization 主报告。
- HTML/Markdown/TXT/CSV
  - 用于人工审阅、截图和轻量审计。

## 核心数据

v736 contract 有 16 行 training rows。

v737 使用：

```text
repeat=320
```

因此训练 corpus 行数为：

```text
16 * 320 = 5120
```

corpus preview 显示：

```text
fixed=fixed
loss=loss
fixed=f
fixed=fi
fixed=fix
loss=l
loss=lo
loss=los
```

这证明 direct-completion surface 已经从 contract 进入真实 corpus。

## 边界检查

materializer 的核心检查包括：

```text
contract_passed
contract_decision
repeat_positive
training_rows_present
heldout_not_in_training_rows
heldout_not_in_corpus
```

其中最关键的是：

- contract decision 必须是 materializer 允许的 ready decision。
- `fixed=|loss=` 不能出现在 training rows。
- `fixed=|loss=` 不能出现在展开后的 corpus lines。

这保证下一版训练不会直接吃到 pair heldout probe。

## 证据

运行截图：

```text
e/737/图片/v737-direct-completion-surface-corpus-materialization.png
```

截图可见：

- `status=pass`
- `decision=pair_readiness_corpus_materialized`
- `Train lines=5120`
- `Eval probes=3`
- corpus preview 含 `fixed=fixed` 和 `loss=loss`

## 一句话总结

v737 把 direct-completion surface 从“合约设计”推进成“真实训练输入”，让 v738 可以用同一 tiny 训练配置验证它是否改善 heldout direct behavior。
