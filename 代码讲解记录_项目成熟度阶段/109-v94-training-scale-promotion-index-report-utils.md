# v94 training scale promotion index report utility migration

## 本版目标

v94 的目标是继续做轻量、定向的质量收口：把 `training_scale_promotion_index.py` 接入公共 `report_utils.py`。
v93 已经把单个 training scale promotion acceptance 的报告基础设施迁移到公共层；v94 顺着同一条链路往后推进，把“多个 promotion 报告如何形成 promoted-only 对比入口”的 index 层也纳入同一套 JSON 写出、Markdown/HTML 转义和 list/dict 归一化规则。

本版解决的问题是：`training_scale_promotion_index.py` 原本仍然维护私有的 `utc_now`、`_dict`、`_list_of_dicts`、`_string_list`、`_md`、`_e` 和 JSON writer。它们和 `report_utils.py` 已有能力重复，会让 promotion acceptance 与 promotion index 在基础报告行为上继续分叉。

v94 的结果是：training scale promotion index 成为公共报告基础层的新消费者。

## 本版明确不做什么

v94 不改变 promotion index 的业务规则。

保持不变的边界包括：

- 只有 `promotion_status == promoted` 且 `training_scale_run.json` 存在的报告才进入 comparison inputs。
- review 和 blocked promotion 继续保留在 index 表格里，但不会进入 compare command。
- 少于两个 promoted comparison inputs 时，compare command 仍然不 ready。
- baseline 仍然只能从 promoted comparison inputs 中选择。
- CSV 字段、Markdown 表格、HTML 表格和 CLI 参数不改名。
- `scripts/index_training_scale_promotions.py` 的输入输出语义不变。

本版只迁移报告 helper，不重写 promoted-only 过滤逻辑，也不合并 promoted comparison、baseline decision 或 next-cycle seed。

## 来自哪条路线

v83 新增 `report_utils.py`。
v84-v93 已经把多层训练规模链路逐步迁移到公共报告基础层：

```text
handoff -> seed -> decision -> run decision -> run comparison -> gated run -> gate -> plan -> workflow -> promotion
```

v94 迁移的是 promotion 之后的索引层：

```text
promotion acceptance -> promotion index -> promoted comparison
```

这说明公共报告基础层不只服务单个运行报告，也开始服务多 promotion 的筛选、索引和后续 compare command 生成入口。

## 关键文件

`src/minigpt/training_scale_promotion_index.py`

这是本版核心迁移文件。它继续负责读取多个 `training_scale_promotion.json`，生成 `promotions` 行、`comparison_inputs`、`summary` 和 `recommendations`，并输出 JSON/CSV/Markdown/HTML。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版复用已有函数：

```text
as_dict
html_escape
list_of_dicts
markdown_cell
string_list
utc_now
write_json_payload
```

`tests/test_training_scale_promotion_index.py`

这是 index 业务测试。它保护 promoted-only compare inputs、review/blocked exclusion、baseline 边界、HTML escaping 和输出文件可读性。

`tests/test_report_utils.py`

这是公共层测试。它继续保护 JSON 写出、CSV 写出、Markdown cell、HTML escaping 和 list/dict defensive normalization。

`scripts/index_training_scale_promotions.py`

这是 CLI 入口。本版不改 CLI，只用它做 smoke，证明迁移后的 index 仍能从 promotion reports 生成 compare command 和 HTML evidence。

`c/94/`

这是本版运行截图和解释归档，保存 tests、smoke、结构检查、Playwright HTML 和文档对齐证据。

## 迁移前的重复点

迁移前，`training_scale_promotion_index.py` 自己维护：

```text
utc_now
_list_of_dicts
_string_list
_dict
_md
_e
```

同时 JSON 输出也在模块内手写：

```text
Path(...).write_text(json.dumps(..., ensure_ascii=False, indent=2))
```

这些能力和 `report_utils.py` 中的工具函数语义一致。继续保留私有副本，会让 index 层与 promotion、workflow、plan、gate、run、comparison、decision 等模块在基础输出规则上产生不必要的重复。

## 迁移后的引用关系

