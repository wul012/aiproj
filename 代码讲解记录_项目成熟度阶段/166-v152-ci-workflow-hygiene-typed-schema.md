# 第一百五十二版代码讲解：CI workflow hygiene typed schema

## 本版目标

v152 是一次轻量、定向的代码质量优化。
目标是让 `ci_workflow_hygiene` 的内部数据结构更清楚，同时修复 action tag major 解析过窄的问题。

本版解决两个问题：

- CI workflow hygiene 的 check、action、summary、report 都是固定结构，但此前大量使用 `dict[str, Any]`，容易让字段名拼写和字段类型漂移。
- `_major()` 只识别 `v6`，遇到 `v6.0.0` 或 `6` 会返回 0，导致 Node 24 native major 判断过于脆弱。

本版不做：

- 不新增新的 CI workflow gate。
- 不改变 `.github/workflows/ci.yml`。
- 不扩大到其它报告模块的大规模 TypedDict 迁移。
- 不改变既有 JSON/Markdown/HTML artifact 格式。

## 前置路线

本版承接 v145-v151 的 CI workflow hygiene 链路：

```text
v145 -> CI workflow hygiene report
v146-v151 -> CI workflow hygiene evidence enters audit, bundle, readiness, registry, maturity
v152 -> CI workflow hygiene implementation quality hardening
```

也就是说，v152 不再继续增加治理层级，而是对已经高频复用的 CI workflow hygiene 源头做一次小型收口。

## 关键文件

```text
src/minigpt/ci_workflow_hygiene.py
tests/test_ci_workflow.py
README.md
c/152/解释/说明.md
```

`ci_workflow_hygiene.py` 是核心实现，负责读取 workflow、收集 action、构建 checks、汇总 summary，并输出 JSON/CSV/Markdown/HTML。

`tests/test_ci_workflow.py` 负责锁住当前 workflow 通过、旧 runtime policy 失败、输出格式可写，以及新增的 action major 解析边界。

## TypedDict 结构

v152 新增四个内部类型：

```text
CiWorkflowCheck
CiWorkflowAction
CiWorkflowSummary
CiWorkflowReport
```

`CiWorkflowCheck` 固定字段：

```text
id
category
target
expected
actual
status
detail
```

`status` 使用：

```text
Literal["pass", "fail"]
```

`CiWorkflowAction` 固定字段：

```text
repository
version
raw
line
node24_native
```

`CiWorkflowSummary` 固定计数字段：

```text
check_count
passed_check_count
failed_check_count
action_count
required_action_count
found_required_action_count
node24_native_action_count
forbidden_env_count
required_step_count
missing_step_count
python_version
```

`CiWorkflowReport` 则把 summary、actions、checks 和 recommendations 组合成最终报告。

## 兼容性边界

本版没有把所有公开渲染入口都改成只接受 `CiWorkflowReport`。

例如：

```text
render_ci_workflow_hygiene_markdown(report: dict[str, Any])
render_ci_workflow_hygiene_html(report: dict[str, Any])
write_ci_workflow_hygiene_outputs(report: dict[str, Any], ...)
```

这些入口仍然接受 `dict[str, Any]`，因为它们经常读取旧 JSON artifact 或测试构造的普通字典。
TypedDict 主要服务内部生成链路，让 `_check()`、`_collect_actions()`、`_build_checks()` 和 `build_ci_workflow_hygiene_report()` 更稳。

## action major 解析

旧逻辑：

```text
^v(?P<major>[0-9]+)$
```

只能识别：

```text
v6
```

新逻辑：

```text
^v?(?P<major>[0-9]+)(?:\.[0-9]+){0,2}$
```

可以识别：

```text
v6
v6.0.0
6
```

这只影响 `node24_native` 的 major 判断。
它不会改变策略层面对 action tag 的精确要求：当前 `REQUIRED_ACTIONS` 仍然要求 `actions/checkout@v6` 和 `actions/setup-python@v6`。

## 测试设计

新增测试：

```text
test_ci_workflow_hygiene_accepts_semver_and_bare_major_action_tags
```

这个测试构造临时 workflow：

```text
actions/checkout@v6.0.0
actions/setup-python@6
```

断言：

- `node24_native_action_count == 2`
- 两个 action 的 `node24_native` 都是 `True`
- 报告总体仍为 `fail`
- check detail 仍提示应升级到期望 major/tag

这个设计区分了两个概念：

- major 能力判断：`v6.0.0` 和 `6` 都是 Node 24 native major。
- 项目策略判断：当前配置仍要求精确 `@v6`。

## 证据边界

v152 证明的是 CI workflow hygiene 源码质量更稳，action 版本解析更不脆弱。

它不证明模型质量提升，也不代表 release gate 或 maturity summary 规则变化。

## 运行与归档

v152 的运行截图和解释放在：

```text
c/152/图片
c/152/解释/说明.md
```

截图覆盖 CI workflow 单测、CI workflow hygiene smoke、source encoding hygiene、maintenance smoke、全量 unittest 和文档对齐检查。

## 一句话总结

v152 把 CI workflow hygiene 从“可运行的治理报告”进一步收紧成“schema 更清楚、版本解析更稳”的低风险质量基座。
