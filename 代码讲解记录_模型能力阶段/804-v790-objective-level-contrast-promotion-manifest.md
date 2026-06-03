# v790 objective-level contrast promotion manifest

## 本版目标和边界

v790 是功能版本，不是拆分维护版本。它接在 v789 objective-level contrast acceptance review 后面，新增 promotion manifest 层：读取 v789 的 accepted review，把 `objective_level_contrast` 路线规范成后续 benchmark history 或 portfolio 可以消费的 manifest。

它解决的问题是：v789 已经做出接受决策，但这个决策还只是 review artifact。后续如果要做模型能力履历、路线组合、回归监控，需要一个更稳定的 promotion manifest，明确记录 route id、promotion status、边界、seed evidence 和 benchmark-history entry。

本版不做：

- 不重新训练。
- 不重新 replay。
- 不重新解释 v772 rollup。
- 不扩大 tiny pair-probe 的模型质量边界。

## 关键新增文件

### `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py`

这是 v790 的核心 builder。它提供：

- `locate_objective_level_contrast_promotion_manifest_acceptance_review(path)`
- `read_json_report(path)`
- `build_objective_level_contrast_promotion_manifest(...)`
- `resolve_exit_code(report, require_pass=...)`

输入可以是 v789 acceptance review 的 JSON 文件，也可以是 v789 输出目录。目录输入会自动定位：

```text
model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.json
```

builder 的核心逻辑分成四层：

1. 读取 acceptance review 的 `summary`、`interpretation`、`source_seed_stability_rollup` 和 `seed_rows`。
2. 运行 promotion manifest checks。
3. 生成 `manifest`，其中包含 route status 和 benchmark history entry。
4. 输出顶层 `summary`、`interpretation`、`issues` 和 `check_rows`。

关键 checks 包括：

- `acceptance_review_passed`
- `acceptance_decision`
- `promotion_allowed`
- `route_id_matches`
- `boundary_scoped`
- `claim_scoped`
- `seed_rows_present`
- `source_rollup_was_review_ready`

其中 `boundary_scoped` 是本版最重要的保护之一：它要求 v789 的 `model_quality_boundary` 必须仍然是 `tiny_required_term_pair_probe_only`。如果有人把 acceptance review 篡改成 `production_model_quality`，v790 会直接失败。

### `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest_artifacts.py`

这是 artifact writer 模块，负责输出：

- JSON
- CSV
- text
- Markdown
- HTML

JSON 是后续机器消费的主证据；CSV 展示 check rows；text 用于命令行摘要；Markdown 和 HTML 用于人工审阅。HTML 页面展示 `Benchmark History Entry`、`Seed Evidence` 和 `Checks`，让审阅者不用打开 JSON 也能确认 promotion manifest 的边界。

### `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py`

这是 CLI 入口，支持：

- `--acceptance-review`
- `--out-dir`
- `--route-id`
- `--require-pass`
- `--force`

`--require-pass` 下，如果 promotion manifest checks 失败，脚本会返回退出码 1。这样它可以直接接入 CI 或后续自动化流水线。

### `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py`

测试覆盖四个关键点：

- 从 accepted review 构建 manifest 能通过。
- route id 不匹配时必须失败。
- model quality boundary 被改宽时必须失败。
- artifact writer 和 CLI 能真实写出 JSON/CSV/text/Markdown/HTML。

这几个测试保护的是 v790 的核心契约：promotion manifest 只能消费 v789 接受过的 objective-level contrast route，并且不能悄悄扩大模型质量声明。

## Manifest 数据结构

v790 输出的 `manifest` 主要字段包括：

- `route_id`
- `route_status`
- `promotion_ready`
- `promotion_scope`
- `model_quality_claim`
- `accepted_seed_count`
- `pair_full_counts`
- `min_pair_full_count`
- `max_pair_full_count`
- `pair_full_strength_spread`
- `benchmark_history_entry`

`benchmark_history_entry` 是本版给后续链路预留的消费入口：

```json
{
  "entry_type": "model_capability_route_promotion",
  "route_id": "objective_level_contrast",
  "status": "ready",
  "boundary": "tiny_required_term_pair_probe_only",
  "model_quality_claim": "seed_stable_pair_probe_route_accepted",
  "seed_count": 3,
  "min_pair_full_count": 2,
  "pair_full_strength_spread": 1
}
```

这里的 `status=ready` 表示它可以进入 benchmark history，不表示可以对外宣称生产模型能力。

## 真实运行证据

本版运行：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py --acceptance-review e\789\解释\model-capability-required-term-pair-readiness-objective-level-contrast-acceptance-review --out-dir e\790\解释\model-capability-required-term-pair-readiness-objective-level-contrast-promotion-manifest --require-pass --force
```

结果：

```text
status=pass
decision=pair_readiness_objective_level_contrast_promotion_manifest_ready
failed_count=0
promotion_manifest_ready=True
promoted_route_id=objective_level_contrast
route_status=promoted
can_feed_benchmark_history=True
benchmark_history_entry_status=ready
model_quality_claim=seed_stable_pair_probe_route_accepted
```

运行证据归档在：

- `e/790/解释/说明.md`
- `e/790/解释/model-capability-required-term-pair-readiness-objective-level-contrast-promotion-manifest/`
- `e/790/图片/v790-objective-level-contrast-promotion-manifest.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py src\minigpt\model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest_artifacts.py scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest.py tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py -q -o cache_dir=runs\pytest-cache-v790-focused
```

结果：

- focused tests: `8 passed`

## 一句话总结

v790 把 v789 的 accepted route 变成 benchmark-history-ready promotion manifest，让 objective-level contrast 从“已接受的实验结论”推进到“可被后续模型能力履历消费的标准化证据”。
