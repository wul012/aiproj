# v921 randomized holdout bounded promotion decision 代码讲解

## 本版目标和边界

v921 的目标是记录 randomized holdout bounded promotion decision。

v920 已经证明 v919 review 和 v918 packet 能通过 bounded gate。v921 在这个基础上做最终 bounded decision：接受一个有边界的模型能力声明。

这个声明的边界是：

```text
randomized_target_hidden_20_case_tiny_checkpoint_only
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不修改 v918-v920 的证据。
- 不批准 production promotion。
- 不声称模型具备通用语言能力。

## 前置链路

```text
v918 candidate promotion packet
  -> v919 packet review
  -> v920 bounded promotion gate
  -> v921 bounded promotion decision
```

v921 是这段 randomized holdout 链路的 bounded acceptance 点。

## 关键文件

### `src/minigpt/randomized_holdout_bounded_promotion_decision.py`

入口函数：

```python
build_randomized_holdout_bounded_promotion_decision(...)
```

输入：

- v920 bounded promotion gate。
- v919 candidate packet review。
- v918 candidate packet。
- 可选三个 source path。
- `minimum_candidate_cases=20`。

输出：

```text
status
decision
failed_count
issues
gate_path
candidate_packet_review_path
candidate_packet_path
gate_summary
candidate_packet_review_summary
candidate_packet_summary
gate
check_rows
final_decision
summary
interpretation
```

### locator 函数

本版提供三个 locator：

```python
locate_randomized_holdout_bounded_promotion_gate(...)
locate_randomized_holdout_candidate_packet_review(...)
locate_randomized_holdout_candidate_packet(...)
```

它们支持 JSON 文件和输出目录两种输入。

## Checks

v921 共 19 条检查。

文件存在性：

```text
gate_file_exists
review_file_exists
packet_file_exists
```

上游状态：

```text
gate_passed
gate_decision_passed
gate_ready
gate_allows_bounded_decision
gate_routes_to_decision
review_passed
packet_passed
```

随机 holdout 一致性：

```text
candidate_count_floor
candidate_counts_match
random_seed_matches
pass_rate_complete
clean_cases_match
source_checks_clean
```

边界约束：

```text
promotion_still_false
approved_for_promotion_false
claim_scopes_expected
```

这些 checks 确保 decision 不只相信 v920 gate 的一句话摘要，而是重新对齐 gate、review、packet 三层证据。

## `_final_decision`

`_final_decision` 是 v921 的核心：

```text
accepted
decision
bounded_promotion_accepted
promotion_ready
approved_for_promotion
candidate_case_count
random_seed
pass_rate
claim_scope
model_quality_claim
review_scope
next_step
```

真实结果：

```text
accepted=True
decision=accept_bounded_randomized_holdout_claim
bounded_promotion_accepted=True
promotion_ready=False
approved_for_promotion=False
candidate_case_count=20
random_seed=914
pass_rate=1.0
claim_scope=randomized_target_hidden_20_case_tiny_checkpoint_only
model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only
next_step=build_randomized_holdout_decision_index
```

`bounded_promotion_accepted=True` 是本版最重要的新字段。

但它与 direct promotion 分开：

```text
promotion_ready=False
approved_for_promotion=False
```

## `_summary`

summary 给下游消费：

```text
randomized_holdout_bounded_promotion_decision_ready
final_decision
bounded_promotion_accepted
promotion_ready
approved_for_promotion
candidate_case_count
random_seed
pass_rate
claim_scope
model_quality_claim
review_scope
next_step
passed_check_count
failed_check_count
```

真实 summary：

```text
randomized_holdout_bounded_promotion_decision_ready=True
final_decision=accept_bounded_randomized_holdout_claim
bounded_promotion_accepted=True
promotion_ready=False
claim_scope=randomized_target_hidden_20_case_tiny_checkpoint_only
failed_check_count=0
```

## `resolve_exit_code`

CLI 支持三个门槛：

```python
resolve_exit_code(
    report,
    require_decision_ready=True,
    require_bounded_acceptance=True,
    require_promotion_ready=False,
)
```

真实运行启用前两个门槛。

测试中保留：

```text
require_promotion_ready -> 1
```

这保护 v921 不会被误读成 production promotion。

## `src/minigpt/randomized_holdout_bounded_promotion_decision_artifacts.py`

artifact 模块输出：

```text
JSON
CSV
TXT
Markdown
HTML
```

HTML 第一屏展示：

- Decision ready。
- Bounded accepted。
- Promotion。
- Cases。
- Seed。
- Pass rate。
- Claim scope。
- Next。

截图里能直接看到 `Bounded accepted=True` 和 `Promotion=False`。

## `scripts/decide_randomized_holdout_bounded_promotion.py`

CLI 参数：

```text
--gate
--candidate-packet-review
--candidate-packet
--minimum-candidate-cases
--out-dir
--require-decision-ready
--require-bounded-acceptance
--require-promotion-ready
--force
```

真实命令：

```powershell
python scripts\decide_randomized_holdout_bounded_promotion.py `
  --gate e\920\解释\randomized-holdout-bounded-promotion-gate `
  --candidate-packet-review e\919\解释\randomized-holdout-candidate-promotion-packet-review `
  --candidate-packet e\918\解释\randomized-holdout-candidate-promotion-packet `
  --out-dir e\921\解释\randomized-holdout-bounded-promotion-decision `
  --require-decision-ready `
  --require-bounded-acceptance `
  --force
```

## 测试覆盖

新增测试：

```text
tests/test_randomized_holdout_bounded_promotion_decision.py
```

覆盖点：

- 干净 gate/review/packet 接受 bounded claim。
- gate 不批准 bounded decision 时失败。
- candidate count 低于 20 时失败。
- direct promotion 被提前置真时失败。
- locator、artifact 输出和 CLI 正常工作。

关键断言：

```text
bounded_promotion_accepted=True
promotion_ready=False
approved_for_promotion=False
claim_scope=randomized_target_hidden_20_case_tiny_checkpoint_only
```

## 运行证据

归档：

```text
e/921/解释/说明.md
e/921/解释/randomized-holdout-bounded-promotion-decision/
e/921/图片/v921-randomized-holdout-bounded-promotion-decision.png
```

Playwright MCP snapshot 确认：

- `Status=pass`
- `Decision ready=True`
- `Bounded accepted=True`
- `Promotion=False`
- `Cases=20`
- `Seed=914`
- `Pass rate=1.0`
- `Claim scope=randomized_target_hidden_20_case_tiny_checkpoint_only`
- 19 条 checks 均为 pass。

## 一句话总结

v921 首次把 randomized target-hidden 20/20 信号记录为 bounded model capability acceptance，但仍然明确拒绝 production promotion。
