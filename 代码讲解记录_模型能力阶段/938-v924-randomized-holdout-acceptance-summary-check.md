# v924 randomized holdout acceptance summary check 代码讲解

## 本版目标和边界

v924 的目标是检查 v923 acceptance summary 是否能从源 v922 decision index 重新推导。

v923 把 bounded acceptance 整理成 accepted/blocked claims，阅读性更强。但越是阅读友好的摘要，越需要防止字段被手动改宽。v924 就是在这个位置补 contract check。

明确不做：

- 不重新训练。
- 不重新跑 checkpoint replay。
- 不修改 v922 或 v923 的源产物。
- 不批准 production promotion。
- 不新增模型能力声明。

## 前置链路

```text
v922 randomized holdout decision index
  -> v923 acceptance summary
  -> v924 acceptance summary contract check
```

v924 的源输入是 v923 summary，但真正的重建依据是 v923 记录的 `source_decision_index`，也就是 v922 index。

## 关键文件

### `src/minigpt/randomized_holdout_acceptance_summary_check.py`

核心入口：

```python
build_randomized_holdout_acceptance_summary_check(...)
```

输入：

- `acceptance_summary`：v923 summary JSON。
- `acceptance_summary_path`：可选，用来解析相对路径。

输出：

```text
status
decision
failed_count
issues
source_acceptance_summary
source_decision_index
source_summary
rebuilt_summary
check_rows
summary
```

### 重建逻辑

`_rebuild_summary(...)` 会读取 `source_decision_index`：

```python
build_randomized_holdout_acceptance_summary(
    read_acceptance_input_json(source_index),
    decision_index_path=source_index,
)
```

这里故意复用 v923 builder，而不是在 check 里复制规则。这样后续如果 summary 的 contract 正常变化，重建路径和生产路径仍然同源。

### 路径解析

`_resolve_source_index(...)` 支持两种情况：

- `source_decision_index` 是可直接访问的路径。
- `source_decision_index` 是相对 summary 文件目录的路径。

真实 v923 记录的是仓库相对路径：

```text
e\922\解释\randomized-holdout-decision-index\randomized_holdout_decision_index.json
```

在仓库根目录运行时可以直接解析。

### CHECKED_SUMMARY_FIELDS

本版集中列出需要比较的 summary 字段：

```text
randomized_holdout_acceptance_summary_ready
bounded_promotion_accepted
accepted_claim_count
blocked_claim_count
candidate_case_count
random_seed
pass_rate
promotion_ready
approved_for_promotion
model_quality_claim
allowed_use
source_count
next_step
```

这些字段覆盖了 ready 状态、bounded acceptance、claim 数量、case/seed/pass rate 和 promotion boundary。

### claims fingerprint

v924 不直接整包比较 JSON，因为 `generated_at` 等字段会自然变化。它只比较稳定 contract fingerprint：

```text
accepted_claims:
  claim_id
  status
  scope
  model_quality_claim
  allowed_use

blocked_claims:
  claim_id
  status
  reason
```

如果有人把 accepted claim 的 `allowed_use` 改成 `production_promotion`，本版测试会失败。

### source_rows fingerprint

source rows 比较以下稳定字段：

```text
kind
status
decision
ready_key
ready_value
promotion_ready
model_quality_claim
```

这能保护 v923 没有丢失 v922 index 的四层来源，也能防止 summary 层把某一层 promotion 边界改掉。

## Artifact writer

`src/minigpt/randomized_holdout_acceptance_summary_check_artifacts.py` 输出：

- JSON：完整 contract check。
- CSV：逐项 check rows。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

HTML 首屏直接显示：

```text
Status
Decision
Ready
Original claims
Rebuilt claims
Failed
```

## CLI

脚本：

```text
scripts/check_randomized_holdout_acceptance_summary.py
```

真实运行：

```powershell
python scripts\check_randomized_holdout_acceptance_summary.py `
  e\923\解释\randomized-holdout-acceptance-summary `
  --out-dir e\924\解释\randomized-holdout-acceptance-summary-check `
  --require-pass `
  --force
```

`--require-pass` 下，只要 contract check 失败就返回 1，适合以后接入 CI 或 release preflight。

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_acceptance_summary_check.py
```

覆盖：

1. 合法 summary 能从 source index 重建，contract check pass。
2. accepted claim 的 `allowed_use` 被篡改时失败。
3. `source_decision_index` 缺失或不存在时失败。
4. CLI `--require-pass` 对篡改 summary 返回 1，并仍写出检查报告。
5. artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

focused 测试结果：

```text
9 passed
```

## 真实运行证据

真实 v924 读取：

```text
e/923/解释/randomized-holdout-acceptance-summary/randomized_holdout_acceptance_summary.json
```

结果：

```text
status=pass
decision=randomized_holdout_acceptance_summary_contract_check_passed
failed_count=0
contract_check_ready=True
original_decision=randomized_holdout_acceptance_summary_ready
rebuilt_decision=randomized_holdout_acceptance_summary_ready
original_accepted_claim_count=1
rebuilt_accepted_claim_count=1
original_blocked_claim_count=3
rebuilt_blocked_claim_count=3
```

截图：

```text
e/924/图片/v924-randomized-holdout-acceptance-summary-check.png
```

## 一句话总结

v924 让 v923 acceptance summary 从“好读”升级成“可重建、可验真”，把 bounded claim 的边界保护延伸到了摘要层。
