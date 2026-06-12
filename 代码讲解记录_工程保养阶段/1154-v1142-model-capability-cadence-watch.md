# v1142 model capability cadence watch 代码讲解

## 本版目标和停止边界

v1142 的目标，是在 v1141 确认 v1135-v1139 模型能力回归准备链路闭合之后，重新发布一份当前项目状态下的 cadence watch，并让它明确说出下一步 due list。用户要求做到 v1142 后停止，让 Claude review，所以本版不是继续实现 due list 中的下一项，而是把项目状态、欠账位置和推荐动作沉淀成可引用证据。

本版不训练模型，不执行 benchmark，不新增模型能力回归结果，也不修改 v1135-v1139 的上游 artifact。它只扩展现有 `model_capability_cadence.py`，新增 v1142 的 writer 和 CLI，生成一份新的 `f/1142` 运行证据。真实报告的 due list 是 `run_selected_model_capability_regression_execution` 和 `schedule_model_capability_regression`。这意味着下一步确实应该进入模型能力执行，但 v1142 自己不越界执行它。这个停止边界很重要，因为用户明确希望做到 v1142 后交给 Claude review，再决定后续方向。

## 为什么不是完全新写一个 cadence 模块

仓库里已经存在 `src/minigpt/model_capability_cadence.py` 和 `scripts/evaluation/check_model_capability_cadence_v1133.py`。Claude 的快速判断里说“v1133 cadence-watch module exists but has no generator script”，这和当前实际仓库状态不完全一致：v1133 的 generator script 已经存在，并且测试文件 `tests/test_model_capability_cadence.py` 也存在。因此 v1142 没有重复造一套 cadence 模块，而是在现有模块上做兼容扩展。

兼容扩展的原则是：保留 `build_model_capability_cadence_report`、`write_model_capability_cadence_outputs` 和 `resolve_exit_code` 的旧入口，让 v1133 测试和旧脚本继续工作；新增 `write_model_capability_cadence_watch_outputs` 和 `scripts/generate_model_capability_cadence_watch_v1142.py`，专门写出 v1142 stem `model_capability_cadence_watch_v1142`。这样既回应了 task-03 的目标，又不会破坏旧版本语义。

## 新增字段和 due list

v1142 给 cadence report 增加了几类新信息。第一类是 refactor freshness。模块新增 `REFACTOR_TERMS`，包括 `dedup`、`refactor`、`shared helper`、`contract-preserving`、`loader helper` 等词。`_classify_section` 会优先识别 refactor，因为 v1140 的 README 内容同时会提到 model capability regression modules，如果先按 model terms 判断，就会误把 v1140 归类为模型能力版本。现在 v1140 会被识别为 `refactor`，并成为最近一次 contract-preserving maintenance slot。

第二类是 explanation freshness。`_explanation_paths` 扫描 `代码讲解记录_*` 目录下的 Markdown 文件，`_latest_numbered_version` 从文件名中提取最新 `v####`。最终真实运行中最新讲解是 v1142，所以 `latest_explanation_version=v1142`，`versions_since_last_explanation=0`。这说明讲解没有落后当前提交版本。

第三类是 evidence freshness。`_latest_evidence_version` 扫描 `f/` 下数字目录，最终真实运行时最新 evidence 是 `f/1142`，所以 `latest_evidence_version=v1142`，`versions_since_last_evidence=0`。这表示运行截图和说明没有滞后。

第四类是 loop follow-through。`_loop_execution_due` 会读取 `f/1141/**/model_capability_regression_loop_trend_v1141.json`，如果其中 `summary.loop_closed=True`，就把 `run_selected_model_capability_regression_execution` 加入 due list。真实运行中 v1141 已经证明 v1135-v1139 的准备链路闭合，因此这个 due item 被触发。

第五类是 non-capability run watch。原有 cadence 逻辑会统计最近 README 版本中连续非 model-capability 的数量。真实运行结果是 `leading_non_capability_run=6`，超过 `max_non_capability_run=4`，因此另一个 due item 是 `schedule_model_capability_regression`。它和第一项在语义上相互印证：一方面准备链路已经闭合，另一方面 cadence 已经提醒不要再继续只做治理和维护。

## CLI 和真实运行

