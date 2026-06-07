# v946 randomized holdout publication registry downstream consumer ack check

## 本版目标与边界

v946 的目标是对 v945 downstream consumer ack 做 contract check：读取 ack 中记录的 v944 review 路径，重新调用 ack builder，再逐字段比对原始 ack 与重建 ack。

这版不训练模型，不新增模型能力证据，也不改变 lookup-only 的消费边界。它只验证 ack 产物是否可重建、是否没有被篡改、是否仍然不允许 production promotion。

前置链路是：

```text
v944 downstream consumer index review
 -> v945 downstream consumer ack
 -> v946 downstream consumer ack contract check
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_check.py`
  - v946 核心校验器。
  - 从 v945 ack 定位 v944 review，再调用 `build_randomized_holdout_publication_registry_downstream_consumer_ack()` 重建 ack。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_check_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack.py`
  - v946 CLI。
  - 支持 `--require-pass`，失败时返回 1。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_check.py`
  - 覆盖正常重建、acked use 篡改、源 review 缺失、CLI 失败码、artifact 输出。

- `e/946/解释/randomized-holdout-publication-registry-downstream-consumer-ack-check/`
  - 使用真实 v945 ack 生成的运行证据。

## 核心数据结构

v946 输出里有四组关键数据：

- `original_summary`：v945 ack 的 summary。
- `rebuilt_summary`：从 v944 review 重建出的 summary。
- `original_ack`：v945 ack 的 ack body。
- `rebuilt_ack`：从 v944 review 重建出的 ack body。

校验字段分为两组：

```python
SUMMARY_FIELDS = [
    "randomized_holdout_publication_registry_downstream_consumer_ack_ready",
    "ack_id",
    "ack_status",
    "consumer_name",
    "entry_count",
    "lookup_key_count",
    "lookup_ready",
    "downstream_ready",
    "contract_check_ready",
    "acked_use",
    "blocked_uses",
    "promotion_ready",
    "approved_for_promotion",
    "consumer_boundary",
    "model_quality_claim",
]
```

`ACK_FIELDS` 则覆盖 ack body 中的源路径、lookup keys、acked use、blocked uses、promotion boundary 和 model quality claim。

## 核心检查逻辑

v946 的 `build_randomized_holdout_publication_registry_downstream_consumer_ack_check()` 做四步：

1. 读取原始 ack 的 summary 和 ack body。
2. 从 `consumer_index_review_path` 定位 v944 review。
3. 用 v944 review 重建一份 ack。
4. 比对 status、decision、failed_count、lookup rows、check rows、summary 字段和 ack body 字段。

关键检查包括：

- `source_consumer_index_review_exists`：源 review 不能丢。
- `status`、`decision`、`failed_count`：顶层结果必须一致。
- `lookup_rows`、`check_rows`：行级证据必须一致。
- `summary.acked_use` 与 `ack.acked_use`：不能从 lookup-only 被篡改成 promotion。
- `summary.promotion_ready` 与 `ack.promotion_ready`：必须继续为 False。

## CLI 运行流程

CLI 接收 ack 目录或 JSON：

```text
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack.py e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack --out-dir e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check --require-pass --force
```

流程：

1. 定位 v945 ack JSON。
2. 读取 ack。
3. 定位 v944 review。
4. 重建 ack。
5. 写出 check JSON、CSV、TXT、Markdown、HTML。
6. 在 `--require-pass` 下，若不一致则返回 1。

## 测试覆盖

新增测试覆盖 5 个场景：

- 可重建的 ack 通过 contract check。
- acked use 被篡改为 production promotion 时，summary 和 ack body 字段都会失败。
- 源 review 缺失时，`source_consumer_index_review_exists` 失败。
- CLI 在 `--require-pass` 下遇到篡改 ack 返回 1。
- artifact writer 和 CLI 输出完整。

这些测试保护的是 ack 的可复核性，而不是简单检查字段存在。

## 运行证据

真实命令输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed
failed_count=0
contract_check_ready=True
original_ack_status=downstream_consumer_acknowledged
rebuilt_ack_status=downstream_consumer_acknowledged
original_acked_use=downstream_governance_lookup_only
rebuilt_acked_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=38
failed_check_count=0
```

Playwright MCP 截图：

```text
e/946/图片/v946-randomized-holdout-publication-registry-downstream-consumer-ack-check.png
```

## 一句话总结

v946 让 downstream consumer ack 具备了可重建 contract check，确认 ack 没有漂移、没有丢源、也没有突破 lookup-only 边界。
