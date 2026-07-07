# v1265 production-excellence A3：artifact schema guard

## 本版目标与边界

v1265 接在 v1264 后面，继续完成 production-excellence A3。v1264 解决的是“能力声明有没有说过头”：一个 handoff、route-promotion 或 publication receipt 是否仍然保持 cached-artifact-only、no-promotion、seed-policy bounded，以及是否有正向和负向 contract test marker。v1265 解决的是另一个更底层的问题：即使声明边界没有变，如果 artifact 的外壳悄悄漂移，字段缺了、类型变了、promotion 字段被改宽，下游读取者仍然会误判。

因此本版新增 artifact schema guard。它不是 JSON Schema 标准库实现，也不引入外部依赖；它是一个针对本项目治理产物的轻量 schema registry 检查器。它读取 committed registry，逐个 artifact 检查 required fields、expected values 和简单 field type。检查失败时 CLI 返回非 0，CI 会阻断。

边界保持清楚：本版不改 experiment card、dataset card、model card 或 publication receipt 的生成语义；不重新训练模型；不修改 cached verdict；不扩张模型质量声明；不迁移旧历史格式。旧的 d/461 model card 只有简化字段，这属于历史兼容事实，不应该被 A3 新 gate 反向要求全量迁移。v1265 保护的是当前 builder 输出形态和一条真实 publication receipt 的 no-promotion envelope。

## 输入与样本选择

`docs/artifact-schema-guard-registry.json` 是本版的事实源。它登记四个 schema：

- `experiment_card_v1`
- `dataset_card_v1`
- `model_card_v1`
- `publication_receipt_v1`

前三个 card schema 使用 v1265 现场生成的当前 builder 样本，路径在 `f/1265/解释/schema-samples/`。这些样本不是科学实验结果，而是 artifact envelope 样本：它们说明当前 card builder 应该输出哪些顶层字段。样本来源仍然来自仓库已有的 d/447 归档 fixture 输入，所以不是凭空手写 JSON。

publication receipt schema 使用真实的 v999 receipt artifact。选择它的原因是：它代表 publication receipt 链的后段产物，包含 `receipt`、`summary`、`interpretation`、`check_rows`，并且明确带有 no-promotion 字段。schema guard 对它检查：

- `summary.granted_use = downstream_governance_lookup_only`
- `summary.promotion_ready = false`
- `summary.approved_for_promotion = false`
- `receipt.granted_use = downstream_governance_lookup_only`
- `receipt.promotion_ready = false`
- `receipt.approved_for_promotion = false`

这和 v1264 的 honest-measurement gate 形成互补：v1264 看 claim boundary 和测试 marker，v1265 看 artifact envelope 和字段形状。

## 核心实现

`src/minigpt/artifact_schema_guard.py` 是核心模块。入口函数 `build_artifact_schema_guard_report()` 接收 registry path 和 project root，输出包含 `status`、`decision`、`summary`、`schemas`、`checks`、`recommendations` 的报告。

检查流程分三层：

1. registry 层：检查 `schema_version=1`、`scope=cards_and_publication_receipts`、`schemas` 非空。
2. schema 层：检查 `schema_id` 非空唯一、`artifact_kind` 存在、`required_fields` 与 `artifact_paths` 非空、`type_checks` 使用已知类型名。
3. artifact 层：确认 artifact path 位于项目内且存在，JSON 可读取为 object，required fields 存在，expected values 相等，type checks 匹配。

字段读取支持 dotted key，例如 `summary.promotion_ready`。这让 registry 可以精确表达 receipt 内部边界，而不是只能检查顶层字段。简单类型名包括 `dict`、`list`、`str`、`int`、`float`、`bool`、`none`。这里不追求复杂 schema 语言，因为本项目的风险重点不是任意嵌套校验，而是防止关键 envelope 字段静默消失或放宽。

`scripts/check_artifact_schema_guard.py` 是 CLI 包装，默认读取 `docs/artifact-schema-guard-registry.json`，默认输出到 `runs/artifact-schema-guard`。它打印 `status`、`decision`、`schema_count`、`artifact_count`、`failed_check_count` 和输出路径。CI 中不需要额外参数，失败即返回 1。

