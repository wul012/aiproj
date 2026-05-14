# v85 promoted seed report-utils migration 代码讲解

## 本版目标

v85 继续 v83-v84 的代码质量收口路线，这次迁移的是 v81 的 next-cycle seed builder：

```text
src/minigpt/promoted_training_scale_seed.py
```

这个模块的职责是读取 v80 promoted baseline decision，结合下一轮语料来源，生成一个可审计的 next-cycle seed。seed 里会包含下一步 `plan_training_scale.py` 命令、来源语料状态、selected baseline 摘要、blocker 和 recommendations。

v85 要解决的问题是：

```text
report_utils 已经服务了 seed handoff 和 controlled execution handoff；
它是否也能服务 seed generation 本身？
```

本版答案是：可以。v85 把 `promoted_training_scale_seed.py` 迁移为 `report_utils` 的第三个消费者。这样从 seed generation 到 seed handoff，再到 controlled execution handoff，已经有一条连续链路共用相同的报告基础工具。

本版明确不做：

- 不改变 seed 的状态判断。
- 不改变 ready/review/blocked 语义。
- 不改变 next plan command 的生成规则。
- 不新增新报告层。
- 不批量迁移所有 promoted 模块。

## 前置路线

v85 接在 v83-v84 的公共化路线之后：

```text
v81 promoted training scale next-cycle seed
 -> v82 promoted training scale seed handoff
 -> v83 shared report utility consolidation
 -> v84 controlled handoff report-utils migration
 -> v85 promoted seed report-utils migration
```

v83 让 `report_utils` 服务 v82 seed handoff。v84 让它服务 v76 controlled execution handoff。v85 再把 v81 seed generation 接进来。

这不是功能扩张，而是代码收口：同一条训练规模治理链里的三个模块，现在共享同一套 JSON/CSV 写出、命令展示、Markdown/HTML 转义和 list/dict 归一化工具。

## 关键文件

```text
src/minigpt/promoted_training_scale_seed.py
src/minigpt/report_utils.py
tests/test_promoted_training_scale_seed.py
tests/test_report_utils.py
c/85/图片
c/85/解释/说明.md
```

`src/minigpt/promoted_training_scale_seed.py` 是本版主要修改点。它的业务函数没有改名：

```text
load_promoted_training_scale_decision
build_promoted_training_scale_seed
write_promoted_training_scale_seed_outputs
render_promoted_training_scale_seed_markdown
render_promoted_training_scale_seed_html
```

`src/minigpt/report_utils.py` 是公共基础层，本版继续复用它，不扩张复杂抽象。

`tests/test_promoted_training_scale_seed.py` 是核心回归测试，保证 ready、review、blocked、missing source 和 HTML escaping 都不变。

`c/85` 是运行截图和解释归档，用来证明代码、测试、smoke、Playwright 和文档闭环完成。

## 迁移内容

迁移前，`promoted_training_scale_seed.py` 自己维护这些私有 helper：

```text
utc_now
_dict
_list_of_dicts
_string_list
_display_command
_quote_command_part
_md
_e
```

迁移后，它从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
display_command as _display_command
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_csv_row
write_json_payload
```

这次没有使用 artifact row，因为 seed generation 的主要输出不是检查已有产物是否存在，而是记录 next plan command 和 source rows。它仍然复用了公共的 JSON/CSV、command display 和转义工具。

## 业务流程保持不变

`build_promoted_training_scale_seed(...)` 的流程仍然是：

```text
1. 读取 promoted baseline decision
2. 定位 selected_baseline 和 training_scale_run.json
3. 检查下一轮 corpus sources 是否存在
4. 汇总 blockers
5. 根据 accepted/review/blocked 计算 seed_status
6. ready/review 时生成 plan_training_scale.py 命令
7. 输出 baseline_seed、next_plan、summary、recommendations
```

迁移后，`plan["command_text"]` 仍然由命令 list 转成人类可读字符串，但实现从本地 `_display_command` 变成公共 `display_command`。

`write_promoted_training_scale_seed_json` 改为调用 `write_json_payload`。

`write_promoted_training_scale_seed_csv` 改为调用 `write_csv_row`。

Markdown 中 source rows 的表格单元格仍然做 `|` 和换行保护，但实现从本地 `_md` 变成公共 `markdown_cell`。

HTML 中 title、decision path、baseline、sources、blockers、recommendations 仍然转义，但实现从本地 `_e` 变成公共 `html_escape`。

## seed 字段语义

seed 报告核心字段仍然是：

```text
seed_status
baseline_seed
next_plan
blockers
summary
recommendations
```

`seed_status` 有三类：

- `ready`：baseline decision accepted，selected run 和 corpus source 都完整，可以继续 plan。
- `review`：baseline decision 是 review，命令可生成，但需要人工确认。
- `blocked`：decision、selected baseline、selected run 或 corpus source 有缺口，不生成可执行命令。

`baseline_seed` 保存上一轮 promoted baseline 的来源，包括 selected name、decision/gate/batch status、readiness score、training scale run path 和 selected run summary。

`next_plan` 保存下一轮规划入口，包括 dataset name、version prefix、source rows、command list、command text、command availability 和 execution readiness。

`summary` 是给 CSV/README/截图快速阅读的摘要，不替代完整 JSON。

## 测试覆盖

`tests/test_promoted_training_scale_seed.py` 覆盖五条路径：

- accepted decision + existing source -> `ready`，生成 `plan_training_scale.py` command。
- review decision + existing source -> `review`，保留 command，但 `execution_ready=False`。
- decision 缺 selected baseline -> `blocked`，不生成 command。
- corpus source 缺失 -> `blocked`，`missing_source_count=1`。
- 输出和渲染 -> JSON/CSV 存在，Markdown 有 Next Plan Command，HTML 转义 `<Seed>`。

这些测试直接保护 v85 的承诺：公共工具迁移不改变 seed 语义。

`tests/test_report_utils.py` 继续验证公共层基础能力，包括 JSON/CSV 写出、command display、Markdown/HTML 转义、artifact row 和 list/dict 归一化。

## 截图归档

v85 的运行截图放在：

```text
c/85/图片
c/85/解释/说明.md
```

截图含义：

- `01-unit-tests.png`：focused tests、compileall、全量 unittest 通过。
- `02-promoted-seed-ready-smoke.png`：ready seed smoke，证明迁移后仍能生成 plan command。
- `03-promoted-seed-blocked-smoke.png`：blocked seed smoke，证明缺失 corpus source 时仍阻断。
- `04-promoted-seed-structure-check.png`：源码、测试、文档、归档结构检查，以及 replacement character 检查。
- `05-playwright-promoted-seed-html.png`：浏览器打开迁移后的 promoted seed HTML。
- `06-docs-check.png`：README、阶段索引和 c archive 索引都更新到 v85。

## 后续原则

到 v85，`report_utils.py` 已经有三个消费者：

```text
promoted_training_scale_seed.py
promoted_training_scale_seed_handoff.py
training_scale_handoff.py
```

这说明公共层已经覆盖“seed 生成 -> seed handoff -> controlled execution handoff”的连续片段。后续可以继续按这个节奏迁移相邻模块，例如 promoted decision 或 promotion，但每次仍应保持小步、测试优先、输出格式不变。

## 一句话总结

v85 把 promoted next-cycle seed builder 接入 `report_utils`，让训练规模治理链的 seed generation 和两个 handoff 模块开始共享同一套报告基础层。
