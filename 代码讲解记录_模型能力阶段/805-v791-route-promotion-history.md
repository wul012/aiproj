# v791 route promotion history ledger

## 本版目标和边界

v791 是功能版本，不是拆分维护版本。它接在 v790 objective-level contrast promotion manifest 后面，新增 route promotion history ledger：读取一个或多个 promotion manifest，生成可追加、可比较、可被后续 portfolio 或 regression review 消费的模型能力历史记录。

本版解决的问题是：v790 只给出单个 route promotion manifest。如果后续继续推进不同 route、不同 seed 或不同 objective，需要一个稳定 ledger 记录每条 promotion 的 route id、readiness、boundary、claim、seed count 和来源路径。v791 就是这个历史入口。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe replay。
- 不把 v790 写进旧 scorecard `benchmark_history.py`，避免旧模块职责变宽。
- 不把 tiny pair-probe promotion 解释成生产模型质量。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_history.py`

这是 v791 的核心 builder，提供：

- `locate_route_promotion_manifest(path)`
- `read_json_report(path)`
- `load_route_promotion_manifest(path)`
- `build_model_capability_route_promotion_history(...)`
- `resolve_exit_code(report, require_ready_history=...)`

输入可以是 promotion manifest JSON 文件，也可以是 v790 输出目录。目录输入会自动寻找：

```text
model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.json
```

builder 的核心流程是：

1. 加载每个 promotion manifest，并记录 `_source_path`。
2. 从 `manifest.benchmark_history_entry` 提取 route id、status、boundary、claim、seed count、pair-full 强度。
3. 结合顶层 `summary` 和 `source_acceptance_review` 判断该 entry 是否 ready。
4. 汇总 `ready_count`、`blocked_count`、`boundary_mismatch_count`、`model_quality_claim` 等字段。
5. 生成 `readiness_requirement`，让 CLI 可以用 `--require-ready-history` 失败退出。

最关键的 readiness 条件是：

- promotion manifest 顶层 `status=pass`。
- `summary.promotion_manifest_ready=True`。
- `summary.can_feed_benchmark_history=True`。
- `benchmark_history_entry.status=ready`。
- `boundary` 必须等于 `tiny_required_term_pair_probe_only`。

这样 v791 不是盲目收集 manifest，而是保证进入 ledger 的条目仍然保持受限边界。

### `src/minigpt/model_capability_route_promotion_history_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是机器消费主证据；CSV 是 ledger 行；text 是 CLI 摘要；Markdown 和 HTML 用于人工审阅。HTML 页面展示 summary stats、readiness requirement、ledger 表格和 recommendations。

### `scripts/build_model_capability_route_promotion_history.py`

这是 CLI 入口，支持：

- `manifests`
- `--names`
- `--min-ready-entries`
- `--required-boundary`
- `--require-ready-history`
- `--out-dir`
- `--title`
- `--force`

`--require-ready-history` 下，如果 readiness requirement 失败，脚本返回 1。它适合后续接到 CI 或持续实验流水线里。

### `tests/test_model_capability_route_promotion_history.py`

测试覆盖：

- 从 ready promotion manifest 构建 history ledger 能通过。
- boundary 被改成 `production_model_quality` 时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v791 的核心契约：route promotion history 只能接纳边界一致、可消费的 promotion manifest。

## Ledger 数据结构

每个 entry 包含：

- `name`
- `source_manifest_path`
- `source_acceptance_review_path`
- `source_seed_stability_rollup_path`
- `route_id`
- `route_status`
- `history_entry_status`
- `promotion_readiness`
- `boundary`
- `boundary_matches`
- `model_quality_claim`
- `seed_count`
- `min_pair_full_count`
- `pair_full_strength_spread`

其中 `promotion_readiness=ready` 只说明该条 route promotion 可以进入模型能力历史，不说明模型能力已达到生产级。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_history.py e\790\解释\model-capability-required-term-pair-readiness-objective-level-contrast-promotion-manifest --names "objective-level contrast v790" --out-dir e\791\解释\model-capability-route-promotion-history --require-ready-history --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_history_ready
entry_count=1
ready_count=1
blocked_count=0
boundary_mismatch_count=0
model_quality_claim=seed_stable_pair_probe_route_accepted
readiness_requirement_status=pass
```

运行证据归档在：

- `e/791/解释/说明.md`
- `e/791/解释/model-capability-route-promotion-history/`
- `e/791/图片/v791-model-capability-route-promotion-history.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_history.py src\minigpt\model_capability_route_promotion_history_artifacts.py scripts\build_model_capability_route_promotion_history.py tests\test_model_capability_route_promotion_history.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_history.py tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py -q -o cache_dir=runs\pytest-cache-v791-focused
```

结果：

- focused tests: `7 passed`

## 一句话总结

v791 把 v790 的单个 promotion manifest 推进为 route promotion history ledger，让模型能力路线从“单点 promotion 证据”变成“可持续追踪和后续消费的历史记录”。
