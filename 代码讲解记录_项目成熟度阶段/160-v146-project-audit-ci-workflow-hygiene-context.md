# 第一百四十六版代码讲解：project audit CI workflow hygiene context

## 本版目标

v146 的目标是把 v145 的 CI workflow hygiene report 接入项目审计。

v145 已经新增 `src/minigpt/ci_workflow_hygiene.py` 和 `scripts/check_ci_workflow_hygiene.py`，让 `.github/workflows/ci.yml` 的 Node 24 native action 策略、Python 3.11、source encoding gate、CI hygiene gate 和 unittest discovery 可以被独立检查。

v146 解决的问题是：这份 CI workflow 策略证据不能只停留在单独的脚本输出里，它应该进入 `project_audit`，成为项目治理成熟度的一部分。

本版不改变模型、训练、推理、benchmark 评分或 release gate 硬规则。它只把 CI workflow hygiene 作为可选审计上下文接入。

## 前置路线

本版承接三条能力：

1. v131 的 project audit artifact split
   - `project_audit` 已经形成“计算审计”和“输出渲染”分层。
   - v146 只扩展审计输入和字段，不破坏 artifact facade。
2. v142-v145 的 hygiene gate 路线
   - v142 让 source encoding/target Python 兼容性进入门禁。
   - v145 让 CI workflow 策略进入门禁。
3. request history summary 接入 project audit 的既有模式
   - request history summary 是可选输入，缺失或非 pass 时给 audit warn。
   - CI workflow hygiene 沿用同样边界：治理证据缺失是 review warning，不是模型失败。

## 关键文件

```text
src/minigpt/project_audit.py
src/minigpt/project_audit_artifacts.py
scripts/audit_project.py
tests/test_project_audit.py
README.md
c/146/解释/说明.md
```

`src/minigpt/project_audit.py` 是核心修改点。`build_project_audit()` 新增 `ci_workflow_hygiene_path` 参数，并把读取到的 hygiene report 注入 checks、summary 和 context。

`src/minigpt/project_audit_artifacts.py` 负责展示层。Markdown 输出增加 `CI workflow hygiene` 输入路径，summary 表增加 CI workflow status 和 failed checks；HTML stat card 增加 CI workflow 状态。

`scripts/audit_project.py` 是 CLI 入口。它新增 `--ci-workflow-hygiene` 参数，让用户可以显式传入 `runs/ci-workflow-hygiene/ci_workflow_hygiene.json`。

`tests/test_project_audit.py` 新增 CI workflow hygiene fixture，并覆盖 pass 与 fail 两种审计结果。

## 核心数据结构

`build_project_audit()` 返回的 audit 新增三个位置：

```text
ci_workflow_hygiene_path
ci_workflow_context
summary.ci_workflow_*
```

`ci_workflow_context` 的结构是：

```text
available
workflow_path
status
decision
check_count
failed_check_count
action_count
node24_native_action_count
forbidden_env_count
missing_step_count
python_version
```

这些字段直接来自 v145 的 `ci_workflow_hygiene.json` summary。它们不重新解析 workflow，也不重新判断 action metadata；project audit 只消费已经生成的 hygiene evidence。

新增 check 的 id 是：

```text
ci_workflow_hygiene
```

当 hygiene report 缺失时：

```text
status = warn
detail = ci_workflow_hygiene.json missing; CI workflow policy was not summarized.
```

当 hygiene report 存在但 `summary.status != pass` 时：

```text
status = warn
detail = status=fail; actions=...; failed_checks=...; forbidden_env=...; missing_steps=...
```

当 hygiene report pass 时：

```text
status = pass
detail = status=pass; actions=2; node24_native=2; failed_checks=0; ...
```

## 为什么是 warn 不是 fail

CI workflow hygiene 是项目治理证据，不是模型质量证据。

它能证明：

- workflow 没有退回旧 action major。
- workflow 没有依赖 force-runtime env。
- workflow 保留 Python 3.11、source encoding gate、CI hygiene gate 和 unittest discovery。

它不能证明：

- 模型 loss 更低。
- 生成质量更强。
- 数据集更大或更干净。
- checkpoint 可以进入生产。

因此 CI hygiene 缺失或失败时，project audit 给 `warn`，提醒用户 review 治理证据；但它不会直接把整个项目审计判为模型层面的 `fail`。这个边界和 request history summary 一致。

## 运行流程

推荐流程是：

```text
scripts/check_ci_workflow_hygiene.py
 -> runs/ci-workflow-hygiene/ci_workflow_hygiene.json

scripts/audit_project.py --ci-workflow-hygiene runs/ci-workflow-hygiene/ci_workflow_hygiene.json
 -> project_audit.json / md / html
```

`project_audit` 内部流程是：

1. 读取 registry。
2. 可选读取 model card。
3. 可选读取 request history summary。
4. 可选读取 CI workflow hygiene report。
5. 构建 run rows。
6. 构建 checks，包括 `ci_workflow_hygiene`。
7. 汇总 summary，包括 `ci_workflow_status` 和 `ci_workflow_failed_checks`。
8. 渲染 JSON/Markdown/HTML。

## 测试覆盖

`tests/test_project_audit.py` 新增和调整了三类断言：

- 完整项目包含 `ci_workflow_hygiene_path` 时，audit 仍然 `pass`，并写入 `ci_workflow_context`。
- CI workflow hygiene report 为 `fail` 时，audit 变成 `warn`，check detail 展示 `failed_checks=3`，recommendations 提示 review `ci_workflow_hygiene.json`。
- 输出 Markdown 包含 `CI workflow hygiene`，证明 artifact 层也展示了新输入。

这组测试保护的是证据链接入，不是 workflow 本身。workflow 本身仍由 v145 的 `tests/test_ci_workflow.py` 和 `scripts/check_ci_workflow_hygiene.py` 保护。

## 截图与归档

v146 的运行截图和解释放在 `c/146`：

- `01-project-audit-tests.png`
- `02-ci-workflow-hygiene-smoke.png`
- `03-source-encoding-smoke.png`
- `04-maintenance-smoke.png`
- `05-full-unittest.png`
- `06-docs-check.png`

这些证据证明 v146 没有把 CI hygiene 做成孤立报告，而是把它接进项目审计，同时保持全量测试和既有维护 smoke 通过。

## 边界说明

本版没有把 `ci_workflow_hygiene` 接入 release gate 的必需项。原因是 release gate 已经承担较强发布阻断职责，直接把新治理证据设为硬门槛可能会让历史 bundle 和旧流程产生不必要断裂。

先进入 project audit 是更稳妥的收口：它能被 release bundle 间接携带，也能让用户在审计层看到 CI hygiene 状态。未来如果这条证据稳定，再考虑是否把它升级为 release gate profile 的显式要求。

## 一句话总结

v146 把 CI workflow hygiene 从独立门禁接入 project audit，让 CI 策略成为项目审计能看见、能评分、能归档的治理上下文。
