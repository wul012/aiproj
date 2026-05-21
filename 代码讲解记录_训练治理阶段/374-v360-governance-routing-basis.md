# 第一百五十四篇代码讲解：第360版 governance routing basis

## 本版目标和边界

v360 的目标是把 v359 的 proposal routing 再解释一层。v359 已经能把治理提案路由到现有 7 条链，并区分 `merge_existing`、`review_before_merge` 和 `reject_new_chain_during_pause`；v360 继续保持这条边界，但把每条提案的匹配依据也写出来，方便看出它到底是 exact match 还是 keyword match。

本版解决的问题是：治理路由不只是“落到哪里”，还要能回答“凭什么落到这里”。

本版不新增治理链，不改变暂停窗口，也不改变现有链的 review_reason / expansion_rule 语义。

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

v360 governance routing basis
  -> exact match / keyword match
  -> show routing evidence in report and CLI
```

## 关键文件

### `src/minigpt/maintenance_policy.py`

`_route_governance_proposals()` 新增：

- `exact_match_count`
- `keyword_match_count`

`_normalize_governance_proposal()` 新增：

- `match_basis`

`_match_governance_chain()` 现在返回带 `match_basis` 的 chain 副本：

- exact chain id 命中时标记 `exact`
- keyword 映射命中时标记 `keyword`

这样路由结果仍然是 `merge_existing` / `review_before_merge` / `reject_new_chain_during_pause`，但提案级别的依据变得可读。

### `src/minigpt/maintenance_policy_artifacts.py`

Markdown 和 HTML 新增展示：

- `Exact matches`
- `Keyword matches`
- `Match basis`

HTML 的 Proposal Routing 表格现在多一列 `Match Basis`，这样页面上能直接看出提案是怎么匹配到现有链的。

### `scripts/check_maintenance_batching.py`

stdout 新增：

- `governance_routing_exact_match_count`
- `governance_routing_keyword_match_count`

这让命令行输出能直接反映 routing basis，而不是只说有多少条提案被并入。

## 测试覆盖

`tests/test_maintenance_policy.py` 新增覆盖：

- keyword 命中的 dataset 提案
- exact 命中的 training-promotion 提案
- 高风险 exact 命中提案会进入 review
- 未匹配提案仍然拒绝新链
- Markdown、HTML、CLI 都能看到 match basis 统计

测试保护的是“路由依据不丢”，不是只看最终决策。

## 运行证据

运行证据放在：

```text
d/360/图片/01-governance-routing-basis.png
d/360/解释/说明.md
```

截图展示：

- routing decision
- exact/keyword match 统计
- 提案级 Match Basis 列

## 一句话总结

v360 让治理提案路由从“知道结果”进一步变成“知道依据”，收口阶段的判断链条更完整了。
