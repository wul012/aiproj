# v948 randomized holdout publication registry downstream consumer ack bundle review

## 本版目标与边界

v948 的目标是审核 v947 downstream consumer ack bundle，确认它是否可以进入 lookup-only publication。v947 负责把 ack 和 ack check 打包；v948 则负责验证 bundle 的证据没有悬空、没有被替换、用途没有漂移。

这版不训练模型，不发布生产模型，也不扩大模型质量声称。它只批准 downstream consumer ack bundle 作为 lookup-only 证据进入下一步 publication。

前置链路：

```text
v945 downstream consumer ack
 -> v946 downstream consumer ack contract check
 -> v947 downstream consumer ack bundle
 -> v948 downstream consumer ack bundle review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.py`
  - v948 核心审核器。
  - 读取 v947 bundle，复算 evidence SHA-256，检查 bundle 状态和边界字段。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 继续使用 evidence rows，方便后续 publication 复用。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.py`
  - v948 CLI。
  - 支持 `--require-review-ready` 和 `--require-publish-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.py`
  - 覆盖 ready review、digest 漂移、evidence kind 缺失、CLI 和 artifact 输出。

- `e/948/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review/`
  - 使用真实 v947 bundle 生成的运行证据。

## 核心数据结构

`review` 是本版主结构：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review-v948",
    "review_status": "approved_for_downstream_consumer_ack_bundle_publication",
    "ack_bundle_path": "...ack_bundle.json",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "publish_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "acked_use": "downstream_governance_lookup_only",
    "evidence_count": 2,
    "evidence_kinds": [
        "downstream_consumer_ack",
        "downstream_consumer_ack_contract_check",
    ],
    "promotion_ready": False,
}
```

这里的 `publish_ready=True` 不是生产发布，而是 lookup-only publication：它只表示 bundle 可以作为下游治理证据公开给后续步骤消费。

## 核心检查逻辑

`_checks()` 生成 19 条检查：

- `ack_bundle_file_exists`：bundle 文件必须存在。
- `ack_bundle_passed`：bundle 顶层 status 必须是 pass。
- `ack_bundle_decision_ready`：decision 必须是 bundle ready。
- `bundle_status_ready`：bundle status 必须指向 review。
- `evidence_count`：必须有两条证据。
- `evidence_kinds`：证据顺序必须是 ack、ack contract check。
- `evidence_files_exist`：两份源证据文件仍必须存在。
- `evidence_digests_match`：当前文件 SHA-256 必须等于 bundle 记录值。
- `evidence_statuses_pass` 与 `evidence_failed_counts_zero`：证据必须全部通过。
- `acked_use_lookup_only`：summary 与 bundle body 都必须保持 lookup-only。
- `promotion_still_false`：promotion 和 approved_for_promotion 都不能打开。
- `source_next_step_matches`：v947 必须路由到本版 review。

其中 digest 复算是 v948 的关键增强：它让 bundle review 不只相信 bundle 里写的 digest，而是重新读取文件计算当前 digest。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.py --ack-bundle e\947\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle --out-dir e\948\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review --require-review-ready --require-publish-ready --force
```

流程：

1. 定位 v947 bundle JSON。
2. 读取 bundle report。
3. 检查 bundle status、evidence rows、lookup-only use、no-promotion。
4. 对 evidence rows 中的文件重新计算 SHA-256。
5. 输出 review JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready bundle 可以生成 ready review。
- evidence SHA-256 被改成错误值时，review 失败。
- evidence row 缺失时，review 失败。
- CLI 和 artifact writer 输出完整。

这组测试保护了“证据完整性”，而不仅是字段存在。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready
failed_count=0
review_status=approved_for_downstream_consumer_ack_bundle_publication
publish_ready=True
acked_use=downstream_governance_lookup_only
evidence_count=2
promotion_ready=False
passed_check_count=19
failed_check_count=0
```

Playwright MCP 截图：

```text
e/948/图片/v948-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review.png
```

## 一句话总结

v948 给 downstream consumer ack bundle 增加了 digest-aware review，确认两份源证据仍真实存在且未漂移，再进入 lookup-only publication。
