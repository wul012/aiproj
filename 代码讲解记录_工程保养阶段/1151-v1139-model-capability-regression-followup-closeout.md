# v1139 model capability regression follow-up closeout 代码讲解

## 本版目标和边界

v1139 的目标，是把 v1135 到 v1138 这一段模型能力回归准备链路正式收口。v1133 的 cadence check 发现项目连续多版偏向文档、命名、索引和工程保养，因此给出 `schedule_model_capability_regression` 的下一步。v1135 把这个 watch 信号转成 bounded regression plan，v1136 盘点已有 source、test 和历史 evidence，v1137 把可执行项整理成 suite manifest，v1138 检查每个 suite row 的 source/test 路径和非晋级边界。到 v1139，项目需要一个轻量但明确的 closeout 入口，证明这条准备链路不是停在若干松散报告里，而是已经被统一关闭，并且下一步可以进入真实执行型模型能力回归。

本版不训练模型，不运行真实 benchmark，不执行 required term coverage、loss signal bridge、decoder anchor distribution 或 holdout scorecard smoke 的模型推理逻辑。它也不宣称模型质量变好。报告中明确保留 `promotion_ready=False` 和 `model_quality_claim=pre_execution_closeout_only`，意思是：v1139 只证明“准备链路已经闭合”，不证明“模型能力已经提升”。这个边界非常重要，因为 aiproj 之前已经有大量治理链、receipt 链和 evidence 链，如果把治理闭环误写成模型效果提升，就会让项目的成熟度判断失真。v1139 的价值是诚实地把准备阶段收束住，然后把下一步指向真实执行。

## 前置链路

v1139 的直接输入是 v1138 生成的 readiness report，路径是 `f/1138/解释/model-capability-regression-suite-readiness-v1138/model_capability_regression_suite_readiness_v1138.json`。这个 report 已经证明 v1137 suite manifest 中的四个 row 都有存在的 source path 和 test path，并且 boundary 保持 `evidence_lookup_not_model_promotion`。v1139 并不重新扫描所有历史文件，也不再重新构建 suite manifest，而是消费 v1138 的 readiness 结论，把它转成 closeout row 和 closeout checks。

这样设计的原因，是让每一层都只承担自己的职责。plan 负责选择要回归的模型能力项，inventory 负责找材料，manifest 负责把材料组织成执行地图，readiness 负责执行前检查，closeout 负责关闭准备链路。如果 v1139 重新做 v1136 或 v1138 的所有工作，代码会变大，职责也会混在一起。现在的实现更像一个清晰的接力棒：v1138 交给 v1139 的是已检查过的 readiness report，v1139 只确认它是否可被关闭，并输出下一步执行动作。

## 关键文件

核心模块是 `src/minigpt/model_capability_regression_followup_closeout.py`。它提供 `locate_readiness_report`、`read_json_report`、`build_model_capability_regression_followup_closeout`、`write_model_capability_regression_followup_closeout_outputs` 和 `resolve_exit_code`。这些函数延续最近几版的结构：定位输入、读取 JSON、构建 report、写出多格式 evidence、根据 `--require-*` 参数决定 CLI exit code。模块没有引入新的复杂依赖，只复用 `readability_report_artifacts.write_readability_outputs` 和 `report_utils` 中的 `as_dict`、`list_of_dicts`、`utc_now`。

CLI 文件是 `scripts/evaluation/close_model_capability_regression_followup_v1139.py`。它属于 `scripts/evaluation/`，因为本轮主题虽然是 closeout，但入口仍然服务于模型能力回归的执行前治理，而不是 publication receipt 或 devtools。CLI 支持目录输入，默认输出到 `runs/model-capability-regression-followup-closeout-v1139`，本次真实运行使用 `--out-dir f/1139/解释/model-capability-regression-followup-closeout-v1139 --require-closeout-ready --force`。`--require-closeout-ready` 的作用是让 closeout 不 ready 时返回非零退出码，适合后续 CI 或脚本串联。

测试文件是 `tests/test_model_capability_regression_followup_closeout.py`。它覆盖 ready、blocked 和 CLI/output 三类场景。ready 场景构造一个 readiness report，验证 closeout status 是 `pass`，`closeout_ready=True`，exit code 为 0。blocked 场景把 readiness 改成 fail，验证 closeout status 变成 `fail`，issues 中包含 `readiness_ready`，并且 `require_closeout_ready` 会返回 1。CLI/output 场景验证目录输入能定位 JSON，五种输出格式都能写出，并且 CLI 可以从目录参数完成 closeout。

运行证据放在 `f/1139`。`f/1139/解释/model-capability-regression-followup-closeout-v1139/` 里有 JSON、CSV、text、Markdown 和 HTML 五种产物，`f/1139/图片/v1139-model-capability-regression-followup-closeout.png` 是 Playwright MCP 对 HTML 的全页截图，`f/1139/解释/说明.md` 是面向读者的短说明。

## 核心数据结构

v1139 report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`source_readiness_path`、`source_readiness_summary`、`rows`、`check_rows`、`closeout`、`summary`、`recommendations` 和 `csv_fieldnames`。这个结构和最近几版保持一致，方便 HTML/Markdown 渲染，也方便后续脚本只读消费。

