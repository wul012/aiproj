# v801 route promotion downstream guard

## 本版目标和边界

v801 是功能版本，接在 v800 route promotion governance snapshot 后面。v800 产出了 contract-verified route card，但下游模块仍然需要一个明确准入入口：谁要消费哪个 route、请求什么 scope、是否仍在 tiny pair-probe boundary 内。

本版解决的问题是：后续模块不能绕过 v800 snapshot 直接读取 accepted route。v801 新增 downstream guard，只有当 snapshot pass、route card present、route contract verified、requested scope 等于 allowed scope、boundary 和 claim 都保持受限时，才返回 access allowed。

本版不做：

- 不重新训练 checkpoint。
- 不重新构建 v800 snapshot。
- 不把 bounded route 推成 production release route。
- 不允许 production scope 消费 tiny pair-probe route。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_downstream_guard.py`

这是 v801 的核心 builder，提供：

- `locate_route_promotion_governance_snapshot(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_downstream_guard(...)`
- `resolve_exit_code(report, require_allowed=...)`

输入是 v800 governance snapshot。目录输入会自动寻找：

```text
model_capability_route_promotion_governance_snapshot.json
```

核心 request 字段：

- `route_id`
- `consumer_name`
- `requested_scope`
- `required_boundary`

核心 checks 包括：

- `snapshot_passed`
- `snapshot_ready`
- `downstream_policy_allowed`
- `route_card_present`
- `route_contract_verified`
- `route_governance_available`
- `requested_scope_allowed`
- `boundary_scoped`
- `claim_bounded`

其中 `requested_scope_allowed` 是本版最关键的保护：`production_model_release` 之类更宽范围会失败。

### `src/minigpt/model_capability_route_promotion_downstream_guard_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续模块消费的主证据；CSV 保存 guard checks；text 适合 CI 日志；Markdown/HTML 用于人工审阅。HTML 页面展示 allowed、consumer、route、scope、boundary 和 checks。

### `scripts/check_model_capability_route_promotion_downstream_guard.py`

这是 CLI 入口，支持：

- `--governance-snapshot`
- `--route-id`
- `--consumer-name`
- `--requested-scope`
- `--required-boundary`
- `--out-dir`
- `--require-allowed`
- `--force`

`--require-allowed` 下，如果 guard fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_downstream_guard.py`

测试覆盖：

- verified route + bounded consumer 可以通过 guard。
- 请求 `production_model_release` 这类更宽 scope 时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v801 的核心边界：下游消费者必须显式声明 bounded scope，且不能绕开 v800 verified route card。

## 真实运行证据

本版运行：

```powershell
python -B scripts\check_model_capability_route_promotion_downstream_guard.py --governance-snapshot e\800\解释\model-capability-route-promotion-governance-snapshot --route-id objective_level_contrast --consumer-name bounded-benchmark-planner --out-dir e\801\解释\model-capability-route-promotion-downstream-guard --require-allowed --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_downstream_guard_allowed
failed_count=0
downstream_guard_ready=True
access_allowed=True
consumer_name=bounded-benchmark-planner
route_id=objective_level_contrast
allowed_scope=bounded_model_capability_governance_only
boundary=tiny_required_term_pair_probe_only
next_step=build_bounded_route_promotion_consumer_plan
```

运行证据归档在：

- `e/801/解释/说明.md`
- `e/801/解释/model-capability-route-promotion-downstream-guard/`
- `e/801/图片/v801-model-capability-route-promotion-downstream-guard.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_downstream_guard.py src\minigpt\model_capability_route_promotion_downstream_guard_artifacts.py scripts\check_model_capability_route_promotion_downstream_guard.py tests\test_model_capability_route_promotion_downstream_guard.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_downstream_guard.py tests\test_model_capability_route_promotion_governance_snapshot.py -q -o cache_dir=runs\pytest-cache-v801-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v801 把 route promotion governance snapshot 变成下游准入机制，让 promoted route 只能在明确 bounded scope 下被消费。
