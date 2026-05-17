# v215 promoted seed handoff clean evidence status contract 代码讲解

## 本版目标

v215 的目标是把 v214 的 clean-evidence readiness 继续收紧成稳定状态域契约。

v214 已经输出：

```text
seed_handoff_clean_evidence_ready
seed_handoff_clean_evidence_status
seed_handoff_clean_evidence_detail
```

但状态值仍然只是代码里的字符串。v215 把合法状态显式定义为 typed/public contract，并把状态域也输出到 artifact 和 CLI，方便后续脚本或报告消费。

## 不做什么

本版不新增新的治理报告，不改变 seed handoff 的执行策略，不改变 planned mode，也不改变 `--execute`。

`seed_handoff_clean_evidence_status_domain` 只是 schema evidence，不是 blocker，也不是 promotion decision。

## 前置路线

本版承接 v212-v214：

```text
suite alignment verdict
-> review recommendations
-> clean-evidence readiness
-> clean-evidence status-domain contract
```

它属于证据链契约硬化，而不是模型能力增强。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

### `SeedHandoffCleanEvidenceStatus`

新增 `Literal` 类型，明确状态只能是：

```text
ready
pending-plan
review
incomplete
```

这让 IDE、静态检查和测试都能围绕同一组合法值工作。

### `SeedHandoffCleanEvidenceReadiness`

新增 `TypedDict`，说明 readiness payload 包含：

- `ready`：布尔值，表示是否可作为 clean comparison evidence。
- `status`：合法状态之一。
- `detail`：人类可读解释。
- `status_domain`：当前公开状态域。

### `SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES`

新增公开常量：

```python
("ready", "pending-plan", "review", "incomplete")
```

测试和后续消费者都可以引用它，而不用复制字符串列表。

### `_clean_evidence_payload()`

新增 payload helper，统一返回 readiness 结构。

v214 中 `_clean_evidence_readiness()` 直接返回多个字典。v215 改为通过 `_clean_evidence_payload()` 返回，这样每个分支都会自动携带同一份 `status_domain`。

## Artifact 输出

`src/minigpt/promoted_training_scale_seed_handoff_artifacts.py` 新增：

```text
seed_handoff_clean_evidence_status_domain
```

CSV 会把 list 通过 `report_utils.csv_cell()` 写成 JSON 字符串。Markdown 直接显示状态域，HTML stats 增加 `Clean evidence domain` 卡片。

这些产物都是最终证据，不是临时检查文件。

## CLI 输出

`scripts/execute_promoted_training_scale_seed.py` 新增：

```text
seed_handoff_clean_evidence_status_domain=[...]
```

这让 smoke、CI 或人工终端不用打开 JSON，也能看到当前状态域。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 新增 `test_clean_evidence_status_domain_is_public_contract()`，直接断言公开状态域的顺序和值。

原有 artifact/CLI 测试也扩展为检查：

- summary 带有 `seed_handoff_clean_evidence_status_domain`
- CSV header 带有该字段
- Markdown/HTML 会展示 status domain
- CLI stdout 会打印 status-domain 行

这些断言保护的是“状态域不能悄悄漂移”。

## 运行证据

本版运行证据归档在 `c/215`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-status-domain-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-status-domain-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、CLI 可见状态域、JSON/CSV/Markdown/HTML 都导出状态域、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v215 让 promoted seed handoff 的 clean-evidence readiness 更适合被下游自动化读取。后续如果 maturity summary、promotion review 或 registry 要消费 clean evidence，不需要猜状态取值，也不需要解析自然语言说明。

## 一句话总结

v215 把 clean-evidence readiness 的合法状态域变成 typed/public contract，让 promoted seed handoff 的机器消费边界更稳定。
