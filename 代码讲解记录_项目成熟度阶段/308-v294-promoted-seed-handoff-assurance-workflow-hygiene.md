# v294 promoted seed handoff assurance workflow hygiene

## 本版目标和边界

v294 的目标是把 v292-v293 新增的 promoted seed handoff assurance smoke 纳入 CI workflow hygiene。

v292 把 smoke 加进 GitHub Actions，v293 给 smoke 增加 summary artifacts。v294 继续收口：CI hygiene 不只检查 source encoding、coverage 和 Node 24 action policy，也检查 assurance smoke 命令是否存在，以及它是否位于 coverage 前。

本版不改变 GitHub Actions 文件本身，不改变 smoke 脚本行为，不改变 coverage 阈值，也不改变模型训练和评估逻辑。

## 前置链路

相关前置版本：

- v292：GitHub Actions 新增 promoted seed handoff assurance smoke。
- v293：smoke 输出顶层 summary JSON/text。
- v294：CI workflow hygiene 保护 smoke step 不被删除或移动到 coverage 后。

这版属于“防 workflow 漂移”的治理版本。

## 关键修改文件

### `src/minigpt/ci_workflow_hygiene.py`

`REQUIRED_COMMAND_FRAGMENTS` 新增：

```python
"promoted_seed_handoff_assurance_smoke": "scripts/check_promoted_seed_handoff_assurance_smoke.py"
```

这会把 assurance smoke 纳入 required command 检查。如果 workflow 删除该命令，CI hygiene 报告会失败。

新增 `REQUIRED_COMMAND_ORDER`：

```python
REQUIRED_COMMAND_ORDER = {
    "promoted_seed_handoff_assurance_smoke_before_coverage": (
        "scripts/check_promoted_seed_handoff_assurance_smoke.py",
        "scripts/run_test_coverage.py",
    ),
}
```

这表示 smoke 必须在 coverage 前执行。

新增 summary 字段：

```text
required_order_count
order_violation_count
```

`_build_checks()` 现在会输出一条 `required_order` check：

```text
id=order:promoted_seed_handoff_assurance_smoke_before_coverage
category=required_order
expected=before
actual=before|after|missing
```

如果 smoke 在 coverage 后，`order_violation_count` 会变成 1，报告状态为 fail。

### `src/minigpt/ci_workflow_hygiene_artifacts.py`

Markdown summary 和 HTML stats 新增 `order_violation_count`。

这样不仅 JSON 能看到顺序问题，人工打开 Markdown/HTML 也能直接看到 workflow 是否存在顺序违规。

### `tests/test_ci_workflow.py`

增强当前 workflow pass 测试：

- 当前 workflow `order_violation_count == 0`。
- checks 里包含 `order:promoted_seed_handoff_assurance_smoke_before_coverage`。

调整旧 runtime policy 测试：

- required step 从 4 增至 5。
- 缺失 step 从 2 增至 3，因为 assurance smoke 现在也是必需项。

新增错误顺序测试：

```python
test_ci_workflow_hygiene_requires_assurance_smoke_before_coverage
```

该测试构造一个 smoke 在 coverage 后的 workflow，确认：

- 报告状态为 fail。
- `missing_step_count == 0`，说明命令都在。
- `order_violation_count == 1`，说明失败原因是顺序漂移。
- `required_order` check 的 detail 会提示 smoke 必须在 coverage 前。

## 输入输出格式

命令不变：

```powershell
python scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene
```

输出 JSON 中新增：

```json
{
  "summary": {
    "required_step_count": 5,
    "missing_step_count": 0,
    "required_order_count": 1,
    "order_violation_count": 0
  }
}
```

`checks` 中新增：

```json
{
  "id": "order:promoted_seed_handoff_assurance_smoke_before_coverage",
  "category": "required_order",
  "target": "promoted_seed_handoff_assurance_smoke_before_coverage",
  "expected": "before",
  "actual": "before",
  "status": "pass"
}
```

## 测试覆盖

本版验证包括：

- `tests.test_ci_workflow`
- governance chain 相关测试
- full unittest
- source encoding hygiene
- coverage gate
- CI workflow hygiene command

这些测试保护的是 workflow policy，不是模型质量。

## 运行证据

运行截图和解释归档在 `c/294`。

关键截图：

- `01-ci-workflow-tests.png`
- `02-ci-workflow-hygiene.png`
- `03-ci-workflow-hygiene-json.png`
- `04-governance-chain-tests.png`
- `05-full-unittest.png`
- `06-source-encoding.png`
- `07-coverage-gate.png`
- `08-docs-check.png`

## 一句话总结

v294 把 promoted seed handoff assurance smoke 从“已经接入 CI”推进为“受 CI workflow hygiene 规则保护，不能缺失也不能移到 coverage 后”。
