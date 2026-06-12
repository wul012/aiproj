# v1141 model capability regression loop trend 代码讲解

## 本版目标和边界

v1141 的目标，是把 v1135 到 v1139 的模型能力回归准备链路作为一个整体进行只读核验。v1135 生成 plan，v1136 做 evidence inventory，v1137 生成 suite manifest，v1138 做 suite readiness，v1139 做 follow-up closeout。每一版都检查了自己的直接上游，但在 v1141 之前，还没有一个报告从端到端角度回答：这五个 artifact 是否都存在，版本顺序是否正确，每个 stage 是否真的 ready，`next_step` 是否一层层接上，source path 是否回指上一阶段，以及最终 closeout 是否真的关闭。

本版不训练模型，不跑 benchmark，不重新执行 v1135-v1139 的生成逻辑，也不修改任何上游 artifact。它的性质是 read-only trend report，或者说闭环总账。它只消费已经归档在 `f/1135` 到 `f/1139` 下的 JSON 文件，输出一份新的 `f/1141` 证据。这个边界延续了前几版的诚实原则：治理闭环不是模型质量提升，loop closed 也不是 promotion。报告里继续保留 `promotion_ready=False` 和 `model_quality_claim=loop_trend_read_only`，防止读者把“准备链路闭合”误读为“模型效果变好”。

## 上游来源

v1141 读取五个真实 artifact。第一份是 `f/1135/解释/model-capability-regression-plan-v1135/model_capability_regression_plan_v1135.json`，它来自 v1135，对 v1133 cadence watch 的 `schedule_model_capability_regression` 做出响应，计划四个回归项。第二份是 `f/1136/解释/model-capability-regression-inventory-v1136/model_capability_regression_inventory_v1136.json`，它盘点四个回归项对应的 source、test 和已有 evidence。第三份是 `f/1137/解释/model-capability-regression-suite-manifest-v1137/model_capability_regression_suite_manifest_v1137.json`，它把 ready inventory row 转成可执行 suite manifest。第四份是 `f/1138/解释/model-capability-regression-suite-readiness-v1138/model_capability_regression_suite_readiness_v1138.json`，它检查 suite row 的 source/test 路径和 boundary。第五份是 `f/1139/解释/model-capability-regression-followup-closeout-v1139/model_capability_regression_followup_closeout_v1139.json`，它关闭准备链路并把下一步指向真实执行型模型能力回归。

这些上游都是只读输入。v1141 不会为了通过检查去修它们，也不会重写它们。若真实运行发现任何一项不一致，正确动作应该是停下来报告哪一项失败，而不是把 v1141 逻辑放宽到“看起来通过”。这也是本版测试加入负例的原因：broken chain reference 和 version order violation 都必须能被抓出来。

## 入口和输出模型

核心模块是 `src/minigpt/model_capability_regression_loop_trend.py`。它定义 `STAGE_SPECS`，把五个 stage 的版本号、stage 名称、目录名、JSON 文件名、ready key、expected next_step 和 source key 固定下来。这样做比在逻辑里散落字符串更稳，也让测试能直接复用同一份 stage spec。

`load_model_capability_regression_loop_reports(root)` 负责从项目根目录定位五个 JSON。它使用 v1140 新增的 `locate_upstream_report` 和 `read_json_object`，说明 v1140 的重构不是孤立的；v1141 已经开始消费共享 loader helper。loader 会把 artifact path 尽量记录为相对项目根目录的路径，这样报告在不同机器上阅读时不会被绝对路径绑死。

`build_model_capability_regression_loop_trend(stage_reports, generated_at=None)` 是主构建函数。它先把每个 stage entry 转成 row，再构造 checks。输出保持项目近期 report 的标准结构：顶层有 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`rows`、`check_rows`、`loop`、`summary`、`recommendations` 和 `csv_fieldnames`。`rows` 用于 HTML/Markdown/CSV 展示，`check_rows` 用于解释为什么 pass 或 fail，`loop` 和 `summary` 则给 CLI、README 和后续模块快速读取。

CLI 是 `scripts/generate_model_capability_regression_loop_trend_v1141.py`。真实运行命令是：

```powershell
python -B scripts\generate_model_capability_regression_loop_trend_v1141.py --out-dir f\1141\解释\model-capability-regression-loop-trend-v1141 --require-loop-closed --force
```

