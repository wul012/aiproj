# v961 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index

## 本版目标与边界

v961 的目标是把 v959 publication 与 v960 publication contract check 合并成 lookup-only index。v959 负责发布，v960 证明发布产物可重建，v961 将两者整理成后续 review 的稳定输入。

这版不训练模型，不生成新的质量声明，不批准 promotion。它只是索引已经通过 contract check 的 publication。

前置链路：

```text
v959 receipt packet index publication
 -> v960 receipt packet index publication contract check
 -> v961 receipt packet index publication index
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index.py`
  - v961 核心 index builder。
  - 同时读取 v959 publication 与 v960 check，检查 publication ready、contract check ready、published use、source 文件、计数和 no-promotion。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出 publication index row，HTML 展示 lookup boundary、index row 和全部 checks。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index.py`
  - v961 CLI。
  - 支持 `--publication`、`--publication-check`、`--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index.py`
  - 覆盖 ready index、contract check 失败、published use 漂移和 artifact/CLI 输出。

- `e/961/解释/receipt-packet-index-publication-index/`
  - 使用真实 v959 publication 与 v960 check 生成的运行证据。

## 核心数据结构

`publication_index` 是本版主结构：

```python
{
    "index_ready": True,
    "publication_index_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index-v961",
    "lookup_scope": "downstream_governance_lookup_only",
    "publication_index_rows": [
        {
            "lookup_key": "publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959",
            "publication_status": "published_for_downstream_receipt_packet_index_lookup_only",
            "published_use": "downstream_governance_lookup_only",
            "contract_check_ready": True,
            "promotion_ready": False,
        }
    ],
    "lookup_ready": True,
    "contract_check_ready": True,
    "next_step": "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index",
}
```

这个结构把发布层与验证层捆在一起：后续 review 只需要消费 v961 index，就能看到 publication 与 contract check 都 clean。

## 核心检查逻辑

`_checks()` 生成 24 条检查：

- publication/check 文件必须存在。
- v959 publication 必须通过且 decision ready。
- v960 check 必须通过且 decision 为 contract check passed。
- publication status 必须与 check 的 original/rebuilt status 一致。
- published use 必须保持 `downstream_governance_lookup_only`。
- lookup ready、packet index row count、source packet row count、source evidence count 必须满足预期。
- source review、source index、source packet、source packet check 文件必须仍存在。
- consumer boundary 与 model quality claim 必须保守。
- promotion 必须始终为 false。
- v959/v960 failed check count 必须为 0。
- v959 next step 必须指向 check，v960 next step 必须指向 index。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index.py --publication e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication --publication-check e\960\解释\receipt-packet-index-publication-check --out-dir e\961\解释\receipt-packet-index-publication-index --require-index-ready --require-lookup-ready --force
```

流程：

1. 定位 v959 publication JSON 和 v960 contract check JSON。
2. 读取 publication summary/body 与 check summary。
3. 校验 status、decision、用途、计数、source 文件、next step 和 no-promotion。
4. 输出 index JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready publication + ready check 可以生成 index。
- contract check 失败时 index 失败。
- publication published use 漂移到 production promotion 时失败。
- artifact writer 和 CLI 输出完整。

这组测试保护后续 review 不会绕过 contract check 直接消费 publication。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_ready
failed_count=0
lookup_scope=downstream_governance_lookup_only
published_use=downstream_governance_lookup_only
publication_index_row_count=1
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=24
failed_check_count=0
```

Playwright MCP 截图：

```text
e/961/图片/v961-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index.png
```

## 一句话总结

v961 把 lookup-only publication 与 contract check 合并成可 review 的索引入口，同时继续阻断 promotion。