`rows` 是 closeout row。它从 v1138 readiness rows 派生，每行包含 `suite_id`、`check_id`、`readiness_status`、`closeout_scope`、`status` 和 `next_action`。如果上游 row 的 `status` 是 `ready`，并且 `boundary_ok` 是 `True`，这一行 closeout 状态就是 `closed`；否则就是 `blocked`。这样 closeout 不需要知道具体 source/test path，它只依赖 readiness 层给出的结果和边界判断。`closeout_scope` 固定为 `pre_execution_readiness`，用来提醒读者：这是执行前关闭，不是执行后评分。

`check_rows` 是本版最关键的保护层。`_checks` 一共检查六项：readiness file 是否存在、readiness report 顶层 status 是否为 pass、readiness 对象里的 `readiness_ready` 是否为 true、readiness rows 是否非空、closeout row 数量是否和 readiness row 数量一致、所有 closeout rows 是否都是 closed。任何一项失败都会进入 `issues`，`status` 变成 fail，`decision` 变成 `repair_model_capability_regression_followup_closeout`。这些检查都很朴素，但刚好卡住了准备链路收口最容易出错的地方：输入文件缺失、上游没通过、空报告、数量漂移、局部 row 没关上。

`closeout` 和 `summary` 都包含 `closeout_ready`、`closed_stage`、`ready_item_count`、`promotion_ready`、`model_quality_claim` 和 `next_step` 等信息。`closed_stage` 是 `plan_inventory_manifest_readiness`，说明关闭的是计划、盘点、manifest、readiness 这四层准备阶段。`next_step` 是 `run_selected_model_capability_regression_execution`，这很明确地把后续推进引向真实执行，而不是继续空转生成更多准备报告。

## 真实运行结果

本次真实命令是：

```powershell
python -B scripts\evaluation\close_model_capability_regression_followup_v1139.py f\1138\解释\model-capability-regression-suite-readiness-v1138 --out-dir f\1139\解释\model-capability-regression-followup-closeout-v1139 --require-closeout-ready --force
```

输出为 `status=pass`、`decision=model_capability_regression_followup_closeout_ready`、`closeout_ready=True`、`ready_item_count=4`、`closed_stage=plan_inventory_manifest_readiness`、`next_step=run_selected_model_capability_regression_execution`。这说明 v1138 的四个 readiness rows 都被 closeout 成功关闭，且没有出现路径丢失、上游状态漂移或边界错误。

Playwright MCP 打开 HTML 后，页面标题是 `MiniGPT model capability regression follow-up closeout v1139`，快照中能看到 `Regression Follow-up Closeout` 表格和 `Recommendations` 区域。截图保存到 `f/1139/图片/v1139-model-capability-regression-followup-closeout.png`。这张图是运行证据的一部分，证明 HTML 产物不是空文件，也能被浏览器正常渲染。

## 测试覆盖

本版测试没有只断言一个 happy path。`test_closeout_ready_from_readiness` 用最小 readiness report 验证 closeout 能通过，保护字段包括 `status`、`summary.closeout_ready`、`summary.next_step` 和 `resolve_exit_code`。`test_closeout_fails_when_readiness_is_blocked` 把 readiness report 改为 blocked，确认 closeout 不会盲目通过，并且 `issues` 会包含 `readiness_ready`。这条测试保护了 v1139 最重要的边界：上游没 ready 时，closeout 必须失败。

`test_outputs_and_cli_are_wired` 验证 artifact writer 和 CLI 都能工作。它写出 JSON、CSV、text、Markdown 和 HTML，然后调用 CLI 使用目录输入和 `--require-closeout-ready`，最后检查 `locate_readiness_report` 能定位到真实 JSON。这条测试保护了实际使用路径，因为真实运行时用户更可能传目录，而不是手动指定 JSON 文件。

本版还跑了 `python -m py_compile` 覆盖新增模块、脚本和测试，并在真实产物生成后继续跑 source encoding hygiene、focused tests、五版合并测试和 `git diff --check`。这些验证分别保护语法、编码、功能、跨版本串联和空白格式。

## 维护意义

v1139 的维护意义不是多写一个报告，而是防止模型能力回归准备链路变成“前面每一步都有产物，但没有明确关闭点”的散装状态。对于一个已经有上千版记录的项目，散装状态会慢慢增加阅读成本：后来的维护者要自己判断哪一步算结束、哪一步该接着做、哪份报告能作为下一步输入。v1139 把这些判断收进一个可运行入口里。

同时，它也纠正了一个容易出现的节奏问题。前面用户多次指出版本推进不能只做很小的整理，模型能力本身也需要回到真实评估。v1135 到 v1139 并没有直接提升模型能力，但它把“回到模型能力回归”的计划、材料、manifest、readiness 和 closeout 都准备好了。这样下一版如果继续做功能，就不应该再继续扩展准备链，而应选择一个 regression item 实际执行，例如 required term coverage 或 holdout scorecard smoke。

边界写清楚也是工程成熟度的一部分。`promotion_ready=False` 和 `model_quality_claim=pre_execution_closeout_only` 不是保守过头，而是避免把治理产物误当成模型效果。真正的能力提升必须来自训练、评估、对比、生成样本或稳定性结果。v1139 只给这些工作打开入口。

## 一句话总结

v1139 把 v1135-v1138 的模型能力回归准备链路收束成可测试、可截图、可复查的 closeout，同时明确不声明模型晋级，把后续路线指向真实执行型能力回归。
