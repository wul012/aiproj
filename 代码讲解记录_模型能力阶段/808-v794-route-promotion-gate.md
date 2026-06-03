# v794 route promotion gate

## 本版目标和边界

v794 是功能版本，不是拆分维护版本。它接在 v792 route promotion portfolio snapshot 和 v793 route promotion regression monitor 后面，新增 route promotion gate：把 portfolio ready 和 regression pass 合成一个下游准入决策。

本版解决的问题是：v792 说明当前 active route 组合是 ready，v793 说明它没有相对 baseline 回归，但下游模块仍然需要一个统一门禁来回答“现在能不能进入 route promotion release packet 或 model capability route review”。v794 就提供这个 gate。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe replay。
- 不新增 route。
- 不扩大 tiny pair-probe 的模型质量声明。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_gate.py`

这是 v794 的核心 builder，提供：

- `locate_route_promotion_portfolio(path)`
- `locate_route_promotion_regression_monitor(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_gate(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 JSON 文件，也可以是输出目录。目录输入分别会自动寻找：

```text
model_capability_route_promotion_portfolio.json
model_capability_route_promotion_regression_monitor.json
```

核心 checks 包括：

- `portfolio_passed`
- `portfolio_decision_ready`
- `regression_monitor_passed`
- `regression_decision_passed`
- `active_routes_present`
- `portfolio_boundary_scoped`
- `regression_boundary_stable`
- `no_lost_active_routes`
- `no_claim_widening`
- `portfolio_checks_clean`
- `regression_checks_clean`

这组 checks 把 v792/v793 的关键字段收束为一个明确准入结论。如果任何一层出现 active route 丢失、boundary 变化、claim 变宽或 failed checks，gate 就会失败。

### `src/minigpt/model_capability_route_promotion_gate_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是机器消费证据；CSV 保存 check rows；text 是 CLI 摘要；Markdown/HTML 用于人工审阅。HTML 页面展示 gate decision、allowed next steps 和 checks。

### `scripts/check_model_capability_route_promotion_gate.py`

这是 CLI 入口，支持：

- `--portfolio`
- `--regression-monitor`
- `--required-boundary`
- `--out-dir`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 gate fail，脚本返回 1。这样后续 release packet 或 route review 可以把它当作前置门禁。

### `tests/test_model_capability_route_promotion_gate.py`

测试覆盖：

- clean portfolio + clean regression monitor 时 gate 通过。
- regression monitor fail 时 gate 失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v794 的核心契约：gate 不能只看 portfolio ready，必须同时看 regression monitor 是否通过。

## Gate 数据结构

v794 输出的 `gate` 包含：

- `gate_ready`
- `gate_decision`
- `allowed_next_steps`
- `blocked_next_steps`
- `active_routes`
- `active_route_count`
- `boundary`
- `model_quality_claim`
- `lost_active_route_count`
- `boundary_changed`
- `claim_changed`

其中 `gate_decision=allow_downstream_model_capability_review` 只表示允许继续构建 release packet 或 route review，不表示生产模型质量已经达标。

## 真实运行证据

本版运行：

```powershell
python -B scripts\check_model_capability_route_promotion_gate.py --portfolio e\792\解释\model-capability-route-promotion-portfolio --regression-monitor e\793\解释\model-capability-route-promotion-regression-monitor --out-dir e\794\解释\model-capability-route-promotion-gate --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_gate_passed
exit_code=0
failed_count=0
route_promotion_gate_ready=True
gate_decision=allow_downstream_model_capability_review
active_route_count=1
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
allowed_next_steps=route_promotion_release_packet,model_capability_route_review
```

运行证据归档在：

- `e/794/解释/说明.md`
- `e/794/解释/model-capability-route-promotion-gate/`
- `e/794/图片/v794-model-capability-route-promotion-gate.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_gate.py src\minigpt\model_capability_route_promotion_gate_artifacts.py scripts\check_model_capability_route_promotion_gate.py tests\test_model_capability_route_promotion_gate.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_gate.py tests\test_model_capability_route_promotion_regression_monitor.py -q -o cache_dir=runs\pytest-cache-v794-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v794 把 route portfolio 和 regression monitor 收束成一个可执行 gate，让模型能力路线从“可审阅证据”推进到“有准入门禁的下游审阅入口”。
