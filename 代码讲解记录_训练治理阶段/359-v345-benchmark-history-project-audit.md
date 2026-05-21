# 第一百三十九篇代码讲解：第345版 benchmark history project audit

本版目标，是让 v343-v344 已经形成的 benchmark history 继续进入 `project_audit`。

v343 负责把 scorecard comparison 和 scorecard decision 串成历史账本；v344 让 maturity narrative 能读取这份历史账本；v345 则把同一份历史评估证据放进项目审计入口。这样 release bundle 或 release gate 之前，审计报告就能直接看到 benchmark history 是否 ready、是否有 review/blocker、是否只是 tiny-smoke plumbing evidence。

本版不做新的训练，不新增 benchmark case，也不改变模型结构。它只消费已有的 `benchmark_history.json`，并把其中的状态、回归和边界字段变成 project audit 的检查项、summary 字段和渲染输出。

## 本版所处链路

前置链路是：

```text
scorecard comparison -> scorecard decision -> benchmark history -> maturity narrative
```

v345 追加的是：

```text
benchmark history -> project audit -> release bundle / release gate
```

因此这一版的价值不是多做一个展示页，而是把历史评估证据放到发布前审计位置，减少“maturity narrative 看到了风险，但 project audit 没看到”的断层。

## 输入输出

新增可选输入：

```text
benchmark_history.json
```

CLI 参数是：

```text
--benchmark-history <path>
```

如果没有显式传入，`project_audit` 会按 registry 位置自动发现：

```text
<registry_dir>/benchmark_history.json
<registry_dir>/benchmark-history/benchmark_history.json
<registry_parent>/benchmark-history/benchmark_history.json
```

输出仍然是原来的三件套：

```text
project_audit.json
project_audit.md
project_audit.html
```

只是其中新增了 benchmark history path、context、check 和 summary 字段。

## 关键文件

`src/minigpt/project_audit_contexts.py`

- 新增 `build_benchmark_history_context()`。
- 新增 `build_benchmark_history_check()`。
- context 负责从 history summary 和 entries 中提取稳定字段。
- check 负责把 ready/review/blocked、regression、model-quality-claim 和 latest boundary 变成 audit 状态。

`src/minigpt/project_audit.py`

- `build_project_audit()` 新增 `benchmark_history_path` 参数。
- 新增 `_resolve_benchmark_history_path()` 自动发现 history ledger。
- `_build_checks()` 追加 `benchmark_history` 检查。
- `_summarize_checks()` 新增 benchmark history summary 字段。
- `_benchmark_history_status()` 统一判断 history 是否审计通过。

`src/minigpt/project_audit_artifacts.py`

- Markdown 顶部列出 benchmark history 输入路径。
- Markdown summary 显示 history status、entries、ready、regressions、boundary。
- HTML stats 显示 `Bench history` 和 `Bench entries`，便于截图审阅。

`scripts/audit_project.py`

- 新增 `--benchmark-history`。
- stdout 打印：

```text
benchmark_history_status
benchmark_history_entries
benchmark_history_ready
benchmark_history_boundary
```

这些字段适合 CI 或人工 smoke 快速读取。

## 核心字段语义

`benchmark_history_status`

- `pass`：history 可用，至少有 entry，至少有 ready entry，没有 review/blocker/regression，且不是 `not_claimed`。
- `warn`：history 缺失、无 ready entry、存在 review/blocker、存在 case regression、存在 generation-quality flag regression，或只是 tiny-smoke plumbing evidence。

`benchmark_history_model_quality_claim`

- `candidate_evidence` 表示这是可作为候选模型评估证据的 history。
- `not_claimed` 表示它只是 tiny smoke 或链路 plumbing evidence，不能宣称模型质量提升。

`benchmark_history_latest_boundary`

- 保存最新 entry 的边界标签，例如 `standard-benchmark-candidate-evidence` 或 `tiny-smoke-plumbing-evidence`。
- 这个字段让 audit 报告能说明“证据类型是什么”，而不是只给出一个分数。

## 测试覆盖

`tests/test_project_audit.py` 新增或增强覆盖：

- 完整项目带 benchmark history 时，audit 可以保持 `pass`。
- benchmark history 进入 review 且有 case regression 时，audit 变成 `warn`。
- 没有显式参数时，audit 能自动发现 `benchmark-history/benchmark_history.json`。
- context helper 能识别 tiny-smoke 的 `not_claimed` 边界。
- Markdown 和 HTML 输出都包含 benchmark history 信息。

这些测试保护的是链路行为：history 不只是被读取，而是真的参与 audit 状态、建议和输出。

## 运行证据

本版证据归档在：

```text
d/345
```

其中包含：

- 聚焦测试截图。
- project audit CLI smoke 截图。
- 全量验证截图。
- 结构和文档扫描截图。
- Playwright/Chrome 打开的 project audit HTML 截图。

## 边界说明

v345 仍然不把 tiny smoke 当成模型质量证明。tiny-smoke history 会通过 `model_quality_claim=not_claimed` 和 `latest_boundary=tiny-smoke-plumbing-evidence` 保留边界，并让 audit 进入 warning。

本版也不替代 maturity narrative。maturity narrative 负责组合叙事；project audit 负责发布前审计。两者共享 benchmark history，但职责不同。

## 一句话总结

v345 把 benchmark history 从成熟度叙事继续推进到项目审计入口，让历史评估证据在 release handoff 前就能被检查、打分和解释。
