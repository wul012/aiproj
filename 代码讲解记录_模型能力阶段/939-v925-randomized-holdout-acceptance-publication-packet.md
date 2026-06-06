# v925 randomized holdout acceptance publication packet 代码讲解

## 本版目标和边界

v925 的目标是把 v923 acceptance summary 和 v924 contract check 打包成 publication packet。

前两版已经完成：

```text
v923: 把 bounded acceptance 写成 accepted/blocked claims
v924: 从 v922 decision index 重建 v923 summary，确认它没有被篡改
```

v925 在这个基础上做发布包，但这里的“发布”不是 production release，而是“给下游审阅和治理使用的只读交接包”。

明确不做：

- 不重新训练。
- 不重新 replay。
- 不重建 v923 或 v924。
- 不批准 production promotion。
- 不把 bounded 20-case tiny-checkpoint 结论扩大成通用质量结论。

## 前置链路

```text
v923 randomized holdout acceptance summary
  + v924 acceptance summary contract check
  -> v925 acceptance publication packet
```

v925 的核心价值是把“内容源”和“验真源”放进同一个 packet。

## 关键文件

### `src/minigpt/randomized_holdout_acceptance_publication_packet.py`

核心入口：

```python
build_randomized_holdout_acceptance_publication_packet(...)
```

输入：

- `acceptance_summary`：v923 summary JSON。
- `contract_check`：v924 check JSON。
- `acceptance_summary_path`：v923 路径。
- `contract_check_path`：v924 路径。

输出：

```text
status
decision
failed_count
issues
acceptance_summary
contract_check_summary
accepted_claims
blocked_claims
evidence_rows
check_rows
packet
summary
interpretation
```

### `evidence_rows`

v925 的 evidence rows 只有两项：

```text
acceptance_summary
acceptance_summary_contract_check
```

这很克制：packet 不再回头引用 v918-v922 全部文件，而是引用 v923 和 v924 这两个已经收束过的上游产物。

### `_checks(...)`

检查项包括：

- `acceptance_summary_passed`
- `acceptance_summary_ready`
- `contract_check_passed`
- `contract_check_ready`
- `contract_rebuild_matches`
- `bounded_acceptance_true`
- `accepted_claim_present`
- `blocked_claims_present`
- `allowed_use_bounded`
- `promotion_still_false`
- `approved_for_promotion_false`
- `evidence_files_exist`

这组检查保护两个方向：

1. 内容必须是真的：v923 pass，v924 pass，且 v924 original/rebuilt decision 一致。
2. 边界不能扩大：allowed use 必须 bounded，promotion 必须 false。

### `packet`

v925 的 `packet` 是下游最直接消费的结构：

```text
packet_ready
handoff_status
accepted_claim_count
blocked_claim_count
candidate_case_count
random_seed
pass_rate
promotion_ready
approved_for_promotion
allowed_use
model_quality_claim
contract_check_ready
accepted_claims
blocked_claims
evidence_rows
next_step
```

真实输出里：

```text
packet_ready=True
handoff_status=ready_for_bounded_acceptance_publication_review
accepted_claim_count=1
blocked_claim_count=3
promotion_ready=False
allowed_use=bounded_model_capability_governance_only
next_step=review_randomized_holdout_acceptance_publication_packet
```

## Artifact writer

`src/minigpt/randomized_holdout_acceptance_publication_packet_artifacts.py` 输出：

- JSON：完整 publication packet。
- CSV：证据文件表。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 首屏突出：

```text
Packet ready
Handoff
Accepted
Blocked
Promotion
Allowed use
Next
```

## CLI

脚本：

```text
scripts/build_randomized_holdout_acceptance_publication_packet.py
```

真实运行：

```powershell
python scripts\build_randomized_holdout_acceptance_publication_packet.py `
  --acceptance-summary e\923\解释\randomized-holdout-acceptance-summary `
  --contract-check e\924\解释\randomized-holdout-acceptance-summary-check `
  --out-dir e\925\解释\randomized-holdout-acceptance-publication-packet `
  --require-packet-ready `
  --force
```

没有使用 `--require-promotion-ready`，因为正确结果仍然是 promotion blocked。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_acceptance_publication_packet.py
```

覆盖：

1. verified summary + check 可以生成 ready packet。
2. contract check fail 时 packet fail。
3. `allowed_use` 被扩大成 production promotion 时 fail。
4. artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

focused 测试：

```text
13 passed
```

## 真实运行证据

真实 v925 读取：

```text
e/923/解释/randomized-holdout-acceptance-summary
e/924/解释/randomized-holdout-acceptance-summary-check
```

结果：

```text
status=pass
decision=randomized_holdout_acceptance_publication_packet_ready
randomized_holdout_acceptance_publication_packet_ready=True
handoff_status=ready_for_bounded_acceptance_publication_review
accepted_claim_count=1
blocked_claim_count=3
promotion_ready=False
allowed_use=bounded_model_capability_governance_only
evidence_count=2
```

截图：

```text
e/925/图片/v925-randomized-holdout-acceptance-publication-packet.png
```

## 一句话总结

v925 把 bounded randomized holdout acceptance 打包成下游可审阅的 publication packet，同时继续把 direct promotion 和通用质量声明挡在边界之外。
