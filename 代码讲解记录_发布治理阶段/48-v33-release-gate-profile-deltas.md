# 48-v33-release-gate-profile-deltas

## 本版目标、来源和边界

v33 的目标是给 v32 的 release gate profile comparison 增加“差异解释”。v32 已经能把多个 release bundle 在 `standard`、`review`、`strict`、`legacy` 下的结果放进一张矩阵，但矩阵只告诉你哪个 profile blocked，仍需要人工去比对 `failed_checks` 才能知道为什么 blocked。

v33 因此新增 `deltas`：以第一个 profile 作为 baseline，默认是 `standard`，然后逐个比较后续 profile。每条 delta 会说明 compared profile 相对 baseline 新增或移除了哪些 failed/warned checks，并生成一句人能直接读懂的 explanation。

本版不做三件事：

- 不改变单个 release gate 的判定规则。
- 不替用户自动选择最终发布 profile。
- 不引入外部配置文件；baseline 仍来自 `--profiles` 的第一个 profile，后续再扩展显式 baseline 参数。

## 关键文件

```text
src/minigpt/release_gate_comparison.py
scripts/compare_release_gate_profiles.py
tests/test_release_gate_comparison.py
README.md
b/README.md
b/33/解释/说明.md
```

核心仍然是 `release_gate_comparison.py`。本版没有新增一个单独模块，而是在 comparison report 内补上 `deltas`、`release_gate_profile_deltas.csv`、Markdown 的 `Profile Deltas` 段落和 HTML 的 `Profile Deltas` 表格。

## deltas 的数据结构

`build_release_gate_profile_comparison` 现在输出：

```json
{
  "rows": [],
  "deltas": [],
  "summary": {
    "delta_count": 3,
    "decision_delta_count": 1,
    "check_delta_count": 1,
    "diverged_bundle_count": 1
  }
}
```

`rows` 仍然是一行一个 bundle/profile 的门禁结果；`deltas` 是一行一个 baseline/compared profile 的差异解释。

一条 delta 的核心字段是：

```text
bundle_path
release_name
baseline_profile
compared_profile
baseline_decision
compared_decision
baseline_gate_status
compared_gate_status
baseline_minimum_audit_score
compared_minimum_audit_score
baseline_require_generation_quality
compared_require_generation_quality
decision_changed
delta_status
added_failed_checks
removed_failed_checks
added_warned_checks
removed_warned_checks
explanation
```

这些字段的目的很明确：不是只说 `strict blocked`，而是说明 `strict` 相对 `standard` 到底多了哪个 failed check。

## baseline 和 compared 的关系

默认 profile 顺序仍然是：

```text
standard
review
strict
legacy
```

因此默认 delta 会比较：

```text
standard -> review
standard -> strict
standard -> legacy
```

如果 CLI 传入：

```powershell
--profiles review strict legacy
```

那么 baseline 就变成 `review`，delta 会比较：

```text
review -> strict
review -> legacy
```

这个设计保持了脚本简单，也让“以哪个策略为基准”在命令行里可以被顺序表达。

## explanation 如何生成

新增 `_delta_between_rows` 会对 baseline row 和 compared row 做集合差：

```text
added_failed_checks   = compared.failed_checks - baseline.failed_checks
removed_failed_checks = baseline.failed_checks - compared.failed_checks
added_warned_checks   = compared.warned_checks - baseline.warned_checks
removed_warned_checks = baseline.warned_checks - compared.warned_checks
```

然后 `_delta_explanation` 把这些差异写成句子。例如 92 分的 bundle 在 `standard` 下通过，但在 `strict` 下失败：

```text
strict changes the decision from approved -> blocked.
It adds failed check(s): audit_score.
Audit-score threshold changes from 90.0 to 95.0.
```

缺少 generation quality audit checks 的旧 bundle 在 `standard` 下 blocked，但在 `legacy` 下 approved：

```text
legacy changes the decision from blocked -> approved.
It removes failed check(s): audit_score, generation_quality_audit_checks.
Generation-quality requirement changes from True to False.
```

这样报告能直接解释“为什么两个 profile 分歧”，不用再让读者手动打开多个 gate report 对比。

## 输出产物

v33 在 v32 的四类输出基础上新增一个 delta CSV：

```text
release_gate_profile_comparison.json
release_gate_profile_comparison.csv
release_gate_profile_deltas.csv
release_gate_profile_comparison.md
release_gate_profile_comparison.html
```

其中：

- JSON 保留完整 `rows` 和 `deltas`。
- comparison CSV 继续保存矩阵行。
- delta CSV 专门保存 baseline/compared 差异，方便表格查看。
- Markdown 和 HTML 都新增 `Profile Deltas` 段落。

## CLI 行为

`scripts/compare_release_gate_profiles.py` 现在会额外打印：

```text
deltas=...
decision_deltas=...
check_deltas=...
```

`outputs` 里也会出现：

```json
{
  "delta_csv": "release_gate_profile_deltas.csv"
}
```

这使得截图或 CI 日志里能直接看到本次比较是否存在 profile 分歧。

## 测试覆盖链路

本版增强了 `tests/test_release_gate_comparison.py`：

- `test_build_profile_comparison_matrix_for_one_bundle`
  - 继续用 92 分 bundle 验证 strict blocked。
  - 新增断言 `delta_count=3`、`decision_delta_count=1`、`check_delta_count=1`。
  - 验证 strict delta 的 `added_failed_checks=["audit_score"]`。

- `test_legacy_profile_can_be_compared_against_missing_generation_quality_bundle`
  - 验证 legacy 相对 standard 移除了 `audit_score` 和 `generation_quality_audit_checks`。
  - 验证 explanation 包含 `removes failed check(s)`。

- `test_write_profile_comparison_outputs`
  - 验证新增 `release_gate_profile_deltas.csv`。
  - 验证 Markdown/HTML 都包含 `Profile Deltas`。

这些断言保护的不是视觉样式，而是“差异解释必须真实来自 gate check 集合差”。

## 归档和截图证据

按照新规则，v33 归档放在：

```text
b/33/图片
b/33/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-release-gate-profile-deltas-smoke.png
03-release-gate-profile-deltas-structure-check.png
04-playwright-release-gate-profile-deltas.png
05-docs-check.png
```

其中 `02` 证明 CLI 会输出 delta 统计和 `delta_csv`；`03` 证明 JSON、CSV、Markdown、HTML 都写入 delta 字段和解释；`04` 证明 HTML 的 `Profile Deltas` 段落能用真实 Chrome 打开；`05` 证明 README、b/33 归档和讲解索引已经闭环。

## 一句话总结

v33 把 release gate profile comparison 从“看见 profile 结果不同”推进到“能解释 profile 为什么不同”。
