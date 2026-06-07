# v951 randomized holdout publication registry downstream consumer ack bundle publication index

## 本版目标与边界

v951 的目标是把 v949 publication 和 v950 publication contract check 合成一个 downstream consumer ack bundle publication index。v949 负责发布 lookup-only artifact，v950 负责证明它可以从 source review 重建；v951 负责把这两份 artifact 放进一个可供后续 review 读取的稳定索引。

这版不训练模型，不扩大模型质量声称，不把 lookup-only publication 变成 promotion。它只是建立索引入口，并保留两条源 evidence row。

前置链路：

```text
v949 downstream consumer ack bundle publication
 -> v950 downstream consumer ack bundle publication contract check
 -> v951 downstream consumer ack bundle publication index
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index.py`
  - v951 核心索引器。
  - 同时读取 publication 和 publication check，验证二者状态、用途、证据数量、source next step 和 no-promotion 边界。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出 publication lookup row；Markdown/HTML 同时展示 source evidence rows 和 check rows。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index.py`
  - v951 CLI。
  - 支持 `--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index.py`
  - 覆盖 ready index、contract check 失败、published use 漂移、CLI 失败返回码和 artifact 输出。

- `e/951/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index/`
  - 使用真实 v949/v950 生成的运行证据。

## 核心数据结构

`publication_index` 是本版主结构：

```python
{
    "index_ready": True,
    "publication_index_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-v951",
    "lookup_scope": "downstream_governance_lookup_only",
    "publication_rows": [
        {
            "lookup_key": "publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949",
            "publication_status": "published_for_downstream_consumer_lookup_only",
            "published_use": "downstream_governance_lookup_only",
            "source_evidence_count": 2,
            "contract_check_ready": True,
            "promotion_ready": False,
        }
    ],
    "source_evidence_rows": [...],
    "next_step": "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index",
}
```

`publication_rows` 是下游 lookup 入口，`source_evidence_rows` 保留 v949 publication 内的两条源证据。这样后续 review 既可以查到 publication 本身，也能追溯到 v945 ack 和 v946 ack contract check。

## 核心检查逻辑

`_checks()` 生成 20 条检查：

- `publication_file_exists` 和 `publication_check_file_exists`：两份 source artifact 必须存在。
- `publication_passed` 与 `publication_decision_ready`：v949 必须是 ready publication。
- `publication_summary_ready`：summary 与 publication body 必须同时 ready。
- `publication_check_passed`、`publication_check_decision_ready`、`contract_check_ready`：v950 contract check 必须通过。
- `publication_status_matches_check`：publication status 必须与 v950 original/rebuilt 都一致。
- `published_use_lookup_only`：publication 与 check 的 original/rebuilt use 都必须保持 lookup-only。
- `lookup_ready`：publication 必须允许 lookup。
- `evidence_count_matches_check`：publication、check original、check rebuilt、实际 evidence rows 都必须是 2。
- `source_evidence_passed` 与 `source_evidence_files_exist`：源 evidence 必须仍存在且 pass。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：消费边界和模型质量声称必须保持保守。
- `promotion_still_false`：promotion 不允许打开。
- `source_publication_checks_clean` 与 `source_contract_checks_clean`：上游检查必须 clean。
- `source_next_steps_match`：v949 必须路由到 v950，v950 必须路由到 v951。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index.py --publication e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication --publication-check e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check --out-dir e\951\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index --require-index-ready --require-lookup-ready --force
```

流程：

1. 定位 v949 publication JSON。
2. 定位 v950 publication contract check JSON。
3. 校验两份 artifact 状态、决策、next step 和 no-promotion 字段。
4. 生成一条 publication lookup row。
5. 保留两条 source evidence rows。
6. 输出 index JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready publication + ready contract check 可以生成 ready index。
- contract check 失败时，index 失败。
- `published_use` 漂移为 production promotion 时，index 失败。
- `--require-index-ready` 在失败输入下返回 1，并写出失败报告。
- CLI 和 artifact writer 输出完整。

这组测试保护的是 publication/check 的合并边界，避免索引层把失败或不该发布的 artifact 包进去。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_ready
failed_count=0
publication_row_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图：

```text
e/951/图片/v951-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index.png
```

## 一句话总结

v951 把 v949 publication 与 v950 contract check 合成 lookup-only publication index，让 downstream review 可以稳定读取并追溯源 evidence。
