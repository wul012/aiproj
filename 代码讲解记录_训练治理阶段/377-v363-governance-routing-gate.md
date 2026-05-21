# v363 governance routing gate

## 本版目标

这一版把 governance proposal routing 的结果变成一个可选门禁：默认仍然只报告，但当命令传入 `--require-clean-governance-routing` 时，只允许 clean merge 路径继续，遇到 review、ambiguous keyword 或 new-chain candidate 就退出 1。

它不新增治理链，不改变七条链定义，也不扩大报告面。它只是把 v359-v362 已经能识别的路由状态变成可执行的 preflight。

## 本版来自哪里

v363 承接的是治理收口路线：

- v357：暂停新增治理链
- v358：补齐 review reason 和 expansion rule
- v359：proposal 优先路由到现有链
- v360：记录 exact / keyword basis
- v361：记录 keyword hit
- v362：多链 keyword 命中进入 review
- v363：可选要求路由必须 clean，否则 CLI stop

这条线的核心是克制：先让现有七条链稳定，再允许后续扩展。

## 关键文件

- `scripts/check_maintenance_batching.py`
  - 新增 `--require-clean-governance-routing` 参数。
  - 新增 `build_governance_routing_requirement()`，把 routing summary 转成门禁对象。
  - 门禁失败时 `raise SystemExit(1)`。
- `src/minigpt/maintenance_policy_artifacts.py`
  - Markdown 输出新增 requirement 状态、决策、exit code、failed reasons。
  - HTML 输出新增 `Routing Requirement` 区块。
  - JSON 通过脚本注入 `routing_requirement`，让机器消费和截图证据一致。
- `tests/test_maintenance_policy.py`
  - 新增 clean pass 和 ambiguous fail 两类脚本测试。
  - 验证 stdout、JSON、Markdown、HTML 四种出口都带门禁证据。

## 核心数据结构

### `routing_requirement`

字段含义如下：

- `required`
  - 本次是否启用了 clean routing gate。
- `status`
  - `not-required`：默认报告模式。
  - `pass`：启用门禁且没有 blocking proposal。
  - `fail`：启用门禁且存在 review 或 new-chain candidate。
- `decision`
  - `report-only`、`continue` 或 `stop`。
- `exit_code`
  - `0` 表示命令可继续。
  - `1` 表示 clean gate 要求下必须停止。
- `blocking_count`
  - `review_count + new_chain_candidate_count`。
- `failed_reasons`
  - `review_required`
  - `ambiguous_keyword`
  - `new_chain_candidate`

`ambiguous_keyword` 作为 failed reason 是为了让失败原因比单纯的 `review_required` 更可解释。

## 运行流程

1. CLI 读取 governance proposals。
2. `build_governance_stabilization_review()` 生成 proposal routing。
3. `build_governance_routing_requirement()` 根据 routing summary 生成门禁对象。
4. 脚本把门禁对象写回 `governance_report["routing_requirement"]`。
5. `write_governance_stabilization_outputs()` 输出 JSON / CSV / Markdown / HTML。
6. stdout 打印门禁状态。
7. 如果 `exit_code=1`，脚本退出 1。

## 输入输出

### clean 输入

两个 proposal 都只命中单链 keyword：

- dataset -> `dataset-provenance`
- registry -> `registry-model-card`

结果：

- `governance_routing_decision=merge_existing`
- `governance_routing_requirement_status=pass`
- `exit_code=0`

### blocked 输入

一个 proposal 同时命中 dataset 和 benchmark：

- dataset/data -> `dataset-provenance`
- benchmark -> `benchmark-history`

结果：

- `governance_routing_decision=review_before_merge`
- `governance_routing_ambiguous_keyword_match_count=1`
- `governance_routing_requirement_status=fail`
- `exit_code=1`

## 测试覆盖

新增测试覆盖：

- 默认不传 `--require-clean-governance-routing` 时，门禁是 `not-required` 且 exit 0。
- clean proposal 传门禁后仍然 pass。
- ambiguous proposal 传门禁后 return code 为 1。
- JSON / Markdown / HTML 都写入 `routing_requirement`。

## 一句话总结

v363 把治理 proposal routing 从“能审计”推进到“能阻断”，让收口期的治理扩展可以接入 CI 或发布前 preflight。
