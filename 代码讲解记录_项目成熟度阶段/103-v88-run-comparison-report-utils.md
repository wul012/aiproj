# v88 training scale run comparison report utility migration

## 本版目标

v88 的目标是继续 `report_utils` 收口路线，把 v73 引入的 `training_scale_run_comparison.py` 迁移到公共报告工具上。

这个模块的职责是读取多份 `training_scale_run.json`，比较它们在 gate、batch、readiness 和 baseline delta 上的差异，并输出：

- comparison JSON
- per-run CSV
- Markdown 报告
- HTML 浏览器报告
- baseline deltas
- best-by-readiness 摘要
- recommendations

v88 要解决的问题是：v87 已经让 run decision 复用公共报告工具，但它的直接上游 comparison 仍然保留了一组私有 helper。这样会让 comparison evidence 和 decision evidence 的输出基础层不一致。

本版把 comparison 层也迁入公共工具，让 v73 comparison 和 v74 decision 这两层相邻证据共用同一套基础设施。

## 本版明确不做什么

v88 不改变 comparison 的评分或排序语义。

下面这些行为保持不变：

- `readiness_score` 的计算方式
- baseline 选择逻辑
- readiness delta 的正负判断
- gate relation 的 improved/regressed/unchanged 判断
- batch relation 的 improved/regressed/changed/unchanged 判断
- best-by-readiness 的选择方式
- recommendations 的生成条件

本版只迁移报告基础设施，不重写比较规则。

## 来自哪条路线

v83 新增 `report_utils.py`，先迁移 promoted seed handoff。

v84 迁移 controlled training scale handoff。

v85 迁移 promoted seed generation。

v86 迁移 promoted baseline decision。

v87 迁移 training scale run decision。

v88 迁移 training scale run comparison。

这一步让原始 training scale 链路中的 comparison evidence 和 decision evidence 都接入公共报告基础层。也就是说，从“比较多个 gated run”到“选择下一次执行候选”的相邻两层，现在不再复制同一批 Markdown/HTML/list/dict/JSON helper。

## 关键文件

`src/minigpt/training_scale_run_comparison.py`

这是本版核心迁移文件。它继续负责读取 runs、生成 run summary、选择 baseline、计算 deltas、生成 summary、渲染 JSON/CSV/Markdown/HTML。

`src/minigpt/report_utils.py`

这是公共报告工具层。本版继续复用它，不扩张新的大型抽象。

`tests/test_training_scale_run_comparison.py`

这是 comparison 业务测试，覆盖 allowed/blocked run 对比、目录输入、baseline 选择、best-by-readiness、HTML 转义、重复名字和空输入异常。

`tests/test_report_utils.py`

这是公共层测试，保护 JSON/CSV 写出、Markdown/HTML 转义、命令展示、artifact row 和 list/dict 归一化。

`scripts/compare_training_scale_runs.py`

这是 CLI 入口。本版不改 CLI 参数，因为迁移只发生在底层 helper，不影响用户如何运行 comparison。

`代码讲解记录_项目成熟度阶段/103-v88-run-comparison-report-utils.md`

这是本文件，记录 v88 的目标、边界、字段语义、测试覆盖和证据链。

`c/88/`

这是 v88 的运行截图和解释归档目录。

## 迁移前的重复点

迁移前，`training_scale_run_comparison.py` 自己维护了：

```text
utc_now
_list_of_dicts
_string_list
_dict
_md
_e
_csv_value
```

同时 JSON 写出也是本模块自己手写：

```text
Path(...).write_text(json.dumps(...))
```

这些能力和 `report_utils.py` 已有原语高度重叠。

## 迁移后的引入关系

v88 让 `training_scale_run_comparison.py` 从 `minigpt.report_utils` 引入：

```text
as_dict as _dict
csv_cell as _csv_value
html_escape as _e
list_of_dicts as _list_of_dicts
markdown_cell as _md
string_list as _string_list
utc_now
write_json_payload
```

这里保留 `_dict`、`_md`、`_e` 等别名，是为了让原有渲染模板尽量不动。这样本版 diff 聚焦在 helper 来源和 JSON 写出，不把表格结构、HTML 样式和字段顺序一起重排。

## 为什么 CSV 仍保留局部循环

`report_utils.write_csv_row` 适合“一份报告一行摘要”的场景。

`training_scale_run_comparison.csv` 是 per-run 多行表格，每个 run 都要合并 baseline delta 字段，因此本版没有强行把它改成单行 writer。

迁移后 CSV 仍由本模块控制字段和循环：

```text
for run in runs:
    row = dict(run)
    row.update(delta)
    writer.writerow(...)
```

但 cell 转换复用公共层：

```text
csv_cell as _csv_value
```

这样既保留多行 CSV 的业务结构，又统一 dict/list 在 CSV 单元格里的序列化方式。

## JSON 输出

`write_training_scale_run_comparison_json` 改为调用：

```text
write_json_payload(report, path)
```

