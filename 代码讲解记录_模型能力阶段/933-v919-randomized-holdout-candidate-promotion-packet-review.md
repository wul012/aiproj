# v919 randomized holdout candidate promotion packet review 代码讲解

## 本版目标和边界

v919 的目标是 review v918 的 randomized holdout candidate promotion packet。

v918 已经把四段证据打包：

```text
v914 randomized suite
v915 dry-run
v916 real replay
v917 replay review
```

v919 不重做这四件事，而是复核 v918 packet 是否完整、可信、边界清楚。

明确不做：

- 不重新训练。
- 不重新执行模型 replay。
- 不重建 candidate packet。
- 不批准 direct promotion。
- 不把 `20/20` tiny replay 结果扩大成生产级模型能力结论。

本版只批准进入 bounded promotion gate。

## 前置链路

```text
v914 randomized target-hidden suite
  -> v915 dry-run
  -> v916 real replay
  -> v917 replay review
  -> v918 candidate promotion packet
  -> v919 packet review
  -> next bounded promotion gate
```

v919 是“候选包是否能进 gate”的检查，不是“模型能否正式 promotion”的最终判定。

## 关键文件

### `src/minigpt/randomized_holdout_candidate_promotion_packet_review.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_holdout_candidate_promotion_packet_review(...)
```

输入：

- v918 candidate packet report。
- 可选 `candidate_packet_path`。
- `minimum_candidate_cases`，默认 `20`。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `candidate_packet_path`
- `source_packet_summary`
- `source_packet`
- `evidence_rows`
- `check_rows`
- `review`
- `summary`
- `interpretation`

### `locate_randomized_holdout_candidate_promotion_packet`

locator 支持两种输入：

- 直接传 `randomized_holdout_candidate_promotion_packet.json`。
- 传 v918 输出目录，自动补齐 JSON 文件名。

真实运行时传的是目录：

```text
e/918/解释/randomized-holdout-candidate-promotion-packet
```

### `_checks`

v919 共有 20 条检查。

源 packet 状态：

```text
candidate_packet_passed
candidate_packet_decision_ready
candidate_packet_summary_ready
packet_ready
handoff_ready_for_review
```

随机 holdout 质量边界：

```text
candidate_case_count_floor
suite_case_count_matches
clean_cases_complete
random_seed_present
pass_rate_complete
negative_control_rejected
candidate_packet_authorized
source_checks_clean
```

证据清单：

```text
evidence_count
evidence_files_exist
evidence_ready
evidence_keeps_promotion_false
```

promotion 边界：

```text
packet_keeps_promotion_false
approved_for_promotion_false
claim_is_candidate_packet_only
```

这组检查的重点是：v919 可以批准 gate，但不能允许 packet 在 review 阶段偷偷变成 promotion。

## `_review`

`_review` 生成 review 层的结果：

```text
review_ready
review_decision
candidate_case_count
random_seed
pass_rate
clean_randomized_case_count
evidence_count
promotion_ready
approved_for_promotion
approved_for_bounded_promotion_gate
model_quality_claim
review_scope
next_step
```

真实 v919 review：

```text
review_ready=True
review_decision=accept_randomized_holdout_candidate_packet_for_bounded_gate
candidate_case_count=20
random_seed=914
pass_rate=1.0
approved_for_bounded_promotion_gate=True
promotion_ready=False
approved_for_promotion=False
model_quality_claim=candidate_packet_review_only
review_scope=bounded_randomized_holdout_candidate_review_only
next_step=build_randomized_holdout_bounded_promotion_gate
```

`approved_for_bounded_promotion_gate=True` 是本版新增能力。

它不是 direct promotion。它只说明 v918 packet 已经足够进入下一层 gate。

## `_summary`

`_summary` 把 review 结果压成下游消费更方便的字段：

```text
randomized_holdout_candidate_promotion_packet_review_ready
review_decision
candidate_case_count
random_seed
pass_rate
clean_randomized_case_count
evidence_count
promotion_ready
approved_for_promotion
approved_for_bounded_promotion_gate
model_quality_claim
review_scope
next_step
passed_check_count
failed_check_count
```

真实 summary：

```text
randomized_holdout_candidate_promotion_packet_review_ready=True
approved_for_bounded_promotion_gate=True
promotion_ready=False
approved_for_promotion=False
passed_check_count=20
failed_check_count=0
```

这里最重要的组合是：

```text
approved_for_bounded_promotion_gate=True
approved_for_promotion=False
promotion_ready=False
```

这说明 gate 可以继续，promotion 还不能继续。

## `resolve_exit_code`

CLI 支持三个门槛：

```python
resolve_exit_code(
    report,
    require_review_ready=True,
    require_gate_approval=True,
    require_promotion_ready=False,
)
```

真实运行启用：

```text
--require-review-ready
--require-gate-approval
```

测试中额外断言：

```text
require_promotion_ready -> 1
```

这个断言保护 v919 的边界：review 通过不等于 promotion 通过。

## `src/minigpt/randomized_holdout_candidate_promotion_packet_review_artifacts.py`

artifact 模块输出：

```text
JSON
CSV
TXT
Markdown
HTML
```

CSV 写 checks，便于快速过滤失败项。

HTML 第一屏展示：

- `Review ready`
- `Cases`
- `Seed`
- `Pass rate`
- `Bounded gate`
- `Promotion`
- `Scope`
- `Next`

这样截图里可以一眼看到 v919 的核心结论：bounded gate 通过，promotion 仍然 false。

## `scripts/review_randomized_holdout_candidate_promotion_packet.py`

CLI 参数：

```text
--candidate-packet
--minimum-candidate-cases
--out-dir
--require-review-ready
--require-gate-approval
--require-promotion-ready
--force
```

真实命令：

```powershell
python scripts\review_randomized_holdout_candidate_promotion_packet.py `
  --candidate-packet e\918\解释\randomized-holdout-candidate-promotion-packet `
  --out-dir e\919\解释\randomized-holdout-candidate-promotion-packet-review `
  --require-review-ready `
  --require-gate-approval `
  --force
```

