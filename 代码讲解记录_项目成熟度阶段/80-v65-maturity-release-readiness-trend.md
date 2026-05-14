# 第六十五版代码讲解：maturity release readiness trend context

## 本版目标、来源和边界

v65 的目标是让 project maturity summary 读取 v64 registry 中的 release readiness trend context。v64 已经能把每个 run 的 `release-readiness-comparison/release_readiness_comparison.json` 汇总到 registry，输出 improved、regressed、panel-changed 计数和 delta leaderboard；但 maturity summary 仍只看版本、归档、capability matrix、registry 基本信息、pair delta 和 request history。

所以本版新增 maturity release readiness trend context：成熟度报告会读取 registry 顶层的 `release_readiness_comparison_counts` 和 `release_readiness_delta_summary`，输出独立的 Release Readiness Trend Context，并在存在 readiness regression 时把 overall status 从 `pass` 降为 `warn`。

本版不做三件事：

- 不重新计算 release readiness comparison，仍消费 v64 registry 的结构化结果。
- 不修改 release gate、project audit、release readiness dashboard 或 registry 的判定规则。
- 不把 maturity summary 变成阻断脚本，它仍是综合评审报告。

## 本版来自哪条路线

这一版属于项目成熟度阶段的发布质量证据汇总路线：

```text
v62 release readiness dashboard
 -> v63 release readiness comparison
 -> v64 registry release readiness tracking
 -> v65 maturity release readiness trend context
```

v62 负责单版就绪总览，v63 负责跨版本比较，v64 负责把比较结果纳入 registry，v65 则让 maturity summary 消费这个趋势上下文。

## 关键新增和修改文件

- `src/minigpt/maturity.py`
  - 新增 `release_readiness_context` 顶层字段。
  - `_summary()` 新增 release readiness trend 字段，并在 regressed 时把 overall status 调整为 `warn`。
  - 新增 `_release_readiness_context()`、`_release_readiness_trend_status()` 和 `_release_readiness_section()`。
  - Markdown 和 HTML 新增 Release Readiness Trend Context。
  - capability spec 和 phase timeline 更新到 v65。
- `scripts/build_maturity_summary.py`
  - CLI 输出新增 `release_readiness_trend_status`、`release_readiness_delta_count`、`release_readiness_regressed_count`，方便 smoke 和自动化检查。
- `tests/test_maturity.py`
  - fixture registry 新增 release readiness comparison counts 和 delta summary。
  - 新增 regression 用例，验证 release readiness regression 会把 maturity overall status 降为 `warn`。
- `README.md`
  - 更新到 v65，加入能力说明、tag、截图索引、讲解索引、学习路线和下一步方向。
- `b/65/解释/说明.md`
  - 说明本版运行截图如何证明 maturity context 的闭环。

## 输入字段和输出结构

输入来自 registry：

```text
release_readiness_comparison_counts
release_readiness_delta_summary
```

其中 `release_readiness_delta_summary` 关注：

```text
delta_count
run_count
regressed_count
improved_count
panel_changed_count
same_count
changed_panel_delta_count
max_abs_status_delta
```

maturity summary 新增顶层：

```text
release_readiness_context
```

它包含：

```text
available
trend_status
comparison_counts
delta_count
run_count
regressed_count
improved_count
panel_changed_count
same_count
changed_panel_delta_count
max_abs_status_delta
```

`trend_status` 的含义：

- `regressed`：至少一个 readiness delta 退化。
- `improved`：没有退化，至少一个 readiness delta 改善。
- `panel-changed`：状态未改善或退化，但 panel 有变化。
- `stable`：有 delta，但状态和 panel 均稳定。
- `None`：registry 中没有 release readiness trend 数据。

summary 中同步新增：

```text
release_readiness_trend_status
release_readiness_delta_count
release_readiness_regressed_count
release_readiness_improved_count
```

## 运行流程

成熟度构建流程变为：

```text
build_maturity_summary()
 -> 读取 README tag、a/b archive、代码讲解记录
 -> 读取 registry.json
 -> _registry_context()
 -> _release_readiness_context()
 -> _request_history_context()
 -> _summary()
 -> Markdown/HTML 渲染 Release Readiness Trend Context
```

如果 `release_readiness_context.trend_status == "regressed"`，`_summary()` 会把整体状态降到 `warn`。这不是发布阻断，而是成熟度评审提醒：项目证据链发现了发布质量退化，不能继续把整体成熟度描述成完全通过。

## 输出产物的作用

`maturity_summary.json` 是最完整的结构化证据，后续脚本可以读取 `release_readiness_context`。

`maturity_summary.md` 是人工审阅版，新增 Release Readiness Trend Context 表格，适合放进版本归档或答辩材料。

`maturity_summary.html` 是浏览器报告，新增 Release trend 和 Readiness deltas 顶部统计卡，以及独立的 Release Readiness Trend Context 区块。

`maturity_summary.csv` 仍保留 capability matrix，不强行塞入 release trend，因为 release trend 是项目级上下文，不是单个 capability row。

## 测试覆盖了什么

`tests/test_maturity.py` 覆盖：

- improved trend 能被读取到 summary 和 `release_readiness_context`。
- maturity summary 输出 JSON/CSV/Markdown/HTML 时，Markdown 和 HTML 都包含 Release Readiness Trend Context。
- regressed trend 会让 `release_readiness_trend_status=regressed`，并把 `overall_status` 降为 `warn`。
- regression 建议会进入 recommendations，提醒先检查 release readiness 退化。

这些测试保护的是：字段能读取、报告能渲染、风险能影响成熟度评审。

## README、截图和归档的证明作用

README 证明 v65 已进入项目能力列表、tag 列表、截图索引、代码讲解索引和学习路线图。

`b/65/图片` 保存真实运行证据：单测、improved smoke、regressed smoke、结构检查、Playwright 浏览器渲染和文档检查。

`b/65/解释/说明.md` 说明每张截图的证明范围。

本篇讲解负责解释为什么 v65 只消费 registry 趋势，而不重复做 release readiness comparison。

## 和后续版本的关系

v65 已经把 release quality trend 接入 maturity summary。下一步可以把 request-history stability、release readiness trend、benchmark scorecards 和 dataset cards 合成一份更面向作品展示的 maturity narrative。

## 一句话总结

v65 把 MiniGPT 的发布质量趋势从 registry 视图推进到 project maturity summary，让成熟度评审能明确看到 release readiness 改善、稳定或退化。
