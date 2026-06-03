# v799 route promotion decision index contract check

## 本版目标和边界

v799 是功能版本，接在 v798 route promotion decision index 后面。v798 已经把 v797 的 accepted bounded route promotion decision 写成 route ledger；v799 的作用是验证这份 ledger 能否从记录的 source decision 重新构建出来。

本版解决的问题是：索引产物一旦进入后续治理链路，就不能只相信 JSON 里写了 `status=pass`。v799 读取 v798 index 里的 source decision 路径，重新调用 v798 builder，再比较关键字段，确认 route id、accepted count、boundary、claim 和 entries 没有被篡改。

本版不做：

- 不重新训练 checkpoint。
- 不重新审阅 v796 release packet review。
- 不重建 v797 review decision。
- 不新增模型质量结论。
- 不扩大 tiny pair-probe 边界。

## 关键新增文件

### `src/minigpt/model_capability_route_promotion_decision_index_check.py`

这是 v799 的核心 checker，提供：

- `locate_route_promotion_decision_index(path)`
- `read_json_report(path)`
- `build_model_capability_route_promotion_decision_index_check(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 v798 index JSON，也可以是 v798 输出目录。目录输入会自动寻找：

```text
model_capability_route_promotion_decision_index.json
```

核心流程：

1. 读取 v798 index。
2. 从 `summary.source_decision_paths` 或 `sources[*].source_decision_path` 找到源 v797 decision。
3. 重新调用 `build_model_capability_route_promotion_decision_index(...)`。
4. 对比原始 index 和 rebuilt index 的关键字段。

核心 checks 包括：

- `source_paths_present`
- `status`
- `decision`
- `failed_count`
- `decision_index_ready`
- `accepted_route_count`
- `route_ids`
- `boundary`
- `model_quality_claim`
- `entries`

其中 `entries` 对比的是 route id、entry status、scope、boundary 和 claim 的指纹，避免 source path 正常但 ledger entry 被手工改写。

### `src/minigpt/model_capability_route_promotion_decision_index_check_artifacts.py`

这是 artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续可消费的结构化 contract check；CSV 保存 check rows；text 适合 CI 日志；Markdown/HTML 用于人工审阅。HTML 页面展示 original/rebuilt route count 和所有比较项。

### `scripts/check_model_capability_route_promotion_decision_index.py`

这是 CLI 入口，支持：

- `--decision-index`
- `--out-dir`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 contract check fail，脚本返回 1。

### `tests/test_model_capability_route_promotion_decision_index_check.py`

测试覆盖：

- 可重建的 index 通过 contract check。
- route entry 被篡改时必须失败。
- source decision path 丢失时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这组测试保护 v799 的核心契约：v798 index 不是不可验证的静态快照，而是可以从 source decision 重建的 ledger。

## 真实运行证据

本版运行：

```powershell
python -B scripts\check_model_capability_route_promotion_decision_index.py --decision-index e\798\解释\model-capability-route-promotion-decision-index --out-dir e\799\解释\model-capability-route-promotion-decision-index-check --require-pass --force
```

结果：

```text
status=pass
decision=model_capability_route_promotion_decision_index_contract_check_passed
failed_count=0
contract_check_ready=True
source_decision_count=1
original_accepted_route_count=1
rebuilt_accepted_route_count=1
```

运行证据归档在：

- `e/799/解释/说明.md`
- `e/799/解释/model-capability-route-promotion-decision-index-check/`
- `e/799/图片/v799-model-capability-route-promotion-decision-index-check.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_route_promotion_decision_index_check.py src\minigpt\model_capability_route_promotion_decision_index_check_artifacts.py scripts\check_model_capability_route_promotion_decision_index.py tests\test_model_capability_route_promotion_decision_index_check.py src\minigpt\__init__.py
python -m pytest tests\test_model_capability_route_promotion_decision_index_check.py tests\test_model_capability_route_promotion_decision_index.py -q -o cache_dir=runs\pytest-cache-v799-focused
```

结果：

- focused tests: `7 passed`

## 一句话总结

v799 给 accepted route decision index 加上可重建 contract check，让后续模型能力治理链路消费的是可复核、未篡改、来源不断链的 bounded route ledger。
