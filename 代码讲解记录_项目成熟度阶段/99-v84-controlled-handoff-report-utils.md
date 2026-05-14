# v84 controlled handoff report-utils migration 代码讲解

## 本版目标

v84 的目标是继续 v83 的代码质量收口，但这次不只验证“新模块可以用公共工具”，而是回头迁移一个更早的核心 handoff 模块：

```text
src/minigpt/training_scale_handoff.py
```

这个模块来自 v76，职责是读取 v75 workflow decision，默认只验证执行命令，显式 `--execute` 时才真正运行选中的训练规模执行命令，并记录 return code、stdout/stderr tail、耗时和训练产物是否存在。

v84 解决的问题是：

```text
v83 已经抽出了 report_utils，但它是否只适合最新的 promoted seed handoff？
还是也能服务更早的 controlled training scale handoff？
```

本版答案是：可以服务。v84 把 v76 handoff 迁移为 `report_utils` 的第二个消费者，减少重复私有 helper，同时保持原有 JSON/CSV/Markdown/HTML 输出格式和测试行为不变。

本版明确不做：

- 不改变 v76 handoff 的业务判断。
- 不改变默认安全策略，仍然默认 planned，不自动执行训练。
- 不新增新的治理报告。
- 不批量迁移所有历史模块。
- 不改变执行命令的 list 形式，也不把命令改成 shell 字符串执行。

## 前置路线

v84 接在 v83 后面：

```text
v76 controlled training scale handoff
 -> v83 shared report utility consolidation
 -> v84 controlled handoff report-utils migration
```

v83 先抽出公共工具，并迁移 v82 `promoted_training_scale_seed_handoff.py`。这一步证明了公共工具能服务“下一轮 plan seed handoff”。

v84 再迁移 v76 `training_scale_handoff.py`。这一步证明公共工具也能服务“workflow decision execution handoff”。两类 handoff 输入不同：

- v82 promoted seed handoff 的输入是 next-cycle seed。
- v76 controlled handoff 的输入是 training-scale workflow decision。

但它们共享同一类报告基础设施：

- JSON 写出。
- CSV 摘要写出。
- artifact row 结构。
- artifact availability 计数。
- command text 展示。
- Markdown/HTML 转义。
- list/dict 防御式归一化。

## 关键文件

```text
src/minigpt/training_scale_handoff.py
src/minigpt/report_utils.py
tests/test_training_scale_handoff.py
tests/test_report_utils.py
c/84/图片
c/84/解释/说明.md
```

`src/minigpt/training_scale_handoff.py` 是本版主要修改点。它的业务函数仍然保留：

```text
load_training_scale_workflow
build_training_scale_handoff
write_training_scale_handoff_outputs
render_training_scale_handoff_markdown
render_training_scale_handoff_html
```

`src/minigpt/report_utils.py` 是 v83 新增的公共工具，本版没有大改它，而是把 v76 handoff 接入它，验证它的抽象是否足够通用。

`tests/test_training_scale_handoff.py` 是主要回归测试。它确保 planned、blocked、execute、failed、输出和 HTML escaping 行为不因迁移改变。

`tests/test_report_utils.py` 继续保护公共层基础合同。

`c/84` 是运行证据归档，用于证明代码迁移、测试、smoke、Playwright 和文档同步都完成。

## 迁移前的问题

迁移前，`training_scale_handoff.py` 内部有一批私有 helper：

```text
utc_now
_artifact
_dict
_list_of_dicts
_string_list
_display_command
_quote_command_part
_md
_e
```

这些 helper 和 v82 promoted seed handoff 里的 helper 高度相似。长期保留会造成两个问题：

1. 同样的输出边界要在多个模块里维护。
2. 后续新报告模块容易继续复制这些函数，让代码量膨胀。

