# v429 promoted seed handoff receipt contract summary check 代码讲解

## 本版目标与边界

v429 的目标是给 v428 的 receipt contract summary 增加自校验能力。v428 已经把 schema-v3 receipt、handoff assurance、embedded sidecar status 和 suite-design count/name 一致性压成一个 compact summary；但如果这个 summary JSON 或 HTML sidecar 被旧产物覆盖，人工看起来仍可能像是“有摘要”。v429 解决的是这个问题：从原始 handoff 重新计算 expected summary，再逐字段比较现有 summary，并校验 text/Markdown/HTML sidecar 是否由 expected summary 渲染而来。

本版不执行训练，不改变 promoted seed handoff 的决策规则，也不新增治理链。它只把 v428 的摘要入口变成可自证的交接合同。

## 前置链路

本版接在 v426-v428 后面：

- v426：automation receipt schema v3 校验 suite-design count/name。
- v427：receipt/check sidecar 被篡改时 embedded receipt check 会失败。
- v428：把 receipt/assurance 结果压成 compact summary。
- v429：对 compact summary 本身做复算校验，防止 JSON/text/Markdown/HTML stale。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`

这是新增的核心模块，单独放置，避免把 v428 summary 模块继续撑大。

核心函数：

```text
check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_path, handoff_path=None)
```

它做四件事：

1. 读取 summary JSON。输入可以是 summary 文件，也可以是 summary 输出目录。
2. 找到 handoff 来源。优先使用 CLI 传入的 `--handoff`，否则使用 summary 里的 `handoff_report_path`。
3. 调用 `build_promoted_training_scale_seed_handoff_receipt_contract_summary()` 重新计算 expected summary。
4. 比较 summary JSON 的关键字段，并校验 text/Markdown/HTML sidecar 是否与 expected summary 的渲染结果一致。

重点比较字段包括：

```text
status
decision
receipt_schema_version
schema_v3_ready
assurance_status
embedded_receipt_check_status
embedded_receipt_check_sidecar_status
suite_design_scopes
issue_count
issues
```

sidecar 校验覆盖：

```text
promoted_training_scale_seed_handoff_receipt_contract_summary.txt
promoted_training_scale_seed_handoff_receipt_contract_summary.md
promoted_training_scale_seed_handoff_receipt_contract_summary.html
```

模块还提供 check 结果的 JSON/text/Markdown/HTML 输出函数。

### `scripts/check_promoted_seed_handoff_receipt_contract_summary.py`

这是新的 CLI 包装层。典型命令：

```text
python -B scripts\check_promoted_seed_handoff_receipt_contract_summary.py d\429\解释\contract-summary --out-dir d\429\解释\contract-summary-check
```

输出包括：

```text
receipt_contract_summary_check_status=pass
receipt_contract_summary_check_actual_status=pass
receipt_contract_summary_check_expected_status=pass
receipt_contract_summary_check_sidecar_status=pass
```

当 summary JSON、text、Markdown 或 HTML 任何一项与 expected summary 不一致时，CLI 返回非零。`--allow-stop` 只用于一致的 stop handoff，不会掩盖 summary mismatch。

### `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`

这是本版新增聚焦测试，没有继续扩展 v428 的 summary 测试文件。

测试覆盖：

- clean path：summary JSON 和三个 sidecar 都与 expected summary 一致，check `pass`。
- JSON tamper：把 `receipt_schema_version` 从 3 改成 2，check `fail`。
- HTML stale：给 HTML sidecar 追加 stale 注释，check `fail`。
- CLI path：真实调用脚本并确认 JSON/text/Markdown/HTML check artifacts 都写出。

### `src/minigpt/__init__.py`

新增 lazy export：

```text
check_promoted_training_scale_seed_handoff_receipt_contract_summary
write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs
```

这样后续 notebook、脚本或 CI 包装器可以从包入口复用 checker。

## 核心数据流

```text
handoff report
  -> v428 contract summary outputs
  -> v429 summary checker
      -> rebuild expected summary from handoff
      -> compare summary JSON
      -> compare text / Markdown / HTML sidecars
  -> summary-check JSON / text / Markdown / HTML
```

v429 的关键是“复算”：它不是读取 summary 后原样相信 summary，而是重新从 handoff report 和 assurance 链路构建 expected summary。

## 测试覆盖

定向验证：

- `python -m py_compile src\minigpt\promoted_training_scale_seed_handoff_receipt_contract_check.py scripts\check_promoted_seed_handoff_receipt_contract_summary.py tests\test_promoted_training_scale_seed_handoff_receipt_contract_check.py`：通过
- `python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt_contract_check.py -q`：`4 passed`

提交前还会跑 v428/v429 receipt contract 相关测试、全量测试、source encoding hygiene 和 `git diff --check`。这些验证分别覆盖新增 checker、前置 summary、全项目回归、编码门禁和补丁格式。

## 运行证据

`d/429` 归档了本版证据：

- `d/429/解释/assurance-smoke/`
- `d/429/解释/contract-summary/`
- `d/429/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.json`
- `d/429/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.txt`
- `d/429/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.md`
- `d/429/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.html`
- `d/429/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check_snapshot.md`
- `d/429/图片/01-receipt-contract-summary-check.png`
- `d/429/解释/说明.md`

Playwright MCP 使用 data URL 渲染本地 check HTML 内容并保存 snapshot 与截图。这是对同一份 HTML 的浏览器渲染验证；原始 HTML 文件仍保留在 `d/429/解释/contract-summary-check/`。

一句话总结：v429 让 promoted seed handoff receipt contract summary 不只是“生成了”，而是能被原始 handoff 复算验证，形成防 stale sidecar 的自校验闭环。
