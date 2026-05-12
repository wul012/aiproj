# 46-v31-release-gate-policy-profiles

## 本版目标、来源和边界

v31 的目标是把 v30 的 release gate 从“若干命令行参数组合”升级成“可命名、可复查、可覆盖的策略档位”。

v30 已经把 generation quality audit checks 变成 release gate 的显式要求，但当项目继续向发布治理阶段推进时，只靠 `--min-audit-score`、`--min-ready-runs` 和 `--allow-missing-generation-quality` 这些散落参数，会让一次发布到底采用了哪种标准不够直观。v31 因此新增 `standard`、`review`、`strict`、`legacy` 四个 policy profile，让 gate report 本身能记录“本次用的是哪种策略”。

本版不做三件事：

- 不改变 release bundle 的输入结构。
- 不新增训练、评估或生成质量算法。
- 不把 warn 状态强行改成 fail；`--fail-on-warn` 仍然是 CLI 层的显式选择。

## 关键文件

```text
src/minigpt/release_gate.py
scripts/check_release_gate.py
tests/test_release_gate.py
README.md
代码讲解记录_发布治理阶段/README.md
a/31/解释/说明.md
```

`release_gate.py` 是本版核心。它新增 profile 定义、profile 解析和覆盖规则，并把解析后的策略写进 `gate_report.json` 的 `policy` 字段。

`check_release_gate.py` 是 CLI 入口。它新增 `--policy-profile`，并保留旧参数作为覆盖项。

`test_release_gate.py` 是保护网。它不仅测试 pass/fail，还测试 profile 列表、防外部修改、未知 profile 报错、strict 阈值、review 阈值、legacy generation quality 兼容，以及显式覆盖优先级。

## policy profile 的数据结构

核心常量是：

```python
DEFAULT_RELEASE_GATE_POLICY_PROFILE = "standard"

RELEASE_GATE_POLICY_PROFILES = {
    "standard": {
        "minimum_audit_score": 90.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
    },
    "review": {
        "minimum_audit_score": 80.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
    },
    "strict": {
        "minimum_audit_score": 95.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": True,
    },
    "legacy": {
        "minimum_audit_score": 80.0,
        "minimum_ready_runs": 1,
        "require_generation_quality": False,
    },
}
```

四个档位的含义是：

```text
standard -> 默认发布策略，保持 v30 行为
review   -> 内部评审策略，降低 audit score 阈值，但仍要求 generation quality 证据
strict   -> 更严格交付策略，提高 audit score 阈值
legacy   -> 旧 bundle 兼容策略，允许缺少 generation quality audit checks
```

这里没有把 profile 做成类或复杂配置文件，是因为当前项目还处在学习型 AI 工程阶段。用一个可读的常量字典更便于讲解，也足够让 JSON、Markdown、HTML 报告记录策略来源。

## 解析流程

新增函数：

```python
resolve_release_gate_policy(
    policy_profile="standard",
    minimum_audit_score=None,
    minimum_ready_runs=None,
    require_generation_quality=None,
)
```

它做四件事：

1. 检查 `policy_profile` 是否存在，不存在就抛出 `ValueError`。
2. 复制 profile 默认值，避免调用方修改全局配置。
3. 用显式参数覆盖 profile 默认值。
4. 返回最终 policy 和 `overrides` 字段。

`overrides` 是本版一个关键证据字段：

```json
{
  "minimum_audit_score": true,
  "minimum_ready_runs": false,
  "require_generation_quality": true
}
```

它说明这次 gate 不是纯 profile 默认行为，而是有人显式覆盖了部分策略值。以后看归档或 CI 日志时，不需要猜 `strict` 为什么只有 90 分阈值，报告里会直接暴露覆盖痕迹。

## build_release_gate 的输入输出边界

`build_release_gate` 的外部输入仍然是 `release_bundle.json`，但策略参数从原来的散落默认值升级为：

```python
build_release_gate(
    bundle_path,
    policy_profile="standard",
    minimum_audit_score=None,
    minimum_ready_runs=None,
    require_generation_quality=None,
)
```

默认值设计很重要：