v84 的迁移把这些重复逻辑改为从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
count_available_artifacts
display_command as _display_command
html_escape as _e
list_of_dicts as _list_of_dicts
make_artifact_row
markdown_cell as _md
string_list as _string_list
utc_now
write_csv_row
write_json_payload
```

这里保留 `_dict`、`_e`、`_md` 这类本地别名，是为了让业务代码的渲染结构尽量少动。迁移重点不是改写风格，而是把重复实现移出模块。

## 核心流程不变

`build_training_scale_handoff(...)` 的主流程没有变化：

```text
1. load_training_scale_workflow 读取 workflow JSON
2. _load_decision 找到 workflow 关联的 decision JSON
3. _command_from_decision 读取 execute_command
4. _handoff_allowed 判断 ready/review/blocked 边界
5. _execution_result 根据 execute 参数决定只计划还是实际运行
6. _artifact_rows 检查预期执行产物
7. _summary 汇总状态
8. render/write 函数输出 JSON/CSV/Markdown/HTML
```

本版只改变这些步骤里的底层工具：

- JSON 文件写出由 `write_json_payload` 负责。
- 单行 CSV 摘要写出由 `write_csv_row` 负责。
- 普通 artifact row 由 `make_artifact_row` 负责。
- artifact 可用数量由 `count_available_artifacts` 负责。
- 命令展示由 `display_command` 负责。
- HTML 转义由 `html_escape` 负责。
- Markdown 表格单元格由 `markdown_cell` 负责。

## artifact row 语义

v76 handoff 检查的产物包括：

```text
training_scale_run.json
training_scale_run.html
batch/training_portfolio_batch.json
batch/training_portfolio_batch.html
batch/variants/*/training_portfolio.json
batch/variants/*/runs/*/checkpoint.pt
```

前四个是固定文件，迁移后用：

```text
make_artifact_row("training_scale_run_json", root / "training_scale_run.json")
```

后两个是聚合类产物，不是单个文件，而是 glob 出来的数量：

```text
make_artifact_row("variant_portfolio_reports", variants_dir, exists=bool(variant_reports), count=len(variant_reports))
make_artifact_row("variant_checkpoints", variants_dir, exists=bool(checkpoints), count=len(checkpoints))
```

这样 artifact row 仍然保持同一个结构：

```json
{
  "key": "variant_checkpoints",
  "path": ".../batch/variants",
  "exists": true,
  "count": 1
}
```

这也是 v83 `make_artifact_row` 要支持显式 `exists` 和 `count` 的原因：它不只服务单个文件，也服务目录聚合检查。

## 输出格式

本版保持原输出文件名不变：

```text
training_scale_handoff.json
training_scale_handoff.csv
training_scale_handoff.md
training_scale_handoff.html
```

JSON 仍然是最终结构化证据，包含 workflow path、decision status、command、execution、artifact rows、summary 和 recommendations。

CSV 仍然是摘要索引，字段包括：

```text
handoff_status
decision_status
execute
returncode
elapsed_seconds
artifact_count
available_artifact_count
command
blocked_reason
```

Markdown 和 HTML 仍然是面向人阅读的证据视图。迁移到公共 escaping 后，HTML 中的 `<handoff>` 仍然会变成 `&lt;handoff&gt;`，避免原始文本被浏览器当作标签解析。

## 测试覆盖

`tests/test_training_scale_handoff.py` 覆盖了五条关键路径：

- `test_validates_review_handoff_without_executing`：review 状态默认允许 planned，但不会执行训练。
- `test_blocks_review_when_allow_review_false`：显式不允许 review 时，handoff 被阻断。
- `test_execute_runs_command_and_detects_artifacts`：执行一个临时命令，真实写出 run、batch、variant、checkpoint 产物，并检查 artifact availability。
- `test_execute_reports_failed_command`：命令非零退出时，状态变成 `failed`，return code 保留。
- `test_outputs_and_renderers_escape_html`：输出 JSON/CSV，Markdown 有 Command section，HTML 正确转义。

这些测试保护了 v84 的核心承诺：迁移公共工具不改变 handoff 行为。

`tests/test_report_utils.py` 继续保护公共工具本身。v84 focused tests 会同时运行这两个测试文件，证明“公共层”和“第二个消费者”都正常。

## 截图归档

v84 运行截图放在：

```text
c/84/图片
c/84/解释/说明.md
```

截图含义：

- `01-unit-tests.png`：focused tests、compileall、全量 unittest 通过。
- `02-controlled-handoff-plan-smoke.png`：planned-mode smoke，证明迁移后仍能读取 workflow decision 并生成 handoff summary。
- `03-controlled-handoff-execute-smoke.png`：execute smoke，证明迁移后仍能运行临时命令、检测 6 类 artifact、写出四种报告。
- `04-controlled-handoff-structure-check.png`：证明源码迁移、测试、文档、归档结构齐全，且没有 replacement character。
- `05-playwright-controlled-handoff-html.png`：浏览器打开迁移后的 HTML 报告，证明 HTML 证据仍然可读。
- `06-docs-check.png`：README、阶段索引和 c archive 索引都已更新到 v84。

## 后续原则

v84 之后，`report_utils.py` 已经有两个消费者：

```text
promoted_training_scale_seed_handoff.py
training_scale_handoff.py
```

这说明公共层不是一次性的“新模块辅助函数”，而是可以逐步承接历史报告代码。后续建议：

- 新增 report/evidence 模块默认使用 `report_utils.py`。
- 修改旧模块时顺手迁移重复 helper。
- 不为了迁移而迁移全部历史文件，避免大面积改动带来输出格式风险。
- 每迁移一个旧模块，都要配对应的 focused test 和 smoke 证据。

## 一句话总结

v84 把 `report_utils` 从“新 handoff 的公共工具”推进为“可回收早期 handoff 重复实现的公共基础层”，让项目代码质量开始真正收敛。
