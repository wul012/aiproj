# v217 promoted seed handoff clean evidence gate diagnostics 代码讲解

## 本版目标

v217 的目标是给 v216 的 `--require-clean-evidence` 补充结构化诊断输出。

v216 已经能让 CLI 在显式要求 clean evidence 时返回 pass/fail。v217 继续补齐“为什么 pass/fail”，让自动化日志不用打开 JSON 或解析完整 summary。

## 不做什么

本版不改变默认 seed handoff 行为，不改变 `--execute`，不改变 `_handoff_allowed()`，不改变 v216 的退出码策略。

它只增加诊断输出，不新增报告层，也不改变 clean-evidence readiness 的计算。

## 前置路线

本版承接：

```text
v214 clean-evidence readiness
v215 status-domain contract
v216 opt-in CLI gate
v217 structured gate diagnostics
```

它属于自动化可诊断性增强。

## `scripts/execute_promoted_training_scale_seed.py`

在 `args.require_clean_evidence` 分支中，v217 新增三行输出：

```python
print(f"clean_evidence_required_status={summary.get('seed_handoff_clean_evidence_status')}")
print(f"clean_evidence_required_ready={clean_evidence_ready}")
print(f"clean_evidence_required_detail={summary.get('seed_handoff_clean_evidence_detail')}")
```

然后继续输出 v216 已有的：

```python
print(f"clean_evidence_required={'pass' if clean_evidence_ready else 'fail'}")
```

这意味着：

- 成功场景可以看到 `status=ready`、`ready=True` 和一致性 detail。
- 失败场景可以看到 `status=pending-plan`、`ready=False` 和需要先 execute 的 detail。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 扩展两条 v216 测试：

1. `test_script_can_require_clean_evidence_after_consistent_execute`

   断言 stdout 包含：

   ```text
   clean_evidence_required_status=ready
   clean_evidence_required_ready=True
   clean_evidence_required_detail=completed handoff has consistent suite alignment
   clean_evidence_required=pass
   ```

2. `test_script_rejects_pending_clean_evidence_when_required`

   断言 stdout 包含：

   ```text
   clean_evidence_required_status=pending-plan
   clean_evidence_required_ready=False
   clean_evidence_required_detail=execute the seed handoff before treating clean comparison evidence as ready
   clean_evidence_required=fail
   ```

这些断言保护的是“gate 判定不变，但诊断信息必须稳定输出”。

## 运行证据

本版运行证据归档在 `c/217`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-gate-diagnostics-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-gate-diagnostics-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、CLI pass/fail 诊断可见、artifacts 仍先写出、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v217 让 clean-evidence gate 更适合进入 CI 或批处理日志。后续如果某次 promoted seed handoff 被拒绝，日志能直接显示是 `pending-plan`、`mismatch`、`missing` 还是其他 review 状态。

## 一句话总结

v217 把 clean-evidence CLI gate 从“只给结果”推进到“结果和原因一起给出”，降低自动化排查成本。
