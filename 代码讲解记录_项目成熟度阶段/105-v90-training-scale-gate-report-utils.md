# v90 training scale gate report utility migration

## 本版目标

v90 的目标是继续 `report_utils` 收口路线，把 v71 引入的 `training_scale_gate.py` 迁移到公共报告工具上。

这个模块的职责是读取 `training_scale_plan.json`，用 `review`、`standard`、`strict` 等 profile 检查训练规模计划是否适合进入后续 gated run。它会输出：

- `training_scale_gate.json`
- `training_scale_gate.csv`
- `training_scale_gate.md`
- `training_scale_gate.html`
- 每条 check 的 status、message、recommendation、details
- overall pass/warn/fail 汇总
- batch command 建议

v90 要解决的问题是：v89 已经让 gated run 接入公共报告工具，v88 已经让 comparison 接入公共报告工具，v87 已经让 decision 接入公共报告工具，但最前面的 profile gate 仍保留私有 JSON/CSV/Markdown/HTML helper。

本版把 gate 层也迁入公共工具，让 gate -> run -> comparison -> decision 四层训练规模证据共享同一套报告基础设施。

## 本版明确不做什么

v90 不改变 profile policy 和 gate check 语义。

下面这些行为保持不变：

- `review`、`standard`、`strict` 的阈值
- tiny corpus 是 warn 还是 fail
- min char count 的 pass/warn/fail 判断
- quality warnings 的判断
- variant count 范围判断
- baseline variant 是否存在的判断
- batch handoff 是否完整的判断
- token budget 和 corpus pass estimate 的判断
- overall status 如何由 fail/warn/pass count 汇总

本版只迁移报告基础设施，不调整准入策略。

## 来自哪条路线

v83 新增 `report_utils.py`。

v87 到 v89 回收了原始 training scale 链路中靠后的三层：

```text
v72 gated run
 -> v73 run comparison
 -> v74 run decision
```

v90 再往前回收 v71 gate：

```text
v71 training scale gate
 -> v72 gated run
 -> v73 run comparison
 -> v74 run decision
```

这样从准入检查到执行候选决策，四层 evidence report 都开始复用公共报告基础设施。

## 关键文件

`src/minigpt/training_scale_gate.py`

这是本版核心迁移文件。它继续负责 policy profile、check 生成、summary 汇总、recommendations、JSON/CSV/Markdown/HTML 输出。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用它已有的 JSON 写出、CSV cell 转换、命令展示、Markdown/HTML 转义、list/dict 归一化和 UTC 时间工具。

`tests/test_training_scale_gate.py`

这是 gate 业务测试，覆盖 review warn、standard fail、输出文件、缺失 baseline、token budget fail、HTML 转义和未知 profile。

`tests/test_report_utils.py`

这是公共层测试，保护 JSON/CSV 写出、命令展示、Markdown/HTML 转义、artifact row 和 list/dict 归一化。

`scripts/check_training_scale_gate.py`

这是 CLI 入口。本版不改参数和退出码语义。

`代码讲解记录_项目成熟度阶段/105-v90-training-scale-gate-report-utils.md`

这是本文件，解释 v90 的迁移目标、边界、字段语义和验证证据。

`c/90/`

这是 v90 的运行截图和解释归档目录。

## 迁移前的重复点

迁移前，`training_scale_gate.py` 自己维护了：

```text
utc_now
_display_command
_list_of_dicts
_string_list
_dict
_md
_e
```

同时 JSON 输出也由本模块手写：

```text
Path(...).write_text(json.dumps(...))
```

CSV details 也在本模块直接 `json.dumps`。

这些能力在 `report_utils.py` 中已有对应原语。继续保留会让 gate、run、comparison、decision 这四层报告行为分叉。

## 迁移后的引入关系

