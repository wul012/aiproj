# v943 randomized holdout publication registry downstream consumer index

## 本版目标与边界

v943 的目标是给 v941 downstream consumer packet 和 v942 consumer packet contract check 增加一层统一索引：下游读取方不再需要分别理解 packet 与 check 的结构，而是可以读取一份 `consumer_index`，同时看到 lookup rows、源证据路径、contract check readiness、blocked uses 和 promotion 边界。

这版不训练模型，不改变 tokenizer、checkpoint 或评估指标，也不把 randomized holdout 的结果升级成生产模型质量结论。它只把已经完成的治理链路整理成“可消费但不可促生产”的索引入口。

前置链路是：

```text
v939 downstream receipt
 -> v940 receipt review
 -> v941 consumer packet
 -> v942 consumer packet contract check
 -> v943 downstream consumer index
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_index.py`
  - v943 的核心构建器。
  - 输入两份 JSON report：consumer packet report 和 consumer packet check report。
  - 输出 `summary`、`consumer_index`、`check_rows`、`issues`、`interpretation`。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_index_artifacts.py`
  - v943 的 artifact writer。
  - 输出 JSON、CSV、TXT、Markdown、HTML 五种格式。
  - HTML 负责运行截图中的可视化报告。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_index.py`
  - v943 CLI 入口。
  - 支持目录或 JSON 文件输入。
  - 支持 `--require-index-ready`、`--require-lookup-ready` 和 `--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_index.py`
  - v943 的聚焦测试。
  - 覆盖正常通过、contract check 失败、lookup key 漂移、CLI 失败码、artifact 输出。

- `e/943/解释/randomized-holdout-publication-registry-downstream-consumer-index/`
  - v943 的真实运行产物。
  - 消费真实 v941 和 v942 归档，而不是测试 fixture。

- `e/943/图片/v943-randomized-holdout-publication-registry-downstream-consumer-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`consumer_index` 是这版的主要结构：

```python
{
    "index_ready": True,
    "consumer_index_id": "randomized-holdout-publication-registry-downstream-consumer-index-v943",
    "lookup_scope": "downstream_governance_lookup_only",
    "consumer_packet_path": "...consumer_packet.json",
    "consumer_packet_check_path": "...consumer_packet_check.json",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "entry_count": 1,
    "packet_rows": [...],
    "lookup_keys": ["publication:randomized-holdout-publication-v928"],
    "lookup_ready": True,
    "contract_check_ready": True,
    "granted_use": "downstream_governance_lookup_only",
    "blocked_uses": [
        "production_promotion",
        "model_quality_expansion",
        "training_data_claim_expansion",
    ],
    "promotion_ready": False,
    "approved_for_promotion": False,
}
```

这里最重要的是两个字段组：

- `lookup_*`：说明它能被下游当成治理索引读取。
- `promotion_*` 与 `blocked_uses`：说明它不能被当成生产 promotion 或模型质量扩展依据。

## 核心检查逻辑

`_checks()` 生成 19 条检查。它们不是简单确认文件存在，而是把 packet 和 check 的关键字段交叉比对：

- `consumer_packet_passed`：源 packet 必须是 pass。
- `consumer_packet_check_passed`：源 contract check 必须是 pass。
- `contract_check_ready`：contract check 的 summary 必须标记 ready。
- `lookup_keys_match_check`：packet 的 lookup keys 必须和 check 中 original/rebuilt lookup keys 一致。
- `granted_use_lookup_only`：packet、original check、rebuilt check 都必须是 downstream lookup only。
- `blocked_uses_complete`：必须保留三类阻断用途。
- `promotion_still_false`：packet、original check、rebuilt check 都不能打开 promotion。
- `source_packet_checks_clean` 与 `source_contract_checks_clean`：前置产物的失败检查数必须为 0。

如果任何一条失败，`status` 会变成 `fail`，`consumer_index.packet_rows` 会被置空，`next_step` 会变成修复动作。

## CLI 运行流程

CLI 会先定位两份输入：

```text
--consumer-packet       目录或 randomized_holdout_publication_registry_downstream_consumer_packet.json
--consumer-packet-check 目录或 randomized_holdout_publication_registry_downstream_consumer_packet_check.json
```

随后：

1. 读取两份 JSON report。
2. 调用 `build_randomized_holdout_publication_registry_downstream_consumer_index()`。
3. 写出 JSON、CSV、TXT、Markdown、HTML。
4. 打印 text 摘要。
5. 根据 `--require-index-ready` 和 `--require-lookup-ready` 决定退出码。

`--require-promotion-ready` 被保留为负向保护：在当前治理边界下它应返回 1，因为 v943 明确保持 `promotion_ready=False`。

## 运行证据

真实命令消费的是历史归档：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_index.py --consumer-packet e\941\解释\randomized-holdout-publication-registry-downstream-consumer-packet --consumer-packet-check e\942\解释\randomized-holdout-publication-registry-downstream-consumer-packet-check --out-dir e\943\解释\randomized-holdout-publication-registry-downstream-consumer-index --require-index-ready --require-lookup-ready --force
```

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_index_ready
failed_count=0
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=19
failed_check_count=0
```

Playwright MCP 打开 HTML 后保存截图到：

```text
e/943/图片/v943-randomized-holdout-publication-registry-downstream-consumer-index.png
```

## 测试覆盖

新增测试覆盖 5 个场景：

- ready packet + ready contract check 可以生成 ready index。
- contract check 被改成 fail 时，index 会失败。
- packet lookup key 被篡改时，`lookup_keys_match_check` 会失败。
- CLI 在 `--require-index-ready` 下遇到篡改 packet 会返回 1，同时仍写出失败证据。
- artifact writer 能输出 JSON、CSV、TXT、Markdown、HTML，并且 CLI 能从目录输入定位源文件。

这组测试保护的是 v943 的消费边界：它不只确认“索引能生成”，还确认索引不能绕过 v942 contract check，也不能把 lookup-only 产物升级成 promotion-ready 产物。

## 一句话总结

v943 把 downstream consumer packet 与 contract check 收束为一个可检索的治理索引，同时继续把模型质量扩展和生产 promotion 明确挡在索引之外。
