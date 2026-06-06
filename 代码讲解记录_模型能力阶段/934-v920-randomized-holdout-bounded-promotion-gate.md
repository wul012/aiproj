# v920 randomized holdout bounded promotion gate 代码讲解

## 本版目标和边界

v920 的目标是建立 randomized holdout bounded promotion gate。

v919 已经 review 了 v918 candidate packet，并批准它进入 bounded gate。v920 不把这个批准直接解释为 promotion，而是把 gate 条件写成独立检查：

- v919 review 文件必须存在。
- v918 packet 文件必须存在。
- review 必须通过。
- packet 必须通过。
- 20-case floor 必须满足。
- review 和 packet 的 case count 必须一致。
- seed 必须一致。
- pass rate 必须保持 `1.0`。
- clean case count 必须等于 candidate count。
- negative control 必须仍为 `0`。
- promotion 相关字段必须仍为 `False`。

明确不做：

- 不重新训练。
- 不重新 replay。
- 不重建 v918 packet。
- 不重做 v919 review。
- 不批准 direct promotion。

本版只允许进入 bounded promotion decision。

## 前置链路

```text
v914 randomized target-hidden suite
  -> v915 dry-run
  -> v916 real replay
  -> v917 replay review
  -> v918 candidate promotion packet
  -> v919 packet review
  -> v920 bounded promotion gate
  -> next bounded promotion decision
```

v920 是 gate，不是 decision。它只回答：“现在有没有资格进入最终 bounded decision？”

## 关键文件

### `src/minigpt/randomized_holdout_bounded_promotion_gate.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_holdout_bounded_promotion_gate(...)
```

输入：

- v919 candidate packet review report。
- v918 candidate packet report。
- 可选 `candidate_packet_review_path`。
- 可选 `candidate_packet_path`。
- `minimum_candidate_cases`，默认 `20`。

输出：

```text
status
decision
exit_code
failed_count
issues
candidate_packet_review_path
candidate_packet_path
candidate_packet_review_summary
candidate_packet_summary
candidate_packet_review
candidate_packet
check_rows
gate
summary
interpretation
```

### locator 函数

本版提供两个 locator：

```python
locate_randomized_holdout_candidate_packet_review(...)
locate_randomized_holdout_candidate_packet(...)
```

它们支持直接传 JSON 文件，也支持传输出目录。

真实运行时传入：

```text
e/919/解释/randomized-holdout-candidate-promotion-packet-review
e/918/解释/randomized-holdout-candidate-promotion-packet
```

## Checks

核心函数：

```python
_checks(...)
```

v920 共 19 条检查。

文件存在性：

```text
review_file_exists
packet_file_exists
```

v919 review 状态：

```text
review_passed
review_decision_ready
review_summary_ready
review_approves_bounded_gate
review_routes_to_gate
```

v918 packet 状态：

```text
packet_passed
packet_ready
```

随机 holdout 一致性：

```text
candidate_count_floor
candidate_counts_match
random_seed_matches
pass_rate_complete
clean_cases_match
packet_negative_control_rejected
source_checks_clean
```

promotion 边界：

```text
promotion_still_false
approved_for_promotion_false
claim_scope_bounded
```

这些 checks 把 v919/v918 的摘要重新对齐一次，避免 gate 只相信单个上游字段。

## `_gate`

`_gate` 生成 gate 本体：

```text
gate_ready
gate_decision
allowed_next_steps
blocked_next_steps
candidate_case_count
random_seed
pass_rate
clean_randomized_case_count
review_scope
handoff_status
promotion_ready
approved_for_promotion
approved_for_bounded_promotion_decision
model_quality_claim
next_step
```

真实 v920 gate：

```text
gate_ready=True
gate_decision=allow_bounded_randomized_holdout_promotion_decision
allowed_next_steps=[
  record_randomized_holdout_bounded_promotion_decision,
  build_randomized_holdout_decision_index
]
candidate_case_count=20
random_seed=914
pass_rate=1.0
promotion_ready=False
approved_for_promotion=False
approved_for_bounded_promotion_decision=True
model_quality_claim=bounded_gate_only
next_step=record_randomized_holdout_bounded_promotion_decision
```

这里的关键边界是：

```text
approved_for_bounded_promotion_decision=True
approved_for_promotion=False
promotion_ready=False
```

这说明可以进入 bounded decision，但还没有批准 promotion。

## `_summary`

`_summary` 给下游压缩 gate 结论：

```text
randomized_holdout_bounded_promotion_gate_ready
gate_decision
candidate_case_count
random_seed
pass_rate
clean_randomized_case_count
review_scope
promotion_ready
approved_for_promotion
approved_for_bounded_promotion_decision
model_quality_claim
next_step
passed_check_count
failed_check_count
```

真实 summary：

```text
randomized_holdout_bounded_promotion_gate_ready=True
gate_decision=allow_bounded_randomized_holdout_promotion_decision
candidate_case_count=20
random_seed=914
pass_rate=1.0
approved_for_bounded_promotion_decision=True
promotion_ready=False
failed_check_count=0
```

## `resolve_exit_code`

CLI 支持三个门槛：

```python
resolve_exit_code(
    report,
    require_gate_ready=True,
    require_decision_approval=True,
    require_promotion_ready=False,
)
```

真实运行启用：

```text
--require-gate-ready
--require-decision-approval
```

测试中保留：

```text
require_promotion_ready -> 1
```

这防止 gate 被误认为 direct promotion。

## `src/minigpt/randomized_holdout_bounded_promotion_gate_artifacts.py`

artifact 模块负责输出：

```text
JSON
CSV
TXT
Markdown
HTML
```

CSV 写 checks。

Markdown/HTML 重点展示：

- Gate ready。
- Gate decision。
- Candidate cases。
- Seed。
- Pass rate。
- Bounded decision approval。
- Promotion false。
- Allowed next steps。

HTML 第一屏刻意展示 `Bounded decision=True` 和 `Promotion=False`，方便截图说明本版边界。

## `scripts/check_randomized_holdout_bounded_promotion_gate.py`

CLI 参数：

```text
--candidate-packet-review
--candidate-packet
--minimum-candidate-cases
--out-dir
--require-gate-ready
--require-decision-approval
--require-promotion-ready
--force
```

真实命令：

```powershell
python scripts\check_randomized_holdout_bounded_promotion_gate.py `
  --candidate-packet-review e\919\解释\randomized-holdout-candidate-promotion-packet-review `
  --candidate-packet e\918\解释\randomized-holdout-candidate-promotion-packet `
  --out-dir e\920\解释\randomized-holdout-bounded-promotion-gate `
  --require-gate-ready `
  --require-decision-approval `
  --force
