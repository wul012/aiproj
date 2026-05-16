# 第一百四十八版代码讲解：release readiness CI workflow hygiene panel

## 本版目标

v148 的目标是把 v147 已经进入 release bundle 的 CI workflow hygiene evidence 继续带入 release readiness dashboard。

v145 让 CI workflow hygiene 能独立产出 JSON/CSV/Markdown/HTML，v146 让 project audit 能审计它，v147 让 release bundle 能携带它。v148 解决的是最终发布总览的问题：人工查看 `release_readiness.html` 时，也应该能看到 CI workflow 是否仍然保持 Node 24 native action 策略、是否有 failed checks、以及这份证据来自哪里。

本版不改变 release gate 的硬规则，不把 CI workflow hygiene 直接升级为阻断项，也不改模型、训练、推理、benchmark 或真实 CI workflow 文件。

## 前置路线

本版承接的证据路线是：

```text
v145 -> ci_workflow_hygiene.json
v146 -> project_audit reads ci_workflow_hygiene.json
v147 -> release_bundle carries ci_workflow_hygiene evidence
v148 -> release_readiness displays ci_workflow_hygiene panel
```

这条路线的价值是让同一份 CI 策略证据逐层进入治理链，而不是停留在一个孤立脚本里。

## 关键文件

```text
src/minigpt/release_readiness.py
scripts/build_release_readiness.py
tests/test_release_readiness.py
README.md
c/148/解释/说明.md
```

`src/minigpt/release_readiness.py` 是核心。它新增 `ci_workflow_hygiene_path` 输入、解析 CI workflow hygiene JSON、生成 CI Workflow Hygiene panel，并把关键状态放入 readiness summary。

`scripts/build_release_readiness.py` 是命令行入口。它新增 `--ci-workflow-hygiene` 参数，并在命令输出里打印 `ci_workflow_status` 和 `ci_workflow_failed_checks`。

`tests/test_release_readiness.py` 扩展 release readiness fixture，让完整 dashboard 同时拥有 registry、release bundle、project audit、release gate、request history、maturity 和 CI workflow hygiene evidence。

## 核心数据结构

`build_release_readiness_dashboard()` 新增参数：

```text
ci_workflow_hygiene_path
```

返回的 `inputs` 新增：

```text
ci_workflow_hygiene_path
```

返回的 `summary` 新增：

```text
ci_workflow_status
ci_workflow_failed_checks
ci_workflow_node24_actions
```

新增 panel：

```text
key: ci_workflow_hygiene
title: CI Workflow Hygiene
status: pass | warn
detail: status=<status>; failed_checks=<n>; node24_native=<n>
source_path: ci_workflow_hygiene.json path or null
```

这些字段是 release readiness 的总览信息，不是 release gate 的 policy 字段。

## 路径解析逻辑

CI workflow hygiene 路径按这个顺序解析：

1. CLI 或函数显式传入的 `ci_workflow_hygiene_path`。
2. release bundle `inputs.ci_workflow_hygiene_path`。
3. release bundle 同级 `runs/ci-workflow-hygiene/ci_workflow_hygiene.json`。

如果能读到 JSON，dashboard 使用 JSON 的 `summary`。如果读不到 JSON，但 v147 的 release bundle 已经带有 `summary.ci_workflow_status` 或 `ci_workflow_context`，dashboard 会退回使用 bundle summary/context，避免旧 bundle 因缺少单独文件而丢失可展示状态。

如果两者都没有，CI Workflow Hygiene panel 会是 `warn`，提示缺少 `ci_workflow_hygiene.json`。

## 状态边界

CI workflow hygiene panel 故意只输出：

```text
pass
warn
```

即使 CI workflow hygiene JSON 自身是 `fail`，release readiness dashboard 也把它显示为 `warn`，并把整体 readiness 推到 `review`。

原因是 release gate 的硬阻断仍然由 release gate、project audit、release bundle 等已有面板决定。CI workflow hygiene 在 v148 阶段是治理提示和人工审查证据，不是突然改变发布策略的强制门槛。

这保证了本版既能看见 CI 策略问题，又不会让历史 release 流程因为新增面板而被意外阻断。

## 运行流程

推荐链路如下：

```text
scripts/check_ci_workflow_hygiene.py
 -> runs/ci-workflow-hygiene/ci_workflow_hygiene.json

scripts/audit_project.py --ci-workflow-hygiene runs/ci-workflow-hygiene/ci_workflow_hygiene.json
 -> runs/audit/project_audit.json

scripts/build_release_bundle.py --audit runs/audit/project_audit.json
 -> release_bundle.json carries ci_workflow_hygiene evidence

scripts/build_release_readiness.py --ci-workflow-hygiene runs/ci-workflow-hygiene/ci_workflow_hygiene.json
 -> release_readiness.json displays CI Workflow Hygiene panel
```

这个流程让 CI workflow hygiene 从独立 gate 进入 audit、bundle、readiness 三层发布治理证据。

## 输出展示

Markdown summary 增加：

```text
CI workflow
```

HTML stats 增加：

```text
CI workflow
```

Panels 增加：

```text
CI Workflow Hygiene
```

CLI 输出增加：

```text
ci_workflow_status=<status>
ci_workflow_failed_checks=<n>
```

这让命令行、机器可读 JSON、Markdown 和 HTML 都能同时看见 CI workflow hygiene 状态。

## 测试覆盖

`tests/test_release_readiness.py` 覆盖了四个关键场景：

- 完整 ready dashboard
  - 断言 `ci_workflow_status=pass`。
  - 断言 `ci_workflow_failed_checks=0`。
  - 断言 panel 集合包含 `ci_workflow_hygiene`。
  - 断言全部 panel 都是 `pass`。
- 缺少 release gate
  - 仍然保持 `incomplete`，证明旧的 gate 证据边界不变。
- release gate 失败
  - 仍然保持 `blocked`，证明硬阻断仍由 gate fail 决定。
- CI workflow hygiene 失败
  - 断言 readiness status 是 `review`。
  - 断言 decision 是 `review`。
  - 断言 CI panel 是 `warn`，不是 `fail`。

这些测试保护了本版最重要的设计边界：CI hygiene evidence 被看见，但不偷偷变成 release gate。

## 截图与归档

v148 的运行截图和解释放在 `c/148`：

- `01-release-readiness-tests.png`
- `02-release-readiness-cli-smoke.png`
- `03-ci-workflow-hygiene-smoke.png`
- `04-source-encoding-smoke.png`
- `05-maintenance-smoke.png`
- `06-full-unittest.png`
- `07-docs-check.png`

这些证据证明 release readiness 已经能展示 CI workflow hygiene panel，同时本版没有破坏源码编码检查、维护检查和全量测试。

## 一句话总结

v148 把 CI workflow hygiene 从 release bundle 继续推进到 release readiness dashboard，让发布总览能看见 CI 策略健康度，但仍把它作为 review 证据而不是 hard block。
