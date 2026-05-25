# v428 promoted seed handoff receipt contract summary 代码讲解

## 本版目标与边界

v428 的目标是把 v426-v427 已经建立的 schema-v3 receipt/embedded/assurance 合同，整理成一个更轻量的 contract summary。以前 CI 或人工交接要确认 promoted seed handoff receipt 是否可靠，需要打开 handoff report、receipt JSON、receipt-check JSON/text、embedded-check JSON/text 和 assurance JSON/text。v428 不替代这些底层证据，而是在它们之上提供一个单入口摘要。

本版不执行训练，不改变 seed handoff 选择逻辑，不新增新的治理链。它只增加一个小模块、一个 CLI 和一组聚焦测试，用于压缩已有 receipt contract 证据。

## 前置链路

本版接在 v426-v427 后面：

- v426：automation receipt 升级到 schema v3，并校验 suite-design regression count/name 字段。
- v427：assurance smoke 检查 suite-design names，且测试证明篡改 sidecar 会失败。
- v428：把 schema version、assurance status、sidecar status、suite-design count/name 一致性汇总成 JSON/text/Markdown/HTML。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`

这是本版新增的核心模块，保持在 300 行以内，避免继续扩大 `promoted_training_scale_seed_handoff_receipt.py` 或 `promoted_training_scale_seed_handoff_assurance.py`。

核心函数：

```text
build_promoted_training_scale_seed_handoff_receipt_contract_summary(path)
```

它先调用 `check_promoted_training_scale_seed_handoff_assurance(path)`，再抽取三层 suite-design scope：

```text
selected
handoff
comparison_ready
```

每个 scope 都包含：

```text
count
names
name_count
count_matches_names
```

这样 CI 或审阅者不用打开 nested assurance payload，也能直接看到 schema-v3 receipt 合同是否完整。

模块还提供四个 renderer/output：

- JSON：机器消费。
- text：shell key/value 读取。
- Markdown：人工审阅。
- HTML：截图和归档。

### `scripts/check_promoted_seed_handoff_receipt_contract.py`

这是新的 CLI 包装层。输入可以是 `promoted_training_scale_seed_handoff.json` 文件，也可以是 handoff 输出目录。典型命令：

```text
python -B scripts\check_promoted_seed_handoff_receipt_contract.py d\428\解释\assurance-smoke\handoff --out-dir d\428\解释\contract-summary
```

它会打印 text 摘要，并写出：

```text
promoted_training_scale_seed_handoff_receipt_contract_summary.json
promoted_training_scale_seed_handoff_receipt_contract_summary.txt
promoted_training_scale_seed_handoff_receipt_contract_summary.md
promoted_training_scale_seed_handoff_receipt_contract_summary.html
```

默认规则是：summary `status=fail` 时退出非零；如果 handoff 是一致的 stop decision，仍按 automation outcome 返回非零，除非显式传入 `--allow-stop`。

### `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`

这是本版新增的聚焦测试文件，没有继续塞进 v426/v427 的 suite-design receipt 测试。

覆盖三类场景：

- `test_contract_summary_flattens_schema_v3_suite_design_scopes`
  - 生成真实 suite-design handoff sidecar。
  - 确认 summary status/schema/sidecar 均通过。
  - 确认 selected/handoff/comparison_ready 三层 count/name 一致性被展开。
  - 确认 text/Markdown/HTML 都渲染出关键字段。

- `test_contract_summary_rejects_tampered_suite_design_sidecar`
  - 篡改 receipt-check JSON 的 suite-design names。
  - 确认 contract summary 变为 `fail`，并把底层 sidecar issue 带到 summary issues 中。

- `test_cli_writes_contract_summary_artifacts`
  - 真实调用新 CLI。
  - 确认 JSON/text/Markdown/HTML 都写出，并且 stdout 包含输出路径。

### `src/minigpt/__init__.py`

新增两个 lazy export：

```text
build_promoted_training_scale_seed_handoff_receipt_contract_summary
write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs
```

这让后续脚本或 notebook 可以通过包入口复用 contract summary，不必直接依赖模块路径。

## 核心数据流

```text
promoted seed handoff report
  -> handoff assurance check
  -> receipt contract summary
  -> JSON / text / Markdown / HTML
  -> CI or handoff reviewer reads one compact artifact
```

contract summary 的价值是降低交接阅读成本：底层 sidecar 继续负责证明，summary 负责把证明结果压缩成稳定入口。

## 测试覆盖

定向验证：

- `python -m py_compile src\minigpt\promoted_training_scale_seed_handoff_receipt_contract.py scripts\check_promoted_seed_handoff_receipt_contract.py tests\test_promoted_training_scale_seed_handoff_receipt_contract.py`：通过
- `python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt_contract.py -q`：`3 passed`

提交前还会跑相关 receipt/assurance 测试、全量测试、source encoding hygiene 和 `git diff --check`。这些验证分别覆盖新模块、旧 receipt 合同、全项目回归、编码门禁和补丁格式。

## 运行证据

`d/428` 归档了本版证据：

- `d/428/解释/assurance-smoke/`
- `d/428/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.json`
- `d/428/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.txt`
- `d/428/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.md`
- `d/428/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.html`
- `d/428/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary_snapshot.md`
- `d/428/图片/01-receipt-contract-summary.png`
- `d/428/解释/说明.md`

Playwright MCP 本轮不能直接访问 `file://`，临时 HTTP server 也没有在当前沙箱里稳定保持，所以截图使用同一份 HTML 内容的 data URL 渲染。归档中仍保留原始 HTML、snapshot 和截图，能证明页面结构可被浏览器渲染。

一句话总结：v428 把 schema-v3 promoted seed handoff receipt 合同从多份底层 sidecar 压缩成一个稳定的 contract summary，让 CI 和人工交接可以先读一个入口再下钻。
