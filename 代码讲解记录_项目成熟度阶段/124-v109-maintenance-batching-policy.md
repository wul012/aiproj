# 第一百零九版代码讲解：Maintenance Batching Policy

## 本版目标

v109 的目标是回应“aiproj 的 utils migration 版本拆得太细”这个质量判断，并把它落成一个能运行、能测试、能截图归档的轻量检查。

它解决的问题是：v83-v108 已经证明 `report_utils` 抽取方向合理，但 v84-v107 里有很多一版只迁一个模块的记录。继续这样推进会让版本粒度过碎，README、截图、讲解和 tag 都被维护型小改动拉长。v108 已经开始把同类低风险迁移合并；v109 则把这个经验写成明确策略。

本版明确不做：

- 不继续迁移新的业务模块到 `report_utils`。
- 不改变训练、推理、评估、发布门禁或已有报告输出。
- 不把版本策略做成复杂流程引擎。
- 不强制所有改动合并；行为、服务/API、契约、UI、大模块或边界不清的变化仍应单独收口。
- 不把历史 v84-v107 tag 重写或合并，只为后续开发提供判断依据。

## 路线来源

本版来自两条前置能力：

```text
v83 report_utils consolidation
 -> v84-v107 single-module migration proofs
 -> v108 batched release governance migration
 -> v109 maintenance batching policy
```

v83 到 v107 的价值是证明公共报告工具边界足够稳；v108 的价值是证明相关低风险迁移可以批量完成；v109 的价值是把“以后应当批量”的判断变成可跑报告，而不是只停留在口头建议。

## 关键文件

- `src/minigpt/maintenance_policy.py`
  - 新增核心策略模块。
  - 负责归一化历史版本条目、识别连续单模块低风险工具迁移、评估下一版提案，并输出 JSON/CSV/Markdown/HTML。
- `scripts/check_maintenance_batching.py`
  - 新增命令行入口。
  - 可读取 `--history` 和 `--proposal` JSON，也提供默认 smoke 数据，方便快速验证策略。
- `tests/test_maintenance_policy.py`
  - 新增单元测试。
  - 覆盖长串单模块迁移告警、批量迁移不告警、低风险提案合并、高风险提案拆分，以及 HTML 转义和输出文件生成。
- `src/minigpt/__init__.py`
  - 导出 `build_maintenance_batching_report`、`build_maintenance_proposal_decision` 和 `write_maintenance_batching_outputs`。
- `README.md`
  - 更新当前版本、使用命令、截图归档和学习地图。
- `c/109/`
  - 保存本版运行截图和说明。
- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加第 124 篇讲解索引和 v109 阶段说明。

## 核心数据结构

`history` 是最近版本历史列表，每个元素可以包含：

```json
{
  "version": "v108",
  "title": "MiniGPT v108 batched release governance report utility migration",
  "category": "report-utils",
  "modules": ["release_gate.py", "release_gate_comparison.py", "request_history_summary.py"],
  "risk_flags": []
}
```

关键字段语义：

- `version`：版本号或 tag 名。
- `title`：版本主题，用于从文本推断类别。
- `category`：维护类别，例如 `report-utils`、`utils-migration`、`docs-only`、`test-helper`。
- `modules`：本版触及的主要模块列表。
- `risk_flags`：风险标记，例如 `behavior_change`、`schema_change`、`service_change`、`ui_change`、`large_module`、`unclear_boundary`。

归一化后的 release entry 会补充：

- `module_count`：模块数量。
- `low_risk_utils`：是否属于低风险维护类别。
- `single_module_utils`：是否是低风险、无高风险标记、且模块数不超过 1 的工具迁移。

`proposal_items` 是下一版候选维护项列表，例如：

```json
[
  {"name": "registry.py report helpers", "category": "report-utils"},
  {"name": "benchmark_scorecard.py report helpers", "category": "report-utils"},
  {"name": "project_audit.py report helpers", "category": "report-utils"}
]
```

提案决策输出包括：

- `decision`
  - `batch`：同类低风险项足够多，建议合并一版。
  - `batch_by_category`：低风险项足够多，但类别不同，应按类别分批。
  - `split`：包含高风险或边界不清项，应先拆成 focused version。
  - `single_ok`：只有一个低风险维护项，可以跟随下一版。
  - `not_applicable`：没有提供提案。
- `target_version_kind`
  - `batched`、`batched-groups`、`focused` 或 `none`。
