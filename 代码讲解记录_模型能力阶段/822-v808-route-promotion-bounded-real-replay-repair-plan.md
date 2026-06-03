# v808 route promotion bounded real replay repair plan

## 本版目标和边界

v808 接在 v807 bounded real replay review 后面。v807 已经说明真实 replay 不能 promotion，但可以进入 repair plan。v808 的目标是把失败 case 转成明确 repair tasks，形成后续 repair seed 的输入。

本版不做：

- 不训练新模型。
- 不修改 v806 replay rows。
- 不把 repair plan 当作模型能力提升。
- 不新增通用问答、摘要或生产推理能力。

## 输入输出

输入：

```text
e/807/解释/model-capability-route-promotion-bounded-real-replay-review/model_capability_route_promotion_bounded_real_replay_review.json
```

输出：

```text
model_capability_route_promotion_bounded_real_replay_repair_plan.json
model_capability_route_promotion_bounded_real_replay_repair_plan.csv
model_capability_route_promotion_bounded_real_replay_repair_plan.txt
model_capability_route_promotion_bounded_real_replay_repair_plan.md
model_capability_route_promotion_bounded_real_replay_repair_plan.html
```

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_plan.py`

这是核心 plan builder，提供：

- `locate_route_promotion_bounded_real_replay_review(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_real_replay_repair_plan(...)`
- `resolve_exit_code(report, require_plan_ready=...)`

它从 v807 的 `case_reviews` 中挑出 `case_pass != True` 的 rows，逐个生成 repair task。

### `repair_tasks`

每个 repair task 包含：

- `task_id`
- `case_id`
- `repair_type`
- `diagnosis`
- `hit_terms`
- `missed_terms`
- `surface_probe`
- `training_focus`
- `required_success_condition`
- `recommended_action`

repair 类型包括：

- `missing_term_retention_repair`
- `prompt_to_required_terms_bridge_repair`
- `general_required_terms_repair`

如果 continuation 中出现未知 token surface，task 会带上 `unknown_token_surface_probe`，提醒下一步 seed 不只看 required terms，还要关注 tokenizer/提示表面。

### `repair_plan`

plan 层记录：

- `ready`
- `task_count`
- `source_pass_rate`
- `target_pass_rate`
- `required_terms`
- `non_goals`
- `proposed_next_artifact`
- `next_step`

本版真实结果是：

```text
task_count=3
source_pass_rate=0.4
target_pass_rate=1.0
proposed_next_artifact=model_capability_route_promotion_bounded_real_replay_repair_seed
```

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_plan_artifacts.py`

这是 artifact writer，输出 JSON/CSV/text/Markdown/HTML。CSV 是后续 seed builder 最容易消费的格式；HTML 用于人工确认每个 failed case 的 repair type 和 training focus。

### `scripts/build_model_capability_route_promotion_bounded_real_replay_repair_plan.py`

CLI 支持：

- `--real-replay-review`
- `--out-dir`
- `--require-plan-ready`
- `--force`

`--require-plan-ready` 下，如果 v807 review 不是 repair-ready，脚本返回 1。

## 真实运行证据

本版实际运行：

```powershell
python -B scripts/build_model_capability_route_promotion_bounded_real_replay_repair_plan.py --real-replay-review e/807/解释/model-capability-route-promotion-bounded-real-replay-review/model_capability_route_promotion_bounded_real_replay_review.json --out-dir e/808/解释/model-capability-route-promotion-bounded-real-replay-repair-plan --require-plan-ready --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_repair_plan_ready
failed_count=0
bounded_real_replay_repair_plan_ready=True
task_count=3
source_pass_rate=0.4
target_pass_rate=1.0
proposed_next_artifact=model_capability_route_promotion_bounded_real_replay_repair_seed
next_step=build_bounded_real_replay_repair_seed
```

## 测试覆盖

测试文件是 `tests/test_model_capability_route_promotion_bounded_real_replay_repair_plan.py`，覆盖：

- failed replay cases 会生成 repair tasks。
- source review 已经 promotion-ready 时，repair plan 必须 fail，避免无意义修复。
- CLI 和 artifact writer 输出 JSON/CSV/text/Markdown/HTML。

本版运行：

```powershell
python -m py_compile src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_plan.py src/minigpt/model_capability_route_promotion_bounded_real_replay_repair_plan_artifacts.py scripts/build_model_capability_route_promotion_bounded_real_replay_repair_plan.py tests/test_model_capability_route_promotion_bounded_real_replay_repair_plan.py
python -m pytest tests/test_model_capability_route_promotion_bounded_real_replay_review.py tests/test_model_capability_route_promotion_bounded_real_replay_repair_plan.py -q -o cache_dir=runs/pytest-cache-v808-focused
```

结果：

- focused tests: `7 passed`

## 截图和归档

运行证据归档在：

- `e/808/解释/说明.md`
- `e/808/解释/model-capability-route-promotion-bounded-real-replay-repair-plan/`
- `e/808/图片/v808-bounded-real-replay-repair-plan-html.png`

Playwright MCP 快照确认 HTML 页面展示：

- `Ready: True`
- `Tasks: 3`
- `Source pass: 0.4`
- `Next: build_bounded_real_replay_repair_seed`

## 一句话总结

v808 把真实 replay 的 3 个失败 case 转成可执行 bounded repair tasks，为下一步生成 repair seed 打下基础。
