# v463 archived path portability CI gate

## 本版目标和边界

v463 的目标是把一次真实 CI 失败固化成防回归能力：v448 归档 handoff 中保存了 Windows 风格路径，Linux runner 会把 `d\448\...` 当成普通文件名。本版新增 archived path portability check，专门验证这些归档路径在规范化后仍能解析到真实 sidecar。

本版不迁移旧归档，不修改 v448 JSON，也不扩大成全仓库路径扫描。检查范围刻意收窄在 receipt、assurance、promoted-handoff 相关引用，避免把历史输入路径误判成必须存在的发布 sidecar。

## 前置链路

本版承接的是 v458-v462 的 receipt failure-smoke CI 链路：

```text
v458 receipt failure smoke in CI
  -> v459 wrapper plan
  -> v460 plan check
  -> v461 readiness carryover
  -> v462 readiness comparison regression
  -> v463 archived path portability gate
```

v463 不是新治理主线，而是给现有 receipt CI 链路补一个跨平台路径前置检查。

## 关键文件

- `scripts/check_archived_path_portability.py`
  - 默认读取 v448 promoted seed receipt handoff 相关 JSON。
  - 递归收集 path-like 字段，只保留 receipt、assurance、promoted-handoff 范围内的引用。
  - 使用 `archived_reference_path()` 和 `resolve_archived_reference_path()` 规范化并解析 Windows/POSIX 路径。
  - 输出 JSON、CSV、text、Markdown、HTML。
- `src/minigpt/report_utils.py`
  - 前一轮 CI hotfix 中新增的 `archived_reference_path()` 和 `resolve_archived_reference_path()` 成为本版检查器的公共基础。
- `.github/workflows/ci.yml`
  - 新增 `Archived path portability check`，放在 CI workflow hygiene 之后、promoted seed handoff assurance 之前。
- `src/minigpt/ci_workflow_hygiene.py`
  - 新增 required command：`scripts/check_archived_path_portability.py`。
  - 新增顺序约束：必须在 receipt failure smoke 和 coverage 之前。
  - 新增 summary 字段：`archived_path_portability_check_present/order_ready/ready`。
- `src/minigpt/ci_workflow_hygiene_artifacts.py`
  - Markdown/HTML 输出新增 archived path readiness 指标。
- `tests/test_archived_path_portability.py`
  - 覆盖 Windows separator 正常解析、缺失引用失败、默认 v448 归档通过、CLI 输出。
- `tests/test_ci_workflow.py`
  - 覆盖 CI workflow hygiene 对新 gate 的存在性、顺序和渲染字段。

## 核心数据结构

检查器输出的 summary 字段：

```json
{
  "status": "pass",
  "decision": "continue",
  "source_count": 4,
  "path_reference_count": 86,
  "windows_separator_count": 86,
  "portable_reference_count": 86,
  "failed_reference_count": 0
}
```

每条引用会记录：

```json
{
  "source_json": "...",
  "json_path": "$.receipt_check.receipt_path",
  "raw": "d\\448\\解释\\promoted-handoff\\...",
  "normalized": "d/448/解释/promoted-handoff/...",
  "resolved": "...",
  "has_windows_separator": true,
  "exists": true,
  "status": "pass"
}
```

这些字段的作用是把“路径能不能跨平台解析”从隐含的文件读取行为，变成可检查、可截图、可放进 CI 的证据。

## 运行流程

默认命令：

```text
python -B scripts/check_archived_path_portability.py --out-dir d/463/解释/archived-path-portability
```

流程如下：

1. 读取默认 v448 receipt handoff 相关 JSON。
2. 递归收集 path-like 字段。
3. 只保留 receipt、assurance、promoted-handoff 相关路径。
4. 将 `\` 规范化成平台可解析路径。
5. 检查规范化后的路径是否存在。
6. 输出多格式报告；若有失败引用，默认返回非零。

## 测试覆盖

本版测试保护三类风险：

- Windows separator 的正常路径应通过。
- 规范化后仍不存在的路径应失败。
- 默认 v448 归档路径应在当前仓库中全部可解析。
- CI workflow hygiene 必须识别新 gate，并检查它在 receipt smoke 和 coverage 之前。

Focused 验证结果：

```text
tests/test_archived_path_portability.py tests/test_ci_workflow.py
12 passed
```

## 运行证据

`d/463` 保存本版证据：

- `解释/archived-path-portability/`
  - checker JSON、CSV、text、Markdown、HTML。
  - Playwright MCP snapshot。
- `解释/ci-workflow-hygiene/`
  - CI workflow hygiene JSON、CSV、Markdown、HTML。
- `图片/archived-path-portability.png`
  - Playwright MCP 截图，确认 HTML 中显示 `status=pass`、86 个 Windows separator references、0 failed references。

## 一句话总结

v463 把 Windows 归档路径在 Linux CI 上的兼容性从“修过一次”推进到“每次 CI 都能证明”，让 receipt 证据链少一个隐蔽的平台差异风险。
