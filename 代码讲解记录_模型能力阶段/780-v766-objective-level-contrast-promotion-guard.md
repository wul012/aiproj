# v766 objective-level contrast promotion guard 代码讲解

## 本版目标和边界

v766 的目标是给 v765 route comparison winner 加一层 promotion guard。v765 已经说明 objective-level contrast 是当前 winner，但 winner 不等于 accepted；v766 的职责是检查 comparison、replay、training 三类证据是否完整，然后把下一步导向 seed stability。

本版不训练，不 replay，不接受 checkpoint。它的结论是 guarded_route_candidate，且 `promotion_allowed=False`。

## 前置路线

- v763：训练 objective-level contrast checkpoint。
- v764：独立 pair-probe replay，三种 pair surface 全 pair-full。
- v765：对比 prior routes，objective-level contrast 胜出。
- v766：promotion guard，确认只能进入 seed stability，不能直接接受。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.py`
  - guard 核心逻辑。
  - 输入 route comparison、objective replay、training run 三份 JSON。
  - 校验 comparison winner、replay ready、checkpoint/tokenizer 存在、direct pair-full、source corpus 规模。
  - 输出 `promotion_allowed=False` 和下一步 seed stability artifact。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 展示 checks、non-goals 和 next action。

- `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.py`
  - CLI 入口。
  - `--comparison`、`--replay`、`--training` 分别输入 v765、v764、v763。

- `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.py`
  - 覆盖 guard ready 但不允许 promotion、comparison 不是 winner 失败、checkpoint 缺失失败、locator 和 artifact 输出。

## guard 检查含义

v766 要求：

- route comparison 必须 pass，decision 必须是 `pair_readiness_objective_level_contrast_replay_wins_needs_promotion_guard`。
- objective route 必须是 best，且 comparison 必须要求 promotion guard。
- v764 replay 必须 pass 且 ready。
- replay 必须 `required_all_pair_full=True`，`pair_full_count>=3`。
- v763 training report 必须 pass。
- checkpoint 和 tokenizer 必须存在。
- direct pair-full 必须已在 training run 中出现。
- source materialized corpus 必须至少 8000 行。

## 输入输出结构

输出核心：

```text
decision=pair_readiness_objective_level_contrast_promotion_guard_ready_for_seed_stability
promotion_guard_ready=True
promotion_allowed=False
guard_result=ready_for_seed_stability
required_next_artifact=pair_readiness_objective_level_contrast_seed_stability_plan
```

这里最重要的是 `promotion_allowed=False`。它说明 v766 是保护门，不是放行门。

## 运行和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.py -q -o cache_dir=runs\pytest-cache-v766-focused
```

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.py --comparison e\765\解释\model-capability-required-term-pair-readiness-objective-level-contrast-route-comparison --replay e\764\解释\model-capability-required-term-pair-readiness-objective-level-contrast-pair-probe-replay --training e\763\解释\model-capability-required-term-pair-readiness-objective-level-contrast-training-run --out-dir e\766\解释\model-capability-required-term-pair-readiness-objective-level-contrast-promotion-guard --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Allowed False`
- `Guard ready_for_seed_stability`
- `Claim guarded_route_candidate`

截图位于：

```text
e/766/图片/v766-objective-level-contrast-promotion-guard.png
```

## 证据链角色

v766 是 acceptance 前保护层。它让项目既承认 v764/v765 的积极信号，也保留工程克制：单 seed 不能直接接受，必须进入 seed stability。

一句话总结：v766 把 objective-level contrast 从 route winner 推进为 guarded candidate，但明确禁止跳过 seed stability。
