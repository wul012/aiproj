# v87 training scale run decision report utility migration

## 本版目标

v87 的目标是继续 `report_utils` 收口路线，把 v74 引入的 `training_scale_run_decision.py` 迁移到公共报告工具上。

这个模块的职责是读取多次 gated training scale run 的 comparison 报告，从中选择下一次最适合进入真实 `--execute` 的 run，并输出：

- decision JSON
- summary CSV
- Markdown 说明
- HTML 浏览器报告
- rejected runs 和原因
- 下一步 execute command

v87 要解决的问题不是“再新增一个训练治理节点”，而是减少这类报告模块中反复复制的小工具：

- JSON 写出
- 单行 CSV 写出
- 命令字符串展示
- Markdown 表格单元格转义
- HTML 转义
- list/dict 防御性归一化
- UTC 时间戳

## 本版明确不做什么

v87 不改训练规模决策语义。

也就是说，下面这些行为保持不变：

- `min_readiness` 如何过滤候选 run
- `require_gate_pass` 如何拒绝 warn gate
- `require_batch_started` 如何拒绝未启动 batch dry-run 的 run
- `ready`、`review`、`blocked` 三种状态如何判断
- 候选 run 如何按 readiness、gate、batch 和 warning 数选择
- execute command 如何从原始 run 的 plan/out_root/gate profile 生成

本版只移动报告基础设施，不重写决策模型。

## 来自哪条路线

v83 开始新增 `src/minigpt/report_utils.py`，先迁移 promoted seed handoff 作为低风险验证点。

v84 把 controlled training scale handoff 接入公共工具。

v85 把 promoted next-cycle seed builder 接入公共工具。

v86 把 promoted baseline decision 接入公共工具。

v87 回到更早的 v74 `training_scale_run_decision.py`，把原始 training scale run execute-candidate selector 也迁入公共层。

这说明 `report_utils` 不只服务 promoted 链路，也能服务 promoted 之前的基础训练规模决策层。

## 关键文件

`src/minigpt/training_scale_run_decision.py`

这是本版的核心迁移文件。它继续负责读取 comparison、筛选 candidates、记录 rejected runs、选择 selected run、生成 execute command，并渲染 JSON/CSV/Markdown/HTML 输出。

`src/minigpt/report_utils.py`

这是 v83 抽出的公共报告工具层。本版继续复用它，没有扩张复杂抽象。

`tests/test_training_scale_run_decision.py`

这是 training scale run decision 的业务测试。它覆盖候选选择、gate pass 要求、readiness 阈值、目录输入解析、HTML 转义和输出文件写出。

`tests/test_report_utils.py`

这是公共工具层测试。它保护 JSON/CSV 写出、命令展示、Markdown/HTML 转义、artifact row 和 list/dict 归一化。

`scripts/decide_training_scale_run.py`

这是 CLI 入口。本版没有改动脚本参数，因为迁移只发生在底层报告 helper，不影响用户执行命令。

`代码讲解记录_项目成熟度阶段/102-v87-run-decision-report-utils.md`

这是本文件，解释 v87 的迁移边界、核心数据结构和证据链。

`c/87/`

这是 v87 的运行截图和解释归档目录，保存测试、smoke、Playwright 和结构检查截图。

## 迁移前的重复点

迁移前，`training_scale_run_decision.py` 自己维护了多组私有 helper：

```text
utc_now
_list_of_dicts
_string_list
_dict
_display_command
_quote_command_part
_md
_e
```

同时，JSON 和 CSV 写出也在模块内直接处理：

```text
Path(...).write_text(json.dumps(...))
csv.DictWriter(...)
```

这些逻辑在多个 evidence/report 模块里都出现过。继续复制会带来两个问题：

- 行为容易轻微分叉，例如 CSV 对 list/dict 的写法、命令带空格时的引用方式、HTML 转义策略。
- 后续维护成本变高，每新增或修正一个基础报告行为，都要在很多模块里重复改。

## 迁移后的引入关系

v87 让 `training_scale_run_decision.py` 从 `minigpt.report_utils` 引入：

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

保留 `_dict`、`_md`、`_e` 这些别名，是为了让渲染代码的局部形状保持稳定。这样本版 diff 集中在 helper 来源和写出函数上，不把 HTML/Markdown 模板重排成大改。

## JSON 输出

`write_training_scale_run_decision_json` 从手写 `json.dumps` 改为调用：

```text
write_json_payload(report, path)
```

这意味着 JSON 写出统一由公共层负责：

- 自动创建父目录
- 使用 UTF-8
- `ensure_ascii=False`
- `indent=2`

这个 JSON 是最终证据，不是临时调试文件。后续 workflow、handoff、截图说明和人工审阅都可以直接读取它。

## CSV 输出

`write_training_scale_run_decision_csv` 仍然由本模块定义字段含义：

```text
decision_status
recommended_action
selected_run
selected_gate_status
selected_batch_status
selected_readiness_score
candidate_count
rejected_count
execute_command
```

变化是实际写出改为：

```text
write_csv_row(row, out_path, fieldnames)
```

字段语义仍属于 run decision 模块；CSV 文件创建、表头写入和 cell 转换交给公共层。

这个 CSV 是摘要证据，适合被脚本、表格工具或后续索引快速读取。

## Markdown 和 HTML 渲染

Markdown 渲染仍然输出：

