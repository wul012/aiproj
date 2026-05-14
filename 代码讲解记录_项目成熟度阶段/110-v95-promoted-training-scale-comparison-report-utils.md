# v95 promoted training scale comparison report utility migration

## 本版目标

v95 的目标是把 `promoted_training_scale_comparison.py` 接入公共 `report_utils.py`，继续完成训练规模 promoted 链路的轻量质量收口。

v93 已经迁移单个 promotion acceptance，v94 迁移多个 promotion 的 index 层。v95 迁移的是 index 后面的 promoted comparison 层：它读取 promotion index，只比较其中真正 promoted 且路径可用的 training scale runs，然后复用原始 `training_scale_run_comparison` 生成比较证据。

本版解决的问题是：`promoted_training_scale_comparison.py` 原本仍然保留私有 `utc_now`、`_dict`、`_list_of_dicts`、`_string_list`、`_md`、`_e` 和 JSON writer。它们和 `report_utils.py` 已有能力重复，使 promoted comparison 与 promotion index 在基础报告行为上继续分叉。

v95 的结果是：promoted-only comparison evidence 也开始复用公共报告基础层。

## 本版明确不做什么

v95 不改变 promoted comparison 的业务策略。

保持不变的边界包括：

- comparison 仍然只消费 promotion index 中 `promoted_for_comparison == true` 的行。
- 少于两个 promoted inputs 时仍然 blocked。
- promoted run 路径缺失时仍然 blocked。
- baseline 不在 promoted comparison inputs 中时仍然 blocked。
- review 和 blocked promotion 继续不能进入 comparison runs。
- `comparison_status` 仍然只在比较成功时为 `compared`。
- CLI `scripts/compare_promoted_training_scale_runs.py` 的参数和输出语义不变。

本版只迁移报告 helper，不重写比较策略，也不改变下游 baseline decision 的输入格式。

## 来自哪条路线

这条收口路线从 v83 的 `report_utils.py` 开始。

v93-v95 是一段连续的 promoted 链路迁移：

```text
training scale promotion acceptance
 -> training scale promotion index
 -> promoted training scale comparison
```

这说明公共报告工具层已经覆盖从单次验收到多次验收索引，再到 promoted-only 比较的连续证据链。

## 关键文件

`src/minigpt/promoted_training_scale_comparison.py`

这是本版核心迁移文件。它读取 `training_scale_promotion_index.json`，解析 promoted inputs，调用 `build_training_scale_run_comparison`，并输出 promoted comparison 的 JSON/CSV/Markdown/HTML 证据。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用：

```text
as_dict
html_escape
list_of_dicts
markdown_cell
string_list
utc_now
write_json_payload
```

`src/minigpt/training_scale_run_comparison.py`

这是被 promoted comparison 复用的基础比较逻辑。本版不改它，只确认 promoted comparison 仍然能把筛选后的 promoted runs 交给它。

`tests/test_promoted_training_scale_comparison.py`

这是本版关键测试。它覆盖只比较 promoted runs、promoted inputs 不足时 blocked、非法 baseline blocked、HTML escaping 和输出文件可读性。

`tests/test_report_utils.py`

继续保护公共工具本身，避免多个报告模块共享后出现隐性格式退化。

`scripts/compare_promoted_training_scale_runs.py`

这是 CLI 入口。本版不改参数，只用它做 smoke，证明迁移后仍能生成 compared 和 blocked 两类报告。

`c/95/`

保存本版运行截图和解释，包括 tests、smoke、结构检查、Playwright HTML 和文档对齐检查。

## 迁移前的重复点

迁移前，`promoted_training_scale_comparison.py` 自己维护：

```text
utc_now
_list_of_dicts
_string_list
_dict
_md
_e
```

JSON 输出也由本模块手写：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

这些能力与 `report_utils.py` 的公共函数重复。v95 将它们统一到公共层，减少后续维护时同一类格式、转义或 defensive normalization 行为出现多份实现。

## 迁移后的引用关系

