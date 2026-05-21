# v361 governance routing keyword hit

## 本版目标

这一版只做一件事：把 v360 里已经识别出来的 `keyword` 路由结果继续补全，明确写出“命中了哪个关键词”。

它解决的是可解释性问题，不是再扩治理链条，不是增加新路由规则，也不是扩展新的版本体系。

## 本版来自哪里

这一版承接的是 v357-v360 的治理稳定化路线：

- v357 先冻结新治理链扩展
- v358 要求每条链都带 review reason 和 expansion rule
- v359 把 proposal 路由到已有链
- v360 记录路由 basis，区分 exact 和 keyword
- v361 继续补 `keyword` 命中的具体词，让报告不只知道“是 keyword”，还知道“是哪一个 keyword”

## 关键改动文件

- `src/minigpt/maintenance_policy.py`
  - 负责把 proposal 归一化、匹配治理链、生成路由决策。
  - 这一版新增 `matched_keyword`，并把它带进 proposal item 和 routing summary。
- `src/minigpt/maintenance_policy_artifacts.py`
  - 负责 JSON 之外的 Markdown / HTML 证据呈现。
  - 这一版把 `matched_keyword`、`keyword_hits` 显式放进表格和摘要。
- `scripts/check_maintenance_batching.py`
  - 负责 CLI 输出。
  - 这一版让 stdout 也能看到命中的关键词列表。
- `tests/test_maintenance_policy.py`
  - 负责验证 exact、keyword、review、reject 三条路由分支。
  - 这一版补了 keyword-hit 的断言，防止字段只改了对象没改出口。

## 核心数据

### `matched_keyword`

当 proposal 通过 keyword 路由进入某条链时，报告会额外记录具体命中的词。

例如：

- `dataset` -> `dataset-provenance`
- `promotion` -> `training-promotion`

### `keyword_hits`

这是 routing 汇总层的命中词列表，用来快速看到本次治理 proposal 里到底走了哪些关键词路径。

它是证据摘要，不是新的路由规则。

## 流程

1. 输入 proposal items。
2. 先做 exact chain id 匹配。
3. 如果 exact 不命中，再走 keyword map。
4. 命中后写入 `match_basis` 和 `matched_keyword`。
5. 汇总层统计 `exact_match_count`、`keyword_match_count` 和 `keyword_hits`。
6. Markdown / HTML / CLI 同步展示。

## 测试覆盖

这版测试保护了三件事：

- keyword 命中时能拿到具体词
- exact 命中时不会误报 keyword
- CLI stdout 和渲染报告都能看到新增字段

## 一句话总结

v361 把治理 proposal 的 keyword 路由从“知道命中了”推进到“知道命中了什么”，证据链更可读，也更适合后续审计。
