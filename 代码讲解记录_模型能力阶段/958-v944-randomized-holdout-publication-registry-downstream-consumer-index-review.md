# v944 randomized holdout publication registry downstream consumer index review

## 本版目标与边界

v944 的目标是审核 v943 生成的 downstream consumer index，确认它是否可以继续进入下游接收确认阶段。v943 负责把 packet 与 contract check 合成一个索引；v944 则负责判断这个索引是不是仍然满足消费边界。

这版不训练模型，不新增模型评估，也不把 randomized holdout 的治理结论转换成生产模型质量结论。它的定位是一个 contract-preserving review：只读、可复核、继续阻断 production promotion。

前置链路是：

```text
v941 consumer packet
 -> v942 consumer packet contract check
 -> v943 downstream consumer index
 -> v944 downstream consumer index review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_index_review.py`
  - v944 核心构建器。
  - 读取 v943 index report，检查索引状态、源证据路径、lookup-only 范围、blocked uses、promotion 边界。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_index_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 是本版截图的来源。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_index_review.py`
  - v944 CLI。
  - 支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_index_review.py`
  - 覆盖成功 review、源 packet 缺失、blocked uses 不完整、CLI 和 artifact 输出。

- `e/944/解释/randomized-holdout-publication-registry-downstream-consumer-index-review/`
  - 消费真实 v943 index 生成的运行证据。

## 核心数据结构

`review` 是 v944 的中心结构：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-index-review-v944",
    "review_status": "approved_for_downstream_consumer_lookup_only",
    "consumer_index_path": "...consumer_index.json",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "entry_count": 1,
    "lookup_keys": ["publication:randomized-holdout-publication-v928"],
    "downstream_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "promotion_ready": False,
    "approved_for_promotion": False,
    "allowed_use": "downstream_governance_lookup_only",
    "blocked_uses": [
        "production_promotion",
        "model_quality_expansion",
        "training_data_claim_expansion",
    ],
}
```

这里的 `approved_for_downstream_consumer_lookup_only` 是有意限定的状态：它说明下游可读这个索引，但不能把它解释为生产发布、泛化质量提升或训练数据结论扩展。

## 核心检查逻辑

`_checks()` 生成 20 条检查，重点比 v943 多了“源证据路径仍存在”：

- `consumer_index_file_exists`：v943 index 文件必须存在。
- `consumer_index_passed`：v943 index 本身必须是 pass。
- `consumer_index_summary_ready`：summary 与 index body 都必须 ready。
- `lookup_scope_downstream`：summary 与 body 都必须是 downstream lookup only。
- `contract_check_ready`：索引承载的 contract check 状态必须 ready。
- `source_packet_file_exists`：v941 packet 路径仍可读取。
- `source_packet_check_file_exists`：v942 packet check 路径仍可读取。
- `blocked_uses_complete`：三类 blocked uses 必须完整保留。
- `promotion_still_false`：summary、index body 和 approved flag 都不能打开 promotion。
- `source_next_step_matches`：v943 的 next step 必须指向本版 review。

这让 v944 不只是“读到一个 pass report”，而是确认索引与它引用的源证据仍保持闭环。

## CLI 运行流程

CLI 输入是 v943 index 目录或 JSON：

```text
--consumer-index e/943/解释/randomized-holdout-publication-registry-downstream-consumer-index
```

执行后会：

1. 定位 `randomized_holdout_publication_registry_downstream_consumer_index.json`。
2. 读取 index report。
3. 构建 review report。
4. 写出 JSON、CSV、TXT、Markdown、HTML。
5. 按 `--require-review-ready` 和 `--require-downstream-ready` 给出退出码。

`--require-promotion-ready` 继续是反向保护；当前正确行为是返回 1，因为 promotion 必须保持关闭。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready index 可以生成 ready review。
- v943 index 指向的源 packet 缺失时，review 失败。
- blocked uses 被缩减时，review 失败。
- CLI 可以从目录输入定位 JSON，并输出五类 artifact。

其中源 packet 缺失测试很关键：它防止 downstream index 变成“只有字段 pass，但源证据已经断裂”的悬空产物。

## 运行证据

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_index_review.py --consumer-index e\943\解释\randomized-holdout-publication-registry-downstream-consumer-index --out-dir e\944\解释\randomized-holdout-publication-registry-downstream-consumer-index-review --require-review-ready --require-downstream-ready --force
```

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_index_review_ready
failed_count=0
review_status=approved_for_downstream_consumer_lookup_only
downstream_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图：

```text
e/944/图片/v944-randomized-holdout-publication-registry-downstream-consumer-index-review.png
```

## 一句话总结

v944 把 v943 的 downstream consumer index 从“可生成”推进到“可审核接收”，同时继续把模型质量扩展和 production promotion 挡在边界外。