- `policy_profile="standard"` 保持 v30 的默认行为。
- `minimum_audit_score=None` 表示使用 profile 阈值。
- `minimum_ready_runs=None` 表示使用 profile 阈值。
- `require_generation_quality=None` 表示使用 profile 要求。

这让旧调用方式仍然成立，也让新调用方式更清楚：

```text
standard profile -> v30 默认门禁
strict profile   -> 更高 audit score 阈值
legacy profile   -> 兼容 v29/v30 之前没有 generation quality audit checks 的 bundle
```

输出里的 `policy` 现在包含：

```json
{
  "policy_profile": "standard",
  "profile_description": "...",
  "required_release_status": "release-ready",
  "required_audit_status": "pass",
  "minimum_audit_score": 90.0,
  "minimum_ready_runs": 1,
  "require_all_evidence_artifacts": true,
  "require_generation_quality_audit_checks": true,
  "overrides": {
    "minimum_audit_score": false,
    "minimum_ready_runs": false,
    "require_generation_quality": false
  }
}
```

这些字段同时进入 JSON、Markdown 和 HTML 报告，因此它们既是运行配置，也是最终发布证据。

## CLI 行为

`scripts/check_release_gate.py` 新增：

```powershell
--policy-profile standard|review|strict|legacy
```

默认是 `standard`。旧参数继续可用：

```powershell
--min-audit-score
--min-ready-runs
--allow-missing-generation-quality
--fail-on-warn
```

它们和 profile 的关系是“显式覆盖优先”。例如：

```powershell
python scripts/check_release_gate.py --bundle runs/release-bundle/release_bundle.json --policy-profile strict --min-audit-score 90
```

这表示本次采用 strict 档位，但 audit score 阈值被显式放回 90。报告中的 `policy_profile=strict` 和 `overrides.minimum_audit_score=true` 会同时保存下来。

CLI 输出新增：

```text
policy_profile=standard
minimum_audit_score=90.0
minimum_ready_runs=1
require_generation_quality=True
```

这些行适合放进截图或 CI 日志，能直接证明本次门禁用的策略。

## 测试覆盖链路

本版测试重点不是只确认函数能跑，而是确认 profile 真正影响 gate 决策：

- `test_release_gate_policy_profiles_are_available`
  - 确认四个 profile 都存在。
  - 确认 `release_gate_policy_profiles()` 返回的是拷贝，外部修改不会污染全局策略。

- `test_resolve_release_gate_policy_rejects_unknown_profile`
  - 防止拼错 profile 时悄悄落到默认策略。

- `test_build_release_gate_passes_ready_bundle`
  - 保护默认 `standard` 仍是 v30 行为。

- `test_strict_profile_raises_audit_score_threshold`
  - 用 `audit_score=92` 证明 strict 的 95 分阈值会阻断发布。

- `test_review_profile_lowers_audit_score_threshold_but_keeps_generation_quality`
  - 用 `audit_score=85` 证明 review 可以放宽分数，但不会放弃 generation quality 证据。

- `test_legacy_profile_allows_missing_generation_quality_checks`
  - 证明 legacy 能兼容旧 bundle，避免历史归档因为新策略无法复查。

- `test_explicit_overrides_take_precedence_over_policy_profile`
  - 证明显式参数优先于 profile，并且 `overrides` 会记录覆盖痕迹。

这些断言保护的是发布治理语义：不同场景用不同策略，但每次策略选择都必须能被报告复查。

## 归档和截图证据

v31 归档放在：

```text
a/31/图片
a/31/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-release-gate-policy-profiles-smoke.png
03-release-gate-policy-profiles-structure-check.png
04-playwright-release-gate-policy-profiles.png
05-docs-check.png
```

其中 `02` 证明四个 profile 能从 CLI/函数层跑通；`03` 证明 JSON/Markdown/HTML 结构中确实写入 profile、阈值和 overrides；`04` 证明 HTML 报告能在真实浏览器中打开；`05` 证明 README、新阶段讲解目录和归档结构已经闭环。

## 一句话总结

v31 把 MiniGPT 的 release gate 从“单次命令参数”推进成“可命名、可复查、可覆盖的发布策略档位”，发布治理阶段正式开始有自己的策略语言。
