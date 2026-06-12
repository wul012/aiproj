# v1133 model capability cadence 代码讲解

## 本版目标和边界

v1133 是工程后期保养五版中的第四版，目标是建立模型能力主线回归节奏。前面三版分别做了 publication 命名止血、README/docs 拆分、publication receipt 模板和 scripts 分层，这些都能降低项目阅读成本，但它们仍然属于治理或维护工作。外部建议里专门提醒：治理链成熟后，需要定期回到模型能力本身。v1133 正是把这条提醒变成可运行检查。

本版不训练新模型，不生成 checkpoint，不跑新的 benchmark scorecard，也不宣称模型能力提升。它做的是 cadence check：读取 README 最近版本段落，判断连续多少个版本没有真实模型能力验证信号。如果连续 run 超过阈值，报告进入 `watch`，并给出 `next_action=schedule_model_capability_regression`。这个设计避免把“提醒该回到模型能力”误写成“已经提升了模型能力”。

这个边界很关键。aiproj 现在已经有丰富的 publication receipt、contract check、index、review、artifact map 和 evidence chain，但这些证明的是治理链可追溯，不证明模型更会生成文本、更能覆盖 required term、更能处理 holdout。v1133 的价值就在于承认这两类能力不同：治理链要继续保养，模型能力也要周期性回归。

## 分类策略

`src/minigpt/model_capability_cadence.py` 是本版核心模块。它读取根 README 中的 `## Latest v... checkpoint` 段落，默认取最近 12 个版本，然后把每个段落分类为 `model-capability`、`governance`、`maintenance` 或 `unknown`。分类依据不是版本号，而是段落里的术语信号。

本版特别收窄了 model capability 术语，避免把“谈到 model capability”误判成“真实模型能力验证”。`MODEL_TERMS` 使用的是更具体的信号，例如 `training run`、`benchmark scorecard`、`benchmark suite`、`required term`、`loss signal`、`decoder`、`unassisted repair`、`exact surface` 和 `capacity probe`。这意味着 v1133 自己虽然在讲 model capability cadence，但不会因为标题里出现 model capability 就被当成真实能力验证版。

`GOVERNANCE_TERMS` 包含 `receipt`、`contract check`、`index`、`review`、`lookup-only` 和 `publication`。这些词通常说明版本在推进治理链。`MAINTENANCE_TERMS` 包含 `readability`、`docs`、`template`、`maintenance` 和 `script layer`，说明版本在做工程保养。分类不是完美自然语言理解，但足够支撑节奏提醒，因为它只需要识别最近一段是否明显缺少真实能力验证。

`_leading_non_capability_run` 从最新版本往后数，遇到第一个 `model-capability` 就停止。真实仓库运行时，最近 12 个版本窗口内没有找到符合收窄术语的模型能力版本，因此 `leading_non_capability_run=12`，超过默认阈值 `max_non_capability_run=4`，报告状态为 `watch`。

## 报告结构

v1133 report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`summary`、`rows`、`recommendations` 和 `csv_fieldnames`。其中 `decision` 始终是 `model_capability_cadence_ready`，表示 cadence 检查本身可用；`status` 则表示当前节奏是否在阈值内。真实运行是 `watch`，不是 fail，因为它不是 CI 故障，而是工程节奏提醒。

`summary` 包含 `scanned_version_count`、`leading_non_capability_run`、`max_non_capability_run`、`latest_model_capability_version`、`next_action` 和 `cadence_ready`。真实值里 `latest_model_capability_version=not_found_in_recent_window`，这说明最近窗口没有能力锚点；`next_action=schedule_model_capability_regression` 则把下一步建议写成机器可读字段。

`rows` 是最近版本的分类表。每行包含 `version`、`category`、`model_signal`、`governance_signal`、`maintenance_signal`、`status` 和 `recommendation`。这样读者可以看到为什么某个版本被归为 maintenance 或 governance，而不是只看一个总数。对于工程决策来说，这比口头说“最近治理太多”更可复查。

`recommendations` 在 watch 状态下会明确三点：leading non-capability run 超过阈值；应安排模型能力回归；候选检查包括 holdout accuracy、required term coverage、loss signal bridge、unassisted repair 和 decoder anchor distribution。这些建议来自外部保养文档，也和 `docs/model-capability-cadence.md` 保持一致。

## CLI 和脚本分层

