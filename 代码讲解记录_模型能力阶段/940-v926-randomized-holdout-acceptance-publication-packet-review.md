# v926 randomized holdout acceptance publication packet review 代码讲解

## 本版目标和边界

v926 的目标是审阅 v925 publication packet，确认它可以进入 bounded downstream publication decision。

v925 已经把 v923 summary 和 v924 contract check 打成 publication packet。v926 不重新生成 packet，而是做审阅层判断：

```text
packet 是否完整？
边界是否还在？
是否只允许 bounded governance use？
是否仍然阻止 production promotion？
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不重新打包 v925。
- 不批准 production promotion。
- 不扩大模型能力声明。

## 前置链路

```text
v925 acceptance publication packet
  -> v926 acceptance publication packet review
```

v926 的输出将下一步路由到：

```text
record_randomized_holdout_publication_decision
```

## 关键文件

### `src/minigpt/randomized_holdout_acceptance_publication_packet_review.py`

核心入口：

```python
build_randomized_holdout_acceptance_publication_packet_review(...)
```

输入：

- `publication_packet`：v925 JSON report。
- `publication_packet_path`：可选源路径。

输出：

```text
status
decision
failed_count
issues
publication_packet_path
source_packet_summary
source_packet
evidence_rows
accepted_claims
blocked_claims
check_rows
review
summary
interpretation
```

### `_checks(...)`

本版检查项包括：

```text
publication_packet_passed
publication_packet_ready_decision
packet_ready
handoff_ready_for_review
accepted_claim_count
blocked_claim_count
allowed_use_bounded
promotion_still_false
approved_for_promotion_false
contract_check_ready
evidence_count
evidence_files_exist
packet_checks_clean
```

这组检查保护三个核心条件：

1. v925 packet 是真的 ready packet。
2. accepted/blocked claims 数量和含义没有被改宽。
3. production promotion 仍然被阻止。

### `review`

通过时 `review` 结构包含：

```text
review_ready=True
review_decision=accept_publication_packet_for_bounded_downstream_review
approved_for_bounded_publication=True
approved_for_promotion=False
promotion_ready=False
accepted_claim_count=1
blocked_claim_count=3
allowed_use=bounded_model_capability_governance_only
review_scope=bounded_randomized_holdout_publication_review_only
next_step=record_randomized_holdout_publication_decision
```

这里的 `approved_for_bounded_publication=True` 不是生产推广，它只允许进入 bounded publication decision。

## Artifact writer

`src/minigpt/randomized_holdout_acceptance_publication_packet_review_artifacts.py` 输出：

- JSON：完整 review report。
- CSV：check rows。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 首屏突出：

```text
Review ready
Bounded publication
Promotion
Accepted
Blocked
Allowed use
Next
```

## CLI

脚本：

```text
scripts/review_randomized_holdout_acceptance_publication_packet.py
```

真实运行：

```powershell
python scripts\review_randomized_holdout_acceptance_publication_packet.py `
  --publication-packet e\925\解释\randomized-holdout-acceptance-publication-packet `
  --out-dir e\926\解释\randomized-holdout-acceptance-publication-packet-review `
  --require-review-ready `
  --require-publication-approval `
  --force
```

同样没有使用 `--require-promotion-ready`，因为正确结果仍是 promotion blocked。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_acceptance_publication_packet_review.py
```

覆盖：

1. 干净 v925 packet 可以通过 bounded publication review。
2. allowed use 扩大成 production promotion 时失败。
3. promotion_ready 被改成 true 时失败。
4. artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

focused 测试：

```text
8 passed
```

## 真实运行证据

真实 v926 读取：

```text
e/925/解释/randomized-holdout-acceptance-publication-packet
```

结果：

```text
status=pass
decision=randomized_holdout_acceptance_publication_packet_review_ready
approved_for_bounded_publication=True
promotion_ready=False
allowed_use=bounded_model_capability_governance_only
review_scope=bounded_randomized_holdout_publication_review_only
```

截图：

```text
e/926/图片/v926-randomized-holdout-acceptance-publication-packet-review.png
```

## 一句话总结

v926 把 randomized holdout publication packet 从“可交接”推进到“已审阅可进入 bounded publication decision”，同时继续阻止 direct promotion。
