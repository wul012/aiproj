# v472：promoted seed handoff receipt schema-v5 issue gate

## 本版目标与边界

v472 的目标是补齐 v471 的状态解释：v471 已经新增 `reason_counts_within_handoff` contract checks，但 legacy schema-v4 reason-count 不一致时，summary issue 没有明确指出这类失败需要 schema v5 承载完整 reason-count contract。

本版只做 contract-preserving hardening，不新增治理链，不改变 promoted seed handoff、receipt schema v5 字段、reason-count scope 结构，也不改变训练或候选选择逻辑。兼容边界很明确：一致的历史 schema-v4 归档仍然可以 pass；只有 legacy reason-count scope 出现 selected 超出 handoff 时，才额外提示 schema v5 gate。

## 关键修改文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_context.py`
  - 在 `contract_issues()` 中加入 legacy reason-count 失败时的 schema-v5 issue。
  - 新增 `reason_count_contract_requires_schema_v5()`，只在 reason-count scope 不一致时触发该 issue，避免破坏旧归档兼容性。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 新增两个边界测试。
  - 一致的 schema-v4 reason map 不触发 schema-v5 issue。
  - 不一致的 schema-v4 reason map 会同时报告 schema-v5 issue 和 selected reason 超出 handoff 的 issue。
- `pyproject.toml`
  - `addopts` 禁用未使用的 `faker` pytest 插件，避免本地 collection 挂住。
  - 显式设置 `asyncio_default_fixture_loop_scope = "function"`，减少 pytest-asyncio 配置噪声。

## 核心函数语义

`contract_issues()` 是 contract summary 的状态入口：

```text
assurance
  -> receipt_schema_version
  -> schema v3/v4 readiness issues
  -> failed legacy reason-count schema-v5 issue
  -> suite-design / boundary / reason-count consistency issues
  -> summary.status
```

v472 之后，CI reason-count contract 在 legacy schema 下出现真实不一致时，不只是 `contract_checks` 中的一行，而是会进入 `issues`，从而影响 `status` 和 `checker_exit_code`。一致的旧归档仍以兼容模式通过。

## 输入输出与证据链角色

输入仍然是 promoted seed handoff report 或目录。输出仍然是 contract summary JSON/text/Markdown/HTML，以及 summary-check JSON/text/Markdown/HTML。

本版没有改变产物格式，只改变失败条件的解释完整性：当 receipt schema 小于 5 时，summary issue 会明确指出 CI reason-count contract 不可用。

## 测试覆盖

测试分两层：

- 新增直接单测：一致的 schema v4 reason-count scope 不产生 schema-v5 issue。
- 新增失败单测：不一致的 schema v4 reason-count scope 必须产生 schema-v5 issue。
- 既有 reason-count smoke：当前 v5 handoff 仍然 `status=pass`，`reason_counts_within_handoff` 三条检查保持通过。

同时修正 pytest collection hygiene，确保普通 `python -m pytest ...` 不会被本地无关插件拖住。

## 运行证据

证据目录：`d/472`

主要文件：

- `d/472/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.json`
- `d/472/解释/contract-summary-check/promoted_training_scale_seed_handoff_receipt_contract_summary_check.json`
- `d/472/图片/01-contract-summary-schema-v5-gate.png`
- `d/472/图片/02-contract-summary-check-schema-v5-gate.png`

这些证据使用 v471 handoff 重新生成，说明当前 schema v5 handoff 下 contract summary 与 summary-check 仍然全部通过；同时全量测试保护 `d/448` 这类历史 schema-v4 归档继续可读。

## 一句话总结

v472 把 promoted seed handoff receipt 的 CI reason-count contract 补成了更稳的 schema-v5 gate：真实不一致会明确失败，兼容的历史归档仍可复算通过。
