# v950 randomized holdout publication registry downstream consumer ack bundle publication check

## 本版目标与边界

v950 的目标是给 v949 downstream consumer ack bundle publication 增加 contract check：读取 v949 publication 记录的 `ack_bundle_review_path`，重新调用 v949 builder，从 v948 review 再生成一次 publication，然后比对两份 publication 的稳定字段。

这版不训练模型，不发布生产模型，也不扩大模型质量声称。它只回答一个问题：v949 publication 是否仍能从源 review 可靠重建。

前置链路：

```text
v947 downstream consumer ack bundle
 -> v948 downstream consumer ack bundle review
 -> v949 downstream consumer ack bundle publication
 -> v950 downstream consumer ack bundle publication contract check
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.py`
  - v950 核心检查器。
  - 定位 v949 publication，解析 source review，重建 publication，并比对 stable summary、publication body、evidence rows 和 check rows。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 记录 36 条检查结果，后续索引可以直接读取。

- `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.py`
  - v950 CLI。
  - 支持 `--require-pass`，失败时返回 1。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.py`
  - 覆盖可重建 publication、published_use 篡改、source review 缺失、CLI 和 artifact 输出。

- `e/950/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check/`
  - 使用真实 v949 publication 生成的运行证据。

## 核心数据结构

`summary` 用 original/rebuilt 成对字段表达重建结果：

```python
{
    "contract_check_ready": True,
    "source_ack_bundle_review": "...ack_bundle_review.json",
    "original_publication_status": "published_for_downstream_consumer_lookup_only",
    "rebuilt_publication_status": "published_for_downstream_consumer_lookup_only",
    "original_published_use": "downstream_governance_lookup_only",
    "rebuilt_published_use": "downstream_governance_lookup_only",
    "original_evidence_count": 2,
    "rebuilt_evidence_count": 2,
    "original_promotion_ready": False,
    "rebuilt_promotion_ready": False,
    "next_step": "index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication",
}
```

`contract_check_ready=True` 的含义是 v949 publication 与从 v948 review 重建出的 publication 完全一致。它不是 promotion ready。

## 核心检查逻辑

`_checks()` 先做 6 条全局比对：

- `source_ack_bundle_review_exists`：v949 记录的 v948 review 必须存在。
- `status`：original 与 rebuilt 顶层 status 必须一致。
- `decision`：original 与 rebuilt decision 必须一致。
- `failed_count`：失败数必须一致。
- `evidence_rows`：publication 携带的两条 evidence row 必须一致。
- `check_rows`：v949 自身 19 条 publication checks 必须一致。

随后 `_field_checks()` 分两组展开：

- `SUMMARY_FIELDS`：比对 publication ready、publication status、consumer、published use、lookup/publish/contract ready、evidence count、promotion boundary、model quality claim。
- `PUBLICATION_FIELDS`：比对 publication body 中的 source paths、evidence rows、boundary 字段和 next step。

最终一共生成 36 条检查。只要 source 缺失、用途漂移、证据漂移或 no-promotion 被打开，check 就会失败。

## CLI 运行流程

真实命令：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.py e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication --out-dir e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check --require-pass --force
```

流程：

1. 定位 v949 publication JSON。
2. 读取 publication report。
3. 从 `ack_bundle_review_path` 定位 v948 source review。
4. 重新调用 v949 publication builder。
5. 比对 original/rebuilt 的 stable fields。
6. 输出 check JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- 可重建 publication 通过 contract check。
- `published_use` 被篡改为 production promotion 时失败。
- source review 缺失时失败。
- `--require-pass` 在失败 check 下返回 1，并仍写出失败报告。
- CLI 和 artifact writer 输出完整。

测试保护的是“发布物可复核”这件事，而不是单纯检查字段存在。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_contract_check_passed
failed_count=0
contract_check_ready=True
original_publication_status=published_for_downstream_consumer_lookup_only
rebuilt_publication_status=published_for_downstream_consumer_lookup_only
original_published_use=downstream_governance_lookup_only
rebuilt_published_use=downstream_governance_lookup_only
passed_check_count=36
failed_check_count=0
```

Playwright MCP 截图：

```text
e/950/图片/v950-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check.png
```

## 一句话总结

v950 把 v949 lookup-only publication 从“已发布”推进到“可从源 review 重建验证”，为后续索引下游 publication 提供 contract 保障。