v1142 新增脚本 `scripts/generate_model_capability_cadence_watch_v1142.py`。它和现有脚本风格一致，支持 `--root`、`--out-dir`、`--max-non-capability-run`、`--require-ready`、`--require-within-cadence` 和 `--force`。真实运行命令是：

```powershell
python -B scripts\generate_model_capability_cadence_watch_v1142.py --out-dir f\1142\解释\model-capability-cadence-watch-v1142 --require-ready --force
```

真实输出为 `status=watch`、`decision=model_capability_cadence_ready`、`leading_non_capability_run=6`、`max_non_capability_run=4`、`latest_model_capability_version=v1136`、`latest_refactor_version=v1140`、`versions_since_last_refactor=2`、`latest_explanation_version=v1142`、`versions_since_last_explanation=0`、`latest_evidence_version=v1142`、`versions_since_last_evidence=0`、`due_count=2`、`due_list=run_selected_model_capability_regression_execution, schedule_model_capability_regression`、`next_action=run_selected_model_capability_regression_execution`。

这里需要解释 `latest_model_capability_version=v1136`。cadence 分类依赖 README 的关键词命中，v1135-v1139 中有一些版本是准备链路、readiness 或 closeout，不都被当作强模型能力信号。v1142 不强行把所有带“model capability”字样的治理版本都当作真实能力证据，这与项目一直强调的边界一致：准备链路和闭环报告不是模型质量提升。也正因为如此，报告给出 `status=watch` 是合理的。

## 测试覆盖

本版扩展了 `tests/test_model_capability_cadence.py`。原有三条测试继续保留：模型版本足够近时 cadence pass，长治理/维护串时 cadence watch，旧 v1133 writer 和 CLI 仍能输出五种格式。新增两条测试覆盖 v1142 due list。

`test_cadence_due_list_follows_closed_regression_loop` 构造一个临时项目，写入 v1141 loop trend JSON，并设置 `loop_closed=True`。测试断言 `due_count=1`，`next_action=run_selected_model_capability_regression_execution`，并且 due 第一项就是同一个 action。这条测试保护了 v1142 最重要的 follow-through：一旦 v1141 说准备链路闭合，cadence watch 就必须把下一步指向真实执行。

`test_cadence_due_list_can_be_empty_when_slots_are_fresh` 构造另一个临时项目，让 README 里最新版本是 refactor，上一版有模型能力信号，同时补齐同版本讲解和 evidence。测试确认 due list 是 `none`，并验证 v1142 writer 和 CLI 输出五种格式。这条测试防止 cadence watch 过度报警：当 refactor、讲解、证据和模型 cadence 都在阈值内时，它不应该制造无意义的 due item。

## 真实证据和截图

v1142 的 artifact 写入 `f/1142/解释/model-capability-cadence-watch-v1142/`，包含 JSON、CSV、text、Markdown 和 HTML。Playwright MCP 打开 HTML 后，页面标题是 `MiniGPT model capability cadence watch v1142`，快照中能看到 `Recent Version Cadence` 表格和 recommendations。截图保存为 `f/1142/图片/v1142-model-capability-cadence-watch.png`。

`f/1142/解释/说明.md` 记录了真实命令和关键结果。README 也新增了 v1142 checkpoint，把 due list 原样写入。这样用户把项目交给 Claude review 时，不需要从命令行日志里翻结果，直接看 README、说明文件和 HTML 截图就能判断本版结论。

## 下一步建议

v1142 的 due list 明确给出两项：`run_selected_model_capability_regression_execution` 和 `schedule_model_capability_regression`。我建议 Claude review 时重点判断：v1143 是否直接选择 `required_term_coverage` 或 `holdout_scorecard_smoke` 作为真实执行项；如果 Claude 认为 cadence 分类太保守，也可以指出哪些 README terms 应该算作 model capability signal。但在没有 review 前，不应继续新增治理报告。

从工程路线看，v1140 已经做了重构，v1141 已经做了闭环总账，v1142 已经发布 cadence due list。现在最合理的停止点已经到达。

## 一句话总结

v1142 把当前项目节奏转成可复查的 cadence watch：维护、讲解和证据都新鲜，但模型能力执行已经到期，下一步应先让 Claude review，再决定 v1143 的真实回归执行项。