`--require-loop-closed` 让 loop 不闭合时返回 1，适合后续串到 CI 或批处理里。

## 核心字段和检查

每个 row 包含 `version`、`stage`、`artifact_exists`、`status`、`decision`、`ready_key`、`ready`、`next_step`、`source_path`、`artifact_path`、`promotion_ready` 和 `model_quality_claim`。这些字段刻意不是只写一个 pass/fail，而是把每个 stage 自己的状态和链路信息都暴露出来。读者可以直接看到 v1135 是 plan，v1136 是 inventory，v1137 是 suite_manifest，v1138 是 suite_readiness，v1139 是 followup_closeout。

`_checks` 保护九个条件。`all_five_artifacts_present` 检查五个 artifact 都存在。`version_order_strict` 检查版本顺序必须是 v1135、v1136、v1137、v1138、v1139。`all_stage_status_pass` 检查每个上游报告顶层 status 都是 pass。`all_stage_ready_flags_true` 检查每个 stage 的 ready flag 都为 true。`closeout_ready_true` 特别确认最后一版 v1139 的 `closeout_ready` 为 true。`next_steps_align` 检查五个 stage 的 `summary.next_step` 是否和预期接力一致。`source_paths_chain_back` 检查 v1136 到 v1139 的 source path 是否逐级回指上一阶段 artifact。`non_promotion_boundary_preserved` 检查所有 stage 的 `promotion_ready` 都是 false。`reports_are_parseable_objects` 检查读取到的 report 都是非空 dict。

这些检查覆盖了闭环报告最容易漏掉的风险。比如五份报告都存在，但 v1137 读的不是 v1136 的 inventory，而是某个旧文件；或者版本顺序在 README 上看着对，但实际传入 list 被交换；或者 closeout_ready 是 false 但顶层 status 仍被误解。v1141 把这些问题变成显式检查项。

## 测试如何保护链路

`tests/test_model_capability_regression_loop_trend.py` 使用 dict fixture 构造五个 stage，而不是用大段字符串拼 JSON。这样更容易看清字段语义，也符合项目最近减少字符串式 fixture 的方向。happy path 测试确认完整链路会得到 `status=pass`、`loop_closed=True`、stage_count 为 5、ready_stage_count 为 5，并且 `require_loop_closed` 返回 0。

负例一是 broken chain reference。测试故意把 v1137 的 `source_inventory_path` 改成 `f/9999/wrong.json`，期望报告失败，并且 issues 中出现 `source_paths_chain_back`。这证明 v1141 不只是检查每个 stage 自己说自己 ready，还会验证 stage 之间是否真的接上。负例二是 version order violation，测试交换 v1135 和 v1136 的 entry，期望 `version_order_strict` 失败。第三类测试覆盖 loader、writer 和 CLI：在临时目录写出五个真实结构的 JSON，再调用 loader 和 CLI，确认五种输出格式都生成。

真实验证中，v1141 焦点测试 4 个通过，真实 CLI 也在 `--require-loop-closed` 下成功退出。Playwright MCP 打开 HTML 后，页面显示 `MiniGPT model capability regression loop trend v1141` 标题、`Regression Loop Stages` 表格和 recommendations，截图保存为 `f/1141/图片/v1141-model-capability-regression-loop-trend.png`。

## 真实结果和后续含义

真实运行结果是 `status=pass`、`decision=model_capability_regression_loop_closed`、`loop_closed=True`、`stage_count=5`、`ready_stage_count=5`、`artifact_present_count=5`、`closeout_ready=True`、`next_step=publish_model_capability_cadence_watch_v1142`。这说明 v1135-v1139 的准备链路确实闭合：五个 artifact 都存在，五个 stage 都 ready，closeout 已完成，且每个阶段都保持非晋级边界。

但是，v1141 仍然不是模型能力提升证据。它是“这条准备链路完成了”的证据。真正的下一步应该交给 v1142 cadence watch，让 cadence watch 根据当前 README 和证据状态给出下一批 due item。若 v1142 指向真实模型能力执行，那么 v1143 之后就不应该继续只做闭环报告，而要选择一个具体回归项实际运行。

## 一句话总结

v1141 把 v1135-v1139 五份单点报告收束成端到端可复查的 loop trend evidence，证明模型能力回归准备链已闭合，同时明确下一步交给 v1142 cadence watch 决定。