```

真实输出：

```text
status=pass
decision=randomized_holdout_bounded_promotion_gate_passed
randomized_holdout_bounded_promotion_gate_ready=True
gate_decision=allow_bounded_randomized_holdout_promotion_decision
candidate_case_count=20
random_seed=914
pass_rate=1.0
approved_for_bounded_promotion_decision=True
promotion_ready=False
model_quality_claim=bounded_gate_only
next_step=record_randomized_holdout_bounded_promotion_decision
passed_check_count=19
failed_check_count=0
```

## 测试覆盖

新增测试：

```text
tests/test_randomized_holdout_bounded_promotion_gate.py
```

覆盖点：

- 干净 v919 review + v918 packet 可以通过 gate。
- review 不批准 gate 时失败。
- packet seed 漂移时失败。
- direct promotion 被提前置真时失败。
- locator、artifact 输出和 CLI 正常工作。

关键断言：

```text
randomized_holdout_bounded_promotion_gate_ready=True
approved_for_bounded_promotion_decision=True
promotion_ready=False
approved_for_promotion=False
resolve_exit_code(require_promotion_ready=True) == 1
```

## 运行证据

归档：

```text
e/920/解释/说明.md
e/920/解释/randomized-holdout-bounded-promotion-gate/
e/920/图片/v920-randomized-holdout-bounded-promotion-gate.png
```

Playwright MCP snapshot 确认：

- `Status=pass`
- `Gate ready=True`
- `Cases=20`
- `Seed=914`
- `Pass rate=1.0`
- `Bounded decision=True`
- `Promotion=False`
- `Claim=bounded_gate_only`
- `Next=record_randomized_holdout_bounded_promotion_decision`
- 19 条 checks 均为 pass。

## 一句话总结

v920 把 v919 review 和 v918 packet 升级为 bounded promotion decision 的合格 gate 输入，但仍然没有批准 direct promotion。
