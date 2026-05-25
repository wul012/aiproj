# v431 promoted seed handoff assurance smoke contract helper 代码讲解

## 本版目标与边界

v431 的目标是把 v430 刚接入 assurance smoke 的 receipt contract summary/check 逻辑拆出来。v430 让一条 smoke 命令同时生成 handoff assurance、contract summary 和 summary-check sidecars，这是正确的集成方向；但它也让 `scripts/check_promoted_seed_handoff_assurance_smoke.py` 增长到 526 行。按照仓库“不要制造难维护巨型文件”的规则，v431 做一次小而明确的维护拆分。

本版不新增字段，不改变 smoke 命令参数，不改变 JSON/text summary 的输出契约，也不改变 promoted seed handoff 的执行规则。它只把一段已经稳定的 contract handling 从脚本挪到 helper 模块。

## 前置链路

本版承接 v426-v430：

- v426：receipt schema v3 校验 suite-design count/name。
- v427：hardening 了 receipt/check sidecar 篡改检测。
- v428：生成 compact receipt contract summary。
- v429：让 compact summary 可以被重算并校验 sidecar。
- v430：把 summary 和 summary-check 接入 assurance smoke。
- v431：拆分 v430 的 contract handling，保持 smoke 契约不变。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_assurance_smoke_contract.py`

这是新增 helper。它的核心函数是：

```text
build_receipt_contract_smoke_checks(
    handoff_dir,
    contract_summary_dir,
    contract_summary_check_dir,
    base_dir,
)
```

函数负责四件事：

1. 调用 v428 的 summary builder，从 handoff 目录生成 receipt contract summary。
2. 写出 summary 的 JSON/text/Markdown/HTML sidecars。
3. 调用 v429 的 summary checker，重新计算 expected summary 并校验 sidecars。
4. 返回 smoke summary 需要提升的 `checks` 字段和本段 contract issues。

返回的字段仍然是 v430 那组：

```text
receipt_contract_status
receipt_contract_decision
receipt_contract_schema_version
receipt_contract_sidecar_status
receipt_contract_issue_count
receipt_contract_summary_json/text/markdown/html
receipt_contract_summary_check_status
receipt_contract_summary_check_decision
receipt_contract_summary_check_sidecar_status
receipt_contract_summary_check_issue_count
receipt_contract_summary_check_json/text/markdown/html
```

模块还定义 `CONTRACT_SMOKE_OUTPUT_KEYS`，用于集中列出必须存在的八个 sidecar 输出路径。这样后续如果 contract sidecar 增减，不需要在主脚本里继续扩散路径检查。

### `scripts/check_promoted_seed_handoff_assurance_smoke.py`

主脚本现在只保留 smoke 编排职责：

```text
写 seed -> 执行 handoff -> 读取 assurance -> 调 helper -> 汇总 checks/issues -> 写 summary -> 打印 stdout
```

v431 把直接依赖 v428/v429 contract 模块的 import 从脚本中移除，改成只调用：

```text
build_receipt_contract_smoke_checks(...)
```

这让脚本从 526 行降到 466 行。更重要的是职责变清楚：脚本管流程，helper 管 receipt contract sidecar 细节。

## 输入输出格式

输入与 v430 相同，仍然由 smoke 脚本内部生成 promoted seed：

```text
d/431/解释/assurance-smoke/seed-source/promoted-seed/promoted_training_scale_seed.json
```

输出也与 v430 相同：

```text
d/431/解释/assurance-smoke/handoff/
d/431/解释/assurance-smoke/contract-summary/
d/431/解释/assurance-smoke/contract-summary-check/
d/431/解释/assurance-smoke/promoted_seed_handoff_assurance_smoke_summary.json
d/431/解释/assurance-smoke/promoted_seed_handoff_assurance_smoke_summary.txt
```

这次拆分的关键是输出契约不变。`checks` 里仍能看到 `receipt_contract_status=pass` 和 `receipt_contract_summary_check_status=pass`，所以 CI 或 shell 读者不需要改解析逻辑。

## 测试覆盖

本版先做编译检查，确保新 helper、主脚本和既有测试能正常导入。

相关回归覆盖：

```text
python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt.py tests\test_promoted_training_scale_seed_handoff_receipt_contract.py tests\test_promoted_training_scale_seed_handoff_receipt_contract_check.py -q
```

结果为 `35 passed`。其中 assurance smoke 集成测试会真实运行主脚本，读取 smoke summary，并断言：

- contract summary status 为 `pass`
- schema version 为 `3`
- summary-check status 为 `pass`
- summary/check 的 JSON/text/Markdown/HTML sidecars 都存在
- stdout 和 text summary 里仍有关键字段

这说明 helper 拆分没有破坏 v430 的外部契约。

## 运行证据

运行证据归档在 `d/431`：

- `d/431/解释/assurance-smoke/`：拆分后的真实 smoke 输出目录。
- `d/431/图片/01-assurance-smoke-contract-helper-check.png`：Playwright MCP 渲染 summary-check HTML 的截图。
- `d/431/解释/assurance-smoke/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check_snapshot.md`：Playwright MCP 页面快照。
- `d/431/解释/说明.md`：运行截图、命令和证据边界说明。

截图仍使用 data URL 渲染同一份 HTML 内容，因为当前环境直接打开本地 `file://` 受限。

## 一句话总结

v431 把 promoted seed handoff assurance smoke 的 receipt contract 细节从主脚本中抽离，降低文件压力，同时保持 v430 的一体化 smoke 证据契约不变。