- generated/status/action
- selected run/gate/batch/readiness
- candidate/rejected count
- execute command code block
- rejected runs 表格
- recommendations

HTML 渲染仍然输出：

- 顶部标题和 comparison path
- stats card
- execute command section
- rejected runs table
- recommendations section

变化在于 Markdown cell 和 HTML escape 不再由本模块私有函数处理，而是复用：

```text
markdown_cell
html_escape
```

这能保证后续多个 HTML/Markdown report 对特殊字符的处理一致。例如测试里会用 `<allowed>` 作为 run name，确认 HTML 中出现的是 `&lt;allowed&gt;`，而不是未经转义的标签。

## 命令展示

`execute_command` 仍然是列表形式，表示真实命令参数：

```text
[
  "python",
  "scripts/run_training_scale_plan.py",
  "--plan",
  "...",
  "--out-root",
  "...",
  "--gate-profile",
  "review",
  "--execute"
]
```

`execute_command_text` 仍然是面向人阅读和复制的字符串。

v87 改为通过公共的 `display_command` 生成字符串。它会处理带空格的参数和双引号，避免不同模块展示命令时规则不一致。

## 决策流程没有改变

`build_training_scale_run_decision` 的核心流程仍然是：

1. 读取 `training_scale_run_comparison.json`
2. 取出 comparison 里的 runs
3. 对每个 run 执行 `_rejection_reasons`
4. 没有 rejection reasons 的 run 进入 candidates
5. 有 rejection reasons 的 run 进入 rejected
6. 用 `_select_candidate` 从 candidates 里选出 selected run
7. 读取 selected run 对应的原始 `training_scale_run.json`
8. 生成 execute command
9. 根据 selected run 和 gate 要求生成 `ready/review/blocked`
10. 输出 summary 和 recommendations

v87 只替换步骤 9 之后的报告基础设施，没有调整步骤 1-8 的决策依据。

## 关键状态语义

`ready`

代表选中的 run 已经满足候选条件，且 gate status 是 `pass`。

`review`

代表选中的 run 可以作为候选，但 gate status 是 `warn`，并且当前没有要求必须 pass。它不是失败，而是需要人工确认警告是否可接受。

`blocked`

代表没有可用候选，或者要求 gate pass 但候选不满足。此时不应该执行下一步训练命令。

## rejected runs 的意义

`rejected_runs` 不是错误日志，而是决策证据。

每个 rejected row 记录：

- run name
- gate status
- batch status
- allowed
- readiness score
- rejection reasons

它解释为什么某些 run 没有进入下一次 execute 阶段。例如：

- gate did not allow this run
- gate failed
- gate is not pass
- batch dry-run was not started
- readiness_score below N

这些原因能让后续复查时知道“为什么选这个 run”，而不是只看到 selected run。

## 测试覆盖

`tests/test_training_scale_run_decision.py` 覆盖了五类关键行为。

第一类是正常选择候选：

- 构造 review gate 下 allowed 的 run
- 构造 standard gate 下 blocked 的 run
- 确认 selected run 是 allowed
- 确认状态是 `review`
- 确认 execute command 包含 `--execute`、`--gate-profile` 和 `review`

第二类是严格 gate pass：

- 打开 `require_gate_pass=True`
- warn-only comparison 被全部拒绝
- 状态变成 `blocked`
- rejected reasons 包含 `gate is not pass`

第三类是 readiness 阈值：

- 提高 `min_readiness`
- 低分候选被拒绝
- rejected reasons 包含具体阈值

第四类是输出和转义：

- 支持传入 comparison directory
- 写出 JSON/CSV/Markdown/HTML 四类产物
- `<allowed>` 在 HTML 中被转义为 `&lt;allowed&gt;`
- JSON schema_version 仍为 1

第五类是无 runs 的非法输入：

- comparison 中 runs 为空时抛出 `ValueError`

这些断言保护的是决策语义，而不仅仅是“文件能写出来”。

`tests/test_report_utils.py` 保护公共层本身：

- artifact row 存在性和 count
- command display 对空格和引号的处理
- Markdown/HTML 转义
- JSON/CSV 父目录创建
- list-of-dicts 过滤非法项

这两组测试放在一起运行，能证明“消费者模块”和“公共工具层”同时正常。

## 运行截图和证据

v87 的运行证据归档到：

```text
c/87/图片
c/87/解释/说明.md
```

其中截图会覆盖：

- focused tests、compileall、full regression
- ready smoke
- blocked smoke
- source/docs/archive structure check
- Playwright/Chrome 打开 HTML
- README 与讲解索引检查

这些截图不是临时调试输出，而是本版提交随附的验证证据。

## 后续开发原则

v87 之后，类似的 report/evidence 模块应优先检查是否能使用 `report_utils.py`。

适合继续迁移的对象包括：

- 仍然自带 `_md`、`_e`、`_dict`、`_list_of_dicts` 的训练治理报告
- 自己手写单行 CSV 摘要的模块
- 自己手写 JSON pretty print 的模块
- 自己实现命令展示字符串的模块

但迁移要保持小步，不应该一次改动所有历史模块。每一版最好只迁移一个边界清晰的消费者，并用 focused tests、smoke 和 HTML 截图证明行为没有变。

## 一句话总结

v87 把原始 training scale run decision 接入 `report_utils`，让公共报告基础层从 promoted 链路回收到了更早的训练规模执行候选决策层。
