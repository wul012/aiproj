# 49-v34-configurable-release-gate-baseline

## 本版目标、来源和边界

v34 的目标是把 v33 的 release gate profile delta explanations 从“默认用第一个 profile 做 baseline”推进到“可以显式指定 baseline profile”。v33 已经能解释 `standard`、`review`、`strict`、`legacy` 之间为什么分歧，但 baseline 只能通过 `--profiles` 的顺序间接控制。这个设计能用，但在讲解、截图和 CI 日志里不够直观。

本版新增 `--baseline-profile`，让使用者可以明确写出“这次用 `review` 作为参照”，再把其他已选择 profiles 都和 `review` 做 delta 对比。

本版不做三件事：

- 不改变单个 release gate 的 pass/warn/fail 判定规则。
- 不新增外部 policy 配置文件。
- 不替用户自动选择最终发布 profile，只解释不同 profile 的差异。

## 本版处在发布治理阶段的哪一环

当前发布治理链路是：

```text
project audit
 -> release bundle
 -> release gate
 -> release gate policy profiles
 -> release gate profile comparison
 -> release gate profile delta explanations
 -> configurable release gate delta baseline
```

v34 不是扩大模型能力，而是让“发布门禁为什么在不同策略下不同”更可控。它把 delta explanation 的参照系从隐含顺序变成显式字段，后续做报告、答辩、审计或 CI 对比时更容易复现。

## 关键文件

```text
src/minigpt/release_gate_comparison.py
scripts/compare_release_gate_profiles.py
tests/test_release_gate_comparison.py
README.md
b/README.md
b/34/解释/说明.md
```

其中核心修改仍集中在 `release_gate_comparison.py`。CLI 只负责接收参数和打印结果，测试负责锁住默认 baseline、显式 baseline、非法 baseline 和输出文件结构。

## baseline_profile 的数据语义

`build_release_gate_profile_comparison` 现在支持：

```python
build_release_gate_profile_comparison(
    bundle_paths,
    policy_profiles=["standard", "review", "strict", "legacy"],
    baseline_profile="review",
)
```

报告会在三个位置写入 baseline：

```text
report["baseline_profile"]
report["summary"]["baseline_profile"]
Markdown/HTML 的 summary 区域
```

这样 JSON 可以被脚本读取，Markdown 可以被人读，HTML 可以在浏览器里直接展示。CLI 也会打印：

```text
baseline_profile=review
```

这行是为了让截图和 CI 日志不必再打开 JSON 文件，也能知道本次 delta 的参照 profile。

## baseline 解析规则

新增 `_resolve_baseline_profile` 后，baseline 的规则变得明确：

```text
1. 如果没有传 --baseline-profile，沿用第一个 selected profile，保持向后兼容。
2. 如果传了 --baseline-profile，它必须是已知 policy profile。
3. 如果传了 --baseline-profile，它还必须包含在 --profiles 选择列表里。
4. deltas 会比较 baseline 与所有其他 selected profiles，顺序继续尊重 --profiles。
```

例如：

```powershell
python scripts/compare_release_gate_profiles.py `
  --bundle runs/release-bundle/release_bundle.json `
  --profiles standard review strict legacy `
  --baseline-profile review `
  --out-dir runs/release-gate-profiles
```

这时 delta 顺序是：

```text
review -> standard
review -> strict
review -> legacy
```

如果不传 `--baseline-profile`，并且 profiles 仍是 `standard review strict legacy`，则继续保持：

```text
standard -> review
standard -> strict
standard -> legacy
```

## deltas 如何受 baseline 影响

v33 的 delta 字段继续保留：

```text
baseline_profile
compared_profile
baseline_decision
compared_decision
added_failed_checks
removed_failed_checks
added_warned_checks
removed_warned_checks
explanation
```

v34 的变化不是多加一类 check，而是改变 baseline row 的选择方式。比如 92 分的 release bundle：

```text
review: approved, minimum_audit_score=80
strict: blocked, minimum_audit_score=95
```

以 `review` 为 baseline 时，`strict` 的 explanation 会说明：

```text
strict changes the decision from approved -> blocked.
It adds failed check(s): audit_score.
Audit-score threshold changes from 80.0 to 95.0.
```

这比“始终拿 standard 做参照”更适合展示 review 视角、strict 视角或 legacy 迁移场景。

## 输出产物

v34 继续输出五类 release gate profile comparison 文件：

```text
release_gate_profile_comparison.json
release_gate_profile_comparison.csv
release_gate_profile_deltas.csv
release_gate_profile_comparison.md
release_gate_profile_comparison.html
```

本版重点验证：

- JSON 顶层包含 `baseline_profile`。
- summary 包含 `baseline_profile`。
- delta CSV 的 `baseline_profile` 列全部等于显式 baseline。
- Markdown 包含 `Baseline profile`。
- HTML header 和 summary 区域展示 baseline。

## CLI 行为

`scripts/compare_release_gate_profiles.py` 新增参数：

```text
--baseline-profile
```

可选值和 policy profiles 一致：

```text
standard
review
strict
legacy
```

CLI 输出新增：

```text
baseline_profile=...
```

这行和 `deltas=...`、`decision_deltas=...`、`check_deltas=...` 一起构成最短可读日志。后续归档截图可以只看命令输出，就知道本次比较用了什么参照系。

## 测试覆盖链路

`tests/test_release_gate_comparison.py` 重点增加了三类断言：

- 默认 baseline 仍是第一个 selected profile，保护 v33 兼容性。
- 显式 `baseline_profile="review"` 后，所有 delta 都以 `review` 为 baseline，并比较 `standard`、`strict`、`legacy`。
- baseline 不在 selected profiles 里时抛出 `ValueError`，避免报告写出无法解释的参照关系。

输出测试还检查 JSON、Markdown 和 HTML 都写入 baseline 信息，防止只改 CLI、不改报告文件。

## 归档和截图证据

本版运行证据放在：

```text
b/34/图片
b/34/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-release-gate-baseline-profile-smoke.png
03-release-gate-baseline-profile-structure-check.png
04-playwright-release-gate-baseline-profile.png
05-docs-check.png
```

其中 `02` 证明 CLI 能打印 `baseline_profile=review`；`03` 证明 JSON/CSV/Markdown/HTML 的 baseline 字段和 review-based deltas 一致；`04` 证明 HTML 报告能用真实 Chrome 打开；`05` 证明 README、b/34 归档和发布治理讲解索引已经闭环。

## 一句话总结

v34 把 release gate profile delta explanation 从“顺序隐含 baseline”推进到“显式、可验证、可截图归档的 baseline profile”，让发布治理报告更适合复现和讲解。
