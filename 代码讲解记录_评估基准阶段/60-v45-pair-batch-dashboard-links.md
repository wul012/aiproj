# 第四十五版代码讲解：pair batch dashboard/playground links

## 本版目标、来源和边界

v43 已经能用固定 prompt suite 批量比较两个 checkpoint，并输出 `pair_generation_batch.json/csv/md/html`。v44 又能读取多个 batch 报告，输出 `pair_batch_trend.json/csv/md/html`。v45 解决的是下一层使用问题：报告已经存在时，dashboard 和 playground 能不能自动发现、展示摘要，并给出浏览器可点开的链接。

本版只做报告入口和解释链路，不改变 checkpoint 推理逻辑，不改变 pair batch/trend 的比较算法，也不引入新的训练流程。

## 所在链路

```text
side-by-side generation
 -> persisted pair artifacts
 -> fixed prompt pair batch comparison
 -> pair batch trend comparison
 -> dashboard/playground report links
```

这一层的价值是把“文件已经写出来了”变成“评审者可以从一个页面找到并打开它”。

## 关键文件

- `src/minigpt/dashboard.py`：发现 pair batch/trend 文件，读取摘要字段，渲染 dashboard 面板。
- `src/minigpt/playground.py`：把 pair batch/trend 文件加入 Run Files 链接，并生成常用命令。
- `tests/test_dashboard.py`：验证 dashboard artifact、summary 和 HTML 链接。
- `tests/test_playground.py`：验证 playground 链接和命令助手。
- `b/45/解释/说明.md`：保存运行截图解释与 tag 含义。

## dashboard artifact 发现

`collect_artifacts` 增加了两组文件：

```text
pair_batch/pair_generation_batch.json
pair_batch/pair_generation_batch.csv
pair_batch/pair_generation_batch.md
pair_batch/pair_generation_batch.html
pair_batch_trend/pair_batch_trend.json
pair_batch_trend/pair_batch_trend.csv
pair_batch_trend/pair_batch_trend.md
pair_batch_trend/pair_batch_trend.html
```

这样 dashboard 不需要调用脚本重新生成报告，只要 run 目录里已经有这些产物，就能把它们纳入 artifact inventory。

## dashboard 摘要和面板

`build_dashboard_payload` 会读取 `pair_batch/pair_generation_batch.json` 和 `pair_batch_trend/pair_batch_trend.json`。摘要字段包括：

- `pair_batch_cases`：batch 报告覆盖了多少个 prompt case。
- `pair_batch_generated_differences`：左右 checkpoint 生成结果不同的 case 数。
- `pair_trend_reports`：trend 报告比较了多少份 batch 报告。
- `pair_trend_changed_cases`：跨报告 equality 状态发生变化的 case 数。

`_pair_batch_section` 渲染 `Pair Batch Reports` 区块。它分成 Batch 与 Trend 两列：左边展示 suite、pair、case 数和平均生成长度 delta；右边展示报告数、case 数、变化 case 数和最大 delta。每列下面都有 HTML、JSON、CSV、Markdown 链接。

## playground Run Files 和命令助手

`playground.py` 的 `_collect_links` 同样加入 pair batch/trend 文件。这样静态 `playground.html` 的 Run Files 区域可以直接打开报告，不必手动去输出目录里找文件。

`build_playground_commands` 增加两个命令键：

- `pair_batch`：示例调用 `scripts/pair_batch.py`，用当前 run 的 checkpoint 和 `wide/checkpoint.pt` 做左右比较。
- `pair_trend`：示例调用 `scripts/compare_pair_batches.py`，把当前 batch 和候选 batch 做趋势比较。

这些命令不是强制配置，而是让学习项目里常见的下一步操作可以从页面复制执行。

## 测试和证据

本版测试覆盖四类风险：

- artifact 没被发现：`test_collect_artifacts_marks_existing_files` 会检查 `pair_batch_html`，结构检查会继续确认 `pair_trend_html`。
- summary 没被读到：`test_build_payload_reads_summary_sources` 会检查 batch/trend 摘要字段。
- dashboard 没链接：`test_render_dashboard_links_pair_batch_reports` 会检查 `Pair Batch Reports`、batch HTML 和 trend HTML 链接。
- playground 没入口：`test_playground_links_pair_batch_reports` 和命令测试会检查 Run Files 链接与 `pair_batch.py`、`compare_pair_batches.py` 命令。

运行证据保存在 `b/45/图片`，包括全量测试、smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v45 把 pair batch/trend 从“可生成的报告文件”推进为“dashboard/playground 可发现、可摘要、可点击复查的评估入口”。