JSON 报告是最终 comparison evidence，不是临时调试文件。它会被 run decision、workflow、截图说明和人工审阅消费。

公共 JSON writer 统一保证：

- 创建父目录
- UTF-8
- `ensure_ascii=False`
- `indent=2`

## Markdown 和 HTML 渲染

Markdown 报告仍然包含：

- generated
- run count
- baseline
- allowed/blocked count
- batch started count
- gate warn/fail count
- runs 表格
- recommendations

HTML 报告仍然包含：

- header
- stats cards
- runs table
- recommendations
- footer

变化在于 Markdown cell 和 HTML escape 改为公共工具：

```text
markdown_cell
html_escape
```

这继续保护特殊字符场景。例如测试中 run name 可以是 `<allowed>`，HTML 必须渲染为 `&lt;allowed&gt;`，不能被浏览器当成标签。

## 核心数据结构

### run summary

每个 run summary 包含：

- `index`
- `name`
- `source_path`
- `status`
- `allowed`
- `execute`
- `gate_status`
- `gate_profile`
- `gate_pass_count`
- `gate_warn_count`
- `gate_fail_count`
- `dataset_name`
- `version_prefix`
- `scale_tier`
- `char_count`
- `warning_count`
- `variant_count`
- `baseline`
- `batch_status`
- `comparison_status`
- `completed_variant_count`
- `blocked_reason`
- `gate_outputs`
- `batch_outputs`
- `readiness_score`

这个结构不是重新训练，也不是重新跑 gate；它是对已有 `training_scale_run.json` 的摘要。

### baseline delta

每个 delta 包含：

- `name`
- `baseline_name`
- `is_baseline`
- `allowed_delta`
- `readiness_delta`
- `gate_relation`
- `batch_relation`
- `explanation`

它解释每个 run 相对 baseline 是更好、更差，还是没有变化。

### summary

summary 汇总：

- baseline name
- run count
- allowed count
- blocked count
- batch started/skipped count
- gate pass/warn/fail count
- readiness improvement/regression count

这个 summary 是后续 decision 层判断上下文的重要入口。

## 运行流程

`build_training_scale_run_comparison` 的流程保持不变：

1. 校验至少有一个 run path。
2. 校验 names 数量和 run paths 对齐。
3. 读取每份 `training_scale_run.json`。
4. 解析展示用 run name。
5. 为每个 run 生成 summary。
6. 选择 baseline。
7. 计算每个 run 对 baseline 的 delta。
8. 汇总 comparison summary。
9. 选择 best-by-readiness。
10. 生成 recommendations。

v88 没有调整这些步骤，只替换输出层的公共 helper。

## 测试覆盖

`tests/test_training_scale_run_comparison.py` 保护五类行为。

第一类是 allowed/blocked 对比：

- allowed run 和 blocked run 都进入 comparison
- allowed count 是 1
- blocked count 是 1
- batch started count 是 1
- gate fail count 是 1
- blocked run 相对 baseline readiness delta 为负
- blocked run batch relation 是 regressed

第二类是输出和目录输入：

- run directory 可以作为输入
- JSON/CSV/HTML 都能写出
- baseline 名称正确写入 JSON
- `load_training_scale_run` 可以从目录加载 `training_scale_run.json`

第三类是 baseline 与 best-by-readiness：

- baseline 可以显式指定为 index
- 即使 baseline 是 blocked，best-by-readiness 仍可选 allowed
- allowed 相对 blocked 的 readiness delta 为正

第四类是渲染安全：

- Markdown 包含 Runs 和 Recommendations
- HTML 对 `<allowed>` 正确转义
- 原始 `<allowed>` 不直接出现在 HTML 中

第五类是输入校验：

- 空输入抛出 `ValueError`
- 重复 names 抛出 `ValueError`

这些断言保护 comparison 语义，而不仅仅是文件是否存在。

`tests/test_report_utils.py` 继续保护公共层本身。v88 focused tests 同时跑 comparison tests 和 report utils tests，证明消费者和公共工具都正常。

## 运行截图和证据

v88 的运行证据归档到：

```text
c/88/图片
c/88/解释/说明.md
```

截图会覆盖：

- focused tests、compileall、full regression
- comparison smoke
- explicit baseline smoke
- source/docs/archive structure check
- Playwright/Chrome HTML 渲染
- README 与讲解索引检查

这些截图是本版证据链的一部分，会随提交保留。

## 后续开发原则

v88 之后，训练规模链路还剩一些早期模块拥有私有 helper，例如 plan、gate、run、workflow、promotion、promotion index 等。

后续继续迁移时，仍应保持小步：

- 一版迁移一个边界清楚的消费者。
- 不混入业务语义调整。
- 保留原字段顺序和输出结构。
- 用 focused tests、smoke、Playwright 和文档索引证明闭环。

## 一句话总结

v88 把 training scale run comparison 接入 `report_utils`，让 gated-run comparison evidence 和 execute-candidate decision evidence 开始共用同一套报告基础设施。