`scripts/evaluation/check_model_capability_cadence_v1133.py` 放在 `scripts/evaluation/` 下。这个路径选择是有意的：v1130 新建 `scripts/publication/`，v1131 新建 `scripts/devtools/`，v1133 则把模型能力节奏检查放到 `scripts/evaluation/`。这样脚本目录开始按用途分层，而不是继续把所有 build/check/review/audit 脚本都堆在根目录。

CLI 支持 `--root`、`--out-dir`、`--max-non-capability-run`、`--require-ready`、`--require-within-cadence` 和 `--force`。真实运行使用 `--require-ready`，因此只要求 cadence 检查本身可用，不要求当前节奏必须 pass。这个选择很重要：当前真实结果就是 watch，如果用 `--require-within-cadence` 会返回 1，适合未来作为更严格 gate；但本版目标是发现问题并记录下一步，不是因为发现需要模型回归就让版本失败。

真实运行命令是：

```powershell
python -B scripts\evaluation\check_model_capability_cadence_v1133.py --out-dir f\1133\解释\model-capability-cadence-v1133 --require-ready --force
```

输出显示 `status=watch`、`decision=model_capability_cadence_ready`、`leading_non_capability_run=12`、`max_non_capability_run=4`、`latest_model_capability_version=not_found_in_recent_window`、`next_action=schedule_model_capability_regression`。这正是本版要留下的证据：当前项目需要在保养批次后回到模型能力验证。

## 文档配套

`docs/model-capability-cadence.md` 是本版新增的稳定文档。它写明 publication receipt 和 maintenance 版本有价值，但不能证明模型改进；建议每三到四个治理或保养版本后安排一次模型能力回归；候选检查包括 holdout accuracy、exact surface repair、required term coverage、loss signal bridge、unassisted repair 和 decoder anchor distribution；publication receipt governance 的 pass 不能被当成训练提升。

`docs/model-training.md` 增加了到 cadence 文档的链接，README 的 Documentation Map 也增加了 `Model capability cadence`。这样读者从项目首页就能看到：模型能力不是被治理链替代的，它有自己的节奏规则。

## 测试覆盖

`tests/test_model_capability_cadence.py` 覆盖三类行为。第一，临时 README 最新段落包含 `benchmark scorecard required term loss signal` 这类真实能力信号时，report 应该 pass，latest model capability version 是最新版本。第二，临时 README 连续只有 publication receipt、readability maintenance 和 contract check review 时，report 应该 watch，next action 是 schedule model capability regression，`require_ready` 返回 0，而 `require_within_cadence` 返回 1。第三，测试 artifact 输出和 CLI，确认五种输出格式存在，CLI 在 `--require-ready` 下返回 0。

这组测试保护了两个关键边界：一是 cadence checker 能识别真实能力锚点；二是发现节奏超限时不会误报工具失败，而是进入 watch 并给出下一步。对于后期工程保养来说，这比简单写一段“以后要记得训练模型”更可靠。

## 运行证据

v1133 输出写入 `f/1133/解释/model-capability-cadence-v1133`，包含 JSON、CSV、text、Markdown 和 HTML。Playwright MCP 打开 HTML 后，快照显示 `MiniGPT model capability cadence v1133`、`Recent Version Cadence` 表格和 `Recommendations` 区域。截图保存为 `f/1133/图片/v1133-model-capability-cadence.png`。

这份证据说明 v1133 没有训练模型，但它真实读取了当前项目 README 的最近版本记录，并把“需要模型能力回归”转成了可追溯 artifact。后续如果继续推进功能版本，就应该优先安排一个模型能力验证版本来回应这个 watch。

## 维护意义

v1133 的维护意义在于防止项目被治理链惯性带偏。AI 工程项目需要证据、收据、索引、review 和文档保养，但最终仍然要回答模型能力有没有变化。v1133 不直接回答这个问题，而是建立一个节奏保护：当最近太多版本都不是模型能力验证时，报告会提醒下一步该回到能力主线。

这个版本也说明“保养”不只是拆文件和写文档。好的后期保养会保护项目方向：命名不要继续恶化，入口不要继续杂乱，模板不要漏边界，模型能力不要被治理报告遮住。v1133 正是第四类保护。

## 一句话总结

v1133 把“治理和维护之后要回到模型能力”从口头建议变成可运行 cadence 报告，当前结果为 watch，并明确建议后续安排一次真实模型能力回归。
