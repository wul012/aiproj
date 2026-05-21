# v341 CI tiny scorecard plan digest gate

## 本版目标和边界

v340 已经有 `check_ci_tiny_scorecard_plan.py`，但它还只是可手动运行的验收工具。v341 的目标是把这个验收工具接入 GitHub Actions，并让 CI workflow hygiene 明确要求它出现在 tiny scorecard wrapper 之后、coverage 之前。

本版不做的事：

- 不改变 tiny benchmark 的训练预算
- 不改变 scorecard、decision 或模型生成逻辑
- 不新增另一套报告系统
- 不把 tiny smoke 结果解释成真实模型能力提升

## 前置路线

```text
v337 CI tiny scorecard wrapper
  -> v338 wrapper invocation plan
  -> v339 summary/check artifact digests
  -> v340 reusable plan digest checker
  -> v341 CI-enforced plan digest gate
```

## 关键文件

- `.github/workflows/ci.yml`
  - 在 tiny scorecard wrapper 后新增 `CI tiny scorecard plan digest check`
  - 命令读取 `runs/tiny-scorecard-comparison-smoke-ci`
  - 输出写入 `runs/ci-tiny-scorecard-plan-check-ci`
  - 位置在 coverage gate 之前
- `src/minigpt/ci_workflow_hygiene.py`
  - 新增 required command fragment：`ci_tiny_scorecard_plan_digest_check`
  - 新增顺序规则：wrapper 必须早于 plan checker
  - 新增顺序规则：plan checker 必须早于 coverage
  - 更新推荐语，让证据漂移检查和 coverage gate 的关系更清楚
- `tests/test_ci_workflow.py`
  - 更新当前 workflow 的通过断言
  - 更新旧 workflow 缺失步骤计数
  - 增加 plan checker 放在 wrapper 前时失败的测试
  - 调整 coverage 提前场景，只断言与 coverage 相关的顺序规则失败
- `README.md`
  - 更新当前版本、成熟度说明、v341 checkpoint 和 tag 说明
- `d/341/`
  - 保存本版命令输出截图和说明

## 核心规则

v341 后，CI 中 tiny scorecard 证据链的顺序是：

```text
run_ci_tiny_scorecard_comparison_smoke.py
  -> check_ci_tiny_scorecard_plan.py
  -> run_test_coverage.py
```

这意味着 coverage 不再是 tiny scorecard evidence 的第一个强制门。CI 会先确认 wrapper 产出的 plan digest 和 summary/check artifact 仍然一致，再进入覆盖率统计。

## CI hygiene 的输入输出

输入仍然是 workflow YAML：

```text
.github/workflows/ci.yml
```

输出仍然是：

```text
ci_workflow_hygiene.json
ci_workflow_hygiene.csv
ci_workflow_hygiene.md
ci_workflow_hygiene.html
```

变化点在 report 的 policy 和 checks：

```text
required_command_fragments.ci_tiny_scorecard_plan_digest_check
required_command_order.ci_tiny_scorecard_plan_check_after_smoke
required_command_order.ci_tiny_scorecard_plan_check_before_coverage
```

这些字段是机器可读的 CI 合约，不是展示性文案。

## 测试覆盖

本版测试保护四类风险：

1. 当前真实 workflow 仍然通过 hygiene。
2. 没有 plan checker 的旧式 workflow 会出现 missing command。
3. coverage 放在证据检查之前会触发顺序失败。
4. plan checker 放在 tiny wrapper 之前会触发 `ci_tiny_scorecard_plan_check_after_smoke` 失败。

同时继续跑 plan checker 和 wrapper 相关测试，确认 v341 没有破坏 v337-v340 的链路。

## 链路角色

v341 把 v340 的“可验收工具”升级为“CI 必跑质量门”：

```text
工具存在
  -> 工具能验收真实 plan
  -> workflow 必须运行这个工具
  -> hygiene 必须检查工具位置
```

这个版本解决的是 CI 合约完整性，不是模型质量本身。tiny run 仍然只代表训练、评估、scorecard、decision 和 artifact digest 链路可以在 CPU 小预算下闭环。

## 一句话总结

v341 把 CI tiny scorecard plan digest 验收从旁路工具推进为 GitHub Actions 的正式质量门，让 tiny benchmark 证据链在 coverage 前完成独立校验。
