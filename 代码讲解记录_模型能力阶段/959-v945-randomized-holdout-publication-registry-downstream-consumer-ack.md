# v945 randomized holdout publication registry downstream consumer ack

## 本版目标与边界

v945 的目标是把 v944 的 downstream consumer index review 转换成一个明确的消费者确认接收记录。v944 证明 index 可以被 lookup-only 消费；v945 记录“下游消费者已确认接收该 lookup-only 索引”。

这版不训练模型，不调整评估指标，也不批准 production promotion。它只是给治理链路增加 ack 节点，方便后续检查 ack 是否可复核、是否仍指向原始 review 和 index。

前置链路是：

```text
v943 downstream consumer index
 -> v944 downstream consumer index review
 -> v945 downstream consumer ack
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack.py`
  - v945 核心构建器。
  - 输入 v944 review report，输出 ack report。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用于 Playwright 截图。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack.py`
  - v945 CLI。
  - 支持 `--require-ack-ready`、`--require-lookup-ready`、`--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack.py`
  - 覆盖 ready review、源 index 缺失、allowed use 漂移、CLI 和 artifact 输出。

- `e/945/解释/randomized-holdout-publication-registry-downstream-consumer-ack/`
  - 使用真实 v944 review 生成的运行证据。

## 核心数据结构

`ack` 是 v945 的核心结构：

```python
{
    "ack_ready": True,
    "ack_id": "randomized-holdout-publication-registry-downstream-consumer-ack-v945",
    "ack_status": "downstream_consumer_acknowledged",
    "consumer_index_review_path": "...consumer_index_review.json",
    "consumer_index_path": "...consumer_index.json",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "entry_count": 1,
    "lookup_keys": ["publication:randomized-holdout-publication-v928"],
    "lookup_ready": True,
    "downstream_ready": True,
    "contract_check_ready": True,
    "acked_use": "downstream_governance_lookup_only",
    "promotion_ready": False,
    "approved_for_promotion": False,
}
```

`acked_use` 是最重要的字段。它固定为 `downstream_governance_lookup_only`，说明 ack 的含义只是消费者确认读取这个治理索引，而不是批准模型上线。

## 核心检查逻辑

`_checks()` 生成 19 条检查：

- `consumer_index_review_file_exists`：v944 review 文件必须存在。
- `consumer_index_review_passed`：v944 review 必须是 pass。
- `consumer_index_review_decision_ready`：v944 decision 必须是 review ready。
- `consumer_index_file_exists`：v944 review 指向的 v943 index 仍必须存在。
- `review_status_lookup_only`：review status 必须是 lookup-only approved。
- `lookup_ready`、`downstream_ready`、`contract_check_ready`：三个消费前置状态都必须为 True。
- `allowed_use_lookup_only`：summary 和 review body 的 allowed use 都必须是 downstream lookup only。
- `blocked_uses_complete`：三类 blocked uses 继续完整保留。
- `lookup_rows_not_promoted`：lookup rows 不能携带 promotion ready。
- `promotion_still_false`：summary、review body、approved flag 都不能打开 promotion。
- `source_next_step_matches`：v944 的 next step 必须指向 ack。

这组检查让 ack 不能绕过 review，也不能在接收记录里悄悄放宽用途。

## CLI 运行流程

CLI 输入是 v944 review 目录或 JSON：

```text
--consumer-index-review e/944/解释/randomized-holdout-publication-registry-downstream-consumer-index-review
```

执行流程：

1. 定位 `randomized_holdout_publication_registry_downstream_consumer_index_review.json`。
2. 读取 review report。
3. 构建 ack report。
4. 写出 JSON、CSV、TXT、Markdown、HTML。
5. 按 `--require-ack-ready` 和 `--require-lookup-ready` 决定退出码。

`--require-promotion-ready` 继续保持为负向验证：当前正确结果是返回 1，因为 promotion 必须关闭。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready review 可以生成 ready ack。
- review 指向的源 index 缺失时，ack 失败。
- allowed use 被改成 production promotion 时，ack 失败。
- CLI 和 artifact writer 输出完整。

其中 allowed-use 漂移测试直接保护边界：即使 review report 其它字段还在，ack 也不能接受 production promotion。

## 运行证据

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack.py --consumer-index-review e\944\解释\randomized-holdout-publication-registry-downstream-consumer-index-review --out-dir e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack --require-ack-ready --require-lookup-ready --force
```

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_ready
failed_count=0
ack_status=downstream_consumer_acknowledged
lookup_ready=True
downstream_ready=True
contract_check_ready=True
acked_use=downstream_governance_lookup_only
promotion_ready=False
passed_check_count=19
failed_check_count=0
```

Playwright MCP 截图：

```text
e/945/图片/v945-randomized-holdout-publication-registry-downstream-consumer-ack.png
```

## 一句话总结

v945 给 downstream lookup-only 消费链路补上消费者 ack 节点，让“可审核接收”进一步变成“已确认接收”，但仍不允许生产 promotion。
