# v430 promoted seed handoff assurance smoke contract summary check 代码讲解

## 本版目标与边界

v430 的目标是把 v428 和 v429 已经做好的 receipt contract summary 能力收进 `check_promoted_seed_handoff_assurance_smoke.py`。此前这条链路要分三步跑：先生成 handoff assurance，再生成 compact contract summary，最后对 summary JSON/text/Markdown/HTML sidecar 做重算校验。v430 解决的是“人工可能只跑第一步或漏跑 summary check”的问题。

本版不执行真实训练，不改变 promoted seed handoff 的决策条件，也不新增治理链。它只是把已有的 contract summary 和 summary-check 接到已有 assurance smoke 中，让一次 smoke 命令形成更完整的证据闭环。

## 前置链路

本版接在 v426-v429 后面：

- v426：automation receipt schema v3 增加 suite-design count/name 合同。
- v427：assurance smoke 能发现 schema-v3 receipt sidecar 的篡改。
- v428：把 handoff assurance 压成 compact receipt contract summary。
- v429：给 compact summary 增加 JSON/text/Markdown/HTML sidecar 自校验。
- v430：把 v428/v429 接入 assurance smoke 默认输出。

## 关键文件

### `scripts/check_promoted_seed_handoff_assurance_smoke.py`

这是本版的核心修改文件。它原本只负责：

1. 构造一个最小 promoted seed handoff 输入。
2. 调用 `execute_promoted_training_scale_seed.py`。
3. 检查 handoff assurance、embedded receipt-check 和 schema-v3 字段。
4. 写出 `promoted_seed_handoff_assurance_smoke_summary.json` 和 `.txt`。

v430 在同一条成功路径上新增两个目录：

```text
contract-summary/
contract-summary-check/
```

新增调用顺序是：

```text
build_promoted_training_scale_seed_handoff_receipt_contract_summary(handoff_dir)
write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(...)
check_promoted_training_scale_seed_handoff_receipt_contract_summary(contract_summary_dir)
write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(...)
```

这样 smoke summary 里会同时出现两组新增字段：

```text
receipt_contract_status
receipt_contract_decision
receipt_contract_schema_version
receipt_contract_sidecar_status
receipt_contract_issue_count
receipt_contract_summary_json/text/markdown/html
```

以及：

```text
receipt_contract_summary_check_status
receipt_contract_summary_check_decision
receipt_contract_summary_check_sidecar_status
receipt_contract_summary_check_issue_count
receipt_contract_summary_check_json/text/markdown/html
```

这些字段的语义很直接：前一组证明 compact summary 自身生成成功且来自 schema-v3 receipt contract；后一组证明 compact summary 及其 text/Markdown/HTML sidecar 可以从原始 handoff 重新计算并比对通过。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

本版没有新增测试文件，而是把断言加到已有 assurance smoke 集成测试里。原因是 v430 的价值不是新建一个独立 checker，而是确认原有 smoke 命令真的把 contract summary/check 串起来。

测试现在额外断言：

```text
receipt_contract_status == pass
receipt_contract_schema_version == 3
receipt_contract_sidecar_status == pass
receipt_contract_issue_count == 0
receipt_contract_summary_check_status == pass
receipt_contract_summary_check_sidecar_status == pass
receipt_contract_summary_check_issue_count == 0
```

同时检查 JSON/text/Markdown/HTML 八个输出文件都存在，并且 stdout/text summary 里能看到 `receipt_contract_status=pass` 和 `receipt_contract_summary_check_status=pass`。

## 输入输出格式

输入仍然是 smoke 脚本内部生成的 promoted seed JSON：

```text
d/430/解释/assurance-smoke/seed-source/promoted-seed/promoted_training_scale_seed.json
```

主要输出分三层：

```text
d/430/解释/assurance-smoke/handoff/
d/430/解释/assurance-smoke/contract-summary/
d/430/解释/assurance-smoke/contract-summary-check/
```

最上层 smoke summary 变成总索引：

```text
d/430/解释/assurance-smoke/promoted_seed_handoff_assurance_smoke_summary.json
d/430/解释/assurance-smoke/promoted_seed_handoff_assurance_smoke_summary.txt
```

它不会替代底层 JSON，而是引用底层 sidecar 路径，并把关键状态字段提升到 `checks` 里，方便 CI 或人工只看 summary 就知道三层检查是否都通过。

## 测试覆盖

本版重点测试不是“函数能调用”，而是链路不会漏侧车：

- 编译检查覆盖 smoke 脚本和相关测试文件，防止导入/语法错误。
- 相关回归覆盖 handoff receipt、contract summary 和 summary-check 三组测试。
- assurance smoke 集成测试会真实运行脚本、读取 summary JSON、检查输出文件存在，并确认 stdout/text summary 都出现新字段。

这保护了两个关键风险：

1. summary/check sidecar 没生成，但 smoke 仍误报 pass。
2. stdout 或 text summary 没有暴露新状态，导致 CI shell 读者看不到合同检查结果。

## 运行证据

运行证据归档在 `d/430`：

- `d/430/解释/assurance-smoke/`：真实 smoke 输出目录。
- `d/430/图片/01-assurance-smoke-contract-summary-check.png`：Playwright MCP 渲染 summary-check HTML 的截图。
- `d/430/解释/assurance-smoke/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check_snapshot.md`：Playwright MCP 页面快照。
- `d/430/解释/说明.md`：运行截图和证据边界说明。

截图使用 data URL 渲染同一份 HTML 内容，因为当前环境直接打开本地 `file://` 受限；这不改变源 HTML 的归档位置。

## 一句话总结

v430 把 promoted seed handoff receipt contract summary 从“可额外单独检查”推进到“随 assurance smoke 默认生成并自检”的训练治理闭环。
