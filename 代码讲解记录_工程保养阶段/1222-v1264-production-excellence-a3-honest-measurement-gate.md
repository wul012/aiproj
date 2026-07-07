# v1264 production-excellence A3：模型能力声明的 honest-measurement gate

## 本版目标与边界

v1264 是 aiproj production-excellence A-track 的 A3 起步版本。前面的 v1261、v1262、v1263 分别把 ruff、mypy、coverage 变成了工程质量门；它们回答的是“代码是否干净”“类型范围是否受控”“测试覆盖是否低于 floor”。A3 要回答的问题不一样：当项目说一个模型能力、一个 route promotion、一个 handoff 或一个 publication receipt “通过”时，这个通过到底意味着什么？它是模型真的可生产使用，还是只是某个 toy-scale、cached-artifact、lookup-only 的治理证据？如果这个边界只写在人的记忆里，版本推进久了以后，很容易把 `status=pass` 误读为“模型生产能力通过”。

本版的目标就是把这种边界变成机械检查：新增 `model capability honest measurement registry`，把已经有 contract-check 保护的代表性能力治理族登记进去，然后由脚本检查每个登记项是否满足 A3 的诚实测量规则。这里的“诚实”不是主观评价，而是若干会失败的条件：必须是 cached-artifact-only；必须 no-training-required；不能带 promotion authority；单种子随机证据不能伪装成稳定能力；必须有真实存在的源 artifact；必须有正向 contract test，也必须有负向、篡改或缺源 test marker。

边界同样重要。本版不重新训练模型，不改变任何科学线的 cached experiment verdict，不修改 `decide()` 阈值，不补写新的模型能力结论，也不把代表性 registry 扩张成“全历史 1000+ 版本已经全部覆盖”。它只在工程/治理线建立一个入口：以后当某个能力治理族要被当作 production-excellence 证据引用时，应先进入 registry，再通过同一套 gate。换句话说，v1264 不是模型能力提升版，而是“别把治理证据说过头”的防线。

## 前置路线

本版直接承接 `docs/production-excellence-aiproj-brief.md` 的 A3：

1. 机制化 house rules：能力版本族要能从缓存证据或 contract test 重新证明，不应该靠重新训练。
2. seed policy：随机指标如果是单种子，只能标注为 exploratory/no-promotion；要说 seed-stable，必须有 multi-seed 证据。
3. artifact schema guard：报告、卡片、receipt 不应在字段上静默漂移。

在 v1264 之前，项目已经有不少单点 contract check，例如 baseline candidate handoff 的 v434 check，以及 route-promotion release readiness 的 summary/index/review 检查链。但这些能力是散落的：每个模块自己知道自己在保护什么，CI 没有一个统一入口去问“这些能力声明是不是仍然诚实”。v1264 的改动就是把散落的规则收束为一个 registry 和一个 CI-backed gate。

## 关键新增文件

`docs/model-capability-honest-measurement-registry.json` 是本版最关键的输入文件。它不是普通说明文档，而是检查器读取的事实源。当前登记两个代表性 family：

- `baseline-candidate-handoff-v433-v434`
- `route-promotion-release-readiness-v1258-v1259`

第一个 family 代表 baseline candidate eval loop 到 handoff 的交接链。它的声明边界是 `not_claimed_no_promotion`，`model_quality_claim` 固定为 `not_claimed`，`seed_evidence_mode` 是 `single_seed`，所以必须带有 `exploratory_no_promotion` 这样的单种子标签。它引用 `d/433` 的 handoff artifact 和 `d/434` 的 handoff check artifact，并要求测试里存在 `test_valid_handoff_check_passes_when_candidate_is_rejected`、`test_tampered_next_baseline_source_fails`、`test_missing_source_loop_report_fails` 等 marker。这组 marker 的意义是：不是只证明 happy path 可以通过，还要证明篡改 `next_baseline` 或删除源 loop report 时会失败。

第二个 family 代表 route-promotion release readiness receipt index/review 链。它允许的 claim 是 `seed_stable_pair_probe_route_accepted`，但 promotion 仍然必须是 false，authority 仍然是 none。这个 family 是 multi-seed 边界，`seed_count=3`，所以它可以比单种子 handoff 多说一点，但仍然只能说 bounded governance / lookup only，不能说 production model quality。它引用 `f/1258` 的 receipt index 和 `f/1259` 的 receipt index review，并检查 review artifact 中 `status=pass`、`failed_count=0`、`promotion_ready=false`、`approved_for_promotion=false`。测试 marker 则覆盖 ready summary、rebuildable index、missing source、claim widening、tampered route entry 等情况。

