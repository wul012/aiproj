# v966 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet check

## 本版目标与边界

v966 的目标是给 v965 receipt packet 增加 contract check。v965 已经把 v964 receipt review 转成 packet rows 和 source evidence rows；v966 再从 v965 packet 中记录的 source review 重新构建一份 packet，并把两份产物的稳定字段逐项比较。

这版不训练模型，不扩大 randomized holdout 的模型质量声明，也不批准 production promotion。它验证的是治理产物可复核，不是证明模型能力变强。

前置链路：

```text
v964 receipt packet index publication receipt review
 -> v965 receipt packet index publication receipt packet
 -> v966 receipt packet index publication receipt packet contract check
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.py`
  - v966 核心 contract checker。
  - 定位 v965 packet，解析其中的 `receipt_review_path`，读取 v964 review，并重新调用 v965 packet builder。
  - 比较 summary、packet body、packet rows、source evidence rows 和 check rows。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 保存 check rows；HTML 展示 contract summary 和逐项检查。

- `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py`
  - v966 CLI。
  - 输入 v965 packet JSON 或目录。
  - 支持 `--require-pass`、`--require-promotion-ready` 和 `--force`。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py`
  - 本版增加可选 `--check-out-dir`。
  - 不传该参数时仍只生成 v965 packet；传入时会同步生成 sidecar contract check。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.py`
  - 覆盖可重建 packet、source path 篡改、source review 丢失、CLI require-pass 失败返回、artifact 输出和 builder sidecar check。

- `e/966/解释/publication-receipt-packet-check/`
  - 使用真实 v965 packet 生成的运行证据。

## 核心数据结构

v966 的 report 保留两套视图：

```python
{
    "source_summary": {...},
    "rebuilt_summary": {...},
    "source_packet": {...},
    "rebuilt_packet": {...},
    "source_packet_rows": [...],
    "rebuilt_packet_rows": [...],
    "source_evidence_rows": [...],
    "rebuilt_evidence_rows": [...],
}
```

`source_*` 来自 v965 原始 JSON，`rebuilt_*` 来自 v964 review 的重新构建结果。check 通过时，两边的稳定字段应完全一致。

`summary` 则给下游消费最关键的结果：

```python
{
    "contract_check_ready": True,
    "original_packet_status": "downstream_receipt_packet_index_publication_receipt_packet_ready",
    "rebuilt_packet_status": "downstream_receipt_packet_index_publication_receipt_packet_ready",
    "original_granted_use": "downstream_governance_lookup_only",
    "rebuilt_granted_use": "downstream_governance_lookup_only",
    "original_source_evidence_count": 2,
    "rebuilt_source_evidence_count": 2,
    "original_promotion_ready": False,
    "rebuilt_promotion_ready": False,
    "next_step": "index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet",
}
```

## 48 项检查

`_check_rows()` 先确认 source review 是否存在，再比较：

- 顶层 `status`、`decision`、`failed_count`。
- `summary` 中的 ready、packet status、consumer、lookup ready、granted use、blocked uses、row count、no-promotion、model quality claim 和 next step。
- `packet` 中的 receipt review path/digest、publication receipt digest、source paths、lookup keys、row count、no-promotion 和 next step。
- `packet_rows`。
- `source_evidence_rows`。
- v965 builder 自己输出的 `check_rows`。

这组检查的意义是：如果有人改了 v965 packet 的 lookup scope、source path、evidence row、source digest 或 no-promotion 字段，v966 都不会只看表面 status，而会通过 rebuilt packet 对比发现漂移。

## CLI 行为

检查脚本：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py e\965\解释\publication-receipt-packet --out-dir e\966\解释\publication-receipt-packet-check --require-pass --force
```

`--require-pass` 下，如果任何字段不一致，进程返回 1。

v965 builder 也新增 sidecar：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py --receipt-review e\964\解释\publication-receipt-review --out-dir <packet-dir> --check-out-dir <check-dir> --require-packet-ready --force
```

这个增强不改变默认行为，只给需要一次性生成 packet + check 的场景补一个入口。

## 测试覆盖

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.py -q -o cache_dir=runs\pytest-cache-v966-focus
```

结果：

```text
11 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v966-full
```

结果：

```text
2199 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1726, syntax_error_count=0
```

测试保护的关键行为：

- 合法 packet 可以从 source review 重建并通过。
- 手动篡改 `packet.source_review_path` 会失败。
- 手动删除或改错 `receipt_review_path` 会失败。
- `--require-pass` 遇到篡改产物返回 1。
- builder 的 `--check-out-dir` 会生成 sidecar check JSON。

## 运行证据

真实 v966 evidence 来自 v965：

```text
status=pass
failed_count=0
contract_check_ready=True
original_packet_status=downstream_receipt_packet_index_publication_receipt_packet_ready
rebuilt_packet_status=downstream_receipt_packet_index_publication_receipt_packet_ready
original_source_evidence_count=2
rebuilt_source_evidence_count=2
passed_check_count=48
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/966/解释/v966-playwright-snapshot.md`
- `e/966/图片/v966-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-check.png`

## 一句话总结

v966 把 v965 receipt packet 从“已经生成”推进到“可以从 v964 review 重建并逐字段审计”，为下一步 index 提供更可靠的输入。
