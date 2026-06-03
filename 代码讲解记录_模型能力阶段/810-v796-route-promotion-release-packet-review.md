# v796 route promotion release packet review

## 本版目标和边界

v796 是功能版本，不是拆分维护版本。它接在 v795 route promotion release packet 后面，新增 release packet review：检查 v795 packet 是否完整、是否保持 tiny pair-probe 边界、是否可以进入 bounded route promotion review。

本版解决的问题是：v795 已经把 portfolio、regression monitor 和 gate 打包，但“有包”不等于“可审阅”。v796 作为审阅入口，只读取 v795 packet，对 packet 自身做完整性和边界检查，给出 review decision。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe replay。
- 不重新读取 v792/v793/v794 源证据。
- 不扩大模型质量声明。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_release_packet_review.py`

这是 v796 的核心 builder，提供：

- `locate_route_promotion_release_packet(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_release_packet_review(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 release packet JSON，也可以是 v795 输出目录。目录输入会自动寻找：

```text
model_capability_route_promotion_release_packet.json
```

核心 checks 包括：

- `release_packet_passed`
- `release_packet_decision_ready`
- `packet_ready`
- `handoff_ready`
- `active_routes_present`
- `boundary_scoped`
- `claim_bounded`
- `evidence_count`
- `evidence_files_exist`
- `packet_checks_clean`

其中 `claim_bounded` 阻止 packet 把 claim 改成 `production_model_quality` 之类更宽的说法；`evidence_files_exist` 确保 v795 packet 里的证据路径没有断链。

### `src/minigpt/model_capability_route_promotion_release_packet_review_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

CSV 保存 check rows；Markdown/HTML 展示 review decision、boundary、claim、scope 和 checks。HTML 页面用于人工确认 packet review 不是只看 status 字段。

### `scripts/review_model_capability_route_promotion_release_packet.py`

这是 CLI 入口，支持：

- `--release-packet`
- `--required-boundary`
- `--out-dir`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 review fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_release_packet_review.py`

测试覆盖：

- ready release packet 可以通过 review。
- claim 被改宽时 review 必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v796 的核心契约：packet review 不能接受扩大后的模型质量声明。

## Review 数据结构

v796 输出的 `review` 包含：

- `review_ready`
- `review_decision`
- `active_routes`
- `active_route_count`
- `boundary`
- `model_quality_claim`
- `handoff_status`
- `evidence_count`
- `review_scope`

`review_scope=bounded_route_promotion_review_only` 是本版的关键边界，说明它只是受限路线审阅，不是生产发布审阅。

## 真实运行证据

本版运行：

```powershell
python -B scripts\review_model_capability_route_promotion_release_packet.py --release-packet e\795\解释\model-capability-route-promotion-release-packet --out-dir e\796\解释\model-capability-route-promotion-release-packet-review --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_release_packet_review_ready
failed_count=0
release_packet_review_ready=True
review_decision=accept_route_promotion_packet_for_bounded_review
active_route_count=1
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
review_scope=bounded_route_promotion_review_only
```

运行证据归档在：

- `e/796/解释/说明.md`
- `e/796/解释/model-capability-route-promotion-release-packet-review/`
- `e/796/图片/v796-model-capability-route-promotion-release-packet-review.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_release_packet_review.py src\minigpt\model_capability_route_promotion_release_packet_review_artifacts.py scripts\review_model_capability_route_promotion_release_packet.py tests\test_model_capability_route_promotion_release_packet_review.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_release_packet_review.py tests\test_model_capability_route_promotion_release_packet.py -q -o cache_dir=runs\pytest-cache-v796-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v796 把 route promotion release packet 推进为可审阅结论，让模型能力路线从“有交接包”进入“可接受受限审阅”的状态。
