# v793 route promotion regression monitor

## 本版目标和边界

v793 是功能版本，不是拆分维护版本。它接在 v792 route promotion portfolio snapshot 后面，新增 route promotion regression monitor：用 baseline/current 两个 portfolio 对比，检查 active route 是否丢失、boundary 是否变化、model quality claim 是否变宽。

本版解决的问题是：v792 已经能形成当前 active route 组合视图，但如果后续继续新增 route、替换 route 或调整 portfolio，很容易出现“active route 丢了但文档没注意到”“tiny pair-probe 边界被放宽但没有明确阻断”的问题。v793 把这些风险变成可运行检查。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 replay。
- 不新增模型路线。
- 不把 tiny pair-probe 结果解释成生产模型质量。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_regression_monitor.py`

这是 v793 的核心 builder，提供：

- `locate_route_promotion_portfolio(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_regression_monitor(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 portfolio JSON，也可以是 portfolio 输出目录。目录输入会自动寻找：

```text
model_capability_route_promotion_portfolio.json
```

builder 的核心流程：

1. 读取 baseline portfolio 和 current portfolio。
2. 按 `route_id` 建立 route card map。
3. 生成 route deltas，判断每条 route 是 `stable_active`、`lost_active_route`、`gained_active_route` 还是 `stable_blocked_or_missing`。
4. 运行 regression checks。
5. 输出 summary、issues、check rows 和 interpretation。

关键 checks 包括：

- `baseline_portfolio_passed`
- `current_portfolio_passed`
- `current_portfolio_ready`
- `no_active_route_loss`
- `no_boundary_changes`
- `no_claim_widening`
- `active_route_count_not_decreased`

其中 `no_claim_widening` 会允许当前声明继续保持 `seed_stable_pair_probe_route...`，但会阻止扩大成其他更宽的模型质量 claim。

### `src/minigpt/model_capability_route_promotion_regression_monitor_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 记录 route delta；Markdown 和 HTML 展示 route deltas 和 checks。HTML 截图能直接看到 lost routes、boundary changed、claim changed 等核心判断。

### `scripts/check_model_capability_route_promotion_regression.py`

这是 CLI 入口，支持：

- `--current`
- `--baseline`
- `--out-dir`
- `--require-pass`
- `--force`

如果不传 `--baseline`，CLI 会默认用 current 作为 baseline，适合建立初始无回归证据。传入不同 baseline/current 后，它就能作为后续 portfolio 更新的 regression gate。

### `tests/test_model_capability_route_promotion_regression_monitor.py`

测试覆盖：

- baseline/current 相同时通过。
- current 把 active route 改成 blocked 时失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v793 的核心契约：active route 丢失必须被发现，不能只靠 README 或人工判断。

## Regression 数据结构

每个 route delta 包含：

- `route_id`
- `baseline_status`
- `current_status`
- `relation`
- `baseline_boundary`
- `current_boundary`
- `baseline_claim`
- `current_claim`
- `baseline_seed_count`
- `current_seed_count`

顶层 summary 包含：

- `lost_active_route_count`
- `gained_active_route_count`
- `boundary_changed`
- `model_quality_claim_changed`
- `baseline_active_route_count`
- `current_active_route_count`
- `failed_check_count`

这些字段可以直接被后续 release、portfolio 或 maturity 检查消费。

## 真实运行证据

本版运行：

```powershell
python -B scripts\check_model_capability_route_promotion_regression.py --current e\792\解释\model-capability-route-promotion-portfolio --baseline e\792\解释\model-capability-route-promotion-portfolio --out-dir e\793\解释\model-capability-route-promotion-regression-monitor --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_regression_monitor_passed
failed_count=0
regression_monitor_passed=True
lost_active_route_count=0
gained_active_route_count=0
boundary_changed=False
model_quality_claim_changed=False
current_model_quality_claim=seed_stable_pair_probe_route_accepted
```

运行证据归档在：

- `e/793/解释/说明.md`
- `e/793/解释/model-capability-route-promotion-regression-monitor/`
- `e/793/图片/v793-model-capability-route-promotion-regression-monitor.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_regression_monitor.py src\minigpt\model_capability_route_promotion_regression_monitor_artifacts.py scripts\check_model_capability_route_promotion_regression.py tests\test_model_capability_route_promotion_regression_monitor.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_regression_monitor.py tests\test_model_capability_route_promotion_portfolio.py -q -o cache_dir=runs\pytest-cache-v793-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v793 把 route portfolio 从“当前组合视图”推进到“可回归检查的能力路线基线”，让后续功能推进有了 active route、边界和 claim 的自动保护。
