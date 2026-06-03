# v802 route promotion consumer plan

## 本版目标和边界

v802 是功能版本，接在 v801 route promotion downstream guard 后面。v801 已经证明 `bounded-benchmark-planner` 可以在 `bounded_model_capability_governance_only` 范围内消费 `objective_level_contrast` route；v802 的作用是把这个准入结论变成下一步 benchmark suite 的执行计划。

本版解决的问题是：下游模块不能只拿到 `access_allowed=True` 就开始自由发挥。v802 明确 route、consumer、scope、boundary、required inputs、plan steps、non-goals 和 proposed next artifact，让后续 suite 构建有稳定输入。

本版不做：

- 不重新训练 checkpoint。
- 不执行 benchmark。
- 不重放模型生成。
- 不扩大模型质量声明。
- 不允许 production release scope。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_consumer_plan.py`

这是 v802 的核心 builder，提供：

- `locate_route_promotion_downstream_guard(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_consumer_plan(...)`
- `resolve_exit_code(report, require_ready_plan=...)`

输入是 v801 downstream guard。目录输入会自动寻找：

```text
model_capability_route_promotion_downstream_guard.json
```

核心 checks 包括：

- `guard_passed`
- `guard_decision_allowed`
- `access_allowed`
- `objective_route_selected`
- `bounded_scope`
- `boundary_scoped`
- `next_step_matches`
- `claim_bounded`
- `consumer_named`

其中 `objective_route_selected` 暂时把本计划限定在 `objective_level_contrast`，因为这是当前 route promotion 链路实际验证过的 route；`bounded_scope` 和 `boundary_scoped` 防止计划变成生产发布计划。

### `consumer_plan`

核心输出结构包括：

- `ready`
- `route_id`
- `consumer_name`
- `allowed_scope`
- `boundary`
- `model_quality_claim`
- `proposed_next_artifact`
- `execution_phase`
- `required_inputs`
- `plan_steps`
- `non_goals`

`proposed_next_artifact=model_capability_route_promotion_bounded_benchmark_suite` 是 v802 最重要的后续锚点。

### `src/minigpt/model_capability_route_promotion_consumer_plan_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存 plan steps；Markdown/HTML 展示 plan steps 和 checks；JSON 是后续 suite builder 消费的结构化证据。

### `scripts/build_model_capability_route_promotion_consumer_plan.py`

这是 CLI 入口，支持：

- `--downstream-guard`
- `--required-boundary`
- `--out-dir`
- `--require-ready-plan`
- `--force`

`--require-ready-plan` 下，如果 plan fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_consumer_plan.py`

测试覆盖：

- allowed guard 可以生成 ready consumer plan。
- guard 被改成 not allowed 时 plan 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v802 的核心边界：consumer plan 只能从明确 allowed 的 bounded guard 构建。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_consumer_plan.py --downstream-guard e\801\解释\model-capability-route-promotion-downstream-guard --out-dir e\802\解释\model-capability-route-promotion-consumer-plan --require-ready-plan --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_consumer_plan_ready
failed_count=0
consumer_plan_ready=True
route_id=objective_level_contrast
consumer_name=bounded-benchmark-planner
allowed_scope=bounded_model_capability_governance_only
proposed_next_artifact=model_capability_route_promotion_bounded_benchmark_suite
plan_step_count=5
```

运行证据归档在：

- `e/802/解释/说明.md`
- `e/802/解释/model-capability-route-promotion-consumer-plan/`
- `e/802/图片/v802-model-capability-route-promotion-consumer-plan.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_consumer_plan.py src\minigpt\model_capability_route_promotion_consumer_plan_artifacts.py scripts\build_model_capability_route_promotion_consumer_plan.py tests\test_model_capability_route_promotion_consumer_plan.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_consumer_plan.py tests\test_model_capability_route_promotion_downstream_guard.py -q -o cache_dir=runs\pytest-cache-v802-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v802 把 downstream guard 的允许结论转成 bounded consumer plan，让下一步 benchmark suite 能在明确边界和非目标下构建。
