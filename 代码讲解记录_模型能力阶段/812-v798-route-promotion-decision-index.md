# v798 route promotion decision index

## 本版目标和边界

v798 是功能版本，接在 v797 route promotion review decision 后面。v797 已经给出了 `accept_bounded_route_promotion`，但后续模块如果直接读取 v797 原始 decision，会反复解析 final decision、active routes、boundary 和 claim。v798 的作用是把这些信息固化成索引，让后续治理模块消费稳定的 route ledger。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe replay。
- 不重新审阅 v796 release packet review。
- 不扩大 `bounded_route_promotion_review_only` 范围。
- 不把 accepted route index 解释成生产模型能力证明。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_decision_index.py`

这是 v798 的核心 builder，提供：

- `locate_route_promotion_review_decision(path)`
- `load_route_promotion_review_decision(path)`
- `build_model_capability_route_promotion_decision_index(...)`
- `resolve_exit_code(report, require_ready_index=...)`

输入可以是一个或多个 v797 decision JSON，也可以是 v797 输出目录。目录输入会自动寻找：

```text
model_capability_route_promotion_review_decision.json
```

核心结构包括：

- `sources`：每个 v797 decision 的状态、最终决策、scope、boundary、claim 和 route entry。
- `entries`：展开后的 route ledger，每条记录对应一个 route。
- `check_rows`：索引构建时的契约检查。
- `summary`：ready 状态、accepted route 数、route ids、boundary 和 claim。

核心 checks 包括：

- `decision_sources_present`
- `accepted_source_present`
- `ready_route_count`
- `blocked_sources_absent`
- `boundary_scoped`
- `review_scope_bounded`

这些 checks 防止 rejected decision、scope 扩大或 boundary 不一致的 route 被写入 accepted index。

### `src/minigpt/model_capability_route_promotion_decision_index_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续模块消费的主证据；CSV 保存 route entries；text 适合 CI 日志；Markdown/HTML 用于人工审阅。HTML 页面展示 accepted route、scope、boundary、claim 和所有 checks。

### `scripts/build_model_capability_route_promotion_decision_index.py`

这是 CLI 入口，支持：

- 一个或多个 decision 输入。
- `--required-boundary`
- `--min-ready-routes`
- `--out-dir`
- `--require-ready-index`
- `--force`

`--require-ready-index` 下，如果索引失败，脚本返回 1。

### `tests/test_model_capability_route_promotion_decision_index.py`

测试覆盖：

- accepted v797 decision 可以构建 ready index。
- final decision 被篡改为 rejected 时 index 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v798 的核心边界：索引只能接收最终 accepted、bounded、tiny pair-probe scoped 的 route promotion decision。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_decision_index.py e\797\解释\model-capability-route-promotion-review-decision --out-dir e\798\解释\model-capability-route-promotion-decision-index --require-ready-index --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_decision_index_ready
failed_count=0
decision_index_ready=True
source_decision_count=1
accepted_route_count=1
route_ids=objective_level_contrast
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
```

运行证据归档在：

- `e/798/解释/说明.md`
- `e/798/解释/model-capability-route-promotion-decision-index/`
- `e/798/图片/v798-model-capability-route-promotion-decision-index.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_decision_index.py src\minigpt\model_capability_route_promotion_decision_index_artifacts.py scripts\build_model_capability_route_promotion_decision_index.py tests\test_model_capability_route_promotion_decision_index.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_decision_index.py tests\test_model_capability_route_promotion_review_decision.py -q -o cache_dir=runs\pytest-cache-v798-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v798 把最终 accepted route promotion decision 变成可复用索引，让后续模型能力治理链路可以消费稳定、可追踪、边界清楚的 route ledger。