真实输出：

```text
status=pass
decision=randomized_holdout_candidate_promotion_packet_review_ready
failed_count=0
randomized_holdout_candidate_promotion_packet_review_ready=True
review_decision=accept_randomized_holdout_candidate_packet_for_bounded_gate
candidate_case_count=20
random_seed=914
pass_rate=1.0
approved_for_bounded_promotion_gate=True
promotion_ready=False
model_quality_claim=candidate_packet_review_only
review_scope=bounded_randomized_holdout_candidate_review_only
next_step=build_randomized_holdout_bounded_promotion_gate
passed_check_count=20
failed_check_count=0
```

## 测试覆盖

新增测试：

```text
tests/test_randomized_holdout_candidate_promotion_packet_review.py
```

覆盖点：

- 干净 candidate packet 被接受进入 bounded gate。
- claim 被篡改成生产级模型质量时失败。
- negative control 不再被拒绝时失败。
- promotion 字段已经为 True 时失败。
- locator、artifact 输出和 CLI 正常工作。

关键断言：

```text
approved_for_bounded_promotion_gate=True
promotion_ready=False
approved_for_promotion=False
resolve_exit_code(require_promotion_ready=True) == 1
```

这正是 v919 的语义核心。

## 运行证据

归档：

```text
e/919/解释/说明.md
e/919/解释/randomized-holdout-candidate-promotion-packet-review/
e/919/图片/v919-randomized-holdout-candidate-promotion-packet-review.png
```

Playwright MCP snapshot 确认：

- `Status=pass`
- `Review ready=True`
- `Cases=20`
- `Seed=914`
- `Pass rate=1.0`
- `Bounded gate=True`
- `Promotion=False`
- `Scope=bounded_randomized_holdout_candidate_review_only`
- `Next=build_randomized_holdout_bounded_promotion_gate`
- 20 条 checks 均为 pass。

## 一句话总结

v919 把 v918 candidate packet 复核为 bounded promotion gate 的合格输入，但仍然没有批准 direct promotion。
