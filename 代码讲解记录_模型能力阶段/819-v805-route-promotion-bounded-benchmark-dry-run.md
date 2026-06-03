# v805 route promotion bounded benchmark dry-run

## 本版目标和边界

v805 是功能版本，接在 v804 bounded benchmark suite review 后面。v804 已经批准 suite 可以执行；v805 不急着跑真实模型，而是先用受控 continuation 验证评分器：正样例应当通过，负控必须失败。

本版不做：

- 不加载 checkpoint。
- 不运行真实生成。
- 不声明模型能力提升。
- 不修改 v803 suite。
- 不扩大 fixed/loss scoring contract。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_bounded_benchmark_dry_run.py`

这是 v805 的核心 dry-run builder，提供：

- `locate_route_promotion_bounded_benchmark_suite(path)`
- `locate_route_promotion_bounded_benchmark_suite_review(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_bounded_benchmark_dry_run(...)`
- `resolve_exit_code(report, require_pass=...)`

输入是 v803 benchmark suite 和 v804 suite review。目录输入会自动寻找：

```text
model_capability_route_promotion_bounded_benchmark_suite.json
model_capability_route_promotion_bounded_benchmark_suite_review.json
```

核心 checks 包括：

- `suite_review_passed`
- `suite_review_approved`
- `benchmark_suite_passed`
- `expected_terms_fixed_loss`
- `dry_rows_present`
- `positive_rows_pass`
- `negative_control_fails`

其中 `negative_control_fails` 是本版关键保护：如果缺少 `loss` 的 continuation 也能通过，说明评分器有问题。

### `dry_run_rows`

每个 dry-run row 包含：

- `case_id`
- `continuation`
- `expected_terms`
- `hit_terms`
- `missed_terms`
- `case_pass`

本版正样例 continuation 是 `fixed loss`，负控是 `fixed only`。

### `src/minigpt/model_capability_route_promotion_bounded_benchmark_dry_run_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存 dry-run rows；Markdown/HTML 展示 pass/hit/missed terms；JSON 是后续真实 replay 前的评分器验证证据。

### `scripts/run_model_capability_route_promotion_bounded_benchmark_dry_run.py`

这是 CLI 入口，支持：

- `--benchmark-suite`
- `--suite-review`
- `--out-dir`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 dry-run fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_bounded_benchmark_dry_run.py`

测试覆盖：

- 正样例 `fixed loss` 让所有 suite cases 通过。
- 正样例缺少 `loss` 时 dry-run 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v805 的核心边界：评分器必须能区分完整 fixed/loss 命中与缺项 continuation。

## 真实运行证据

本版运行：

```powershell
python -B scripts\run_model_capability_route_promotion_bounded_benchmark_dry_run.py --benchmark-suite e\803\解释\model-capability-route-promotion-bounded-benchmark-suite --suite-review e\804\解释\model-capability-route-promotion-bounded-benchmark-suite-review --out-dir e\805\解释\model-capability-route-promotion-bounded-benchmark-dry-run --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_bounded_benchmark_dry_run_passed
failed_count=0
bounded_benchmark_dry_run_ready=True
case_count=5
passed_case_count=5
negative_control_passed=False
next_step=run_bounded_route_promotion_real_replay
```

运行证据归档在：

- `e/805/解释/说明.md`
- `e/805/解释/model-capability-route-promotion-bounded-benchmark-dry-run/`
- `e/805/图片/v805-model-capability-route-promotion-bounded-benchmark-dry-run.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_bounded_benchmark_dry_run.py src\minigpt\model_capability_route_promotion_bounded_benchmark_dry_run_artifacts.py scripts\run_model_capability_route_promotion_bounded_benchmark_dry_run.py tests\test_model_capability_route_promotion_bounded_benchmark_dry_run.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_bounded_benchmark_dry_run.py tests\test_model_capability_route_promotion_bounded_benchmark_suite_review.py -q -o cache_dir=runs\pytest-cache-v805-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v805 把 bounded benchmark suite 推进到 scorer dry-run 通过状态，确认 fixed/loss 评分契约能正确识别正样例和负控。
