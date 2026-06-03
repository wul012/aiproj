# v797 route promotion review decision

## 本版目标和边界

v797 是功能版本，接在 v796 route promotion release packet review 后面。v796 的结论是 release packet 可以进入 bounded route promotion review；v797 则把这个 review 结果收束成最终的受限路线推广决策。

本版解决的问题是：审阅通过不等于最终可接受。v797 新增一层 decision builder，检查 v796 review 的状态、决策、scope、active route、boundary、model quality claim 和源 review check 是否都保持干净，然后给出 `accept_bounded_route_promotion`。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 pair-probe replay。
- 不重新构造 v795 release packet。
- 不把 tiny pair-probe 的路线推广解释成生产级模型质量。
- 不扩大 `bounded_route_promotion_review_only` 这个审阅范围。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_review_decision.py`

这是 v797 的核心 builder，提供：

- `locate_route_promotion_release_packet_review(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_review_decision(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 v796 review JSON，也可以是 v796 输出目录。目录输入会自动寻找：

```text
model_capability_route_promotion_release_packet_review.json
```

核心 checks 包括：

- `review_passed`
- `review_decision_ready`
- `review_accepts_packet`
- `review_scope_bounded`
- `active_route_present`
- `boundary_scoped`
- `claim_bounded`
- `source_review_checks_clean`

这些 checks 保护的是“最终接受决策不能越界”。其中 `review_scope_bounded` 防止把审阅范围改成生产发布，`claim_bounded` 防止把模型质量声明改宽，`source_review_checks_clean` 确保 v796 的源 review 没有失败项。

### `src/minigpt/model_capability_route_promotion_review_decision_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续模块可消费的结构化证据；CSV 保存 check rows；text 适合 CI 日志；Markdown 和 HTML 用于人工审阅。HTML 页面不是装饰，它展示 status、decision、final decision、active route count、boundary、claim、scope 和每条 check。

### `scripts/decide_model_capability_route_promotion_review.py`

这是 CLI 入口，支持：

- `--release-packet-review`
- `--out-dir`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 v797 decision fail，脚本返回 1。结构通过但源 review 不是可接受状态时，不会被误报为通过。

### `tests/test_model_capability_route_promotion_review_decision.py`

测试覆盖：

- v796 的 ready review 可以生成 accepted final decision。
- review scope 被篡改成 `production_release_review` 时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v797 的关键边界：最终决策只能接受受限 pair-probe route promotion，不能接受范围扩大后的审阅。

## Decision 数据结构

v797 输出的 `final_decision` 包含：

- `ready`
- `decision`
- `next_step`
- `review_scope`
- `active_routes`
- `active_route_count`
- `boundary`
- `model_quality_claim`

其中 `decision=accept_bounded_route_promotion` 是本版最重要的结果；`review_scope=bounded_route_promotion_review_only` 是最重要的边界。二者必须同时出现，才说明本版接受的是受限路线推广，而不是生产模型发布。

## 真实运行证据

本版运行：

```powershell
python -B scripts\decide_model_capability_route_promotion_review.py --release-packet-review e\796\解释\model-capability-route-promotion-release-packet-review --out-dir e\797\解释\model-capability-route-promotion-review-decision --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_final_review_accepted
failed_count=0
route_promotion_review_decision_ready=True
final_decision=accept_bounded_route_promotion
active_route_count=1
boundary=tiny_required_term_pair_probe_only
model_quality_claim=seed_stable_pair_probe_route_accepted
review_scope=bounded_route_promotion_review_only
```

运行证据归档在：

- `e/797/解释/说明.md`
- `e/797/解释/model-capability-route-promotion-review-decision/`
- `e/797/图片/v797-model-capability-route-promotion-review-decision.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_review_decision.py src\minigpt\model_capability_route_promotion_review_decision_artifacts.py scripts\decide_model_capability_route_promotion_review.py tests\test_model_capability_route_promotion_review_decision.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_review_decision.py tests\test_model_capability_route_promotion_release_packet_review.py -q -o cache_dir=runs\pytest-cache-v797-focused
```

结果：

- focused tests: `6 passed`

## 一句话总结

v797 把 route promotion release packet review 推进为最终受限接受决策，让模型能力路线从“可审阅”进入“可接受 bounded route promotion”的状态。
