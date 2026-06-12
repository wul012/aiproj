# v1136 model capability regression inventory 代码讲解

## 本版目标和边界

v1136 的目标，是把 v1135 的模型能力回归计划进一步落到“仓库里到底有没有可复用证据路径”。v1135 已经把 v1133 的 cadence watch 转成四个计划项：required term coverage、loss signal bridge、decoder anchor distribution 和 holdout scorecard smoke。但计划本身还不能说明项目马上能执行 suite，因为可能没有对应脚本、源码或测试。v1136 负责扫描这些基础材料，判断每个计划项是否 ready。

本版不新增模型训练，不运行真正的 scorecard，不评判模型好坏，也不把“存在脚本/测试”解释为能力通过。它的 `model_quality_claim` 是 `inventory_only`，意思是只证明证据路径可用，不证明模型能力改善。这个边界延续 v1135 的 plan-only 原则，并为 v1137 的 suite manifest 做准备。

## 输入和扫描范围

v1136 的输入是 v1135 的真实计划 JSON：`f/1135/解释/model-capability-regression-plan-v1135/model_capability_regression_plan_v1135.json`。`locate_regression_plan` 支持文件或目录输入，目录输入会自动定位这个 JSON，避免用户手工复制长文件名。`read_json_report` 使用 `utf-8-sig`，并要求顶层是 JSON object。

扫描范围包括 `scripts`、`src/minigpt`、`tests` 和 `f`。前三个目录用于判断是否存在执行入口、业务模块和测试；`f` 用于寻找历史 artifact JSON。v1136 不读取所有文件内容，而是根据路径和文件名里的关键词做轻量 inventory。这是有意的：本版要回答“材料在哪里”，不是重新执行所有材料的业务逻辑。

## 关键词映射

`KEYWORD_MAP` 是本版的关键配置。`required_term_coverage` 对应 `required_term` 和 `coverage`；`loss_signal_bridge` 对应 `loss_signal` 和 `loss_signal_bridge`；`decoder_anchor_distribution` 对应 `decoder_anchor` 和 `anchor_distribution`；`holdout_scorecard_smoke` 对应 `holdout` 和 `scorecard`。这些关键词来自 v1135 的四个计划项，也贴近现有仓库命名。

`_matching_files` 会在指定目录下递归匹配 Python 或 JSON 文件，只要路径里出现任意关键词就计入。这样可以覆盖历史长命名文件，也可以覆盖后续短别名文件。真实运行结果显示四个计划项都 ready，说明仓库已有足够材料组织下一步 suite manifest。

## 输出结构

v1136 report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`source_plan_path`、`source_plan_summary`、`rows`、`check_rows`、`inventory`、`summary`、`recommendations` 和 `csv_fieldnames`。

每个 inventory row 包含 `check_id`、`script_count`、`source_count`、`test_count`、`artifact_count`、`sample_script`、`sample_source`、`sample_test`、`sample_artifact`、`status` 和 `recommendation`。这些字段不只给数量，还给样例路径，方便读者快速跳转到已有材料。`status` 为 `ready` 的条件是至少有脚本或源码，并且有测试。artifact 可以增强证据，但不作为 ready 的唯一条件，因为有些检查可能先有代码测试，再由后续版本生成新 artifact。

`inventory` 对象记录 `inventory_ready`、`planned_item_count`、`ready_item_count`、`next_step`、`promotion_ready` 和 `model_quality_claim`。真实运行中 `planned_item_count=4`、`ready_item_count=4`，因此 `next_step=build_model_capability_regression_suite_manifest_v1137`。

## 检查逻辑

`_checks` 保护六个条件：plan 文件存在、plan status 是 pass、plan_ready 为 true、plan rows 非空、inventory rows 数量等于 plan rows 数量、所有 inventory items 都 ready。只要某项没有脚本/源码或缺测试，`all_inventory_items_ready` 就会失败，report 状态变成 fail。

测试覆盖了这个边界。第一条测试写入计划、脚本、源码和测试，inventory 应该 pass。第二条测试只写脚本不写测试，inventory 应该 fail，并且 `require_inventory_ready` 返回 1。第三条测试覆盖 artifact 输出和 CLI，确认目录输入能定位 plan JSON，五种输出格式都存在。

测试中也遇到和 v1135 类似的临时目录生命周期问题：如果在 `TemporaryDirectory` 退出后再调用 locate 函数，目录已经不存在，函数不能再判断它是目录。修正方式同样是在 `with` 内先求出 located path，再做断言。这个修复让测试更准确，不影响业务实现。

## CLI 和真实运行

CLI 是 `scripts/evaluation/inventory_model_capability_regression_evidence_v1136.py`。它继续放在 `scripts/evaluation/`，因为这是模型能力回归链的一部分。真实运行命令是：

```powershell
python -B scripts\evaluation\inventory_model_capability_regression_evidence_v1136.py f\1135\解释\model-capability-regression-plan-v1135 --out-dir f\1136\解释\model-capability-regression-inventory-v1136 --require-inventory-ready --force
```

真实输出为 `status=pass`、`decision=model_capability_regression_inventory_ready`、`inventory_ready=True`、`planned_item_count=4`、`ready_item_count=4`、`next_step=build_model_capability_regression_suite_manifest_v1137`。Playwright MCP 打开 HTML 后，页面显示 `Regression Evidence Inventory` 表格和建议区，截图保存为 `f/1136/图片/v1136-model-capability-regression-inventory.png`。

## 维护意义

v1136 的意义，是避免下一步能力回归变成“新造一套评估体系”。项目已经积累了大量 required term、loss signal、decoder anchor、holdout scorecard 相关代码和测试。先做 inventory，可以让 v1137 的 suite manifest 选择已有路径，减少重复、降低维护成本，也符合工程后期保养“先复用，再扩展”的原则。

这版也继续回答“模型能力有没有提升”的问题：还没有。本版只证明能力回归材料可用。真正的能力结果要等 suite manifest 和后续执行/检查版本来给出。这样的层次划分让项目不会把工程可读性或证据完整性误报为模型能力提升。

## 一句话总结

v1136 把 v1135 的四项模型能力回归计划映射到仓库已有脚本、源码、测试和 artifact 线索，确认它们都 ready，为 v1137 组织 suite manifest 提供了实证入口。
