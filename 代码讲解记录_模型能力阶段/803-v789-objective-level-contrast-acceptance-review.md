# v789 objective-level contrast acceptance review

## 本版目标和边界

v789 是功能版本，不是维护拆分版本。它接在 v772 objective-level contrast seed-stability rollup 后面，新增一个 acceptance review 层：读取三 seed rollup，检查是否满足接受条件，并在 tiny required-term pair-probe benchmark 边界内允许该 route 被接受。

本版不做：

- 不重新训练 checkpoint。
- 不重新运行 replay。
- 不修改 v772 rollup。
- 不把结果上升为生产级模型质量。

它解决的问题是：v772 已经证明三 seed replay 可进入接受评审，但仍保留 `promotion_allowed=False`。v789 把这个“等待评审”的状态推进为明确的 `accepted` 或 `fix` 决策。

## 关键新增文件

### `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py`

核心 builder 模块，提供：

- `locate_objective_level_contrast_acceptance_review_rollup(path)`
- `read_json_report(path)`
- `build_objective_level_contrast_acceptance_review(...)`
- `resolve_exit_code(report, require_pass=...)`

它读取 seed-stability rollup，抽取 seed replay rows，然后执行 acceptance checks。

关键设置：

- `minimum_pair_full_count=2`
- `require_uniform_strength=False`

这意味着默认接受规则不是“每个 seed 都达到 3/3 pair-full”，而是“每个 seed 至少保留 2 个 pair-full surfaces”。这是对 v772 证据的实际响应：`3636=3`，`3737=2`，`3838=2`，强度不完全一致但满足最低强度。

### `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review_artifacts.py`

artifact writer 模块，输出：

- JSON
- CSV
- text
- Markdown
- HTML

HTML 页面展示 seed replay 表格和 check rows，便于人工确认接受结论不是单字段硬写出来的。

### `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py`

CLI 入口，支持：

- `--rollup`
- `--out-dir`
- `--minimum-pair-full-count`
- `--require-uniform-strength`
- `--require-pass`
- `--force`

这个脚本让 v789 可以直接消费真实 `e/772` 归档。

### `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py`

测试覆盖：

- ready rollup 被接受。
- `minimum_pair_full_count=3` 时拒绝。
- `--require-uniform-strength` 时因 `3/2/2` 强度不一致拒绝。
- artifact writer 和 CLI 接线可运行。

## Acceptance Checks

v789 的 check rows 包含：

- `rollup_passed`
- `rollup_decision_ready`
- `rollup_acceptance_review_ready`
- `rollup_not_preapproved`
- `observed_expected_seed_count`
- `all_seed_replays_ready`
- `minimum_pair_full_strength`
- `uniform_strength_when_required`
- `rollup_checks_clean`

其中 `rollup_not_preapproved` 很关键：它要求上游 rollup 仍然是 `promotion_allowed=False`，说明 v789 是独立评审，不是重复确认一个已经允许 promotion 的 artifact。

## 真实运行证据

本版运行：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py --rollup e\772\解释\model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-rollup --out-dir e\789\解释\model-capability-required-term-pair-readiness-objective-level-contrast-acceptance-review --require-pass --force
```

结果：

```text
status=pass
decision=pair_readiness_objective_level_contrast_acceptance_review_accepted
promotion_allowed=True
accepted_route=objective_level_contrast
model_quality_boundary=tiny_required_term_pair_probe_only
min_pair_full_count=2
pair_full_strength_spread=1
```

运行证据归档在：

- `e/789/解释/说明.md`
- `e/789/解释/model-capability-required-term-pair-readiness-objective-level-contrast-acceptance-review/`
- `e/789/图片/v789-objective-level-contrast-acceptance-review.png`

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py src\minigpt\model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review_artifacts.py scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review.py tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup.py -q -o cache_dir=runs\pytest-cache-v789-focused
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v789
```

结果：

- focused tests: `8 passed`
- source encoding: `status=pass`

## 一句话总结

v789 把 objective-level contrast 从“多 seed rollup 可进入评审”推进到“在 tiny pair-probe 边界内接受该 route”，让治理链真正消费并转化模型实验结果。
