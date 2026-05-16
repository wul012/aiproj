# 第一百四十七版代码讲解：release bundle CI workflow hygiene evidence

## 本版目标

v147 的目标是把 CI workflow hygiene 从 project audit 继续带入 release bundle。

v145 新增了可运行的 `ci_workflow_hygiene` gate。v146 让 `project_audit` 可以读取并审计这份报告。v147 解决的是发布证据包层面的问题：release bundle 应该能携带这份 CI workflow 策略证据，方便后续 release readiness、release gate profile 或人工审查使用。

本版不改变 release gate 硬规则，不把 CI workflow hygiene 直接设为阻断项，也不改变模型、训练、推理或 benchmark 逻辑。

## 前置路线

本版承接：

```text
v145 -> ci_workflow_hygiene.json
v146 -> project_audit reads ci_workflow_hygiene.json
v147 -> release_bundle carries ci_workflow_hygiene evidence
```

这条路线的重点是让证据逐层进入现有治理链，而不是每新增一份报告就变成孤立产物。

## 关键文件

```text
src/minigpt/release_bundle.py
scripts/build_release_bundle.py
tests/test_release_bundle.py
README.md
c/147/解释/说明.md
```

`src/minigpt/release_bundle.py` 是核心修改点。`build_release_bundle()` 新增 `ci_workflow_hygiene_path` 参数，并支持从 `project_audit.json` 的 `ci_workflow_hygiene_path` 自动解析报告位置。

`scripts/build_release_bundle.py` 新增 `--ci-workflow-hygiene` 参数，允许用户显式传入 `runs/ci-workflow-hygiene/ci_workflow_hygiene.json`。

`tests/test_release_bundle.py` 扩展 fixture，让 release bundle 测试同时拥有 registry、model card、project audit、request history summary 和 CI workflow hygiene evidence。

## 核心数据结构

release bundle 新增输入字段：

```text
inputs.ci_workflow_hygiene_path
```

summary 新增字段：

```text
ci_workflow_status
ci_workflow_failed_checks
ci_workflow_node24_actions
```

context 新增字段：

```text
ci_workflow_context.available
ci_workflow_context.workflow_path
ci_workflow_context.status
ci_workflow_context.decision
ci_workflow_context.check_count
ci_workflow_context.failed_check_count
ci_workflow_context.action_count
ci_workflow_context.node24_native_action_count
ci_workflow_context.forbidden_env_count
ci_workflow_context.missing_step_count
ci_workflow_context.python_version
```

artifact rows 新增三项：

```text
ci_workflow_hygiene_json
ci_workflow_hygiene_md
ci_workflow_hygiene_html
```

这些 artifact row 的作用是让 release bundle 能在一个位置列出 CI workflow hygiene 的机器可读报告、Markdown 报告和 HTML 报告。

## 路径解析逻辑

`_resolve_ci_workflow_hygiene_path()` 按优先级解析：

1. 用户显式传入的 `ci_workflow_hygiene_path`。
2. `project_audit.json` 中的 `ci_workflow_hygiene_path`。
3. registry 同级或上级常见目录：

```text
ci_workflow_hygiene.json
ci-workflow-hygiene/ci_workflow_hygiene.json
../ci-workflow-hygiene/ci_workflow_hygiene.json
```

这个设计和 request history summary 的解析方式保持一致，让 release bundle 可以从 audit 自动继承证据，也允许脚本显式覆盖路径。

## 运行流程

推荐链路如下：

```text
scripts/check_ci_workflow_hygiene.py
 -> runs/ci-workflow-hygiene/ci_workflow_hygiene.json

scripts/audit_project.py --ci-workflow-hygiene runs/ci-workflow-hygiene/ci_workflow_hygiene.json
 -> runs/audit/project_audit.json

scripts/build_release_bundle.py --audit runs/audit/project_audit.json
 -> release_bundle.json carries ci_workflow_hygiene evidence
```

也可以显式传入：

```text
scripts/build_release_bundle.py --ci-workflow-hygiene runs/ci-workflow-hygiene/ci_workflow_hygiene.json
```

## 输出展示

Markdown summary 增加：

```text
CI workflow status
CI workflow failed checks
```

HTML stat cards 增加：

```text
CI workflow
```

Evidence Artifacts 里增加 CI workflow hygiene 的 JSON/Markdown/HTML。这样 release bundle 的人工阅读页面和机器可读 JSON 都能看见 CI workflow 策略证据。

## 测试覆盖

`tests/test_release_bundle.py` 新增和调整了三类断言：

- `test_build_release_bundle_summarizes_ready_release`
  - 断言 summary 里有 `ci_workflow_status=pass` 和 `ci_workflow_failed_checks=0`。
  - 断言 artifacts 包含 `ci_workflow_hygiene_json`。
  - 断言 `ci_workflow_context.status=pass`。
- `test_build_release_bundle_accepts_explicit_ci_workflow_hygiene_path`
  - 断言显式传入的 path 被写入 inputs。
  - 断言 summary 能读取 Node 24 native action 数。
  - 断言 artifacts 包含 HTML 报告。
- `test_write_release_bundle_outputs`
  - 断言 Markdown 输出包含 `CI workflow status`。

这些测试证明 release bundle 消费的是 v145/v146 产物，而不是重新解析 workflow。

## 为什么暂不改 release gate

v147 只把 CI workflow hygiene 放进 release bundle，不把它设为 release gate 的强制项。

原因是 release gate 是阻断层，直接新增硬规则会影响旧 bundle 和旧 profile。更稳妥的顺序是：

1. v145 生成证据。
2. v146 审计证据。
3. v147 打包证据。
4. 未来如果稳定，再考虑某个 profile 是否要求这项证据。

这样治理链路逐步收口，不会因为新增证据而突然让历史发布流程失效。

## 截图与归档

v147 的运行截图和解释放在 `c/147`：

- `01-release-bundle-tests.png`
- `02-ci-workflow-hygiene-smoke.png`
- `03-source-encoding-smoke.png`
- `04-maintenance-smoke.png`
- `05-full-unittest.png`
- `06-docs-check.png`

这些证据证明 release bundle 已经能携带 CI workflow hygiene evidence，同时全量测试、源码 hygiene 和维护 smoke 都保持通过。

## 一句话总结

v147 把 CI workflow hygiene 从 project audit 继续推进到 release bundle，让发布证据包能携带 CI workflow 策略治理证据，但暂不把它变成 release gate 硬阻断。
