# v918 randomized holdout candidate promotion packet 代码讲解

## 本版目标和边界

v918 的目标是把 v914-v917 的 randomized target-hidden holdout 链路整理成一份 candidate promotion packet。

v917 的结论是：20 条 seeded randomized target-hidden prompt 在真实 replay 中 `20/20` 命中，并且 review 没发现目标词泄漏、已知 task hint、重复 prompt 或非 randomized prompt。因此 v917 允许进入 candidate promotion packet。

v918 不扩大这个结论。它只做证据打包和契约检查：

- 四个源产物必须都存在。
- suite、dry-run、real replay、review 必须都通过。
- seed 必须一致。
- case count 必须一致。
- replay pass rate 必须保持 `1.0`。
- dry-run 负控必须仍然失败。
- promotion 必须仍然是 `False`。

明确不做：

- 不重新训练。
- 不重新执行模型 replay。
- 不改写 v914 suite。
- 不批准 direct promotion。
- 不把 tiny GPT 的局部 holdout 结果包装成生产级模型质量。

## 前置链路

```text
v914 randomized target-hidden suite
  -> v915 dry-run
  -> v916 real replay
  -> v917 replay review
  -> v918 candidate promotion packet
  -> next packet review
```

v918 是从“review 允许候选包”到“候选包可复核”的中间层。它让后续 review 不必在四个目录里手工找证据。

## 关键文件

### `src/minigpt/randomized_holdout_candidate_promotion_packet.py`

这是本版核心 builder。

入口函数：

```python
build_randomized_holdout_candidate_promotion_packet(...)
```

输入：

- v917 replay review report。
- v916 real replay report。
- v915 dry-run report。
- v914 randomized suite report。
- 可选的四个 source path。

