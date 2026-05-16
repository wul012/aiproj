# 第一百四十一版代码讲解：maturity narrative scorecard decision

## 本版目标

v141 的目标是把 v140 新增的 `benchmark_scorecard_decision.json` 接入 `maturity_narrative`。上一版已经能把 scorecard comparison 转成 promote/review/blocked 决策，但这个决策仍是单独证据；本版让成熟度叙事能看到它，并把 selected run、status counts、review/blocker 数量和 generation-quality flag delta 写入 portfolio-level JSON/Markdown/HTML。

本版不新增模型训练能力，不改变 benchmark scorecard decision 的判定规则，也不扩展 release gate。它只做一件事：把已有 scorecard promotion evidence 融入成熟度叙事，让评审时少跳一个报告。

## 前置路线

这版承接的是 v137-v140 的评估证据增强路线：

- v137 给 generation quality 增加 flag taxonomy。
- v138 把 flag taxonomy 接入 benchmark scorecard。
- v139 把 flag taxonomy delta 接入跨 scorecard comparison。
- v140 基于 comparison 生成 scorecard promotion decision。
- v141 把 decision 接入 maturity narrative。

所以 v141 的价值不是“又多一个报告”，而是把分散证据收回 maturity narrative，让成熟度报告真正解释 promotion decision。

## 关键文件

`src/minigpt/maturity_narrative.py` 是核心修改点。`build_maturity_narrative` 新增 `benchmark_scorecard_decision_paths` 参数，如果调用方显式传入路径，就读取这些 decision；如果没有传入，就在项目根目录下搜索 `runs/**/benchmark-scorecard-decision/benchmark_scorecard_decision.json`。

`src/minigpt/maturity_narrative_artifacts.py` 负责输出层。它不重新计算 decision，只把 narrative summary 中的 decision count、selected run 和 selected flag delta 展示到 Markdown 与 HTML 统计卡中。

`scripts/build_maturity_narrative.py` 是 CLI 入口。它新增 `--benchmark-scorecard-decision` 参数，并在命令输出中打印 `benchmark_scorecard_decisions` 和 `benchmark_decision_selected_run`，方便 smoke 直接证明链路接上。

`tests/test_maturity_narrative.py` 新增 fixture 中的 scorecard decision。测试不依赖真实训练，而是构造最小 JSON 来验证 mature narrative 是否正确读取、汇总、渲染和写入 evidence matrix。

## 输入与发现规则

新增输入字段是：

```python
benchmark_scorecard_decision_paths: list[str | Path] | None = None
```

它有两种使用方式：

1. CLI 或代码显式传入一个或多个 `benchmark_scorecard_decision.json`。
2. 未传入时，由 `_discover_scorecard_decisions(root)` 在 `runs/**/benchmark-scorecard-decision/benchmark_scorecard_decision.json` 下自动发现。

自动发现保持只读，不修改 run 目录，也不假设每个 run 都必须有 decision。这样 maturity narrative 可以兼容旧项目，也能消费新项目的 promotion decision。

## summary 字段

本版新增的 summary 语义集中在这几个字段：

- `benchmark_decision_count`：读取到多少份 scorecard decision。
- `benchmark_decision_status_counts`：按 promote/review/blocked 等状态计数。
- `benchmark_decision_selected_run`：第一份包含 selected candidate 的 decision 中选中的 run。
- `benchmark_decision_review_item_count`：所有 candidate 的 review item 总数。
- `benchmark_decision_blocker_count`：所有 candidate 的 blocker 总数。
- `benchmark_decision_selected_flag_delta`：selected run 的 generation-quality total flags delta。

这些字段不替代原始 decision JSON。它们只是 maturity narrative 的摘要层，用来回答“有没有 promotion decision、选了谁、是否还有风险、生成质量问题类型是否变多”。

## 新 section

`_sections` 新增 `Benchmark Promotion Decision` 区块。它的状态来自 decision status counts：

- 有 `blocked` 时视为 `fail`。
- 有 `review` 或 `warn` 时视为 `warn`。
- 有 `promote` 或 `pass` 时视为 `pass`。
- 没有 decision 时视为 `missing`。

claim 由 `_benchmark_decision_claim` 生成。比如存在 selected run 时，它会说明 selected run 和 flag delta；没有 decision 时，它会明确 maturity narrative 尚未包含 scorecard promotion decision。

这个 section 的边界很重要：它说明 maturity narrative 只是消费 decision，不重新裁决 benchmark，也不把 governance evidence 误写成模型能力证明。

## evidence matrix

`_evidence_matrix` 新增 `scorecard promotion decision` 行。该行记录每份 decision 的路径、状态、关联 section 和只读说明。

它的作用是把 decision 文件放入 maturity narrative 的证据矩阵，方便后续 HTML、Markdown 或人工审查追踪到原始 JSON。它不是最终准入结论；最终结论仍看 decision 自己的 blockers、review items、status 和人工判断。

## 输出层

Markdown 的 `Portfolio Summary` 增加：

- `Benchmark decisions`
- `Scorecard decision run`
- `Scorecard decision flag delta`

HTML 的统计卡增加：

- `Decisions`
- `Decision run`

输出层只读 summary，不读取原始 decision 文件。这样 `maturity_narrative_artifacts.py` 仍保持 artifact writer 职责，不把数据发现和业务汇总逻辑混进去。

## CLI 流程

`scripts/build_maturity_narrative.py` 的新参数是：

```text
--benchmark-scorecard-decision <path>
```

可以重复传入。若不传入，核心函数会按项目根自动发现。CLI smoke 里能看到：

```text
benchmark_scorecard_decisions=1
benchmark_decision_selected_run=demo-run
```

这两行是 v141 的关键运行证据：成熟度叙事确实看到了 scorecard promotion decision，而不是只生成了旧版 narrative。

## 测试覆盖

`tests/test_maturity_narrative.py` 的 fixture 新增了一个最小 scorecard decision：

- `status=promote`
- selected candidate 为 `demo-run`
- selected generation-quality flag delta 为 `-2`
- 包含 baseline 和 candidate evaluation

测试覆盖四层保护：

- summary 中 `benchmark_decision_count`、`benchmark_decision_selected_run`、`benchmark_decision_selected_flag_delta` 正确。
- section 列表中存在 `Benchmark Promotion Decision`。
- evidence matrix 中存在 `scorecard promotion decision`。
- Markdown/HTML 输出能展示 scorecard decision 相关信息。

这能防止后续改 maturity narrative 时把 promotion decision 入口、摘要或展示层意外删掉。

## 截图与归档

v141 的运行截图和解释放在 `c/141`：

- `01-unit-tests.png`：单测、编译和全量 unittest。
- `02-maintenance-smoke.png`：维护批处理和 module pressure。
- `03-maturity-narrative-scorecard-decision-smoke.png`：CLI smoke 证明 decision 被消费。
- `04-playwright-maturity-narrative-scorecard-decision-html.png`：Chrome/Playwright 打开 HTML。
- `05-docs-check.png`：README、归档索引、代码讲解索引和 source encoding 检查。

这些截图用于证明本版闭环，不用于证明模型能力变强。

## 一句话总结

v141 把 benchmark promotion decision 从单点报告推进到成熟度叙事层，让 MiniGPT 的评估证据链从 flag taxonomy 到 scorecard、comparison、decision、maturity narrative 形成连续闭环。
