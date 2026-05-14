# v91 training scale plan report utility migration

## 本版目标

v91 的目标是继续做一次轻量、定向的质量优化，把 v70 引入的 `training_scale_plan.py` 迁移到公共 `report_utils.py` 上。

这次推进来自一个很明确的判断：aiproj 现在不适合做大重构，更适合把高频报告模块里重复的小工具逐步收口。v83 已经新增 `report_utils.py`，v84-v90 已经把 handoff、seed、decision、comparison、run 和 gate 等消费者迁移进来。v91 继续向上游推进，把训练规模链路最前面的 planner 也接入公共报告基础层。

本版解决的问题是：v90 之后，`gate -> run -> comparison -> decision` 四层证据已经共享报告工具，但它们的上游 `plan` 仍然保留私有 JSON 写出、命令展示、Markdown cell、HTML escape 和 list/dict 归一化函数。继续保留这些私有 helper，会让训练规模链路的第一份 evidence 和后续 evidence 在基础行为上分叉。

v91 的结果是：

```text
plan -> gate -> run -> comparison -> decision
```

这五层训练规模证据开始共享同一套报告基础设施。

## 本版明确不做什么

v91 不改训练规模规划策略。

下面这些业务行为保持不变：

- `scale_tier` 的 tiny/small/medium/large 边界。
- `safe_block_size_for_char_count` 的 tiny corpus block size 调整规则。
- smoke/baseline/extended variants 的默认参数。
- `training_scale_variants.json` 的 batch-compatible schema。
- `training_scale_plan.csv` 的多行 variant matrix。
- planner CLI 参数、输出路径和打印字段。
- 数据质量报告、fingerprint、warning/recommendation 的语义。

本版只迁移报告基础设施，不把它扩张成新的 planner abstraction，也不合并 training scale 的业务模块。

## 来自哪条路线

v83 新增 `report_utils.py`，先迁移 promoted seed handoff 作为低风险验证点。

之后的路线是：

```text
v84 controlled training scale handoff
v85 promoted training scale seed
v86 promoted baseline decision
v87 training scale run decision
v88 training scale run comparison
v89 gated training scale run
v90 training scale gate
```

v91 再迁移：

```text
v70 training scale plan
```

这让原始 training scale 链路从规划、准入、执行转交、对比到执行候选决策都进入同一套公共报告基础层。

## 关键文件

`src/minigpt/training_scale_plan.py`

这是本版核心迁移文件。它继续负责读取训练语料来源、构造 prepared dataset、生成 dataset report 和 quality report、判断语料规模、生成 variants、估算 token budget、输出 JSON/CSV/Markdown/HTML 和 batch handoff command。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用它已有的：

```text
as_dict
display_command
html_escape
list_of_dicts
markdown_cell
string_list
utc_now
write_json_payload
```

`tests/test_training_scale_plan.py`

这是 planner 的业务测试，保护 sources summary、variants 生成、batch-compatible variants 文件、tiny corpus warning、block size 调整、non-recursive source scan、HTML escaping 和 scale tier 边界。

`tests/test_report_utils.py`

这是公共层测试，保护 JSON/CSV 写出、artifact row、command display、Markdown/HTML 转义和 list/dict 归一化。

`scripts/plan_training_scale.py`

这是 planner 的 CLI 入口。本版不改 CLI 参数，只用它做 smoke，证明迁移后仍能生成 `training_scale_plan.json`、`training_scale_variants.json`、CSV、Markdown 和 HTML。

`代码讲解记录_项目成熟度阶段/106-v91-training-scale-plan-report-utils.md`

这是本讲解文件，用来解释为什么 v91 是轻量质量优化，而不是架构重构。

`c/91/`

这是 v91 的运行截图和解释归档。它保存 focused tests、full regression、CLI smoke、tiny corpus smoke、结构检查、Playwright HTML 截图和文档检查。

## 迁移前的重复点

迁移前，`training_scale_plan.py` 自己维护了：

```text
utc_now
_display_command
_list_of_dicts
_string_list
_dict
_md
_e
```

同时 JSON 写出使用本地实现：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

