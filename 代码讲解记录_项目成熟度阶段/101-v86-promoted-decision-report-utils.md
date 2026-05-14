# v86 promoted decision report-utils migration 代码讲解

## 本版目标

v86 继续 `report_utils` 收口路线，这次迁移的是 v80 的 promoted baseline decision：

```text
src/minigpt/promoted_training_scale_decision.py
```

这个模块负责读取 promoted comparison，筛选可以作为下一轮 baseline 的 promoted runs，选出最合适的 baseline，并把 rejected runs 和选择原因写成 JSON/CSV/Markdown/HTML 证据。

v86 要解决的问题是：

```text
report_utils 已经覆盖 seed generation、seed handoff、controlled execution handoff；
它能否继续向 seed 上游延伸到 baseline selector？
```

本版答案是：可以。v86 把 promoted baseline decision 迁移为 `report_utils` 的第四个消费者。这样 promoted baseline decision -> promoted seed -> promoted seed handoff -> controlled execution handoff 这段链路开始共享同一套报告基础工具。

本版明确不做：

- 不改变 baseline 选择算法。
- 不改变 accepted/review/blocked 判断。
- 不改变 rejected runs 的原因计算。
- 不新增新报告层。
- 不迁移 promoted comparison 等更上游模块。

## 前置路线

v86 接在 v80-v85 的链路后面：

```text
v80 promoted training scale baseline decision
 -> v81 promoted training scale next-cycle seed
 -> v82 promoted training scale seed handoff
 -> v83 shared report utility consolidation
 -> v84 controlled handoff report-utils migration
 -> v85 promoted seed report-utils migration
 -> v86 promoted decision report-utils migration
```

v85 已经让 seed generation 接入公共工具。v86 再向上游推进一步，让 baseline decision 也接入公共工具。

这次仍然是代码质量收口，不是功能扩张。

## 关键文件

```text
src/minigpt/promoted_training_scale_decision.py
src/minigpt/report_utils.py
tests/test_promoted_training_scale_decision.py
tests/test_report_utils.py
c/86/图片
c/86/解释/说明.md
```

`src/minigpt/promoted_training_scale_decision.py` 是本版主要修改点。它的业务 API 保持不变：

```text
load_promoted_training_scale_comparison
build_promoted_training_scale_decision
write_promoted_training_scale_decision_outputs
render_promoted_training_scale_decision_markdown
render_promoted_training_scale_decision_html
```

`src/minigpt/report_utils.py` 继续作为公共基础层提供 JSON/CSV 写出、Markdown/HTML 转义、list/dict 归一化和 UTC 时间。

`tests/test_promoted_training_scale_decision.py` 保护 baseline selector 的核心行为。

`c/86` 保存运行截图和解释，用来证明迁移是可验证的。

## 迁移内容

迁移前，`promoted_training_scale_decision.py` 自己维护这些私有 helper：

```text
utc_now
_dict
_list_of_dicts
_string_list
_md
_e
```

迁移后，它从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_csv_row
write_json_payload
```

这次不需要 `display_command`，因为 baseline decision 本身不生成 shell/CLI command。它主要输出 selected baseline、candidate/rejected counts、rejected reasons 和 recommendations。

## 业务流程保持不变

`build_promoted_training_scale_decision(...)` 的流程仍然是：

```text
1. 读取 promoted comparison
2. 解析 comparison summary
3. 从 promotions 中抽出 promoted rows
4. 根据 readiness、gate、batch、run path 计算 rejection reasons
5. 从 candidates 中选择最佳 baseline
6. 根据 selected/rejected/comparison blockers 得出 decision_status
7. 输出 selected_baseline、rejected_runs、summary 和 recommendations
```

本版没有改变 `_rejection_reasons`、`_select_candidate` 或 `_decision_status`。因此 baseline 选择语义保持不变。

变更集中在输出层：

- JSON 写出改为 `write_json_payload`。
- CSV 写出改为 `write_csv_row`。
- Markdown 表格单元格改为 `markdown_cell`。
- HTML 转义改为 `html_escape`。
- JSON 外部结构读取的防御式归一化改为 `as_dict`、`list_of_dicts`、`string_list`。

## 输出格式

输出文件名保持不变：

```text
promoted_training_scale_decision.json
promoted_training_scale_decision.csv
promoted_training_scale_decision.md
promoted_training_scale_decision.html
```

CSV 字段保持不变：

```text
decision_status
selected_baseline
selected_gate_status
selected_batch_status
selected_readiness_score
candidate_count
rejected_count
comparison_status
```

HTML 仍然展示 decision、selected baseline、gate、batch、score、candidate/rejected counts 和 rejected runs table。

Markdown 仍然展示 rejected runs 表格和 recommendations。

## 测试覆盖

`tests/test_promoted_training_scale_decision.py` 覆盖四条核心路径：

- compared promoted runs 中能选出 baseline。
- 只有一个 candidate 时会 blocked。
- 上游 comparison 不是 compared 时会 blocked。
- 输出和 HTML escaping 仍然正常。

`tests/test_report_utils.py` 继续保护公共工具自身。

focused tests 同时运行这两个测试文件，证明“第四个消费者”和“公共层”都正常。

## 截图归档

v86 的运行截图放在：

```text
c/86/图片
c/86/解释/说明.md
```

截图含义：

- `01-unit-tests.png`：focused tests、compileall、全量 unittest 通过。
- `02-promoted-decision-accepted-smoke.png`：accepted smoke，证明迁移后仍能选出 baseline。
- `03-promoted-decision-blocked-smoke.png`：blocked smoke，证明上游 evidence 不完整时仍阻断。
- `04-promoted-decision-structure-check.png`：源码、测试、文档、归档结构检查，以及 replacement character 检查。
- `05-playwright-promoted-decision-html.png`：浏览器打开迁移后的 promoted decision HTML。
- `06-docs-check.png`：README、阶段索引和 c archive 索引都更新到 v86。

## 后续原则

到 v86，`report_utils.py` 已经覆盖四个消费者：

```text
promoted_training_scale_decision.py
promoted_training_scale_seed.py
promoted_training_scale_seed_handoff.py
training_scale_handoff.py
```

这说明公共工具已经不只是单点抽象，而是在连续业务链路里发挥作用。后续可以继续迁移 promoted comparison 或 promotion index，但仍应保持小步、测试优先、输出格式不变。

## 一句话总结

v86 把 promoted baseline decision 接入 `report_utils`，让 baseline selector 到 seed/handoff 的连续链路共享同一套报告基础设施。
