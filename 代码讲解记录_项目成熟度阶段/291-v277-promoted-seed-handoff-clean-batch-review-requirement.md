# v277 promoted seed handoff clean batch-review requirement

## 本版目标和边界

v277 的目标是给 promoted seed handoff 增加一个可选的 clean batch-review requirement contract。

v276 已经把 `baseline_seed.handoff_clean_batch_review` 投影到 seed handoff summary、artifact 和 CLI 输出。本版进一步提供机器可判定的 gate object：`clean_batch_review_requirement`。它让自动化可以明确要求 selected clean-required handoff evidence 必须是 `clean`。

本版不改变默认 handoff 行为，不改变 plan command 的执行逻辑，也不重新计算上游 promoted comparison/decision/seed 的筛选结果。只有调用方显式传入 `require_clean_batch_review=True`，或者 CLI 使用 `--require-clean-batch-review`，才会把 dirty clean-required evidence 转成失败退出。

## 前置链路

本版接在 clean batch-review 系列之后：

- v273：promoted comparison 排除 dirty clean-required promoted inputs。
- v274：promoted decision 拒绝 dirty clean-required baseline candidates。
- v275：promoted seed 保留 selected clean batch-review evidence。
- v276：promoted seed handoff 展示 selected clean batch-review evidence。
- v277：promoted seed handoff 在显式要求时把这份 evidence 变成 `pass/fail` gate。

这条链路的重点是“默认审查可见，自动化严格可选”。这样项目不会因为默认验证变严格而破坏旧用法，但严肃自动化可以选择更硬的门禁。

## 核心数据结构

### `SeedHandoffCleanBatchReviewRequirement`

位置：`src/minigpt/promoted_training_scale_seed_handoff_review.py`

字段语义：

- `required`
  - 调用方是否显式要求 clean batch-review gate。
- `status`
  - `not-required`、`pass`、`fail` 三选一。
- `clean`
  - 当前 selected handoff evidence 是否满足 clean 语义。
  - 如果 selected handoff 不要求 clean batch review，视为 clean。
  - 如果 selected handoff 要求 clean batch review，只有 selected status 为 `clean` 才为 true。
- `selected_required`
  - 上游 selected handoff 是否要求 clean batch review。
- `selected_status`
  - 上游 selected handoff 的 clean batch-review 状态。
- `detail`
  - 人类可读解释，用于 CLI 和 artifact。
- `status_domain`
  - 稳定公开枚举，便于脚本或测试验证。

公开枚举是：

```python
("not-required", "pass", "fail")
```

## 关键函数

### `build_seed_handoff_clean_batch_review_requirement(summary, required=False)`

输入是 seed handoff summary，输出是 requirement object。

核心规则：

```text
selected_required = bool(summary["selected_handoff_require_clean_batch_review"])
selected_status = summary["selected_handoff_clean_batch_review_status"]
clean = not selected_required or selected_status == "clean"

if not required:
    status = "not-required"
elif clean:
    status = "pass"
else:
    status = "fail"
```

这保持了两个边界：

- 证据是否干净和是否要求门禁是两件事。
- dirty evidence 在默认模式下会被记录和推荐处理，但不会导致 CLI 失败。

### `build_promoted_training_scale_seed_handoff(..., require_clean_batch_review=False)`

位置：`src/minigpt/promoted_training_scale_seed_handoff.py`

本版新增参数 `require_clean_batch_review`，并在 report 中写入：

```text
clean_batch_review_requirement
```

同时把 requirement 传给 recommendation builder，让 pass/fail 都有明确的审查动作。

### `execute_promoted_training_scale_seed.py --require-clean-batch-review`

CLI 新增 strict 参数：

```powershell
python scripts/execute_promoted_training_scale_seed.py <seed> --require-clean-batch-review
```

输出新增：

```text
clean_batch_review_required_selected_status=<status>
clean_batch_review_required_clean=<True|False>
clean_batch_review_required_detail=<detail>
clean_batch_review_required=<not-required|pass|fail>
```

当 requirement status 为 `fail` 时，CLI 返回非零。

## Artifact 输出

`src/minigpt/promoted_training_scale_seed_handoff_artifacts.py` 现在把 requirement 写入：

- CSV：
  - `clean_batch_review_requirement_required`
  - `clean_batch_review_requirement_status`
  - `clean_batch_review_requirement_clean`
  - `clean_batch_review_requirement_selected_required`
  - `clean_batch_review_requirement_selected_status`
  - `clean_batch_review_requirement_status_domain`
- Markdown：
  - `Clean batch-review requirement`
  - detail
  - status domain
- HTML：
  - `Clean batch gate`
  - `Clean batch gate domain`
- JSON：
  - 完整 `clean_batch_review_requirement` object。

这些产物是后续自动化和人工审查共同消费的最终证据，不是临时日志。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 增加了多层断言：

- public status domain 固定为 `not-required/pass/fail`。
- helper 在默认、clean、dirty 三种情况下返回正确 status。
- 默认 builder 写出 `not-required`，保持兼容。
- clean seed 使用 `--require-clean-batch-review` 时 CLI 通过，并写出 pass artifact。
- dirty clean-required seed 使用 `--require-clean-batch-review` 时 CLI 非零退出，并写出 fail artifact。
- CSV、Markdown、HTML、JSON 都包含新 requirement 字段。

这组测试保护的是“可选严格门禁”的边界，而不是模型训练能力。

## 链路角色

v277 在链路中的角色是：

```text
promoted seed handoff evidence visibility
  -> opt-in automation gate
```

它不会替代 v273-v276 的上游筛选和传递，而是给 seed handoff 层增加最终自动化保险：当用户或 CI 明确要求 clean batch-review 时，dirty clean-required evidence 不能继续悄悄通过。

## 运行证据

运行截图和解释归档在 `c/277`。

验证包括：

- seed handoff focused tests。
- promoted comparison/decision/seed/seed handoff 相关链路 tests。
- full unittest。
- source encoding hygiene。
- Playwright/Chrome 打开的 HTML artifact。

## 一句话总结

v277 把 promoted seed handoff 的 clean batch-review evidence 升级为可选机器门禁，在保持默认兼容的同时，让严格自动化能够明确拒绝 dirty clean-required handoff evidence。