这些能力和 `report_utils.py` 已有原语重叠。planner 是 training scale 链路的入口，它的报告输出越基础，越应该和后续 gate/run/comparison/decision 采用同一套底层规则。

## 迁移后的引入关系

v91 让 `training_scale_plan.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
display_command as _display_command
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

这里保留 `_dict`、`_md`、`_e` 等旧别名，是为了让 Markdown/HTML 模板的改动保持最小。这样本版是一场基础工具迁移，而不是模板重写。

## JSON 输出

`write_training_scale_plan_json` 改为：

```text
write_json_payload(report, path)
```

`write_training_scale_variants_json` 仍然构造原来的 batch handoff payload：

```text
schema_version
generated_at
source
dataset
variants
```

但写文件动作改为：

```text
write_json_payload(payload, path)
```

这两个 JSON 的角色不同：

- `training_scale_plan.json` 是 planner 的完整机器可读证据。
- `training_scale_variants.json` 是给 v69 training portfolio batch runner 消费的 handoff 文件。

v91 没有改变它们的字段，只统一 JSON writer。

## CSV 输出

`training_scale_plan.csv` 是 per-variant 多行矩阵，不是单行摘要。

因此本版没有强行使用 `report_utils.write_csv_row`。它仍然保留本地 `csv.DictWriter` 循环，因为每个 variant 都需要独立一行：

```text
name
scale_tier
dataset_version
max_iters
eval_interval
batch_size
block_size
n_layer
n_head
n_embd
seed
token_budget
corpus_pass_estimate
description
```

这是一处有意保留的边界：公共工具收束重复基础行为，但不牺牲当前报告的表格结构。

## Markdown 和 HTML 渲染

Markdown 报告仍然包含：

- generated time
- scale tier
- dataset/version
- source count
- char count
- quality summary
- variants file
- variant matrix
- batch command
- recommendations
- quality issues

HTML 报告仍然包含：

- header
- stats cards
- variant table
- batch handoff command
- recommendations
- quality issues
- footer

变化在于 Markdown cell、HTML escape、command display、list/dict normalization 改为公共工具：

```text
markdown_cell
html_escape
display_command
list_of_dicts
string_list
as_dict
```

这样后续如果要修复命令展示或转义规则，只需要在公共层维护。

## 核心数据结构

`build_training_scale_plan` 返回的 report 仍然保持原结构。

顶层字段包括：

```text
schema_version
title
generated_at
project_root
out_root
sources
recursive
dataset
sources_detail
quality_issues
variants
variant_matrix
batch
recommendations
```

`dataset` 汇总语料身份和质量：

```text
name
version_prefix
description
source_count
char_count
line_count
unique_char_count
unique_char_ratio
fingerprint
short_fingerprint
scale_tier
quality_status
warning_count
issue_count
duplicate_line_count
```

`variant_matrix` 是给人审阅的训练规模矩阵。它把每个 variant 的模型参数和预算估算展开：

```text
name
description
scale_tier
dataset_version
max_iters
eval_interval
batch_size
block_size
context_adjustment
n_layer
n_head
n_embd
seed
token_budget
corpus_pass_estimate
```

`batch` 是给后续 v69 batch runner 使用的入口：

```text
variants_path
out_root
baseline
command
```

## 运行流程

planner 的主流程仍然是：

```text
输入 sources
 -> build_prepared_dataset
 -> build_dataset_report
 -> build_dataset_quality_report
 -> scale_tier
 -> _recommended_variants
 -> _fit_variant_contexts
 -> _variant_matrix_row
 -> batch command
 -> write_training_scale_plan_outputs
