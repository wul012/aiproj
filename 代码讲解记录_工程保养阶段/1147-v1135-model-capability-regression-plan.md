# v1135 model capability regression plan 代码讲解

## 本版目标和边界

v1135 的目标，是把 v1133 的模型能力 cadence `watch` 转成一个明确、可运行、可归档的模型能力回归计划。v1133 已经证明最近窗口内连续多个版本都偏治理或工程保养，下一步建议是 `schedule_model_capability_regression`。如果继续只写 receipt、template、artifact map，项目会越来越像“治理证据机器”，但 MiniGPT 的核心仍然应该周期性回答模型能力有没有被真实检查。因此 v1135 从这个 watch 结果出发，安排四类小而明确的回归项。

本版不训练新模型，不生成 checkpoint，不宣称模型质量提升，也不把计划项当成能力证据。它的 `model_quality_claim` 明确是 `plan_only`，`promotion_ready` 固定为 `False`。这和过去 publication receipt 的 no-promotion 边界是一致的：治理或计划通过，只代表下一步安排合理，不代表模型可以上线或晋级。真正的能力验证要等后续版本读取已有 evidence 或运行更具体的评估检查。

这个边界非常重要。用户之前问过“推进这么久，训练了 LLM 的能力有多少提升吗”，答案其实应该谨慎：治理链、文档链、收据链都能提升工程质量，但不能自动提升模型能力。v1135 正是在这个问题上收束，不再继续用治理链代替能力链，而是把能力回归作为接下来版本的明确目标。

## 输入来源

v1135 的输入是 v1133 的真实 cadence 报告：`f/1133/解释/model-capability-cadence-v1133/model_capability_cadence_v1133.json`。这个报告不是测试 fixture，它来自上一批真实运行，里面记录了 `status=watch`、`leading_non_capability_run=12`、`max_non_capability_run=4`、`latest_model_capability_version=not_found_in_recent_window` 和 `next_action=schedule_model_capability_regression`。

`src/minigpt/model_capability_regression_plan.py` 中的 `locate_cadence_report` 支持传入 JSON 文件或目录。如果传入目录，就自动定位 `model_capability_cadence_v1133.json`。这样 CLI 可以直接接收 `f/1133/解释/model-capability-cadence-v1133`，减少用户记长文件名的成本。`read_json_report` 使用 `utf-8-sig` 读取 JSON，并要求顶层必须是 object，避免错误输入静默通过。

## 核心检查

`build_model_capability_regression_plan` 首先提取 cadence report 的 `summary`，然后调用 `_checks`。检查项包括 cadence 文件是否存在、cadence 工具是否 ready、source status 是否为 watch、next action 是否为 `schedule_model_capability_regression`，以及 leading non-capability run 是否真的超过阈值。也就是说，v1135 不是任何时候都生成计划；只有当上游 cadence 确实要求模型回归时，计划才 ready。

测试里覆盖了这个边界：当 cadence status 是 `watch` 且 next action 是 `schedule_model_capability_regression` 时，report 为 pass；如果 cadence status 是 `pass` 且 next action 是 `continue_current_plan`，report 会 fail，并且 issues 中包含 `cadence_watch_detected`。这保护了 v1135 不会在项目节奏正常时硬插一个模型回归计划。

## 回归项设计

本版计划包含四个回归项。第一是 `required_term_coverage`，用于检查 bounded prompts 中关键术语是否仍然可见。它对应过去项目里的 required term coverage、uptake、pair surface 等能力线。第二是 `loss_signal_bridge`，用于把治理节奏重新连接到可度量的 loss 或 score signal。第三是 `decoder_anchor_distribution`，用于观察生成 anchor 是否仍然 bounded，避免模型只是复读模板。第四是 `holdout_scorecard_smoke`，用于在 receipt-heavy run 后保留一个小的 holdout scorecard 回路。

这四项不是随便列清单，而是刻意覆盖 surface、training-signal、decoder 和 holdout 四个面向。它们足够小，适合在后续几版逐步落地；也足够具体，避免“做一次模型评估”这种空泛任务。v1135 把这些项写入 `rows`，每行包含 `check_id`、`scope`、`evidence_kind`、`status` 和 `reason`。

## 输出结构

v1135 report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`source_cadence_path`、`source_cadence_summary`、`plan`、`rows`、`check_rows`、`summary`、`recommendations` 和 `csv_fieldnames`。其中 `plan` 是核心对象，记录 `plan_ready`、`plan_status`、`source_watch_reason`、`regression_item_count`、`next_step`、`promotion_ready` 和 `model_quality_claim`。

真实运行里 `plan_ready=True`，`regression_item_count=4`，`next_step=inventory_model_capability_regression_evidence_v1136`。这个 next step 不是随意写的，它说明 v1136 应该做证据清单，而不是直接宣称完成回归。先知道已有能力证据在哪里，再组织 suite manifest，才是比较稳的工程路线。

输出仍然复用 `readability_report_artifacts.py`，生成 JSON、CSV、text、Markdown 和 HTML。这个复用延续了 v1130-v1134 的保养策略：新报告不再重复写一套渲染器，业务模块只定义数据和检查，通用输出层负责格式。

## CLI 和运行证据

CLI 是 `scripts/evaluation/plan_model_capability_regression_v1135.py`，继续放在 `scripts/evaluation/` 下。它接收 cadence 路径、输出目录、`--require-plan-ready` 和 `--force`。真实命令是：

```powershell
python -B scripts\evaluation\plan_model_capability_regression_v1135.py f\1133\解释\model-capability-cadence-v1133 --out-dir f\1135\解释\model-capability-regression-plan-v1135 --require-plan-ready --force
```

真实输出为 `status=pass`、`decision=model_capability_regression_plan_ready`、`plan_ready=True`、`regression_item_count=4`、`source_next_action=schedule_model_capability_regression`、`next_step=inventory_model_capability_regression_evidence_v1136`。Playwright MCP 打开 HTML 后，页面显示 `Regression Plan Items` 表格和 `Recommendations` 区域，截图保存到 `f/1135/图片/v1135-model-capability-regression-plan.png`。

## 测试覆盖

`tests/test_model_capability_regression_plan.py` 覆盖三类行为。第一，cadence watch 可以生成 ready plan，并且计划项数量等于 `REGRESSION_ITEMS`。第二，cadence 没有 watch 时计划失败，防止在节奏正常时乱插回归计划。第三，输出和 CLI 都连通，目录输入可以定位 cadence JSON，五种 artifact 输出都存在。

测试过程中还暴露了一个临时目录生命周期问题：最初把 `locate_cadence_report(cadence_path.parent)` 的断言放到了 `TemporaryDirectory` 退出之后，目录被删除后函数无法判断它是目录。修复方式是把 located path 在临时目录内部求出，再在外部断言值。这是一个测试质量修正，没有影响业务逻辑。

## 维护意义

v1135 是从工程保养回到模型能力的拐点。它没有急着训练模型，也没有把治理报告包装成能力结果，而是先把回归计划定清楚：为什么要做，做哪四项，输入来自哪里，下一步是什么，边界是什么。这样的顺序比“看到 watch 就立刻写一个通过报告”更可靠。

这版也继续保持 scripts 分层：模型能力相关入口放在 `scripts/evaluation/`，publication 入口放在 `scripts/publication/`，文档和 artifact map 放在 `scripts/devtools/`。这样前一批可读性保养并没有停留在文档里，而是继续影响新版本的文件布局。

## 一句话总结

v1135 把 v1133 的 cadence watch 转成四项 bounded 模型能力回归计划，明确下一步是证据清单，而不是把计划误当成模型能力提升。
