# 第一百四十篇代码讲解：第346版 benchmark history release bundle

本版目标，是让 v345 已经接入 `project_audit` 的 benchmark history 继续进入 `release_bundle`。

v343 负责生成 benchmark history ledger；v344 让 maturity narrative 消费它；v345 让 project audit 审计它；v346 负责把这份历史评估证据带入 release handoff 包。这样版本交付时，release bundle 不只看到 audit score、request history、CI hygiene、coverage，也能看到 benchmark history 的 ready/review/blocker、regression、quality claim 和 latest boundary。

本版不训练模型，不生成新的 benchmark 结果，也不改变 release gate 策略。它只把已有 `benchmark_history.json` 或 audit 中的 benchmark history context 复制到 release bundle 的输入、摘要、产物列表和渲染输出。

## 本版所处链路

前置链路是：

```text
scorecard comparison -> scorecard decision -> benchmark history
benchmark history -> maturity narrative
benchmark history -> project audit
```

v346 追加的是：

```text
project audit / benchmark history -> release bundle
```

它的角色是 handoff 保真：前面审计过的 benchmark history，不应该在 release bundle 层丢失。

## 输入输出

新增可选输入：

```text
--benchmark-history <path>
```

如果没有显式传入，`build_release_bundle()` 会优先从 `project_audit.json` 的 `benchmark_history_path` 读取；如果 audit 中没有路径，再扫描 registry 邻近目录：

```text
<registry_dir>/benchmark_history.json
<registry_dir>/benchmark-history/benchmark_history.json
<registry_parent>/benchmark-history/benchmark_history.json
```

输出仍然是：

```text
release_bundle.json
release_bundle.md
release_bundle.html
```

新增的是 summary、inputs、artifacts、context 和渲染层里的 benchmark history 字段。

## 关键文件

`src/minigpt/release_bundle.py`

- `build_release_bundle()` 新增 `benchmark_history_path` 参数。
- `_resolve_benchmark_history_path()` 支持从 audit 或 registry 邻近目录发现 history。
- `_collect_release_artifacts()` 把 `benchmark_history.json/md/html` 加入 release artifacts。
- `_benchmark_history_context()` 从独立 history 文件或 audit context 中提取字段。
- `_build_summary()` 新增 benchmark history status、entry、ready、review、blocked、regression、quality claim、latest boundary。

`src/minigpt/release_bundle_artifacts.py`

- Markdown summary 增加 benchmark history 状态、entries、ready、regression、boundary。
- HTML stats 增加 `Bench history` 和 `Bench entries`。

`scripts/build_release_bundle.py`

- 新增 `--benchmark-history` 参数。
- stdout 增加：

```text
benchmark_history_status
benchmark_history_entries
benchmark_history_ready
benchmark_history_boundary
```

这些字段适合在命令行或 CI smoke 中快速确认 handoff 包是否保留了历史评估证据。

## 核心字段语义

`benchmark_history_status`

- 优先使用 audit summary 中的 status。
- 如果 audit 没有 status，则根据独立 history context 推导。
- review、blocked、case regression、generation-quality flag regression、没有 ready entry，或 `model_quality_claim=not_claimed` 都会推导为 `warn`。

`benchmark_history_context`

- 如果独立 `benchmark_history.json` 可用，从 history summary 和最新 entry 构建。
- 如果独立文件缺失但 audit 中有 `benchmark_history_context`，保留 audit context。
- 这样 release bundle 能在 artifact 缺失时仍然说明 audit 当时看到的 benchmark history 边界。

`benchmark_history_latest_boundary`

- 说明最新 benchmark history entry 属于标准 benchmark 候选证据，还是 tiny smoke plumbing evidence。
- 这是 release handoff 里最关键的边界字段之一。

## 测试覆盖

`tests/test_release_bundle.py` 新增/增强覆盖：

- release-ready bundle 能携带独立 benchmark history 文件。
- artifacts 中包含 `benchmark_history_json`。
- context 中能看到 latest decision status。
- audit-only warning context 在独立 history 文件缺失时仍能被 release bundle 保留。
- Markdown/HTML 渲染能显示 benchmark history summary。

这些测试保护的是 handoff 保真，不只是字段存在。

## 运行证据

本版证据归档在：

```text
d/346
```

其中包含聚焦测试、release bundle CLI smoke、全量验证、结构扫描和 Playwright/Chrome 打开的 release bundle HTML 截图。

## 边界说明

v346 仍然不把 tiny smoke 当成模型质量证明。如果 history 或 audit context 中标记为 `not_claimed` 或 `tiny-smoke-plumbing-evidence`，release bundle 会保留这个边界，而不是把它包装成 release-ready 模型能力证明。

本版也不修改 release gate 的阻断策略。它先确保 release bundle 能携带 benchmark history 证据；是否让 release gate 进一步强制检查这类字段，应作为后续版本单独处理。

## 一句话总结

v346 把 benchmark history 从 project audit 带入 release bundle，让历史评估证据在版本 handoff 包中可见、可审计、可解释。
