# v800 route promotion governance snapshot

## 本版目标和边界

v800 是功能版本，接在 v798 route promotion decision index 和 v799 decision index contract check 后面。v798 解决“accepted route 如何索引”，v799 解决“索引能否从源 decision 重建”，v800 进一步把这两类证据合成一个可消费的治理快照。

本版解决的问题是：后续模块不应该分别解析 index 和 contract check，再自己判断 route 是否可用。v800 直接输出 `route_cards`，每张卡包含 route id、accepted 状态、contract verification、governance status、scope、boundary、claim 和 allowed downstream use。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe。
- 不重建 v798 index。
- 不重做 v799 contract check。
- 不扩大 tiny pair-probe 的模型质量声明。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_governance_snapshot.py`

这是 v800 的核心 builder，提供：

- `locate_route_promotion_decision_index(path)`
- `locate_route_promotion_decision_index_check(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_governance_snapshot(...)`
- `resolve_exit_code(report, require_ready_snapshot=...)`

输入是 v798 decision index 和 v799 contract check。目录输入会分别自动寻找：

```text
model_capability_route_promotion_decision_index.json
model_capability_route_promotion_decision_index_check.json
```

核心结构包括：

- `index_summary`：来自 v798 的 accepted route 摘要。
- `contract_check_summary`：来自 v799 的 original/rebuilt 对比摘要。
- `route_cards`：后续模块可消费的治理状态卡。
- `downstream_policy`：明确是否允许 downstream 读取，以及允许范围。
- `check_rows`：快照自身的输入契约检查。

核心 checks 包括：

- `decision_index_passed`
- `decision_index_ready`
- `contract_check_passed`
- `contract_check_ready`
- `route_cards_present`
- `verified_route_cards`
- `accepted_route_count_matches`
- `boundary_scoped`

其中 `accepted_route_count_matches` 把 v798 和 v799 的 original/rebuilt route count 绑定起来，防止 downstream 消费一个没有经过重建确认的 route card。

### `src/minigpt/model_capability_route_promotion_governance_snapshot_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续模块消费的主证据；CSV 保存 route cards；text 适合 CI 日志；Markdown/HTML 用于人工审阅。HTML 页面展示 route cards 和 checks。

### `scripts/build_model_capability_route_promotion_governance_snapshot.py`

这是 CLI 入口，支持：

- `--decision-index`
- `--index-check`
- `--required-boundary`
- `--out-dir`
- `--require-ready-snapshot`
- `--force`

`--require-ready-snapshot` 下，如果快照 fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_governance_snapshot.py`

测试覆盖：

- v798 index + v799 check 可以生成 ready governance snapshot。
- contract check 被改成 fail 时 snapshot 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v800 的核心边界：只有 index ready 且 contract check ready 的 route 才能进入 downstream governance snapshot。

## 真实运行证据

本版运行：

```powershell
python -B scripts\build_model_capability_route_promotion_governance_snapshot.py --decision-index e\798\解释\model-capability-route-promotion-decision-index --index-check e\799\解释\model-capability-route-promotion-decision-index-check --out-dir e\800\解释\model-capability-route-promotion-governance-snapshot --require-ready-snapshot --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_governance_snapshot_ready
failed_count=0
governance_snapshot_ready=True
verified_route_count=1
route_ids=objective_level_contrast
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
next_step=publish_bounded_route_promotion_governance_snapshot
```

运行证据归档在：

- `e/800/解释/说明.md`
- `e/800/解释/model-capability-route-promotion-governance-snapshot/`
- `e/800/图片/v800-model-capability-route-promotion-governance-snapshot.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_governance_snapshot.py src\minigpt\model_capability_route_promotion_governance_snapshot_artifacts.py scripts\build_model_capability_route_promotion_governance_snapshot.py tests\test_model_capability_route_promotion_governance_snapshot.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_governance_snapshot.py tests\test_model_capability_route_promotion_decision_index_check.py tests\test_model_capability_route_promotion_decision_index.py -q -o cache_dir=runs\pytest-cache-v800-focused
```

结果：

- focused tests: `10 passed`

## 一句话总结

v800 把 accepted route index 和可重建 contract check 合并成治理快照，让后续模块可以直接消费经过验证、边界清楚的 route card。
