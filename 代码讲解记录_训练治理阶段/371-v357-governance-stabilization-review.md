# 第一百五十一篇代码讲解：第357版 governance stabilization review

## 本版目标和边界

v357 的目标是把“aiproj 暂停新治理链 2-3 天，稳定/裁剪现有 7 条”的判断落到代码里。项目已经有 dataset snapshot、benchmark history、registry/model card、release readiness、CI/coverage、training promotion、maturity portfolio 等多条链路，继续新增 report family 的收益开始下降。

本版解决的问题是：将“暂不新增治理链、先检查现有链是否有消费者和证据”的规则做成 `maintenance_policy` 的一部分。

本版不新增新的业务治理链，不训练模型，不改变 release gate 或 model card 的判定，也不删除任何现有链路。

## 前置链路

本版承接两条既有能力：

```text
v109 maintenance batching policy
  -> 低风险工具迁移要合并发版

v110+ module pressure audit
  -> 大文件/压力模块只做定向拆分

v357 governance stabilization review
  -> 新治理链暂停，现有 7 条先稳定、复核、合并
```

它的关键点是“放进已有维护策略”，而不是另起一个 governance report 链。这样本版本身也遵守了收口原则。

## 关键文件

### `src/minigpt/maintenance_policy.py`

新增 `build_governance_stabilization_review()`。

默认 7 条治理链写在 `DEFAULT_GOVERNANCE_CHAINS`：

- `dataset-provenance`
- `benchmark-history`
- `registry-model-card`
- `release-readiness`
- `ci-coverage-hygiene`
- `training-promotion`
- `maturity-portfolio`

每条链都有固定字段：

```python
id
name
action
consumer
evidence
next_action
```

`action` 支持：

- `keep`：保留主干链。
- `watch`：保留但观察重复和膨胀。
- `merge`：后续应并入已有链。
- `cut`：后续可裁剪。

`_governance_summary()` 汇总：

- `chain_count`
- `keep_count`
- `watch_count`
- `merge_count`
- `cut_count`
- `missing_consumer_count`
- `missing_evidence_count`
- `consolidation_candidate_count`

默认 7 条链全部有 consumer 和 evidence，所以状态是 `pass`，决策是 `pause_new_governance_chains`。如果出现 `merge/cut` 或缺 consumer/evidence，则状态进入 `review`。

### `src/minigpt/maintenance_policy_artifacts.py`

新增 governance stabilization 的 artifact writer：

- `write_governance_stabilization_json`
- `write_governance_stabilization_csv`
- `write_governance_stabilization_markdown`
- `write_governance_stabilization_html`
- `write_governance_stabilization_outputs`

Markdown 和 HTML 都展示 summary、7 条链、consumer、evidence、next action 和 recommendations。CSV 则保留机器可读行，方便后续比较或裁剪。

这些产物是维护证据，不是发布门禁。

### `scripts/check_maintenance_batching.py`

这个脚本原本输出 maintenance batching 和 module pressure。v357 没有新建脚本，而是在原脚本里默认追加 governance stabilization 输出。

新增参数：

```text
--governance-chains
--governance-pause-days
--skip-governance-stabilization
```

stdout 新增：

```text
governance_status=pass
governance_decision=pause_new_governance_chains
governance_pause_days=3
governance_chain_count=7
governance_keep_count=5
governance_watch_count=2
governance_consolidation_candidate_count=0
```

这样 CI 日志或本地 shell 不打开 HTML，也能看到“暂停新增治理链”的状态。

## 测试覆盖

`tests/test_maintenance_policy.py` 新增三类测试：

- 默认 7 条链评审：断言 `pass`、`pause_new_governance_chains`、`chain_count=7`、`keep=5`、`watch=2`。
- merge/cut 候选：构造需要合并和裁剪的链，断言进入 `pause_and_consolidate_governance_chains`。
- 输出与脚本 stdout：检查 JSON/CSV/Markdown/HTML 存在，HTML 转义正常，脚本真实输出 governance 状态字段。

这些测试保护的是维护节奏规则：新增治理链前，必须先解释能否并入现有 7 条。

## 运行证据

运行证据放在：

```text
d/357/图片/01-governance-stabilization-review.png
d/357/解释/说明.md
```

截图可以看到：

- `Decision = pause_new_governance_chains`
- `Pause days = 3`
- `Chains = 7`
- `Keep = 5`
- `Watch = 2`
- 每条链的 consumer、evidence 和 next action

## 一句话总结

v357 把“暂停新增治理链、稳定/裁剪现有 7 条”落成维护策略评审，让 aiproj 的下一阶段先收口，再决定是否扩展。