v95 让 `promoted_training_scale_comparison.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

保留旧别名是有意的。这样 Markdown/HTML 渲染和 comparison 行处理代码不用重排，迁移集中在 helper 来源，不把质量收口变成大重构。

## 核心数据结构

`comparison_inputs`

这是 promoted comparison 的输入摘要，字段包括：

```text
run_count
names
training_scale_run_paths
resolved_paths
missing_paths
baseline_name
compare_command_ready
```

其中 `resolved_paths` 是实际传给 `build_training_scale_run_comparison` 的路径，`missing_paths` 决定是否 blocked。

`promotions`

这是从 promotion index 继承并增强的行级证据。每行保留：

```text
name
promotion_status
promoted_for_comparison
training_scale_run_path
training_scale_run_exists
comparison_status
allowed
gate_status
batch_status
readiness_score
```

review/blocked promotion 可以出现在 `promotions` 里，但不会进入 `comparison.runs`。

`summary`

这是本报告的核心摘要：

```text
comparison_status
promotion_index_status
promotion_count
promoted_count
comparison_ready_count
compared_run_count
baseline_name
best_by_readiness
allowed_count
blocked_count
gate_warn_count
gate_fail_count
blocked_reason
```

它让后续 baseline decision 可以直接判断 promoted comparison 是否真的可用。

## 输出格式说明

`promoted_training_scale_comparison.json`

这是机器可读的最终证据。后续 promoted baseline decision 会读取它。v95 只把写出动作替换成 `write_json_payload`，不改 JSON 字段结构。

`promoted_training_scale_comparison.csv`

这是 promoted runs 的行级比较表，包含 status、allowed、gate、batch、readiness、baseline relation 和 explanation。

`promoted_training_scale_comparison.md`

这是人读版，展示 promoted inputs、comparison 表格、blockers 和 recommendations。`markdown_cell` 负责保护表格格式。

`promoted_training_scale_comparison.html`

这是浏览器版证据。`html_escape` 继续保护标题、run name、路径和 explanation，避免输入文本直接进入 HTML。

## 运行流程

主流程保持不变：

```text
load_training_scale_promotion_index
 -> _promotion_rows
 -> _comparison_inputs
 -> build_training_scale_run_comparison
 -> _merge_comparison_rows
 -> _summary
 -> write_promoted_training_scale_comparison_outputs
```

其中 `_comparison_inputs` 是安全边界：它只从 promoted rows 生成 names 和 paths。后续基础比较函数不会看到 review/blocked promotion。

## 测试如何覆盖链路

`test_compares_only_promoted_runs_from_index`

构造两个 promoted 和一个 review，断言 comparison runs 只有 promoted 的 alpha/beta，没有 review。这保护 promoted-only 策略。

`test_blocks_when_promoted_input_is_insufficient`

只给一个 promoted 和一个 review，断言 comparison blocked，并出现 at least two promoted runs 的 blocker。这保护不足输入的门禁。

`test_invalid_baseline_is_reported_as_blocked`

传入不存在的 baseline，断言报告 blocked，而不是抛出到 CLI 外层导致无证据失败。

`test_outputs_and_renderers_escape_html`

用 `<Promoted Compare>`、`<alpha>`、`<beta>` 这类输入，断言 HTML 转义仍然存在，证明迁移到公共 `html_escape` 后浏览器证据边界没有退化。

`tests.test_report_utils`

保护公共层本身。由于 v95 增加了一个新的消费者，公共层测试继续是这次迁移的底座。

## 本版证据

v95 证据归档在：

```text
c/95/图片
c/95/解释/说明.md
```

关键截图包括：

- focused tests、compile check 和 full regression。
- promoted comparison 成功比较两个 promoted inputs 的 smoke。
- promoted inputs 不足时 blocked 的 smoke。
- 结构检查，确认私有 helper 已移除、公共工具已引用、文档和归档已对齐。
- Playwright/Chrome 打开生成后的 HTML 报告。
- README、阶段索引和 `c/README.md` 的 v95 文档检查。

## 后续推进原则

后续可以继续迁移与 promoted comparison 相邻的 baseline decision、generation quality 或 release bundle 等模块，但仍然要坚持：

- 只迁移已有测试覆盖的模块。
- 只迁移 helper 完全同源的代码。
- 不为了代码量去碰训练核心、模型核心或推理服务核心。
- 每次迁移都要保留一个业务 smoke，证明策略没变。

## 一句话总结

v95 把 promoted training scale comparison 接入公共报告工具层，让 promoted-only 索引到 promoted-only 比较的证据链共享同一套报告基础设施，同时保留只比较 promoted runs 的边界。