- `groups`
  - 按类别分组后的候选项，供 Markdown/HTML 展示。

## 核心函数

`build_maintenance_batching_report(history, proposal_items=...)`

这是总入口。它先把历史版本归一化，再扫描连续 `single_module_utils` run，最后评估下一版提案，输出完整报告。

报告的 `summary` 中最重要的字段是：

- `status`
  - `warn` 表示连续单模块低风险迁移超过阈值。
  - `pass` 表示当前历史节奏没有触发碎片化告警。
- `decision`
  - `batch_next_related_work` 表示下一批同类维护要合并。
  - `continue_with_policy` 表示继续按策略推进即可。
- `longest_single_module_utils_run`
  - 最长连续单模块低风险迁移长度。
- `single_module_utils_limit`
  - 默认阈值为 3。

`build_maintenance_proposal_decision(items)`

这个函数只看下一版提案。它的规则很朴素：

```text
有高风险项 -> split
同类低风险项数量 >= 2 -> batch
多类别低风险项数量 >= 2 -> batch_by_category
单个低风险项 -> single_ok
没有提案 -> not_applicable
```

这种设计刻意保持保守。它不试图替开发者决定所有版本规划，只把“是否又在把低风险小迁移拆太碎”这个具体问题显性化。

`write_maintenance_batching_outputs(report, out_dir)`

这个函数写出：

- `maintenance_batching.json`
- `maintenance_batching.csv`
- `maintenance_batching.md`
- `maintenance_batching.html`

JSON 是后续脚本可消费的结构化证据；CSV 是总览字段；Markdown 适合代码审查；HTML 适合浏览器截图归档。

## 运行流程

默认 smoke 命令：

```powershell
python scripts/check_maintenance_batching.py --out-dir runs/maintenance-batching
```

流程是：

```text
默认近期历史 + 默认下一版提案
 -> build_maintenance_batching_report()
 -> write_maintenance_batching_outputs()
 -> 打印 status、decision、proposal_decision 和输出路径
```

如果提供自定义输入：

```powershell
python scripts/check_maintenance_batching.py --history history.json --proposal proposal.json --out-dir runs/maintenance-batching
```

`history.json` 和 `proposal.json` 都是 JSON list。这样后续版本可以在发版前把候选维护项放进去，先得到一个轻量判断。

## 为什么它是轻量优化

v109 没有引入新的训练能力，也没有把项目推向生产级版本管理系统。它的价值在于把质量建议变成工程约束：

- 低风险同类清理不要再一模块一 tag。
- 高风险变化不要为了“批量”而藏在维护版本里。
- README 和代码讲解不用再为每个 helper 迁移膨胀一篇。
- 以后推进时可以引用一份可运行报告，而不是反复口头解释。

这也回应了截图里的评分：版本粒度 D 的判断合理，但修复方式不应是大重构，而应是先建立节奏规则，再在后续版本里遵守。

## 测试覆盖

`tests/test_maintenance_policy.py` 覆盖了五类风险：

- 连续 4 个单模块 `report-utils` 迁移会得到 `warn`。
- v108 这种 3 模块批量迁移不会计入单模块 run。
- 3 个同类低风险提案会得到 `batch`。
- 含 `service_change` 的提案会得到 `split`，避免服务/API 变化混入维护批次。
- JSON/CSV/Markdown/HTML 输出都能生成，HTML 对 `<Maintenance>` 等文本做转义。

这些断言保护的是版本节奏语义，而不是表面输出格式。若以后有人放宽规则导致高风险项也被 batch，测试会失败。

## 证据闭环

v109 的证据放在 `c/109`：

- `01-unit-tests.png`：证明聚焦测试、compileall 和全量 unittest 通过。
- `02-maintenance-policy-smoke.png`：证明默认 CLI 能识别碎片化历史并建议批量提案。
- `03-maintenance-policy-structure-check.png`：证明模块、脚本、测试、README、讲解和 c 归档都对齐。
- `04-maintenance-policy-output-check.png`：证明 JSON/CSV/Markdown/HTML 关键字段存在。
- `05-playwright-maintenance-policy-html.png`：证明 HTML 报告能在真实 Chrome 中渲染。
- `06-docs-check.png`：证明 README、c/README 和项目成熟度阶段索引都引用 v109。

## 一句话总结

v109 把“utils migration 版本粒度过碎”的合理批评转化为可运行的维护批量策略，让后续 MiniGPT 版本推进从能继续拆功能，进一步走向能控制版本节奏。