v90 让 `training_scale_gate.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
csv_cell as _csv_value
display_command as _display_command
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

保留 `_dict`、`_md`、`_e` 等别名，是为了让原有渲染模板保持稳定，避免把 helper 迁移变成大规模 HTML/Markdown 重写。

## JSON 输出

`write_training_scale_gate_json` 改为调用：

```text
write_json_payload(report, path)
```

这个 JSON 是 gate 层的核心机器可读证据。后续 gated run 会读取 gate summary，comparison 又会读取 run summary，因此 gate JSON 的结构必须保持稳定。

公共 JSON writer 统一保证：

- 自动创建父目录
- UTF-8
- `ensure_ascii=False`
- `indent=2`

## CSV 输出

`training_scale_gate.csv` 是 per-check 多行表格。每条 check 都有：

```text
code
status
message
recommendation
details
```

它不是单行摘要，所以本版没有强行使用 `write_csv_row`。本模块仍然保留多行 `csv.DictWriter` 循环，但 `details` 单元格改为复用：

```text
csv_cell as _csv_value
```

这样 dict/list 的 CSV 序列化方式与其他 report 保持一致。

## Markdown 和 HTML 渲染

Markdown 报告仍然包含：

- generated
- profile
- status
- plan path
- dataset/version
- scale
- char count
- variant count
- warning count
- checks table
- recommendations
- batch command

HTML 报告仍然包含：

- header
- stats cards
- checks table
- recommendations
- batch handoff command section

变化在于 Markdown cell、HTML escape 和 command display 改为公共工具：

```text
markdown_cell
html_escape
display_command
```

测试里会用 `<demo>` 作为 dataset name，确认 HTML 中出现 `&lt;demo&gt;`，而不是未经转义的 `<demo>`。

## 核心检查语义

`training_scale_gate.py` 的核心仍然是 `_build_checks`。

它会检查：

- `plan_schema`
- `source_count`
- `dataset_fingerprint`
- `min_char_count`
- `tiny_corpus`
- `quality_warnings`
- `variant_count`
- `baseline_variant`
- `batch_handoff`
- `variant_dataset_versions`
- `token_budget`
- `corpus_pass_estimate`

每个 check 都输出：

- `code`
- `status`
- `message`
- `recommendation`
- `details`

v90 没有改变任何 check 的触发条件。

## overall status

`_status_summary` 的规则保持不变：

- 只要有一个 fail，overall 是 `fail`
- 没有 fail 但有 warn，overall 是 `warn`
- 没有 fail/warn，overall 是 `pass`

这个规则直接影响 v72 gated run 是否能启动 batch handoff，因此 v90 必须保持不动。

## profile policy

三个 profile 仍然保持原阈值：

`review`

面向 smoke/review，允许 tiny/small corpus 用 warn 通过，质量警告上限更宽。

`standard`

面向常规执行，tiny/small corpus 和 quality warnings 更容易 fail。

`strict`

面向更严格的执行前准入，要求更大语料、更少 corpus pass、更窄 variant 数量。

v90 不修改这些 profile，只迁移报告 helper。

## 测试覆盖

`tests/test_training_scale_gate.py` 覆盖七类行为。

第一类是 review profile：

- tiny plan 在 review 下是 `warn`
- fail count 为 0
- tiny_corpus check 是 warn
- plan summary 的 variant_count 与 plan variants 数量一致

第二类是 standard profile：

- tiny 或 warning plan 在 standard 下是 fail
- min_char_count 是 fail
- quality_warnings 是 fail

第三类是输出和加载：

- plan JSON 可以加载
- gate JSON/CSV/HTML 可以写出
- JSON 中 plan_path 保持正确
- overall status 属于 pass/warn/fail

第四类是缺失 baseline：

- batch baseline 被改成 missing
- baseline_variant check 变成 fail

第五类是 token budget：

- 人为提高 token_budget
- token_budget check 变成 fail

第六类是 HTML 转义：

- dataset name 使用 `<demo>`
- HTML 中必须出现 `&lt;demo&gt;`
- 原始 `<demo>` 不能直接出现

第七类是未知 profile：

- profile 不存在时快速抛出 `ValueError`

这些断言保护的是 gate policy 和 check 语义，而不仅是报告文件存在。

`tests/test_report_utils.py` 继续保护公共工具本身。v90 focused tests 同时跑 gate tests 和 report utils tests，证明消费者和公共层都正常。

## 运行截图和证据

v90 的运行证据归档到：

```text
c/90/图片
c/90/解释/说明.md
```

截图会覆盖：

- focused tests、compileall、full regression
- review profile smoke
- standard profile smoke
- source/docs/archive structure check
- Playwright/Chrome HTML 渲染
- README 与讲解索引检查

这些截图是本版提交随附的证据链。

## 后续开发原则

v90 之后，原始 training scale 链路还剩 `training_scale_plan.py` 和更高层 workflow/promotion 模块可以继续小步迁移。

继续推进时要保持：

- 不修改 policy profile。
- 不修改 pass/warn/fail 业务判断。
- 不重排输出字段。
- 每版只迁移一个边界清晰的消费者。
- 用 tests、smoke、Playwright 和文档索引闭环。

## 一句话总结

v90 把 training scale gate 接入 `report_utils`，让 gate、run、comparison、decision 四层训练规模证据开始共享同一套报告基础设施。
