# v952 randomized holdout publication registry downstream consumer ack bundle publication index review

## 本版目标与边界

v952 的目标是审核 v951 downstream consumer ack bundle publication index，确认它能否进入 downstream receipt。v951 负责把 publication 和 contract check 合成索引；v952 则检查这个索引是否真的可被下游 lookup-only 消费。

这版不训练模型，不发布生产模型，不扩大模型质量声称。它只批准后续记录 receipt，继续禁止 production promotion。

前置链路：

```text
v949 publication
 -> v950 publication contract check
 -> v951 publication index
 -> v952 publication index review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.py`
  - v952 核心审核器。
  - 检查 v951 index 的 source paths、publication rows、source evidence rows、lookup-only use、contract readiness 和 no-promotion 边界。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 记录 review 的 21 条检查。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.py`
  - v952 CLI。
  - 支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.py`
  - 覆盖 ready review、source evidence 缺失、published use 漂移、CLI 失败返回码和 artifact 输出。

- `e/952/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review/`
  - 使用真实 v951 index 生成的运行证据。

## 核心数据结构

`review` 是本版主结构：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review-v952",
    "review_status": "approved_for_downstream_publication_lookup_only",
    "publication_row_count": 1,
    "source_evidence_count": 2,
    "downstream_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "allowed_use": "downstream_governance_lookup_only",
    "promotion_ready": False,
    "next_step": "record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt",
}
```

`review_status` 表示只批准 downstream publication lookup，不代表生产模型发布。

## 核心检查逻辑

`_checks()` 生成 21 条检查：

- `publication_index_file_exists`：v951 index 文件必须存在。
- `publication_index_passed` 与 `publication_index_decision_ready`：v951 必须是 ready index。
- `publication_index_summary_ready`：summary 与 index body 必须同时 ready。
- `lookup_scope_downstream` 与 `published_use_lookup_only`：查阅范围和用途必须保持 lookup-only。
- `lookup_ready` 与 `contract_check_ready`：index 必须可查阅且带 ready contract check。
- `publication_rows_present`：必须只有一条 publication row。
- `lookup_keys_present`：lookup key 必须使用 `publication:` 命名空间。
- `publication_rows_not_promoted`：publication row 不允许 promotion。
- `source_evidence_count`、`source_evidence_passed`、`source_evidence_files_exist`：两条源 evidence 必须存在且 pass。
- `source_publication_file_exists` 与 `source_publication_check_file_exists`：v949/v950 源 artifact 必须仍存在。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：消费边界和模型质量声称必须保守。
- `promotion_still_false`：promotion 不允许打开。
- `source_checks_clean`：v951 上游检查必须 clean。
- `source_next_step_matches`：v951 必须路由到本版 review。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.py e\951\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index --out-dir e\952\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review --require-review-ready --require-downstream-ready --force
```

流程：

1. 定位 v951 publication index JSON。
2. 读取 index report。
3. 检查 index readiness、source artifact、publication row、source evidence row。
4. 验证 lookup-only use 和 no-promotion 边界。
5. 输出 review JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready index 可以生成 ready review。
- source evidence 缺失时 review 失败。
- published use 漂移为 production promotion 时 review 失败。
- `--require-review-ready` 在失败输入下返回 1，并写出失败报告。
- CLI 和 artifact writer 输出完整。

这组测试保护的是 index 进入 downstream receipt 前的审核边界。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_ready
failed_count=0
review_status=approved_for_downstream_publication_lookup_only
publication_row_count=1
source_evidence_count=2
downstream_ready=True
promotion_ready=False
passed_check_count=21
failed_check_count=0
```

Playwright MCP 截图：

```text
e/952/图片/v952-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review.png
```

## 一句话总结

v952 审核 v951 publication index 的 lookup-only 消费边界，并把链路推进到下游 receipt 记录。
