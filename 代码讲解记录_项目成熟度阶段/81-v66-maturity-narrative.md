# 第六十六版代码讲解：release-quality maturity narrative

## 本版目标、来源和边界

v66 的目标是把项目里已经存在的成熟度、发布趋势、请求历史、benchmark 和数据卡证据合成一份面向人阅读的 release-quality maturity narrative。v65 已经让 project maturity summary 能看到 registry 中的 release readiness trend，但读者仍要分别打开 maturity summary、registry、request history summary、benchmark scorecard 和 dataset card，才能判断这个项目是不是适合展示、答辩或交接。

所以本版新增一层叙事报告：它不再继续拆 `links/trends/dashboard`，而是把多份证据归并成一个 portfolio-facing 的入口，输出 JSON、Markdown 和 HTML。

本版明确不做四件事：

- 不重新训练模型，也不声称模型能力因此提升。
- 不重新计算 benchmark scorecard 或 dataset card，仍消费已有结构化证据。
- 不替代 release gate 的阻断逻辑，叙事报告只给 `ready`、`review`、`incomplete` 的汇总判断。
- 不把 MiniGPT 描述成生产 LLM，它仍是 from-scratch 学习型 AI 工程。

## 本版来自哪条路线

这一版属于项目成熟度阶段的证据收口路线：

```text
v48 project maturity summary
 -> v49-v54 benchmark scorecard / dataset card
 -> v60-v61 request history summary / audit gates
 -> v62-v65 release readiness dashboard / comparison / registry trend / maturity trend
 -> v66 release-quality maturity narrative
```

前面版本已经把单点证据做得比较完整，v66 的重点是把它们组织成一份可阅读、可归档、可截图、可交接的叙事报告。

## 关键新增和修改文件

- `src/minigpt/maturity_narrative.py`
  - 新增核心构建器、JSON/Markdown/HTML 写出函数和 HTML 渲染器。
  - 读取 maturity summary、registry、request history summary、benchmark scorecard 和 dataset card。
  - 输出 `summary`、`sections`、`evidence_matrix`、`recommendations` 和 `warnings`。
- `scripts/build_maturity_narrative.py`
  - 新增命令行入口。
  - 支持显式传入 `--maturity`、`--registry`、`--request-history-summary`、多个 `--benchmark-scorecard` 和多个 `--dataset-card`。
  - 默认写入 `runs/maturity-narrative/`。
- `tests/test_maturity_narrative.py`
  - 新增 ready、review、incomplete、输出写入、HTML 转义测试。
  - 保护叙事报告的状态判定、证据矩阵、输出结构和浏览器安全渲染。
- `README.md`
  - 更新当前版本、能力列表、tag、运行命令、截图索引、讲解索引和下一步路线。
- `b/66/解释/说明.md`
  - 说明 v66 的运行证据、截图含义和 tag 含义。

## 核心输入和字段语义

`build_maturity_narrative()` 的输入是项目根目录和一组可选路径：

```text
maturity_path
registry_path
request_history_summary_path
benchmark_scorecard_paths
dataset_card_paths
```

如果没有显式传入路径，默认发现规则是：

```text
runs/maturity-summary/maturity_summary.json
runs/registry/registry.json
runs/request-history-summary/request_history_summary.json
runs/**/benchmark-scorecard/benchmark_scorecard.json
datasets/**/dataset_card.json
```

核心输出字段：

```text
schema_version
title
generated_at
project_root
inputs
summary
sections
evidence_matrix
recommendations
warnings
```

`summary` 是机器可读的总览，重点字段包括：

```text
portfolio_status
current_version
maturity_status
average_maturity_level
registry_runs
release_readiness_trend_status
release_readiness_regressed_count
release_readiness_improved_count
request_history_status
request_history_records
request_history_timeout_rate
benchmark_scorecard_count
benchmark_status_counts
benchmark_avg_score
benchmark_weakest_case
dataset_card_count
dataset_status_counts
dataset_warning_count
```

`portfolio_status` 的含义：

