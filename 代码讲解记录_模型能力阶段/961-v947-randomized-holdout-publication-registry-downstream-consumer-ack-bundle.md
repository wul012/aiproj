# v947 randomized holdout publication registry downstream consumer ack bundle

## 本版目标与边界

v947 的目标是把 v945 downstream consumer ack 和 v946 ack contract check 打包成一个 bundle，作为后续 review 的输入。v945 记录消费者确认接收，v946 验证 ack 可重建，v947 则把两份证据合成一个可审核证据包。

这版不训练模型，不做生产发布，也不改变模型质量声称。它只做证据打包，并继续保持 `downstream_governance_lookup_only` 和 `promotion_ready=False`。

前置链路：

```text
v945 downstream consumer ack
 -> v946 downstream consumer ack contract check
 -> v947 downstream consumer ack bundle
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle.py`
  - v947 核心构建器。
  - 输入 ack report 和 ack check report。
  - 输出 `bundle`、`evidence_rows`、`check_rows`、`summary`。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 记录 evidence rows，方便机器读取。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle.py`
  - v947 CLI。
  - 支持 `--consumer-ack`、`--consumer-ack-check`、`--require-bundle-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle.py`
  - 覆盖 ready bundle、ack check 失败、acked use 漂移、CLI 和 artifact 输出。

- `e/947/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle/`
  - 使用真实 v945 和 v946 生成的运行证据。

## 核心数据结构

`bundle` 是本版核心：

```python
{
    "bundle_ready": True,
    "bundle_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-v947",
    "bundle_status": "ready_for_downstream_consumer_ack_review",
    "consumer_ack_path": "...consumer_ack.json",
    "consumer_ack_check_path": "...consumer_ack_check.json",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "entry_count": 1,
    "lookup_key_count": 1,
    "lookup_keys": ["publication:randomized-holdout-publication-v928"],
    "acked_use": "downstream_governance_lookup_only",
    "evidence_count": 2,
    "promotion_ready": False,
}
```

`evidence_rows` 是本版新增价值：

```python
[
    {
        "kind": "downstream_consumer_ack",
        "path": "...consumer_ack.json",
        "sha256": "...",
        "status": "pass",
        "decision": "randomized_holdout_publication_registry_downstream_consumer_ack_ready",
        "failed_count": 0,
    },
    {
        "kind": "downstream_consumer_ack_contract_check",
        "path": "...consumer_ack_check.json",
        "sha256": "...",
        "status": "pass",
        "decision": "randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed",
        "failed_count": 0,
    },
]
```

这让后续 review 不只知道文件路径，还能验证文件内容是否与 bundle 记录一致。

## 核心检查逻辑

`_checks()` 覆盖 20 条条件：

- ack 文件和 ack check 文件必须存在。
- ack 必须 pass，decision 必须是 ack ready。
- ack check 必须 pass，decision 必须是 contract check passed。
- `contract_check_ready` 必须为 True。
- acked use 必须在 ack、original check、rebuilt check 三处都保持 downstream lookup only。
- blocked uses 必须完整。
- lookup/downstream/contract check 必须 ready。
- promotion 必须在 ack 和 original/rebuilt check 中都为 False。
- ack 的 next step 必须指向 check，check 的 next step 必须指向 bundle。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle.py --consumer-ack e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack --consumer-ack-check e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check --out-dir e\947\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle --require-bundle-ready --require-lookup-ready --force
```

流程：

1. 定位 v945 ack JSON 和 v946 ack check JSON。
2. 读取两份报告。
3. 校验来源、状态、decision、lookup-only 和 promotion 边界。
4. 为两份源证据计算 SHA-256。
5. 输出 bundle JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready ack + ready check 可以生成 ready bundle。
- ack check 被改成 fail 时 bundle 失败。
- acked use 漂移到 production promotion 时 bundle 失败。
- CLI 和 artifact writer 输出完整。

这些测试保护的是“bundle 不能包装坏证据”和“bundle 不能把 lookup-only 证据改写成 promotion 证据”。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready
failed_count=0
bundle_status=ready_for_downstream_consumer_ack_review
acked_use=downstream_governance_lookup_only
evidence_count=2
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图：

```text
e/947/图片/v947-randomized-holdout-publication-registry-downstream-consumer-ack-bundle.png
```

## 一句话总结

v947 把 downstream consumer ack 与 contract check 打包成带 digest 的审核包，为后续 review 提供了稳定证据入口。
