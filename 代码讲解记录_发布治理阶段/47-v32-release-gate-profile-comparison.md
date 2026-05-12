# 47-v32-release-gate-profile-comparison

## 本版目标、来源和边界

v32 的目标是把 v31 的 `standard`、`review`、`strict`、`legacy` 四个 release gate policy profile 从“单次选择一个 profile 检查”升级成“同一个报告里横向比较多个 profile”。

v31 解决了“本次 gate 用什么策略”的问题，但仍然需要多次运行脚本才能知道同一个 release bundle 在 `standard`、`review`、`strict`、`legacy` 下分别是 approved、needs-review 还是 blocked。v32 新增 profile comparison report，用一张矩阵把一个或多个 bundle 在多个策略下的门禁结果放在一起。

本版不做三件事：

- 不改变 `release_bundle.json` 的结构。
- 不改变单次 release gate 的 pass/warn/fail 判定。
- 不自动替用户选择最终发布策略；报告只给出对比证据。

## 关键文件

```text
src/minigpt/release_gate_comparison.py
scripts/compare_release_gate_profiles.py
tests/test_release_gate_comparison.py
README.md
代码讲解记录_发布治理阶段/README.md
b/32/解释/说明.md
```

`release_gate_comparison.py` 是本版核心模块。它复用 v31 的 `build_release_gate`，对每个 bundle 和每个 profile 生成一次 gate，再把结果压平成矩阵行。

`compare_release_gate_profiles.py` 是 CLI 入口。它支持重复传入 `--bundle`，也支持用 `--profiles` 选择比较哪些 profile。

`test_release_gate_comparison.py` 是本版保护网，覆盖单 bundle、多 bundle、legacy 缺少 generation quality、输出文件和 HTML escaping。

## 报告结构

核心入口是：

```python
build_release_gate_profile_comparison(
    bundle_paths,
    policy_profiles=None,
    minimum_audit_score=None,
    minimum_ready_runs=None,
    require_generation_quality=None,
)
```

默认 profile 顺序是：

```text
standard
review
strict
legacy
```

输出报告的主要结构是：

```json
{
  "schema_version": 1,
  "title": "MiniGPT release gate profile comparison",
  "generated_at": "...",
  "bundle_paths": ["..."],
  "policy_profiles": ["standard", "review", "strict", "legacy"],
  "summary": {
    "bundle_count": 1,
    "profile_count": 4,
    "row_count": 4,
    "approved_count": 3,
    "needs_review_count": 0,
    "blocked_count": 1
  },
  "rows": [],
  "recommendations": []
}
```

这里的 `rows` 是矩阵的核心。每一行代表一个 bundle 在一个 profile 下的 gate 结果。

## rows 字段语义

一条 row 记录这些字段：

```text
bundle_path
release_name
policy_profile
profile_description
gate_status
decision
audit_score_percent
minimum_audit_score
ready_runs
minimum_ready_runs
require_generation_quality_audit_checks
pass_count
warn_count
fail_count
failed_checks
warned_checks
```

这些字段有两个作用：

- 给人看：HTML/Markdown 能直接看出 strict 为什么 blocked、legacy 为什么 approved。
- 给机器读：JSON/CSV 能被后续脚本、CI 或表格工具消费。

`failed_checks` 和 `warned_checks` 是本版最重要的解释字段。它们不是只写 `blocked`，而是把导致该 profile 不通过的 gate check id 列出来，比如：

```text
audit_score
generation_quality_audit_checks
```

这让 profile 之间的差异有了可追踪证据。

## CLI 行为

新增脚本：

```powershell
python scripts/compare_release_gate_profiles.py --bundle runs/release-bundle/release_bundle.json --profiles standard review strict legacy --out-dir runs/release-gate-profiles
```

多个 bundle 可以重复传入：

```powershell
python scripts/compare_release_gate_profiles.py --bundle runs/release-a/release_bundle.json --bundle runs/release-b/release_bundle.json
```

输出目录包含：

```text
release_gate_profile_comparison.json
release_gate_profile_comparison.csv
release_gate_profile_comparison.md
release_gate_profile_comparison.html
```

CLI 会打印：

```text
bundles=...
profiles=...
rows=...
approved=...
needs_review=...
blocked=...
outputs=...
```

默认情况下，比较报告即使包含 blocked profile 也返回 0，因为“看到 strict 阻断”本身可能就是比较任务的预期结果。需要 CI 对 blocked 失败时，可以加：

```powershell
--fail-on-blocked
```

## 输出格式为什么都保留

本版保留四种输出：

- JSON：保留完整结构，适合后续模块消费。
- CSV：适合表格扫描，也适合把多个 bundle/profile 结果导入数据分析工具。
- Markdown：适合 README、release note 或人工 review。
- HTML：适合浏览器里查看矩阵，并用 Playwright/Chrome 归档截图。

这和前面 registry、model card、project audit、release bundle、release gate 的证据链风格一致：同一份事实同时服务机器消费和人工复查。

## 测试覆盖链路

本版新增测试覆盖这些点：

- `test_build_profile_comparison_matrix_for_one_bundle`
  - 用 92 分 bundle 证明 standard/review/legacy 通过，strict 因 `audit_score` 阻断。

- `test_legacy_profile_can_be_compared_against_missing_generation_quality_bundle`
  - 用缺少 generation quality audit checks 的 bundle 证明 legacy 可以通过，standard/review 会阻断。

- `test_profile_comparison_supports_multiple_bundles`
  - 证明一个报告可以覆盖多个 release bundle。

- `test_profile_comparison_rejects_empty_or_unknown_inputs`
  - 防止空输入或未知 profile 生成误导性报告。

- `test_write_profile_comparison_outputs`
  - 证明 JSON、CSV、Markdown、HTML 四类产物都能写出。

- `test_profile_comparison_renderers_escape_release_text`
  - 保护 HTML 输出不会把 release name 当成可执行标签。

## 归档和截图证据

按照新规则，v32 归档放在：

```text
b/32/图片
b/32/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-release-gate-profile-comparison-smoke.png
03-release-gate-profile-comparison-structure-check.png
04-playwright-release-gate-profile-comparison.png
05-docs-check.png
```

其中 `02` 证明 CLI 能生成 profile comparison 报告；`03` 证明 JSON/CSV/Markdown/HTML 结构都包含矩阵字段和 blocked/approved 统计；`04` 证明 HTML 能通过真实 Chrome 打开；`05` 证明 README、b/32 归档和新阶段讲解索引已经闭环。

## 一句话总结

v32 把 release gate policy profiles 从“一个一个跑的策略档位”推进成“可以横向比较多个 bundle 和多个 profile 的发布治理矩阵”。