`docs/model-capability-honest-measurement-policy.md` 是 registry 背后的文字规则。它写清楚为什么要区分 cached-artifact check 与 retraining，为什么单种子随机证据只能 exploratory，为什么 receipt/handoff/route-promotion artifact 不能自己拥有 promotion authority。这份文档服务读者和评审；真正会失败的是 registry checker。

`src/minigpt/model_capability_honest_measurement.py` 是核心实现。它的入口函数是 `build_model_capability_honest_measurement_report()`，输入 registry 路径和 project root，输出一个报告字典。报告包含：

- `status`
- `decision`
- `registry_path`
- `summary`
- `families`
- `checks`
- `recommendations`

其中 `summary` 聚合 family 数量、check 数量、失败数量、cached-artifact-only family 数、no-training-required family 数、multi-seed family 数和 single-seed family 数。`checks` 是逐条机械检查，字段包括 `family_id`、`check_id`、`expected`、`actual`、`status`、`detail`。这种结构和现有 CI hygiene、type analysis、coverage report 的风格一致：不是只给一句 pass/fail，而是让失败项可以定位到具体 family 和具体规则。

`scripts/check_model_capability_honest_measurement.py` 是 CLI 包装。它负责解析参数、调用核心 builder、写输出，并打印摘要。默认 CI 路径是：

```powershell
python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement
```

它会输出 JSON、CSV、Markdown、HTML 四种格式。JSON 给机器消费，CSV 便于快速筛失败项，Markdown 便于日志审查，HTML 便于截图归档。

`tests/test_model_capability_honest_measurement.py` 是本版的核心测试。它覆盖五类场景：当前 registry 通过；单种子 stochastic family 如果把 label 改成 `seed_stable_claim` 会失败；如果登记了不存在的 negative marker 会失败；如果 source artifact 路径不存在会失败；输出和 CLI 正常工作。这里的负向测试很重要，因为 A3 gate 的价值不是“能生成一个 report”，而是后续有人改宽 claim、删掉缺源测试、搬丢 artifact 时，它会拦住。

## 核心流程

检查器首先读取 registry。registry 本身可以是项目内路径，也可以是测试中临时复制出来的外部文件；但 registry 里引用的 artifact 和 test module 必须解析到项目根目录内。这个设计是本版测试驱动出来的：临时 registry 用来模拟篡改场景，不应该被“必须在项目根内”的路径规则误杀；但真正受检的 source artifact 和 test module 必须留在项目内，避免 registry 指向任意外部文件。

读取 registry 后，`_build_checks()` 先做全局检查：`schema_version=1`、`scope=engineering_governance_lane_only`、family 列表非空。之后逐个 family 进入 `_family_checks()`。每个 family 会接受几组检查：

1. 身份与边界检查：`family_id` 非空且唯一，`cached_artifact_only=true`，`no_training_required=true`，`promotion_authority=none`，`promotion_ready_expected=false`。
2. seed policy 检查：`seed_evidence_mode` 必须在允许集合内。如果是 stochastic + multi-seed，`seed_count` 至少为 2；如果是 stochastic + single-seed，`single_seed_label` 必须包含 `exploratory`、`not_claimed` 或 `no_promotion` 这类边界词。
3. 路径检查：`source_artifacts` 和 `contract_test_modules` 都必须是非空 list，每个路径都必须存在并且位于项目根内。
4. 测试 marker 检查：把 contract test module 读成文本，逐个查找 positive 和 negative marker。这样可以防止测试文件存在但关键负向测试被删掉。
5. artifact guard 检查：读取登记的 JSON artifact，确认 required fields 存在，并确认 expected values 没有漂移。例如 v1259 review artifact 必须保留 `promotion_ready=false` 和 `approved_for_promotion=false`。

最后，失败项数量为 0 时，报告 `status=pass`、`decision=continue_with_honest_measurement_gate`；否则为 `status=fail`、`decision=repair_honest_measurement_gate`。这让 CI 能以一个明确的退出码阻止 claim boundary 漂移。

## CI 与工程健康接入

`.github/workflows/ci.yml` 新增了 `Model capability honest measurement gate`，放在 `Scoped type analysis gate` 之后、`Archived path portability check` 之前，当然也在 coverage 之前。顺序选择是有意的：如果能力声明边界已经坏了，应该用一个小而聚焦的 gate 先失败，不必等全量 coverage 跑完才暴露问题。

`src/minigpt/ci_workflow_hygiene_policy.py` 同步加入 required command fragment 和两条 order rule：

- `model_capability_honest_measurement_after_type_analysis`
- `model_capability_honest_measurement_before_coverage`

这意味着未来如果有人从 CI 删除该 gate，或把它放到 coverage 后面，`scripts/check_ci_workflow_hygiene.py` 会失败。v1264 的 real hygiene run 显示 `check_count=48`、`failed_check_count=0`、`required_order_count=25`、`order_violation_count=0`。