## 测试覆盖

`tests/test_artifact_schema_guard.py` 覆盖四个关键场景。第一，当前 registry 必须通过，并确认 `schema_count=4`、`artifact_count=4`、`failed_check_count=0`。第二，向 experiment card schema 追加不存在的 required field 后必须失败，证明 required fields 不是摆设。第三，把 publication receipt schema 的 `summary.promotion_ready` 期望值改成 true 后必须失败，证明 no-promotion envelope 被机械保护。第四，输出和 CLI wiring 必须正常，JSON/CSV/Markdown/HTML 都要生成。

这组测试的意义在于防止两类退化：一类是 artifact 形状漂移但 CI 不知道；另一类是 registry 自己写坏了却还能通过。尤其是 promotion widening 负向测试，它和 A3 的诚实测量目标直接相关：publication receipt 可以作为治理 lookup 证据，但不能静默变成 promotion 许可。

## CI 与工程健康接入

`.github/workflows/ci.yml` 新增 `Artifact schema guard`，位置在 `Model capability honest measurement gate` 之后、archive portability 和 coverage 之前。这个顺序表达了 A3 的两层含义：先检查声明边界，再检查 artifact envelope，然后才进入后续 portability、normalization 和 coverage。

`src/minigpt/ci_workflow_hygiene_policy.py` 新增 required command fragment 和两条顺序规则：

- `artifact_schema_guard_after_honest_measurement`
- `artifact_schema_guard_before_coverage`

因此，如果后续有人删掉 schema guard，或把它放到 coverage 后面，CI workflow hygiene 会失败。v1265 聚焦运行显示 `check_count=51`、`failed_check_count=0`、`required_order_count=27`、`order_violation_count=0`。

`scripts/_bootstrap.py` 和 `scripts/_engineering_health.py` 也把它加入本地 health。现在 `python -B scripts/check_engineering_health.py` 会依次跑 source encoding、docs readability、CI hygiene、static analysis、type analysis、honest measurement、artifact schema guard、normalization guard。

## 静态与类型范围

本版把 `scripts/check_artifact_schema_guard.py` 与 `src/minigpt/artifact_schema_guard.py` 加入 ruff strict paths，并把二者加入 `docs/static-analysis/mypy-scope.json`。`scope_floor` 从 10 提升到 12。这个调整很关键：A3 新增的是治理门，本身不能逃离 A1/A2 建立的工程门。聚焦 mypy run 显示 `target_count=12`、`diagnostic_count=0`、`scope_issue_count=0`。

## 运行证据

核心报告位于 `f/1265/解释/artifact-schema-guard/`：

- `artifact_schema_guard.json`
- `artifact_schema_guard.csv`
- `artifact_schema_guard.md`
- `artifact_schema_guard.html`

本版的 schema samples 位于 `f/1265/解释/schema-samples/`，包括 experiment card、dataset card、model card 三类当前输出。Playwright MCP 打开 HTML 报告后，snapshot 显示 `Status pass`、`Decision continue_with_artifact_schema_guard`、`Schemas 4`、`Artifacts 4`、`Checks 125`、`Failures 0`。截图保存为 `f/1265/图片/artifact-schema-guard-v1265.png`。

覆盖率证据同步归档在 `f/1265/解释/test-coverage/`。本版完整覆盖率门显示 `line_coverage_percent=90.99`、`fail_under=88.98`、`status=pass`。这里的覆盖率不是为了证明 artifact schema guard 本身已经覆盖所有历史格式，而是证明新增模块、CLI、CI wiring 与既有测试体系一起运行时没有拉低项目当前 floor。它和 schema guard 报告的关系是互补的：schema guard 报告证明产物形状可机械复核，coverage 报告证明本版新增治理入口没有以牺牲测试纪律为代价。

## 一句话总结

v1265 把 card 和 publication receipt 的输出形状变成 CI 可失败的 schema guard，使 A3 从“声明边界诚实”进一步推进到“artifact envelope 也不能静默漂移”。
