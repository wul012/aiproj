# v795 route promotion release packet

## 本版目标和边界

v795 是功能版本，不是拆分维护版本。它接在 v794 route promotion gate 后面，新增 route promotion release packet：把 v792 portfolio、v793 regression monitor 和 v794 gate 三份证据打成一个可交接包。

本版解决的问题是：v794 已经给出 gate pass，但后续 route promotion review 不应该再到多个目录里手工找证据。v795 把必要证据路径、active route、boundary、claim、gate decision 和 checks 聚合到同一个 release packet。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe replay。
- 不新增 route。
- 不把 tiny pair-probe 结果解释成生产模型质量。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_release_packet.py`

这是 v795 的核心 builder，提供：

- `locate_route_promotion_portfolio(path)`
- `locate_route_promotion_regression_monitor(path)`
- `locate_route_promotion_gate(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_release_packet(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 JSON 文件，也可以是输出目录。目录输入会自动定位：

```text
model_capability_route_promotion_portfolio.json
model_capability_route_promotion_regression_monitor.json
model_capability_route_promotion_gate.json
```

核心 checks 包括：

- `portfolio_passed`
- `regression_monitor_passed`
- `gate_passed`
- `gate_ready`
- `active_routes_present`
- `no_lost_active_routes`
- `boundary_stable`
- `claim_not_widened`
- `evidence_files_exist`

其中 `evidence_files_exist` 很关键：release packet 不只看 JSON 字段，还检查 portfolio、monitor、gate 三份源文件路径是否存在，避免交接包引用断链。

### `src/minigpt/model_capability_route_promotion_release_packet_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存 evidence rows；Markdown/HTML 展示 evidence 和 checks。HTML 页面能直接确认 packet 是否 ready、handoff status、证据数量和源路径存在性。

### `scripts/build_model_capability_route_promotion_release_packet.py`

这是 CLI 入口，支持：

- `--portfolio`
- `--regression-monitor`
- `--gate`
- `--out-dir`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 release packet fail，脚本返回 1。后续 route promotion review 可以把它作为输入。

### `tests/test_model_capability_route_promotion_release_packet.py`

测试覆盖：

- clean portfolio/monitor/gate 时 packet 通过。
- gate 失败时 packet 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v795 的核心契约：release packet 不能绕过 gate，也不能忽略证据源路径。

## Release Packet 数据结构

v795 输出的 `packet` 包含：

- `packet_ready`
- `handoff_status`
- `active_routes`
- `active_route_count`
- `boundary`
- `model_quality_claim`
- `gate_decision`
- `lost_active_route_count`
- `boundary_changed`
- `model_quality_claim_changed`
- `route_cards`
- `evidence_rows`

`evidence_rows` 当前有三类：

- `portfolio`
- `regression_monitor`
- `gate`

每一行都记录 path 和 exists，方便后续审阅和自动检查。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_release_packet.py --portfolio e\792\解释\model-capability-route-promotion-portfolio --regression-monitor e\793\解释\model-capability-route-promotion-regression-monitor --gate e\794\解释\model-capability-route-promotion-gate --out-dir e\795\解释\model-capability-route-promotion-release-packet --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_release_packet_ready
failed_count=0
release_packet_ready=True
handoff_status=ready_for_route_promotion_review
active_route_count=1
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
evidence_count=3
```

运行证据归档在：

- `e/795/解释/说明.md`
- `e/795/解释/model-capability-route-promotion-release-packet/`
- `e/795/图片/v795-model-capability-route-promotion-release-packet.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_release_packet.py src\minigpt\model_capability_route_promotion_release_packet_artifacts.py scripts\build_model_capability_route_promotion_release_packet.py tests\test_model_capability_route_promotion_release_packet.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_release_packet.py tests\test_model_capability_route_promotion_gate.py -q -o cache_dir=runs\pytest-cache-v795-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v795 把 route portfolio、regression monitor 和 gate 聚合成 release packet，让模型能力路线从“有准入门禁”推进到“有可审阅交接包”。
