# v931 randomized holdout publication registry packet 代码讲解

## 本版目标和边界

v931 的目标是把 v929 entry 和 v930 contract check 合成一个 packet：

```text
v929 publication registry entry
  + v930 registry entry contract check
  -> v931 publication registry packet
```

它回答的问题是：

```text
已登记且已复核的 randomized holdout publication entry 是否可以交给 manifest 层消费？
```

回答是可以：

```text
ready_for_publication_registry_manifest
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不生成完整 manifest。
- 不批准 production promotion。
- 不扩大 bounded randomized holdout claim。

## 前置链路

v931 消费两份真实产物：

```text
e/929/解释/randomized-holdout-publication-registry-entry
e/930/解释/randomized-holdout-publication-registry-entry-check
```

v929 证明 entry 已 registered；v930 证明 entry 可从 v928 source index 重建。v931 把这两层证据组合成一个交接包。

v931 的下一步路由到：

```text
build_randomized_holdout_publication_registry_manifest
```

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_packet.py`

核心入口：

```python
build_randomized_holdout_publication_registry_packet(...)
```

输入：

- `registry_entry_report`：v929 entry JSON。
- `registry_entry_check_report`：v930 check JSON。
- `registry_entry_path`：可选 entry 路径。
- `registry_entry_check_path`：可选 check 路径。

输出：

```text
status
decision
failed_count
issues
registry_entry_path
registry_entry_check_path
source_registry_entry_summary
source_registry_entry_check_summary
evidence_rows
check_rows
packet
summary
interpretation
```

### locator

两个 locator 允许 CLI 接收 JSON 文件或输出目录：

```python
locate_randomized_holdout_publication_registry_entry(...)
locate_randomized_holdout_publication_registry_entry_check(...)
```

如果输入是目录，自动补齐：

```text
randomized_holdout_publication_registry_entry.json
randomized_holdout_publication_registry_entry_check.json
```

### `evidence_rows`

v931 记录两类证据：

```text
registry_entry
registry_entry_contract_check
```

每行包含：

```text
kind
path
exists
```

这是后续 manifest 读取 packet 时的最小证据索引。

### `_checks(...)`

主要检查：

1. entry 和 contract check 文件都存在。
2. v929 entry `status=pass`。
3. v929 entry decision ready。
4. v929 summary ready。
5. v929 registry status 是 `registered`。
6. v930 check `status=pass`。
7. v930 check decision 是 `randomized_holdout_publication_registry_entry_contract_check_passed`。
8. v930 check summary ready。
9. entry id 与 check 里的 original/rebuilt entry id 一致。
10. bounded publication 在 entry/check 三处都为 true。
11. consumer boundary 在 entry/check 三处都为 `governance_lookup_only`。
12. allowed use 保持 `bounded_model_capability_governance_only`。
13. model quality claim 保持 `bounded_randomized_target_hidden_holdout_claim_only`。
14. promotion 和 approved_for_promotion 都是 false。
15. entry 和 check 的 failed_check_count 都为 0。

这些检查保证 packet 只打包“已登记且可复核”的 entry。

### `packet`

通过时，packet 的核心字段为：

```text
packet_ready=True
handoff_status=ready_for_publication_registry_manifest
entry_id=randomized-holdout-publication-v928
registry_status=registered
contract_check_ready=True
bounded_publication_accepted=True
promotion_ready=False
approved_for_promotion=False
accepted_claim_count=1
blocked_claim_count=3
candidate_case_count=20
random_seed=914
pass_rate=1.0
allowed_use=bounded_model_capability_governance_only
model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only
consumer_boundary=governance_lookup_only
evidence_count=2
next_step=build_randomized_holdout_publication_registry_manifest
```

## Artifact writer

`src/minigpt/randomized_holdout_publication_registry_packet_artifacts.py` 输出：

- JSON：完整 packet report。
- CSV：evidence rows。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 展示 stats、evidence、checks 三个区域。

## CLI

脚本：

```text
scripts/build_randomized_holdout_publication_registry_packet.py
```

真实运行：

```powershell
python scripts\build_randomized_holdout_publication_registry_packet.py `
  --registry-entry e\929\解释\randomized-holdout-publication-registry-entry `
  --registry-entry-check e\930\解释\randomized-holdout-publication-registry-entry-check `
  --out-dir e\931\解释\randomized-holdout-publication-registry-packet `
  --require-packet-ready `
  --require-bounded-publication `
  --force
```

`--require-promotion-ready` 仍然应失败，因为本版明确不允许 direct promotion。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_publication_registry_packet.py
```

覆盖：

1. 干净 v929 entry + v930 check 可以生成 packet。
2. contract check fail 时 packet 失败。
3. consumer boundary 被扩大时 packet 失败。
4. locator、artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

fixture 路线：

```text
ready_check_inputs
  -> build_randomized_holdout_publication_registry_entry_check
  -> build_randomized_holdout_publication_registry_packet
```

测试里曾出现一次 Windows 临时路径过深导致 fixture 写文件失败，已通过减少一层 helper 子目录修复，未改生产逻辑。

## 真实运行证据

真实 v931 读取：

```text
e/929/解释/randomized-holdout-publication-registry-entry
e/930/解释/randomized-holdout-publication-registry-entry-check
```

结果：

```text
status=pass
decision=randomized_holdout_publication_registry_packet_ready
handoff_status=ready_for_publication_registry_manifest
contract_check_ready=True
bounded_publication_accepted=True
promotion_ready=False
consumer_boundary=governance_lookup_only
passed_check_count=16
failed_check_count=0
```

截图：

```text
e/931/图片/v931-randomized-holdout-publication-registry-packet.png
```

## 一句话总结

v931 把 verified registry entry 和 contract check 合成 manifest-ready packet，继续保持 governance lookup 边界和 production promotion 阻断。
