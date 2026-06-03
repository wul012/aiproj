# v804 route promotion bounded benchmark suite review

## 本版目标和边界

v804 是功能版本，接在 v803 route promotion bounded benchmark suite 后面。v803 已经生成 5 个 prompt cases；v804 的作用是先审核 suite 自身，不让后续 dry-run 拿到 expected terms 缺失、prompt 重复或 boundary 变宽的 suite。

本版不做：

- 不运行模型生成。
- 不训练 checkpoint。
- 不计算真实通过率。
- 不修改 v803 suite。
- 不把 review 结果当作模型质量提升证明。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_benchmark_suite_review.py`

这是 v804 的核心 reviewer，提供：

- `locate_route_promotion_bounded_benchmark_suite(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_benchmark_suite_review(...)`
- `resolve_exit_code(report, require_ready_review=...)`

输入是 v803 bounded benchmark suite。目录输入会自动寻找：

```text
model_capability_route_promotion_bounded_benchmark_suite.json
```

核心 checks 包括：

- `suite_passed`
- `suite_decision_ready`
- `suite_ready`
- `case_count`
- `expected_terms`
- `case_reviews_clean`
- `prompt_uniqueness`
- `next_artifact_review`

`case_reviews_clean` 来自逐 case 审核，每个 case 必须 prompt 存在、expected terms 正好是 `fixed/loss`，且不能命中禁止的 heldout-like prompt surface。

### `case_reviews`

每个 case review 包含：

- `case_id`
- `prompt_present`
- `expected_terms`
- `expected_term_count`
- `has_fixed_loss`
- `forbidden_surface_hits`
- `review_status`

这让后续 dry-run 前能直接看到每个 prompt case 的执行资格。

### `src/minigpt/model_capability_route_promotion_bounded_benchmark_suite_review_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存 case reviews；Markdown/HTML 展示 approved 状态和逐 case review；JSON 是后续 dry-run builder 消费的结构化证据。

### `scripts/review_model_capability_route_promotion_bounded_benchmark_suite.py`

这是 CLI 入口，支持：

- `--benchmark-suite`
- `--out-dir`
- `--require-ready-review`
- `--force`

`--require-ready-review` 下，如果 review fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_bounded_benchmark_suite_review.py`

测试覆盖：

- ready suite 可以通过 review。
- expected terms 不完整时 review 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v804 的核心边界：dry-run 只能消费 expected terms 完整、prompt review 干净的 bounded suite。

## 真实运行证据

本版运行：

```powershell
python -B scripts\review_model_capability_route_promotion_bounded_benchmark_suite.py --benchmark-suite e\803\解释\model-capability-route-promotion-bounded-benchmark-suite --out-dir e\804\解释\model-capability-route-promotion-bounded-benchmark-suite-review --require-ready-review --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_benchmark_suite_review_ready
failed_count=0
bounded_benchmark_suite_review_ready=True
approved_for_execution=True
case_count=5
passed_case_review_count=5
next_step=run_bounded_route_promotion_benchmark_dry_run
```

运行证据归档在：

- `e/804/解释/说明.md`
- `e/804/解释/model-capability-route-promotion-bounded-benchmark-suite-review/`
- `e/804/图片/v804-model-capability-route-promotion-bounded-benchmark-suite-review.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_bounded_benchmark_suite_review.py src\minigpt\model_capability_route_promotion_bounded_benchmark_suite_review_artifacts.py scripts\review_model_capability_route_promotion_bounded_benchmark_suite.py tests\test_model_capability_route_promotion_bounded_benchmark_suite_review.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_bounded_benchmark_suite_review.py tests\test_model_capability_route_promotion_bounded_benchmark_suite.py -q -o cache_dir=runs\pytest-cache-v804-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v804 把 bounded benchmark suite 推进为 approved-for-execution 状态，为下一步 dry-run replay 提供了干净、可审阅的 suite review。