v94 让 `training_scale_promotion_index.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

保留 `_dict`、`_md`、`_e` 等旧别名，是为了让渲染代码最小变化。这样迁移范围集中在 helper 来源，而不是同时重排 Markdown/HTML 渲染结构。

## 核心数据结构

`promotions`

这是 index 的主表。每一行代表一个输入 promotion report，关键字段包括：

```text
name
promotion_status
promoted_for_comparison
training_scale_run_path
training_scale_run_exists
variant_count
ready_variant_count
required_artifact_count
available_required_artifact_count
primary_variant
primary_checkpoint
missing_required
blockers
review_items
```

`promoted_for_comparison` 是最关键的布尔字段。它不是只看 promotion status，而是同时要求 `training_scale_run_path` 指向的文件真实存在。

`comparison_inputs`

这是给下一步 `compare_training_scale_runs.py` 消费的机器可读入口，关键字段包括：

```text
run_count
names
training_scale_run_paths
baseline_name
compare_command_ready
compare_command
```

当 promoted comparison inputs 少于两个时，`compare_command_ready` 仍然是 false。这样 review/blocked promotion 不会因为出现在 index 中就误进入后续模型能力比较。

`summary`

这是给 README、HTML、Markdown 和 CLI 输出看的摘要：

```text
promotion_count
promoted_count
review_count
blocked_count
missing_count
comparison_ready_count
compare_command_ready
non_comparable_count
```

## 输出格式说明

`training_scale_promotion_index.json`

这是最终机器可读证据，用于后续 promoted comparison 或人工审查。v94 只把写出动作换成 `write_json_payload`，字段结构保持不变。

`training_scale_promotion_index.csv`

这是 promotion 行级摘要，适合横向查看哪些 run 可比较、哪些因为 review/blocked 没进入 compare inputs。

`training_scale_promotion_index.md`

这是轻量阅读版，包含 promotions 表格、compare command 和 recommendations。`markdown_cell` 负责处理换行和表格分隔符，避免路径或名称破坏表格。

`training_scale_promotion_index.html`

这是浏览器证据。`html_escape` 继续保护标题、名称、路径和列表项，避免输入中出现 `<Index>` 或 `<alpha>` 时直接进入 HTML。

## 运行流程

本版迁移后的主流程仍然是：

```text
load_training_scale_promotion
 -> _promotion_row
 -> _comparison_inputs
 -> _summary
 -> _recommendations
 -> write_training_scale_promotion_index_outputs
```

其中 `_comparison_inputs` 是边界最重要的一步。它只读取 `promoted_for_comparison` 为 true 的行，生成 names、training scale run paths、baseline 和 compare command。

## 测试如何覆盖链路

`test_indexes_promoted_reports_and_builds_compare_inputs`

构造两个 promoted promotion reports，断言 promoted count、comparison ready count、baseline name、names 和 compare command 都正确。这保护了“两个 promoted 才能形成比较命令”的主路径。

`test_excludes_review_and_blocked_reports_from_compare_inputs`

构造 promoted、review、blocked 三类报告，断言 comparison inputs 只包含 promoted。这个测试保护 v94 最重要的业务边界：index 可以展示 review/blocked，但不能把它们送进模型比较。

`test_baseline_must_be_promoted_for_comparison`

尝试把 review report 设为 baseline，期望抛出 `ValueError`。这个测试保护 baseline 选择边界。

`test_outputs_and_renderers_escape_html`

用带尖括号的标题和名称生成 HTML，断言浏览器文本被转义。这个测试说明迁移到 `html_escape` 后，HTML 安全边界仍然存在。

`tests.test_report_utils`

验证公共工具本身，防止后续改动破坏被多个报告模块共享的 JSON、CSV、Markdown、HTML 和 list/dict 行为。

## 本版证据

v94 证据归档在：

```text
c/94/图片
c/94/解释/说明.md
```

关键截图包括：

- focused tests、compile check 和 full regression。
- 两个 promoted reports 生成 compare command 的 smoke。
- review/blocked reports 不进入 compare inputs 的 smoke。
- 结构检查，确认源码迁移、讲解文件、README 和 `c/94` 归档都对齐。
- Playwright/Chrome 打开生成后的 HTML 报告。
- 文档检查，确认 README、阶段索引和 c README 都同步到 v94。

这些证据共同证明：v94 是一次报告基础设施收口，而不是 promotion index 策略重写。

## 后续推进原则

后续如果继续迁移相邻模块，优先选择：

- 已经有单测覆盖的 report 模块。
- 私有 helper 与 `report_utils.py` 完全同源的模块。
- 能通过 smoke 证明业务边界没有变化的模块。

不建议为了追求代码量去迁移模型核心、训练核心或高风险推理服务路径。这个阶段的收益来自可维护性和证据链一致性，而不是功能堆叠。

## 一句话总结

v94 把 training scale promotion index 接入公共报告工具层，让 promoted-only 索引层和 promotion acceptance 层共享同一套报告基础设施，同时保留只让 promoted run 进入后续比较的边界。