输出：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_replay_review`
- `source_real_replay`
- `source_dry_run`
- `source_holdout_suite`
- `replay_review_summary`
- `real_replay_summary`
- `dry_run_summary`
- `holdout_suite_summary`
- `evidence_rows`
- `check_rows`
- `packet`
- `summary`
- `interpretation`

### locator 函数

本版提供四个 locator：

```python
locate_randomized_holdout_replay_review(...)
locate_randomized_holdout_real_replay(...)
locate_randomized_holdout_dry_run(...)
locate_randomized_holdout_suite(...)
```

它们支持两种输入：

- 直接传 JSON 文件。
- 传输出目录，自动补齐默认 JSON 文件名。

这让 CLI 可以直接吃 `e/917/解释/...` 这样的目录，不需要用户记完整文件名。

### `read_json_report`

`read_json_report` 使用 `utf-8-sig` 读取 JSON。

这个细节是为了兼容历史上偶尔出现的 BOM 文件。CI 里已经有 source encoding 检查，但读取端仍然保持保守兼容。

## Evidence Manifest

核心函数：

```python
_evidence_rows(...)
```

它生成 4 行 manifest：

```text
randomized_replay_review
randomized_real_replay
randomized_dry_run
randomized_suite
```

每行字段：

```text
kind
path
exists
status
decision
ready_key
ready_value
promotion_ready
role
```

这份 manifest 的作用不是重新计算模型结果，而是把四个源文件的角色、状态和路径放到同一个只读视图中。

其中 `role` 明确写出每份证据承担的职责：

- replay review：授权候选包，同时阻止 direct promotion。
- real replay：证明真实 checkpoint 在 20 条 randomized target-hidden prompt 上通过。
- dry-run：证明 scoring contract 会拒绝 `fixed only` 负控。
- suite：定义 20 条 target-hidden randomized prompt。

## Checks

核心函数：

```python
_checks(...)
```

v918 共生成 23 条检查。

输入状态检查：

```text
replay_review_passed
real_replay_passed
dry_run_passed
suite_passed
```

ready summary 检查：

```text
replay_review_ready
real_replay_ready
dry_run_ready
suite_ready
real_model_signal_ready
```

候选包边界检查：

```text
candidate_packet_authorized
review_blocks_direct_promotion
review_routes_to_packet
all_inputs_keep_promotion_false
```

随机 holdout 一致性检查：

```text
candidate_count_at_least_twenty
suite_cases_match_summary
case_counts_consistent
random_seed_consistent
pass_rate_complete
clean_randomized_cases_complete
target_hidden_complete
no_task_hints_or_leakage
```

证据路径检查：

```text
all_evidence_files_exist
```

这些检查保护两件事：

1. v918 不能丢掉任何上游证据。
2. v918 不能把 candidate packet 偷偷升级成 promotion。

## `_packet`

`_packet` 生成给下游 review 使用的核心包：

```text
packet_ready
handoff_status
candidate_case_count
suite_case_count
random_seed
randomized_case_factor
passed_case_count
pass_rate
clean_randomized_case_count
positive_dry_run_passed_case_count
negative_dry_run_passed_case_count
candidate_packet_authorized
promotion_ready
approved_for_promotion
model_quality_claim
next_step
evidence_rows
```

真实 v918 packet 中：

```text
packet_ready=True
candidate_case_count=20
random_seed=914
pass_rate=1.0
clean_randomized_case_count=20
candidate_packet_authorized=True
promotion_ready=False
approved_for_promotion=False
model_quality_claim=candidate_packet_only
next_step=review_randomized_holdout_candidate_promotion_packet
```

这里最重要的是 `model_quality_claim=candidate_packet_only`。

它表达的是：这份包可以进入候选 review，但不等于模型已经完成推广。

## `_summary`

`_summary` 把 packet 和 checks 压成一层可读摘要：

```text
randomized_holdout_candidate_promotion_packet_ready
handoff_status
candidate_case_count
suite_case_count
random_seed
randomized_case_factor
passed_case_count
pass_rate
clean_randomized_case_count
positive_dry_run_passed_case_count
negative_dry_run_passed_case_count
candidate_packet_authorized
promotion_ready
approved_for_promotion
model_quality_claim
next_step
evidence_count
passed_check_count
failed_check_count
```

真实结果：

```text
randomized_holdout_candidate_promotion_packet_ready=True
candidate_case_count=20
random_seed=914
pass_rate=1.0
clean_randomized_case_count=20
candidate_packet_authorized=True
promotion_ready=False
failed_check_count=0
```

## `resolve_exit_code`

CLI 支持两个门槛：

```python
resolve_exit_code(
    report,
    require_packet_ready=True,
    require_promotion_ready=False,
)
```

`--require-packet-ready` 用于本版真实运行和 CI 风格验证。

`--require-promotion-ready` 则是更严格的未来门槛。v918 真实运行不使用它，因为本版边界就是不能批准 promotion。

单测里显式断言：

```text
require_packet_ready -> 0
require_promotion_ready -> 1
```

这能防止未来有人误把候选包当成正式 promotion。

## `src/minigpt/randomized_holdout_candidate_promotion_packet_artifacts.py`

artifact 模块负责输出：

```text
JSON
CSV
TXT
Markdown
HTML
```

它不做业务判断，只消费 builder 产出的 report。

CSV 写 evidence manifest，方便后续脚本按行检查源证据。

Markdown 和 HTML 同时展示：

- 顶部摘要。
- Evidence Manifest。
- Checks。

HTML 卡片里刻意把 `Packet ready=True` 和 `Promotion=False` 放在第一屏，因为这是 v918 的核心边界。

## `scripts/build_randomized_holdout_candidate_promotion_packet.py`

CLI 参数：

```text
--replay-review
--real-replay
--dry-run
--holdout-suite
--out-dir
--require-packet-ready
--require-promotion-ready
--force
```

真实运行命令：

```powershell
python scripts\build_randomized_holdout_candidate_promotion_packet.py `
  --replay-review e\917\解释\randomized-target-hidden-holdout-replay-review `
  --real-replay e\916\解释\randomized-target-hidden-holdout-real-replay `
  --dry-run e\915\解释\randomized-target-hidden-holdout-dry-run `
  --holdout-suite e\914\解释\randomized-target-hidden-holdout-suite `
  --out-dir e\918\解释\randomized-holdout-candidate-promotion-packet `
  --require-packet-ready `
  --force
```

输出：

```text
status=pass
decision=randomized_holdout_candidate_promotion_packet_ready
failed_count=0
randomized_holdout_candidate_promotion_packet_ready=True
candidate_case_count=20
random_seed=914
pass_rate=1.0
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_candidate_promotion_packet.py
```

覆盖点：

- 干净链路生成 candidate packet，但 promotion 仍为 False。
- review 未授权 candidate packet 时失败。
- dry-run 负控通过时失败。
- seed 不一致时失败。
- locator、artifact 输出和 CLI 都能正常工作。

关键断言：

```text
randomized_holdout_candidate_promotion_packet_ready=True
promotion_ready=False
resolve_exit_code(require_packet_ready=True) == 0
resolve_exit_code(require_promotion_ready=True) == 1
```

这组断言保护本版最重要的语义：候选包已准备好，正式 promotion 仍被挡住。

## 运行证据

运行证据归档：

```text
e/918/解释/说明.md
e/918/解释/randomized-holdout-candidate-promotion-packet/
e/918/图片/v918-randomized-holdout-candidate-promotion-packet.png
```

Playwright MCP snapshot 看到：

- `Status=pass`
- `Packet ready=True`
- `Cases=20`
- `Seed=914`
- `Pass rate=1.0`
- `Candidate=True`
- `Promotion=False`
- 4 个 evidence source 均存在。
- 23 条 checks 均通过。

## 一句话总结

v918 把 randomized target-hidden 的干净 20/20 信号变成可复核的候选 promotion 包，同时明确把正式 promotion 留在下一层 review 之后。
