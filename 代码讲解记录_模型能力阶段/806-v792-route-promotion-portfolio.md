# v792 route promotion portfolio snapshot

## 本版目标和边界

v792 是功能版本，不是拆分维护版本。它接在 v791 route promotion history ledger 后面，新增 route promotion portfolio snapshot：读取 history ledger，把 ready route promotion 整理成一个模型能力路线组合视图。

本版解决的问题是：v791 已经能保存 route promotion history，但 history 更偏流水账；后续如果要做 regression monitor 或 portfolio review，需要一个“当前 active routes 是什么、是否都保持边界、是否有 blocked route 混入”的组合视图。v792 就是这个消费层。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 replay。
- 不回写或修改 v791 history。
- 不把 tiny pair-probe 结果解释成生产模型质量。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_portfolio.py`

这是 v792 的核心 builder，提供：

- `locate_route_promotion_history(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_portfolio(...)`
- `resolve_exit_code(report, require_ready_portfolio=...)`

输入可以是 v791 history JSON，也可以是 v791 输出目录。目录输入会自动寻找：

```text
model_capability_route_promotion_history.json
```

builder 的核心流程：

1. 读取 history 的 `entries`、`summary` 和 `readiness_requirement`。
2. 把每个 history entry 转成 route card。
3. 运行 portfolio checks。
4. 生成 `portfolio`，列出 active routes、blocked routes、boundary 和 next consumers。
5. 输出顶层 summary 和 interpretation。

关键 checks 包括：

- `history_passed`
- `history_readiness_passed`
- `minimum_ready_routes`
- `no_blocked_routes`
- `no_boundary_mismatches`
- `boundary_matches_history`
- `claims_are_bounded`

其中 `no_boundary_mismatches` 和 `claims_are_bounded` 是本版的边界保护：即使 history 里出现 route，也不能因为进入 portfolio 就扩大成生产模型质量声明。

### `src/minigpt/model_capability_route_promotion_portfolio_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续自动化消费的主证据；CSV 是 route card 表；text 是 CLI 摘要；Markdown/HTML 用于人工审阅。HTML 页面展示 summary stats、Route Cards 和 Checks。

### `scripts/build_model_capability_route_promotion_portfolio.py`

这是 CLI 入口，支持：

- `--history`
- `--min-ready-routes`
- `--required-boundary`
- `--require-ready-portfolio`
- `--out-dir`
- `--title`
- `--force`

`--require-ready-portfolio` 下，如果 portfolio checks 失败，脚本返回退出码 1。这样后续版本可以把它接入 regression monitor 或 CI。

### `tests/test_model_capability_route_promotion_portfolio.py`

测试覆盖：

- 从 ready history 构建 portfolio 能通过。
- history entry boundary 被改宽时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v792 的核心契约：portfolio 只能由 ready history 生成，且 route card 不能丢失 tiny pair-probe 边界。

## Portfolio 数据结构

v792 输出的 `portfolio` 包含：

- `portfolio_type`
- `portfolio_ready`
- `boundary`
- `active_routes`
- `blocked_routes`
- `route_count`
- `active_route_count`
- `blocked_route_count`
- `next_consumers`

每个 `route_card` 包含：

- `route_id`
- `portfolio_status`
- `promotion_readiness`
- `route_status`
- `boundary`
- `model_quality_claim`
- `seed_count`
- `min_pair_full_count`
- `pair_full_strength_spread`
- `source_history_path`
- `source_manifest_path`
- `source_acceptance_review_path`
- `source_seed_stability_rollup_path`

这些字段让后续模块既能看到当前 active route，也能追溯回 v790 manifest、v789 acceptance review 和 v772 seed-stability rollup。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_portfolio.py --history e\791\解释\model-capability-route-promotion-history --out-dir e\792\解释\model-capability-route-promotion-portfolio --require-ready-portfolio --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_portfolio_ready
failed_count=0
route_promotion_portfolio_ready=True
route_count=1
active_route_count=1
blocked_route_count=0
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
```

运行证据归档在：

- `e/792/解释/说明.md`
- `e/792/解释/model-capability-route-promotion-portfolio/`
- `e/792/图片/v792-model-capability-route-promotion-portfolio.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_portfolio.py src\minigpt\model_capability_route_promotion_portfolio_artifacts.py scripts\build_model_capability_route_promotion_portfolio.py tests\test_model_capability_route_promotion_portfolio.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_portfolio.py tests\test_model_capability_route_promotion_history.py -q -o cache_dir=runs\pytest-cache-v792-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v792 把 route promotion history 推进成 route portfolio snapshot，让模型能力阶段从“历史记录”进入“当前 active route 组合视图”，为后续回归监控准备输入。
