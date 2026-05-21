# v362 governance ambiguous keyword review

## 本版目标

这一版只解决一个边界问题：如果一条治理提案同时命中多个已有治理链的关键词，它不能被自动并入第一个命中的链，而应该进入 review。

它不新增治理链，不改变七条治理链的默认定义，也不扩展新的 dashboard 或报告层。v362 的目标是让 v357-v361 已经建立的治理暂停机制更稳一点。

## 本版来自哪里

v362 承接的是治理稳定化路线：

- v357：暂停新治理链扩展，先观察现有七条链。
- v358：要求每条链有 `review_reason` 和 `expansion_rule`。
- v359：把新 proposal 优先路由进现有链。
- v360：记录 exact / keyword 的 `match_basis`。
- v361：记录 keyword 路由命中的具体 `matched_keyword`。
- v362：当 keyword 同时命中多条链时，记录全部命中并转入 review。

这个顺序很重要：v362 不是功能扩张，而是给已有路由逻辑补一个保守边界。

## 关键文件

- `src/minigpt/maintenance_policy.py`
  - 负责 proposal routing 的核心决策。
  - `_match_governance_chain()` 现在不再遇到第一个 keyword 就返回，而是收集所有命中的链。
  - `_normalize_governance_proposal()` 根据 `match_basis=ambiguous_keyword` 把 proposal 标记为 `review`。
- `src/minigpt/maintenance_policy_artifacts.py`
  - 负责把 JSON 之外的 Markdown/HTML 证据渲染出来。
  - 本版增加 `ambiguous_keyword_match_count`、`ambiguous_keyword_hits`、`matched_keywords`、`matched_chains` 展示。
- `scripts/check_maintenance_batching.py`
  - 负责命令行 smoke 输出。
  - 本版把 ambiguous keyword 计数和命中词输出给 CI/shell 读者。
- `tests/test_maintenance_policy.py`
  - 负责锁住 exact、普通 keyword、高风险 review、unmatched reject、ambiguous review 的行为。
  - 新测试用 `dataset benchmark bridge` 触发多链命中。

## 核心数据结构

### `match_basis`

v362 后的主要取值包括：

- `exact`：用户显式指定了已有链 id。
- `keyword`：文本只命中一个治理链的关键词集合。
- `ambiguous_keyword`：文本命中多个治理链。
- 空字符串：没有命中任何已有链。

### `matched_keywords`

这是 ambiguous 场景的关键词列表。

例如 smoke 中的提案：

```text
Dataset benchmark bridge
dataset snapshot should be reviewed beside benchmark history before promotion
```

会命中：

- dataset/data -> `dataset-provenance`
- benchmark -> `benchmark-history`
- promotion -> `training-promotion`

因此它不能被自动 merge。

### `matched_chains`

这是被命中的治理链列表。报告仍保留 `suggested_chain`，但 ambiguous 情况下它只是第一建议链，不是自动合并目标。

## 运行流程

1. CLI 读取 `--governance-proposals` JSON。
2. `build_governance_stabilization_review()` 构造七条默认治理链。
3. `_route_governance_proposals()` 遍历 proposal。
4. `_match_governance_chain()` 先做 exact id 匹配。
5. exact 不命中时，keyword map 收集所有命中链。
6. 如果只命中一条链，按普通 `keyword` 处理。
7. 如果命中多条链，写入 `ambiguous_keyword`，并由 `_normalize_governance_proposal()` 转成 `review`。
8. JSON/Markdown/HTML/CLI 同步输出计数、命中词和命中链。

## 产物说明

- `governance_stabilization.json`
  - 机器可读的最终证据。
  - 包含 proposal item 的 `match_basis`、`matched_keywords`、`matched_chains`。
- `governance_stabilization.md`
  - 面向人读的审查记录。
  - Proposal Routing 表格能直接看到为什么跨链 proposal 进入 review。
- `governance_stabilization.html`
  - 用于截图和浏览器检查。
  - v362 的截图归档在 `d/362`。
- CLI stdout
  - 给 CI 或快速 shell 检查使用。
  - 关键字段是 `governance_routing_ambiguous_keyword_match_count` 和 `governance_routing_ambiguous_keyword_hits`。

## 测试覆盖

`tests/test_maintenance_policy.py` 的新增断言保护了这些行为：

- 多链 keyword 命中时 `decision=review_before_merge`。
- ambiguous item 的 `route_decision=review`。
- `keyword_match_count` 不会把 ambiguous 计入普通 keyword。
- `ambiguous_keyword_match_count=1`。
- `matched_chains` 包含 dataset、benchmark、training promotion 三条链。
- CLI stdout 输出 ambiguous keyword 相关字段。

这些断言保护的是治理边界，不是模型效果。它们证明项目在暂停扩链阶段不会把跨链提案静默吞进某一个已有链。

## 一句话总结

v362 给治理提案路由加上多链关键词复核边界，让“合并进已有链”更克制，也让后续维护者能看清一个提案为什么需要人工 review。
