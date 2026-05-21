# 第一百五十三篇代码讲解：第359版 governance proposal routing

## 本版目标和边界

v359 的目标是延续 v357-v358 的治理链收口路线，把“新提案先并入现有 7 条链”的判断也落进 `maintenance_policy`。v357 先暂停新增治理链，v358 再补齐每条链的 `review_reason` 和 `expansion_rule`；v359 继续不新增第 8 条链，但开始接受 proposal items，并给出 `merge_existing`、`review_before_merge`、`reject_new_chain_during_pause` 三种路由结果。

本版解决的问题是：新的治理想法到来时，先判断它能不能落到现有链，而不是马上制造新的报告层。

本版不训练模型，不新增新的治理链类型，不改变已有 7 条链的 action/consumer/evidence 语义。

## 前置链路

```text
v357 governance stabilization review
  -> pause_new_governance_chains
  -> 7 chains, keep/watch/merge/cut

v358 governance stabilization reasons
  -> review_reason
  -> expansion_rule
  -> missing reason/rule becomes review

v359 governance proposal routing
  -> proposed_items
  -> route into existing chains first
  -> unmatched/high-risk items go to review or reject
```

## 关键文件

### `src/minigpt/maintenance_policy.py`

`build_governance_stabilization_review()` 新增 `proposed_items` 参数。它仍然会先规范化 7 条链、计算 summary，但现在会再调用 `_route_governance_proposals()`，把新提案转成可审查的 routing 结果。

核心返回结构多了两块：

- `proposal_routing`
- `recommendations` 中针对 routing decision 的补充建议

`_route_governance_proposals()` 负责汇总提案路由结果：

- `decision = not_applicable`：没有给提案时
- `decision = merge_existing`：全部都能并入现有链
- `decision = review_before_merge`：有高风险或弱匹配项，先复核
- `decision = reject_new_chain_during_pause`：出现无法并入现有链的新链候选

`_normalize_governance_proposal()` 把单条提案转成统一结构：

- `title`
- `target_chain`
- `suggested_chain`
- `route_decision`
- `risk_flags`
- `reason`
- `expansion_rule`

`_match_governance_chain()` 先按目标链 id 精确匹配，再按关键词映射做弱匹配。这样可以把 `dataset`、`benchmark`、`registry`、`release`、`ci`、`promotion`、`maturity` 这些常见治理语义落到现有链。

### `src/minigpt/maintenance_policy_artifacts.py`

JSON 继续保留完整 report；Markdown 和 HTML 新增 `Proposal Routing` 区块。

输出重点是：

- 路由决策
- 提案数量
- 并入现有链数量
- 需要复核数量
- 新链候选数量

HTML 里新增一个 routing table，把 `target_chain`、`suggested_chain`、`route_decision`、`reason`、`expansion_rule` 直接展示出来。

### `scripts/check_maintenance_batching.py`

新增 `--governance-proposals` 参数，允许 CLI 从 JSON 列表读取提案。

stdout 新增：

- `governance_routing_decision`
- `governance_routing_item_count`
- `governance_routing_merge_existing_count`
- `governance_routing_review_count`
- `governance_routing_new_chain_candidate_count`

这让命令行结果可以直接告诉 CI：新提案是被收口到现有链，还是需要人工复核。

## 测试覆盖

`tests/test_maintenance_policy.py` 新增四类覆盖：

- 默认没有提案时，routing 为 `not_applicable`
- 普通提案能路由进现有链
- 高风险提案进入 `review_before_merge`
- 无匹配提案进入 `reject_new_chain_during_pause`

同时还检查：

- Markdown/HTML 包含 `Proposal Routing`
- CLI stdout 包含 routing counts

这些测试保护的是“治理收口阶段仍能消化新提案”，而不是只会拒绝扩张。

## 运行证据

运行证据放在：

```text
d/359/图片/01-governance-proposal-routing.png
d/359/解释/说明.md
```

截图展示：

- governance stabilization 仍保持 7 条链
- proposal routing 显示 `merge_existing`
- 两条提案分别落到 `dataset-provenance` 和 `training-promotion`

## 一句话总结

v359 让治理稳定评审从“暂停新增链”升级成“先把新提案路由进现有链”，把收口期做成了可执行的接纳机制。
