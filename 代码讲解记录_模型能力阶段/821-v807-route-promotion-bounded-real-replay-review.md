# v807 route promotion bounded real replay review

## 本版目标和边界

v807 接在 v806 bounded real replay 后面。v806 已经加载真实 checkpoint 执行 5 个 prompt cases，结果是 `2/5` 通过、`model_route_quality_ready=False`。v807 不再重跑模型，而是把这份真实 replay 结果做成审查报告：哪些 case 通过，哪些 case 部分命中，哪些 case 完全没命中，以及下一步该进入什么 repair 计划。

本版不做：

- 不训练新 checkpoint。
- 不修改 v806 replay 输出。
- 不把 2/5 包装成 promotion ready。
- 不新增更强模型质量声明。
- 不改变 fixed/loss scoring contract。

## 输入输出

输入：

```text
e/806/解释/model-capability-route-promotion-bounded-real-replay/model_capability_route_promotion_bounded_real_replay.json
```

输出：

```text
model_capability_route_promotion_bounded_real_replay_review.json
model_capability_route_promotion_bounded_real_replay_review.csv
model_capability_route_promotion_bounded_real_replay_review.txt
model_capability_route_promotion_bounded_real_replay_review.md
model_capability_route_promotion_bounded_real_replay_review.html
```

JSON 是后续 repair plan 的机器输入；CSV/Markdown/HTML 是人工审查证据。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_review.py`

这是 v807 的核心 review builder，提供：

- `locate_route_promotion_bounded_real_replay(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_real_replay_review(...)`
- `resolve_exit_code(report, require_review_pass=..., require_promotion_ready=...)`

它的核心判断仍然拆成两层：

- `status=pass` 表示 v806 replay evidence 可以被审查。
- `summary.promotion_ready=False` 表示模型还不能被放行。
- `summary.repair_review_ready=True` 表示这份 replay 已经足够支持下一步定向修复。

### `case_reviews`

每个 case review 包含：

- `case_id`
- `case_pass`
- `expected_terms`
- `hit_terms`
- `missed_terms`
- `continuation_chars`
- `unknown_token_surface`
- `diagnosis`
- `severity`
- `recommended_action`

本版诊断类型包括：

- `case_passed`
- `partial_required_terms_generated`
- `no_required_terms_generated`
- 带未知 token 表面的失败会追加 `_with_unknown_token_surface`

这比 v806 只列 hit/missed 更进一步：它开始把失败类型转成 repair action。

### `check_rows`

v807 的 checks 只验证审查输入是否可靠：

- `real_replay_status_passed`
- `real_replay_executed`
- `case_reviews_present`
- `case_count_matches_summary`
- `no_source_execution_failures`

注意：`promotion_ready=False` 不算 check failure。因为本版的职责是审查真实 replay，不是要求模型一定通过。

### `src/minigpt/model_capability_route_promotion_bounded_real_replay_review_artifacts.py`

这是 artifact writer，输出 JSON/CSV/text/Markdown/HTML。

CSV 保存 case 级诊断；HTML 首页直接展示：

```text
Promotion ready=False
Repair ready=True
Passed=2/5
Next=build_bounded_real_replay_repair_plan
```

### `scripts/review_model_capability_route_promotion_bounded_real_replay.py`

CLI 支持：

- `--real-replay`
- `--out-dir`
- `--minimum-pass-rate-for-repair-review`
- `--require-review-pass`
- `--require-promotion-ready`
- `--force`

`--require-review-pass` 用于验证审查链路；`--require-promotion-ready` 用于强制模型全部通过。v807 真实运行只使用前者，因为当前模型并未全部通过。

## 真实运行证据

本版实际运行：

```powershell
python -B scripts/review_model_capability_route_promotion_bounded_real_replay.py --real-replay e/806/解释/model-capability-route-promotion-bounded-real-replay/model_capability_route_promotion_bounded_real_replay.json --out-dir e/807/解释/model-capability-route-promotion-bounded-real-replay-review --require-review-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_real_replay_review_needs_repair
failed_count=0
bounded_real_replay_review_ready=True
promotion_ready=False
repair_review_ready=True
passed_case_count=2
failed_case_count=3
pass_rate=0.4
next_step=build_bounded_real_replay_repair_plan
```

这说明 v807 成功把真实 replay 结果转成审查结论：不 promotion，进入 repair plan。

## 测试覆盖

测试文件是 `tests/test_model_capability_route_promotion_bounded_real_replay_review.py`，覆盖：

- 部分命中 replay 会得到 `review_needs_repair`。
- 全部命中 replay 才会得到 `review_accepted`。
- 源 replay fail 时 review 必须 fail。
- CLI 和 artifact writer 输出 JSON/CSV/text/Markdown/HTML。

本版运行：

```powershell
python -m py_compile src/minigpt/model_capability_route_promotion_bounded_real_replay_review.py src/minigpt/model_capability_route_promotion_bounded_real_replay_review_artifacts.py scripts/review_model_capability_route_promotion_bounded_real_replay.py tests/test_model_capability_route_promotion_bounded_real_replay_review.py
python -m pytest tests/test_model_capability_route_promotion_bounded_real_replay.py tests/test_model_capability_route_promotion_bounded_real_replay_review.py -q -o cache_dir=runs/pytest-cache-v807-focused
```

结果：

- focused tests: `8 passed`

## 截图和归档

运行证据归档在：

- `e/807/解释/说明.md`
- `e/807/解释/model-capability-route-promotion-bounded-real-replay-review/`
- `e/807/图片/v807-bounded-real-replay-review-html.png`

Playwright MCP 快照确认 HTML 页面展示：

- `Promotion ready: False`
- `Repair ready: True`
- `Passed: 2/5`
- `Next: build_bounded_real_replay_repair_plan`

## 一句话总结

v807 把 v806 的真实模型输出缺口转成可执行审查结论：当前不能 promotion，但已经具备进入 bounded real replay repair plan 的证据。