- `ready`：成熟度、发布趋势、请求历史、benchmark scorecard 和 dataset card 证据都存在，且没有 review/fail 信号。
- `review`：证据存在，但存在发布退化、成熟度警告、请求历史警告、benchmark 警告或数据质量警告。
- `incomplete`：缺 maturity、release trend、request history summary、benchmark scorecard 或 dataset card 中的关键证据。

这里特别保留了 `0` 的语义，例如 `release_readiness_regressed_count=0` 必须表示“没有退化”，不能被 Python 的 truthy/falsy 规则误判为缺失。

## 核心运行流程

运行流程可以理解成五步：

```text
读取输入 JSON
 -> 提取 maturity/release/request/benchmark/dataset 摘要
 -> 计算 portfolio_status
 -> 生成 narrative sections 和 evidence matrix
 -> 写出 JSON/Markdown/HTML
```

`sections` 是人类叙事层，固定包含：

```text
Project Maturity
Release Quality Trend
Local Serving Stability
Benchmark Quality
Data Governance
Portfolio Boundary
```

每个 section 都包含：

```text
key
title
status
claim
evidence
boundary
next_step
```

这让报告不是简单列字段，而是同时说明“可以主张什么、证据在哪里、边界是什么、下一步怎么做”。

`evidence_matrix` 是证据索引层，每一行记录：

```text
area
status
path
exists
signal
note
```

其中 `exists` 用来证明引用路径在当前工程里真实存在，`signal` 用来说明该文件贡献的是成熟度、发布质量、服务稳定性、benchmark 还是数据治理信号。

## JSON、Markdown 和 HTML 的角色

`maturity_narrative.json` 是最终机器证据，适合后续自动读取。它保留完整字段、输入路径、状态和 warnings。

`maturity_narrative.md` 是评审和代码仓库中最容易阅读的文本证据。它把 summary、sections、evidence matrix 和 recommendations 写成稳定 Markdown。

`maturity_narrative.html` 是展示和截图证据。它使用转义后的文本渲染标题、状态卡、叙事面板和证据表格，并用 Playwright/Chrome 做浏览器验证。

这些产物都是最终证据，不是临时文件；临时 smoke fixture 和日志不进入版本库，任务收口时清理。

## 测试覆盖了什么

`tests/test_maturity_narrative.py` 覆盖五类判断：

- ready 路径：完整证据链会得到 `portfolio_status=ready`，并正确汇总 v66、release trend、request history、benchmark 平均分、最弱 case 和 dataset warning。
- review 路径：release readiness regression 会让叙事报告进入 `review`，并输出需要人工复核的建议。
- incomplete 路径：缺少 request history summary 时，即使 maturity summary 里有旧上下文，也不能把 portfolio 判为 ready。
- 输出写入：JSON、Markdown、HTML 都会生成，Markdown 和 HTML 包含 Evidence Matrix 与关键 section。
- HTML 转义：标题里的 `<Narrative>` 会被转成 `&lt;Narrative&gt;`，避免报告渲染时把输入文本当作标签。

这些断言保护的是证据链可信度：如果后续有人改状态规则、删字段、误吞 `0`、漏掉输出或破坏 HTML 转义，测试会直接失败。

## README、归档和截图的证明作用

README 负责说明 v66 已经进入当前版本能力、给出 CLI 用法、登记 tag、列出截图和讲解索引。

`b/66/图片/` 保存真实命令输出、CLI smoke、结构检查、Playwright/Chrome 截图和文档检查截图。

`b/66/解释/说明.md` 解释每张截图证明的环节，避免截图只变成图片堆积。

本篇代码讲解说明模块职责、字段语义、运行流程、边界和测试覆盖，用来和代码、README、运行证据共同组成 v66 闭环。

## 一句话总结

v66 把 MiniGPT 的成熟度、发布趋势、请求历史、benchmark 和数据卡证据收口成一份 release-quality maturity narrative，让项目从“证据很多”推进到“能把证据讲成一份可交接的成熟度故事”。
