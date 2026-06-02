# v736 direct-completion surface contract

## 本版目标和边界

v736 的目标是承接 v735 closeout plan，生成一个可物化的 `pair_readiness_direct_completion_surface_contract`。

本版不做训练、不比较 checkpoint、不宣称模型质量提升。它解决的是训练输入形态问题：v731-v734 证明 direct-prompt bridge rows 没有带来 hit 提升，还引入了 loss prompt 下的 fixed 污染，所以 v736 改用更短、更直接的 completion surface。

## 前置链路

```text
v733 bridge training
 -> zero direct hits, loss prompt fixed pollution
v734 bridge comparison
 -> no improvement + pollution introduced
v735 bridge closeout plan
 -> proposed_next_artifact = pair_readiness_direct_completion_surface_contract
v736 direct-completion surface contract
 -> ready for corpus materialization
```

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_direct_completion_surface_contract.py`
  - 读取 v735 closeout plan。
  - 构造 direct-completion surface contract。
  - 检查来源、row balance、eval probe 保留和 heldout pair leakage。
- `src/minigpt/model_capability_required_term_pair_readiness_direct_completion_surface_contract_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用于运行截图和人工核查。
- `scripts/run_model_capability_required_term_pair_readiness_direct_completion_surface_contract.py`
  - CLI 入口，支持 `--require-pass` 和 `--force`。
- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 将 `pair_readiness_direct_completion_surface_contract_ready` 加入可物化 decision。
  - 将新 JSON 文件名加入目录定位列表。
- `tests/test_model_capability_required_term_pair_readiness_direct_completion_surface_contract.py`
  - 覆盖 ready contract、错误 next artifact、materializer 兼容、五格式输出和 row family 平衡。

## 核心数据结构

v736 的核心结构是 `DIRECT_COMPLETION_SURFACE_ROW_FAMILIES`。

主要 row family：

- `exact_direct_completion`
  - `fixed=fixed`
  - `loss=loss`
- `fixed_prefix_ladder`
  - `fixed=f`
  - `fixed=fi`
  - `fixed=fix`
- `loss_prefix_ladder`
  - `loss=l`
  - `loss=lo`
  - `loss=los`
- `paired_order_forward`
  - 表示 fixed/loss 的正向配对顺序。
- `paired_order_reverse`
  - 表示 loss/fixed 的反向配对顺序。
- `direct_boundary_contrast`
  - 用于防止 fixed/loss 互相污染。

这些行合计 16 行。它们会进入下一版 materialized corpus，而 eval probes 仍然是：

```text
fixed=
loss=
fixed=|loss=
```

这里的边界很重要：训练行可以包含 `fixed=fixed`，但不能直接包含 heldout prompt `fixed=` 或 pair probe `fixed=|loss=` 作为完整训练行。

## 核心检查

v736 的主要检查项：

```text
closeout_plan_passed
closeout_plan_decision
next_artifact_matches
training_rows_present
exact_fixed_completion_present
exact_loss_completion_present
prefix_ladder_balance
paired_forward_present
paired_reverse_present
evaluation_probes_present
no_exact_eval_row_overlap
heldout_pair_absent
```

这些检查保护三件事：

1. 来源必须确实是 v735 closeout plan，不能随便拿其他报告当输入。
2. direct surface 不能再变成单侧补丁，fixed/loss prefix 行数必须对称。
3. heldout pair probe 仍然只作为评估输入，不能泄漏到训练 corpus。

## 输出产物

v736 输出目录：

```text
e/736/解释/model-capability-required-term-pair-readiness-direct-completion-surface-contract/
```

关键产物：

- JSON：后续 v737 materializer 消费。
- CSV：检查行审计。
- TXT：命令行摘要。
- Markdown：轻量说明。
- HTML：浏览器截图证据。

截图：

```text
e/736/图片/v736-direct-completion-surface-contract.png
```

## 测试覆盖

聚焦测试覆盖：

- 正常 v735 closeout 输入能生成 ready contract。
- `proposed_next_artifact` 被篡改时失败。
- 新 contract 能被现有 materializer 接受。
- JSON/CSV/TXT/Markdown/HTML 五格式输出完整。
- fixed/loss prefix ladder 数量相同，heldout pair probe 不在训练行中。

## 一句话总结

v736 把 bridge route 的失败结论转化为更直接、更平衡、可物化的 completion-surface contract，为下一轮真实 tiny 训练提供新输入。
