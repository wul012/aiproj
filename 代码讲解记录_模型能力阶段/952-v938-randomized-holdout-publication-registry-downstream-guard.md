# v938 randomized holdout publication registry downstream guard 代码讲解

## 本版目标和边界

v938 的目标是给 v937 lookup index review 增加一层 downstream guard：

```text
v937 lookup index review
  -> v938 downstream guard
```

v937 已经确认 lookup index 可以进入 downstream governance lookup。v938 继续收紧边界，把“允许下游治理查阅”和“禁止生产晋级/结论扩张”放进同一个可复核产物中。

本版明确不做：

- 不重新训练模型。
- 不重新跑 holdout replay。
- 不修改 v936/v937 源证据。
- 不把 bounded randomized holdout 结论升级成生产级模型能力。

## 前置链路

v938 读取真实 v937 产物：

```text
e/937/解释/randomized-holdout-publication-registry-lookup-index-review
```

v937 的关键结论是：

- `review_status=approved_for_downstream_governance_lookup_only`
- `downstream_ready=True`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `rejected_use=production_promotion`

v938 不改变这些事实，只把它们转成更明确的消费护栏。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_guard.py`

核心入口：

```python
build_randomized_holdout_publication_registry_downstream_guard(...)
```

输入：

- `lookup_index_review_report`：v937 lookup index review JSON。
- `lookup_index_review_path`：v937 JSON 路径，用于检查真实文件存在。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
lookup_index_review_path
source_lookup_index_review_summary
source_lookup_index_review
entry_rows
check_rows
guard
summary
interpretation
```

`guard` 是本版核心数据结构：

```text
guard_ready
guard_id
guard_status
lookup_index_review_path
entry_count
lookup_keys
downstream_ready
lookup_ready
contract_check_ready
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
allowed_use
blocked_uses
next_step
```

其中最重要的是三类边界字段：

- `allowed_use=downstream_governance_lookup_only`
- `blocked_uses=[production_promotion, model_quality_expansion, training_data_claim_expansion]`
- `promotion_ready=False`

这三类字段共同说明：该产物只允许下游治理查阅，不能被下游误用成生产晋级凭据。

### `src/minigpt/randomized_holdout_publication_registry_downstream_guard_artifacts.py`

负责输出 JSON、CSV、TXT、Markdown 和 HTML。

JSON 是机器消费的最终证据；CSV 提供 entry rows；TXT 适合 CI 日志；Markdown 和 HTML 用于人工审阅与截图归档。

HTML 页面突出展示：

- status / guard ready / downstream / lookup / promotion / failed
- allowed use
- blocked uses
- next step
- entries
- checks

### `scripts/build_randomized_holdout_publication_registry_downstream_guard.py`

CLI 负责读取 v937 输入、生成 v938 输出，并根据参数决定退出码。

关键参数：

```text
--lookup-index-review
--out-dir
--require-guard-ready
--require-downstream-ready
--require-promotion-ready
--force
```

当前正常使用 `--require-guard-ready --require-downstream-ready`。如果使用 `--require-promotion-ready`，应返回失败，因为 v938 明确不批准 promotion。

## 核心检查

v938 有 16 个检查点：

```text
lookup_index_review_file_exists
lookup_index_review_passed
lookup_index_review_decision_ready
review_summary_ready
review_status_downstream_only
downstream_ready
lookup_ready
contract_check_ready
consumer_boundary_governance
allowed_use_downstream_only
rejected_use_production_promotion
promotion_still_false
lookup_keys_publication_namespace
entries_not_promoted
source_checks_clean
source_next_step_matches
```

这些检查共同保护三件事：

- v937 源 review 必须真实存在并通过。
- downstream lookup 可以继续消费。
- production promotion 和能力结论扩张必须保持阻断。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_guard.py
```

覆盖场景：

- ready 的 v937 review 可以生成 guard ready 的 v938 护栏。
- 如果 `rejected_use` 被改成 `none`，检查失败。
- 如果 `promotion_ready=True`，检查失败。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。
- `resolve_exit_code(... require_promotion_ready=True)` 必须返回失败。

聚焦测试：

```text
8 passed
```

## 真实运行证据

真实 v937 输入生成 v938 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_guard_ready
guard_status=downstream_governance_lookup_allowed
downstream_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
allowed_use=downstream_governance_lookup_only
blocked_uses=['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']
passed_check_count=16
failed_check_count=0
```

证据目录：

```text
e/938/解释/randomized-holdout-publication-registry-downstream-guard
e/938/图片/v938-randomized-holdout-publication-registry-downstream-guard.png
```

## 链路角色

v938 不是新的治理主线，而是 v937 的消费边界收口层。它让后续模块可以安全读取 publication registry lookup 结果，同时不能越界宣称：

- 已生产晋级。
- 模型能力已扩大。
- 训练数据结论已扩大。

## 一句话总结

v938 把 downstream lookup 从“已审阅可用”推进到“有明确护栏地可用”，让下游只能按治理查阅方式消费随机 holdout 发布登记结果。
