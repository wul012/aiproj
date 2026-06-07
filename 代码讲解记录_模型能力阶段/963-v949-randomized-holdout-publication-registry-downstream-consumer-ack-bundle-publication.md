# v949 randomized holdout publication registry downstream consumer ack bundle publication

## 本版目标与边界

v949 的目标是把 v948 审核通过的 downstream consumer ack bundle review 转成一个正式的 lookup-only publication artifact。v948 已经负责检查 ack bundle 的 evidence digest、文件存在性和 no-promotion 边界；v949 则负责把这个审核结果发布给后续下游检查步骤读取。

这版不训练模型，不生成新 checkpoint，不扩大模型质量声称，也不把 randomized holdout 的 bounded evidence 解释为生产 readiness。它只发布一个治理查阅入口，并把下一步路由到 publication contract check。

前置链路：

```text
v945 downstream consumer ack
 -> v946 downstream consumer ack contract check
 -> v947 downstream consumer ack bundle
 -> v948 downstream consumer ack bundle review
 -> v949 downstream consumer ack bundle publication
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.py`
  - v949 核心发布器。
  - 读取 v948 review report，检查 review 是否 pass、是否 publish ready、是否 lookup ready、证据是否完整、用途是否保持 lookup-only。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 延续 evidence rows，让 v950 可以继续读取两条源证据。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.py`
  - v949 CLI。
  - 支持 `--require-publication-ready`、`--require-lookup-ready`、`--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.py`
  - 覆盖 ready publication、publish_ready 漂移、source bundle 缺失、CLI 和 artifact 输出。

- `e/949/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication/`
  - 使用真实 v948 review 生成的运行证据。

## 核心数据结构

`publication` 是本版主结构：

```python
{
    "publication_ready": True,
    "publication_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949",
    "publication_status": "published_for_downstream_consumer_lookup_only",
    "ack_bundle_review_path": "...ack_bundle_review.json",
    "ack_bundle_path": "...ack_bundle.json",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "published_use": "downstream_governance_lookup_only",
    "publish_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "evidence_count": 2,
    "promotion_ready": False,
    "approved_for_promotion": False,
    "next_step": "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication",
}
```

这里的 `publication_status` 明确写成 `published_for_downstream_consumer_lookup_only`。这不是模型发布状态，而是治理证据发布状态：下游可以查阅 ack bundle 的证据链，但不能把它解释成生产 promotion。

## 核心检查逻辑

`_checks()` 生成 19 条检查：

- `ack_bundle_review_file_exists`：v948 review JSON 必须存在。
- `ack_bundle_review_passed`：v948 review 顶层 status 必须是 pass。
- `ack_bundle_review_decision_ready`：decision 必须是 review ready。
- `ack_bundle_review_summary_ready`：summary 和 body 都必须 ready。
- `ack_bundle_file_exists`：v948 review 指向的 v947 ack bundle 必须仍存在。
- `review_status_publishable`：review status 必须批准 lookup-only publication。
- `publish_ready`、`lookup_ready`、`contract_check_ready`：发布前的三个 ready 信号必须一致。
- `evidence_count` 和 `evidence_kinds`：必须保留 ack 与 ack contract check 两条 evidence row。
- `evidence_files_exist` 和 `evidence_statuses_pass`：源证据必须存在且 status 均为 pass。
- `acked_use_lookup_only`：summary 和 body 都必须保持 lookup-only。
- `consumer_boundary_governance`：消费边界必须保持 governance lookup only。
- `model_quality_claim_bounded`：模型质量声称必须保持 bounded randomized target-hidden holdout claim only。
- `promotion_still_false`：promotion 和 approved_for_promotion 都必须为 False。
- `source_checks_clean`：v948 源审核不能有失败检查。
- `source_next_step_matches`：v948 必须路由到本版 publication。

这些检查的重点是“发布不改变语义”：v949 只是把已审核的 bundle 公开给下游读取，不允许字段在发布时偷偷变成 promotion。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.py --ack-bundle-review e\948\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review --out-dir e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication --require-publication-ready --require-lookup-ready --force
```

流程：

1. 定位 v948 ack bundle review JSON。
2. 读取 review report。
3. 检查 review readiness、publish readiness、lookup readiness、contract-check readiness。
4. 保留两条 evidence row，确认源文件存在且状态为 pass。
5. 生成 publication JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready review 可以生成 ready publication。
- `publish_ready` 被改为 False 时，publication 失败。
- review 指向的 ack bundle 缺失时，publication 失败。
- CLI 和 artifact writer 输出完整，并能定位 review 输出目录。

这组测试保护了从 review 到 publication 的状态边界，尤其是 publish-ready、lookup-only 和 no-promotion 三个字段不会在发布时被绕开。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready
failed_count=0
publication_status=published_for_downstream_consumer_lookup_only
published_use=downstream_governance_lookup_only
evidence_count=2
promotion_ready=False
passed_check_count=19
failed_check_count=0
```

Playwright MCP 截图：

```text
e/949/图片/v949-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication.png
```

## 一句话总结

v949 把 digest-aware reviewed downstream consumer ack bundle 发布为 lookup-only publication，并把下一步推进到 publication contract check，同时继续锁住 no-promotion 边界。
