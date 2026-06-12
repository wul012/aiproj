# v1138 model capability regression suite readiness 代码讲解

## 本版目标和边界

v1138 的目标，是对 v1137 的 suite manifest 做执行前 readiness check。v1137 已经把四个模型能力回归项整理成 suite row，但 manifest 本身仍然可能出现路径漂移、测试缺失或边界被改写。v1138 负责在 closeout 前确认这些条件都成立：每个 suite row 有存在的 source/test 路径，boundary 仍然是 `evidence_lookup_not_model_promotion`，suite 数量和 readiness 数量一致。

本版不执行 suite，不跑模型，不判断模型能力是否通过。它的 `model_quality_claim` 是 `readiness_only`。这意味着 v1138 只证明“可以进入下一步 closeout 或后续执行”，不能被理解为“模型能力回归已经完成”。这个边界延续 v1135-v1137 的分层：plan、inventory、manifest、readiness 都是准备链路，不是模型结果本身。

## 输入和数据结构

v1138 输入是 `f/1137/解释/model-capability-regression-suite-manifest-v1137/model_capability_regression_suite_manifest_v1137.json`。`locate_suite_manifest` 支持目录输入，自动定位这个 JSON。`read_json_report` 继续使用 `utf-8-sig` 并要求 JSON object。

`build_model_capability_regression_suite_readiness` 读取 suite report 的 `suite` 对象和 `rows`。每个 suite row 被 `_readiness_row` 转成 readiness row，字段包括 `suite_id`、`check_id`、`source_exists`、`test_exists`、`boundary_ok`、`primary_source`、`primary_test`、`status` 和 `recommendation`。如果 source 和 test 都存在，且 boundary 正确，row 状态就是 `ready`；否则是 `blocked`。

## 检查逻辑

`_checks` 保护六个条件：suite 文件存在、suite status 是 pass、suite_ready 为 true、suite rows 非空、readiness rows 数量和 suite rows 一致、所有 readiness rows 都 ready。这样可以覆盖三类常见漂移：输入文件路径错了、上游 suite 没 ready、suite row 的 source/test/boundary 出问题。

测试覆盖 ready 和 missing test 两种场景。ready 场景会创建真实 source 文件和 test 文件，readiness pass；missing test 场景只创建 source，不创建 test，readiness fail，并且 `require_readiness_ready` 返回 1。第三条测试覆盖 CLI 和五种输出格式，保证目录输入和 artifact writer 都能工作。

## CLI 和真实运行

CLI 是 `scripts/evaluation/check_model_capability_regression_suite_readiness_v1138.py`。真实命令是：

```powershell
python -B scripts\evaluation\check_model_capability_regression_suite_readiness_v1138.py f\1137\解释\model-capability-regression-suite-manifest-v1137 --out-dir f\1138\解释\model-capability-regression-suite-readiness-v1138 --require-readiness-ready --force
```

真实输出为 `status=pass`、`decision=model_capability_regression_suite_readiness_ready`、`readiness_ready=True`、`ready_item_count=4`、`suite_item_count=4`、`next_step=close_model_capability_regression_followup_v1139`。这说明四个 suite row 的 source/test 路径都存在，boundary 也保持正确。

Playwright MCP 打开 HTML 后，页面显示 `Regression Suite Readiness` 表格和建议区，截图保存为 `f/1138/图片/v1138-model-capability-regression-suite-readiness.png`。

## 输出含义

v1138 report 的 `readiness` 对象包含 `readiness_ready`、`ready_item_count`、`suite_item_count`、`next_step`、`promotion_ready` 和 `model_quality_claim`。真实运行中 `readiness_ready=True`，`ready_item_count=4`，`suite_item_count=4`，下一步是 `close_model_capability_regression_followup_v1139`。

`summary` 也镜像这些字段，便于 CLI 和后续 closeout 快速读取。`recommendations` 明确提示：使用 readiness 输出关闭 follow-up loop，但 closeout 必须诚实，readiness 不是模型质量分数；如果 source/test path 漂移，需要先修 manifest。

## 维护意义

v1138 的维护意义是防止 suite manifest 变成“看起来完整但执行不了”的清单。路径存在性和测试存在性是最朴素但非常重要的检查。对于高速迭代项目，文件移动、重命名或路径拷贝错误很常见；readiness check 把这些风险挡在 closeout 前。

同时，v1138 也让本轮模型能力回归链更完整。v1135 负责计划，v1136 负责材料，v1137 负责执行地图，v1138 负责执行前检查。到这里，项目已经把“该回到模型能力验证”推进成一个可审计的准备闭环。

还需要特别说明的是，readiness check 不是能力执行的替代品。它检查的是“后续检查能不能被可靠触发”，不是“后续检查的结果是否为好”。如果没有这一层，closeout 很容易只看 suite manifest 的表面结构，忽略某个测试文件已经不存在、某个 source path 已经重命名、或者 boundary 字段被复制时改错。v1138 把这些低级但常见的问题提前暴露出来，让 v1139 的 closeout 可以基于更稳的事实：四个 suite row 都有可定位的代码和测试入口，且仍然明确不允许把准备状态解释为 promotion。

这种分层也给后续真正执行模型能力回归留下空间。后续如果要进一步推进，可以在 readiness 通过之后增加执行型版本：实际运行 required term coverage、loss signal bridge、decoder anchor 或 holdout scorecard 中的一项或多项，再把真实结果写入新的 evidence。v1138 不抢这个角色，它只把执行前地基垫平。

## 一句话总结

v1138 确认 v1137 的四项模型能力回归 suite row 都具备 source/test 路径和非晋级边界，为 v1139 follow-up closeout 提供了可复查依据。
