# v932 randomized holdout publication registry manifest 代码讲解

## 本版目标和边界

v932 的目标是把 v931 交接出来的 registry packet 变成一个 manifest：

```text
v931 publication registry packet
  -> v932 publication registry manifest
```

它解决的问题是：

```text
已登记、已复核、并且明确 bounded 的 randomized holdout publication entry，
是否可以被整理成后续只读治理查询可消费的 manifest？
```

本版回答是可以：

```text
randomized_holdout_publication_registry_manifest_ready
```

同时，v932 还做了必要维护：把 v927-v931 链路中重复出现的 publication 边界常量集中到 `randomized_holdout_publication_constants.py`，减少后续某个模块单独改错字符串的风险。

明确不做：

- 不重新训练。
- 不重新 checkpoint replay。
- 不新增模型质量结论。
- 不把 bounded publication 改成 production promotion。
- 不把 manifest 当成线上发布批准书。

## 前置链路

v932 消费真实 v931 产物：

```text
e/931/解释/randomized-holdout-publication-registry-packet
```

v931 的职责是把 v929 registered entry 和 v930 contract check 打包成 manifest-ready packet。v932 不回头重建 v929/v930，而是检查 v931 packet 是否保持这些关键状态：

- `registry_status=registered`
- `contract_check_ready=True`
- `bounded_publication_accepted=True`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `consumer_boundary=governance_lookup_only`
- `next_step=build_randomized_holdout_publication_registry_manifest`

只有这些字段同时成立，manifest 才能 ready。

## 关键文件

### `src/minigpt/randomized_holdout_publication_constants.py`

这是本版的维护收敛点。

集中定义：

```python
RANDOMIZED_HOLDOUT_PUBLICATION_ALLOWED_USE
RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM
RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY
RANDOMIZED_HOLDOUT_PUBLICATION_DECISION_SCOPE
RANDOMIZED_HOLDOUT_PUBLICATION_ENTRY_ID
RANDOMIZED_HOLDOUT_PUBLICATION_SOURCE_KINDS
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_ENTRY_CHECK_NEXT_STEP
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_NEXT_STEP
```

这些值原来散落在 decision、decision index、registry entry、entry check、packet 等模块里。集中后，后续如果要调整 publication boundary，至少会从一个文件进入，而不是在多处硬编码里碰运气。

### `src/minigpt/randomized_holdout_publication_registry_manifest.py`

核心入口：

```python
build_randomized_holdout_publication_registry_manifest(...)
```

输入：

- `registry_packet_report`：v931 packet JSON。
- `registry_packet_path`：packet 文件路径，可选但推荐传入，用来生成证据路径和文件存在性检查。
- `title`：报告标题。
- `generated_at`：可选生成时间，测试可固定。

输出的顶层结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
registry_packet_path
source_packet_summary
source_packet
check_rows
manifest
summary
interpretation
```

其中 `manifest` 是后续消费者最关心的只读摘要：

```text
manifest_ready
manifest_id
manifest_scope
registry_packet_path
entry_count
entries
entry_id
registry_status
contract_check_ready
bounded_publication_accepted
promotion_ready
approved_for_promotion
consumer_boundary
next_step
```

### `src/minigpt/randomized_holdout_publication_registry_manifest_artifacts.py`

负责把 manifest report 写成多种产物：

- JSON：完整结构，用于后续程序消费。
- CSV：只列 entry 摘要，便于人工扫描。
- TXT：关键状态行，适合 CI 日志。
- Markdown：讲解和归档阅读。
- HTML：Playwright 截图和本地审阅。

它不重新判断业务逻辑，只渲染 `build_randomized_holdout_publication_registry_manifest` 的结果。

### `scripts/build_randomized_holdout_publication_registry_manifest.py`

CLI 入口：

```powershell
python scripts\build_randomized_holdout_publication_registry_manifest.py `
  --registry-packet e\931\解释\randomized-holdout-publication-registry-packet `
  --out-dir e\932\解释\randomized-holdout-publication-registry-manifest `
  --require-manifest-ready `
  --require-bounded-publication `
  --force
```

重要参数：

- `--registry-packet` 可传 JSON 文件，也可传输出目录。
- `--require-manifest-ready` 要求 manifest ready，否则返回 1。
- `--require-bounded-publication` 要求 bounded publication 被接受。
- `--require-promotion-ready` 是故意保守的附加门槛；当前真实链路应该返回 1，因为 v932 不批准 promotion。

## 核心检查

v932 的 `_checks` 共有 16 个检查点：

```text
registry_packet_file_exists
registry_packet_passed
registry_packet_decision_ready
packet_summary_ready
handoff_manifest_ready
registry_status_registered
contract_check_ready
bounded_publication_accepted
consumer_boundary_governance
allowed_use_bounded
model_quality_claim_bounded
promotion_still_false
approved_for_promotion_false
evidence_count
source_checks_clean
source_next_step_matches
```

这些检查的重点不是提高模型能力，而是保护 publication 证据链不漂移：

- packet 必须真的存在。
- packet 必须是 v931 ready 状态。
- entry 必须已 registered。
- contract check 必须 ready。
- consumer boundary 必须仍是 governance lookup。
- publication 只能是 bounded claim。
- promotion 必须保持 false。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_manifest.py
```

测试覆盖四类场景：

1. ready packet 可以生成 pass manifest。
2. 手动把 `contract_check_ready` 改成 false 后，manifest 必须 fail。
3. 手动把 `consumer_boundary` 扩成 `production_lookup` 后，manifest 必须 fail。
4. artifact writer、locator 和 CLI 都能正确工作。

聚焦链路测试覆盖 v927-v932：

```text
27 passed
```

这能证明常量收敛没有破坏前序 publication decision、index、registry entry、contract check 和 packet。

## 真实运行证据

真实 v931 输入生成 v932 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_manifest_ready
failed_count=0
entry_count=1
registry_status=registered
contract_check_ready=True
bounded_publication_accepted=True
promotion_ready=False
consumer_boundary=governance_lookup_only
passed_check_count=16
failed_check_count=0
```

证据目录：

```text
e/932/解释/randomized-holdout-publication-registry-manifest
e/932/图片/v932-randomized-holdout-publication-registry-manifest.png
```

Playwright MCP 打开的 HTML 页面显示 manifest ready、entry count、registry、boundary 和 failed count，说明 HTML 产物不是空文件，也不是未渲染状态。

## 链路角色

v932 在整条模型能力链里扮演的是“只读 manifest 汇总层”：

```text
真实 randomized holdout replay
  -> review
  -> bounded promotion decision
  -> decision index
  -> acceptance summary
  -> publication packet
  -> publication decision
  -> registry entry
  -> contract check
  -> registry packet
  -> registry manifest
```

它把“这个 tiny checkpoint 在 20 个随机目标隐藏样本上通过”整理成治理查询入口，但不把该结论扩大为通用模型质量承诺。

## 一句话总结

v932 把 verified publication registry packet 收束为可查询 manifest，并通过常量收敛降低边界字段漂移风险，让 randomized holdout 的 bounded publication 更适合后续治理消费。
