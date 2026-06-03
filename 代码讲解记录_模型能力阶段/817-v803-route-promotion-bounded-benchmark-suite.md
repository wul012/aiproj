# v803 route promotion bounded benchmark suite

## 本版目标和边界

v803 是功能版本，接在 v802 route promotion consumer plan 后面。v802 只说明下游应该构建 bounded benchmark suite；v803 则真正生成 suite：包含 prompt cases、expected terms、scoring contract 和 guardrails。

本版解决的问题是：前几版已经完成 route promotion 的准入、计划和边界，但还缺“下一步到底评什么”。v803 将 `objective_level_contrast` route 转成 5 个 PromptCase 兼容的 benchmark cases，期望 terms 固定为 `fixed` 和 `loss`。

本版不做：

- 不重新训练 checkpoint。
- 不运行模型生成。
- 不判定模型是否通过 suite。
- 不把 expected-term suite 当成生产模型质量证明。
- 不修改 heldout/training 数据。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_benchmark_suite.py`

这是 v803 的核心 builder，提供：

- `locate_route_promotion_consumer_plan(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_benchmark_suite(...)`
- `resolve_exit_code(report, require_ready_suite=...)`

输入是 v802 consumer plan。目录输入会自动寻找：

```text
model_capability_route_promotion_consumer_plan.json
```

核心 checks 包括：

- `consumer_plan_passed`
- `consumer_plan_ready`
- `route_objective_level_contrast`
- `bounded_scope`
- `next_artifact_matches`
- `plan_steps_present`
- `non_goals_present`

这些 checks 确保 suite 只能从 ready consumer plan 生成，且不能把 next artifact 改成 production release suite。

### `benchmark_suite`

核心输出结构包括：

- `suite_name`
- `suite_version`
- `route_id`
- `consumer_name`
- `allowed_scope`
- `boundary`
- `model_quality_claim`
- `cases`
- `scoring_contract`
- `guardrails`
- `proposed_next_artifact`

`cases` 内部每条都有：

- `case_id`
- `prompt_case`
- `expected_terms`
- `required_term_count`

其中 `prompt_case` 使用项目已有 `PromptCase` dataclass 生成，便于后续与 eval suite 工具衔接。

### `src/minigpt/model_capability_route_promotion_bounded_benchmark_suite_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存 cases；Markdown/HTML 展示 cases 和 checks；JSON 是后续 suite review 或 replay 消费的结构化证据。

### `scripts/build_model_capability_route_promotion_bounded_benchmark_suite.py`

这是 CLI 入口，支持：

- `--consumer-plan`
- `--out-dir`
- `--require-ready-suite`
- `--force`

`--require-ready-suite` 下，如果 suite fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_bounded_benchmark_suite.py`

测试覆盖：

- ready consumer plan 可以生成 ready benchmark suite。
- next artifact 被改成 production release suite 时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v803 的核心边界：suite 是 bounded route benchmark，不是生产发布评估。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_bounded_benchmark_suite.py --consumer-plan e\802\解释\model-capability-route-promotion-consumer-plan --out-dir e\803\解释\model-capability-route-promotion-bounded-benchmark-suite --require-ready-suite --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_benchmark_suite_ready
failed_count=0
bounded_benchmark_suite_ready=True
suite_name=route-promotion-objective-level-contrast-bounded-suite
route_id=objective_level_contrast
case_count=5
expected_terms=fixed,loss
proposed_next_artifact=model_capability_route_promotion_bounded_benchmark_suite_review
```

运行证据归档在：

- `e/803/解释/说明.md`
- `e/803/解释/model-capability-route-promotion-bounded-benchmark-suite/`
- `e/803/图片/v803-model-capability-route-promotion-bounded-benchmark-suite.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_bounded_benchmark_suite.py src\minigpt\model_capability_route_promotion_bounded_benchmark_suite_artifacts.py scripts\build_model_capability_route_promotion_bounded_benchmark_suite.py tests\test_model_capability_route_promotion_bounded_benchmark_suite.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_bounded_benchmark_suite.py tests\test_model_capability_route_promotion_consumer_plan.py -q -o cache_dir=runs\pytest-cache-v803-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v803 把 route promotion consumer plan 推进为具体 bounded benchmark suite，让下一步可以围绕真实 prompt cases 做 review 或 replay。