`scripts/_bootstrap.py` 和 `scripts/_engineering_health.py` 也接入了新 entrypoint。这样本地 `python -B scripts/check_engineering_health.py` 会一起跑 honest-measurement gate，而不是只在 GitHub Actions 上才知道它存在。`tests/test_engineering_health.py` 更新了顺序断言，确认新 gate 的输出目录是 `runs/engineering-health/model-capability-honest-measurement`。

## 静态与类型门的加固

因为 v1264 新增的是一个工程质量门，它本身也必须被质量门保护。因此本版把以下文件加入 ruff strict paths：

- `scripts/check_model_capability_honest_measurement.py`
- `src/minigpt/model_capability_honest_measurement.py`

同时把它们加入 `docs/static-analysis/mypy-scope.json`，并把 `scope_floor` 从 8 提升到 10。这个细节不应该跳过：如果只是把 target list 增加到 10，却把 floor 留在 8，那么未来有人删掉两个新增 target，mypy scope 仍可能通过。v1264 把 floor 同步上调，符合 ratchet 只能收紧不能静默放松的原则。

第一次运行 mypy 时抓到了一个真实的小问题：输出 writer 用 lambda 直接返回了 `Path.write_text()` 的整数返回值，而 `write_output_bundle` 期望 writer 返回 `None`。这不是运行时大 bug，但严格类型门指出了接口契约不一致。本版改成显式 `write_markdown()` 和 `write_html()` 函数，返回值自然为 `None`。这正好说明 A1/A3 的组合是有意义的：新 gate 不是“自己检查别人”，它也要接受既有工程门约束。

## 运行证据

本版核心 evidence 存在 `f/1264/解释/model-capability-honest-measurement/`，包括：

- `model_capability_honest_measurement.json`
- `model_capability_honest_measurement.csv`
- `model_capability_honest_measurement.md`
- `model_capability_honest_measurement.html`

核心运行结果是：

```text
status=pass
decision=continue_with_honest_measurement_gate
family_count=2
failed_check_count=0
```

Playwright MCP 打开 HTML 报告后，snapshot 确认页面上有：

- `Status: pass`
- `Decision: continue_with_honest_measurement_gate`
- `Families: 2`
- `Checks: 68`
- `Failures: 0`
- `Single-seed: 1`

截图保存为 `f/1264/图片/honest-measurement-v1264.png`。这个截图证明的不是模型能力本身，而是报告页面可读、关键字段可见、HTML 输出没有空白或渲染失败。

## 测试覆盖

新增测试 `tests/test_model_capability_honest_measurement.py` 覆盖了 A3 gate 的主要失败模式。`test_current_registry_passes` 保护当前 registry；`test_single_seed_stochastic_claim_must_be_exploratory` 防止单种子 stochastic 证据被说成稳定 claim；`test_missing_negative_marker_fails` 防止负向测试消失；`test_missing_source_artifact_fails` 防止 artifact 路径丢失；`test_outputs_and_cli_are_wired` 保护输出格式和 CLI exit code。

除新增测试外，v1264 还更新并验证了：

- `tests/test_ci_workflow.py`：新 gate 必须出现在 CI hygiene 的 required command 和 order checks 中。
- `tests/test_engineering_health.py`：本地 aggregate health 包含新 gate。
- `tests/test_project_configuration.py`：真实 CI 和 START_HERE 都引用新 gate。
- `tests/test_type_analysis.py`：mypy scope 机制本身保持正常。

这些测试不是互相重复，而是在不同层面保护同一件事：真实 CI 有该 gate；CI hygiene 知道该 gate；本地 health 能跑该 gate；文档入口告诉维护者怎么跑；类型/静态门保护 gate 自身。

## 本版价值

v1264 的价值在于给“模型能力治理”补了一个总开关。过去每个能力版本都可以很认真地写自己的报告，但读者仍要靠上下文判断：这个 pass 是不是意味着可以 promotion？这个 seed-stable 是不是多种子？这个 receipt 是不是 lookup-only？现在，至少对于进入 registry 的 family，这些问题会被机械检查回答。

这也回应了用户之前关于“前 1000 多版是否冗余”的疑问：历史版本的价值不在于每个 report 都单独成为产品功能，而在于沉淀出一组可以被后续 gate 固化的工程规则。v1264 正是在做这种固化：把散落在 v433/v434、v1258/v1259 等版本里的诚实边界抽成统一检查入口。它没有否定历史版本，反而开始让历史版本变成可复用的证据库。

## 一句话总结

v1264 把“模型能力声明不能说过头”从人工自觉推进为 CI 可失败的 honest-measurement gate，为后续 A3 artifact schema guard 和 A5 docs honesty closeout 打下了机械基础。