```

`_fit_variant_contexts` 仍然是 tiny corpus 的重要保护点。如果语料太小，它会通过 `safe_block_size_for_char_count` 降低 block size，避免默认 90/10 split 之后验证集无法采样 batch。

这点和 v76 的 tiny-corpus 执行修复有关。v91 不改这条逻辑，只证明迁移公共 helper 后它仍然有效。

## 为什么这条建议合理

用户给出的判断是：当前阶段需要“收口型优化”，不需要“架构级重构”。

对 aiproj 来说这是合理的：

- 项目已经有很多治理产物，继续新增大功能容易让代码膨胀。
- v83-v90 已经证明 `report_utils` 是可复用的低风险公共层。
- `training_scale_plan.py` 是 gate 的直接上游，迁移它能让训练规模链路更完整。
- 这次迁移只删除重复 helper，不改变业务策略，回归风险小。
- 测试和 smoke 可以直接覆盖 JSON、variants handoff、tiny corpus 和 HTML 渲染。

所以 v91 不是为了“看起来更抽象”而改代码，而是把已经被多版验证过的公共工具继续覆盖到一个明确边界的消费者。

## 测试覆盖

`tests/test_training_scale_plan.py` 覆盖七类行为。

第一类是 source summary 和 variants：

- `schema_version` 为 1。
- source count 正确。
- scale tier 属于合法集合。
- 至少生成一个 variant。
- batch baseline 是第一个 variant。
- batch command 指向 `run_training_portfolio_batch.py`。
- token budget 计算稳定。

第二类是 outputs 和 batch compatibility：

- `write_training_scale_plan_outputs` 写出 JSON、variants、CSV、Markdown、HTML。
- `training_scale_variants.json` 可以被 batch runner 加载。
- batch plan 的 variant count 和 baseline 与 planner report 对齐。
- variants payload 的 `source` 是 `training_scale_plan`。

第三类是 tiny corpus：

- tiny corpus 的 scale tier 是 `tiny`。
- max variants 可以限制为 1。
- warning count 大于等于 1。
- recommendations 中保留 tiny 提示。
- block size 被降低。
- `context_adjustment` 被写入 variant。

第四类是 block size 边界：

- 507 字符语料把 64 调整为 48。
- 3 字符语料把 block size 调整到 1。
- 大语料保留 64。
- 负字符数和非法 requested block size 抛出 `ValueError`。

第五类是 non-recursive scan：

- `recursive=False` 时只读取顶层 `.txt`。
- nested source 不会混入 source details。

第六类是渲染转义：

- Markdown 包含 Batch Command。
- HTML 把 `<demo>` 转义为 `&lt;demo&gt;`。
- 原始 `<demo>` 不直接出现在 HTML。

第七类是 scale tier 边界：

- 0 是 tiny。
- 2,000 是 small。
- 20,000 是 medium。
- 200,000 是 large。
- 负数抛出 `ValueError`。

这些测试保护的是 planner 的业务行为，而不仅仅是文件能写出来。

`tests/test_report_utils.py` 继续保护公共工具本身。v91 focused tests 同时跑 planner tests 和 report utils tests，证明消费者和公共层都正常。

## 运行截图和证据

v91 的运行证据归档到：

```text
c/91/图片
c/91/解释/说明.md
```

截图覆盖：

- focused tests、compileall、full regression。
- planner CLI smoke。
- tiny corpus smoke。
- source/docs/archive structure check。
- Playwright/Chrome 打开 planner HTML。
- README、代码讲解索引、c README 文档一致性检查。

其中 Playwright 截图证明 HTML 不是只写了文件，而是可以被真实 Chrome 打开。CLI smoke 证明 `training_scale_variants.json` 仍然能作为 batch handoff 产物存在。

## 后续开发原则

v91 之后，`plan -> gate -> run -> comparison -> decision` 五层已经完成公共工具收束。

后续继续做轻量质量优化时，可以考虑更高层模块：

- `training_scale_workflow.py`
- `training_scale_promotion.py`
- `training_scale_promotion_index.py`
- `promoted_training_scale_comparison.py`

但仍然应该保持小步迁移：

- 每版只迁移一个边界清楚的消费者。
- 不改业务判断。
- 不重排输出 schema。
- 不把多行 CSV 强行改成单行 helper。
- 保留 focused tests、full regression、smoke、Playwright 和文档索引闭环。

## 一句话总结

v91 把 training scale planner 接入 `report_utils`，让 plan、gate、run、comparison、decision 五层训练规模证据共享同一套报告基础设施，并用测试和运行截图证明这只是低风险收口，不是业务策略重构。
