# v1137 model capability regression suite manifest 代码讲解

## 本版目标和边界

v1137 的目标，是把 v1136 的 evidence inventory 组织成一个 bounded suite manifest。v1135 说明为什么要回到模型能力，v1136 说明四个计划项在仓库里都有可复用脚本、源码、测试和 artifact 线索。v1137 则把这些线索整理成 suite row，让后续 v1138 可以检查这个 suite 是否具备执行前 readiness。

本版仍然不执行模型评估，不训练模型，不算分，也不声明模型能力变好。它的 `model_quality_claim` 是 `manifest_only`，`promotion_ready=False`。manifest 的价值是把输入、测试、artifact hint 和边界放到同一张表里，减少后续执行时的查找成本。它是执行地图，不是执行结果。

## 输入来源

v1137 的输入是 `f/1136/解释/model-capability-regression-inventory-v1136/model_capability_regression_inventory_v1136.json`。这个 inventory 已经证明四个计划项都有 ready 状态。`locate_inventory_report` 支持文件或目录输入，目录输入时自动定位 `model_capability_regression_inventory_v1136.json`。这延续 v1135/v1136 的入口友好策略。

`read_json_report` 仍然要求 JSON 顶层是 object。这个小约束很重要，因为后续 report builder 都依赖字典字段；如果误传 CSV 或 list JSON，应该尽早失败，而不是生成空 manifest。

## suite row 设计

`_suite_row` 把每个 ready inventory row 转成 suite row。字段包括 `suite_id`、`check_id`、`primary_source`、`primary_test`、`artifact_hint`、`status` 和 `boundary`。`suite_id` 使用 `capability-regression-01` 这种稳定编号，便于后续 readiness check 引用；`check_id` 保留 v1135 的四个能力项；`primary_source` 优先使用 inventory 的 sample source，如果没有则使用 sample script；`primary_test` 指向对应测试；`artifact_hint` 指向历史 JSON 线索；`boundary` 固定为 `evidence_lookup_not_model_promotion`。

这个 boundary 是本版的核心保护。v1137 虽然把 suite 组织起来，但它并不说这些检查已经通过，也不说模型质量提升。它只说：后续可以沿这些路径做 regression readiness 或执行。每一行都带边界，能避免后续消费者把 manifest 当成结果。

## 检查逻辑

`_checks` 包含七项：inventory 文件存在、inventory status passed、inventory_ready 为 true、inventory rows 非空、suite rows 数量等于 ready inventory 数量、suite rows 都有 primary test、suite rows 都保持 boundary。只要 inventory 未 ready、缺测试，或 boundary 被改掉，manifest 就会 fail。

测试覆盖了这些边界。ready inventory 能生成 pass manifest；inventory_ready 为 false 时 manifest fail，issues 中包含 `inventory_ready`；CLI 和 artifact 输出都被覆盖，五种输出格式都能生成，目录输入也能定位 JSON。这样 v1137 不只是把数据搬一遍，而是检查了 manifest 对后续执行是否足够可信。

## 输出结构

v1137 report 包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`source_inventory_path`、`source_inventory_summary`、`rows`、`check_rows`、`suite`、`summary`、`recommendations` 和 `csv_fieldnames`。

`suite` 对象记录 `suite_ready`、`suite_item_count`、`execution_mode`、`next_step`、`promotion_ready` 和 `model_quality_claim`。真实运行里 `suite_ready=True`、`suite_item_count=4`、`execution_mode=reuse_existing_evidence_paths`、`next_step=check_model_capability_regression_suite_readiness_v1138`。这说明下一版应该做 readiness check，而不是直接写 closeout。

## CLI 和运行证据

CLI 是 `scripts/evaluation/build_model_capability_regression_suite_manifest_v1137.py`。真实运行命令：

```powershell
python -B scripts\evaluation\build_model_capability_regression_suite_manifest_v1137.py f\1136\解释\model-capability-regression-inventory-v1136 --out-dir f\1137\解释\model-capability-regression-suite-manifest-v1137 --require-suite-ready --force
```

输出显示 `status=pass`、`decision=model_capability_regression_suite_manifest_ready`、`suite_ready=True`、`suite_item_count=4`、`next_step=check_model_capability_regression_suite_readiness_v1138`。Playwright MCP 打开 HTML 后，页面中可见 `Regression Suite Manifest` 表格和建议区，截图保存为 `f/1137/图片/v1137-model-capability-regression-suite-manifest.png`。

## 维护意义

v1137 的意义是把模型能力回归链从“计划”和“材料盘点”推进到“可执行清单”。如果没有 manifest，后续 readiness check 需要重新解释 inventory；有了 manifest，readiness check 只要检查 suite 行是否有 source/test/artifact hint、边界是否正确、数量是否匹配。这样链路更清楚，也更容易维护。

这版也继续体现“复用优先”。suite row 来自 v1136 的 existing evidence paths，不新增一堆新评估脚本。对于一个历史版本很多的项目，复用已有能力线索比继续扩展新治理链更稳。

## 一句话总结

v1137 把 v1136 的 ready inventory 行整理成四项 bounded suite manifest，为 v1138 的 readiness check 提供了清晰、带边界的执行地图。
