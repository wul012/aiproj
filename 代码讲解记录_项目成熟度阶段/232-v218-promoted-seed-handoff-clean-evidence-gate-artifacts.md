# v218 promoted seed handoff clean evidence gate artifacts 代码讲解

## 本版目标

v218 的目标是把 clean-evidence CLI gate 的结果持久化到 seed handoff artifact。

v216 让 CLI 可以显式要求 clean evidence，v217 让 stdout 输出结构化诊断。v218 继续补齐证据闭环：即使终端日志丢失，JSON/CSV/Markdown/HTML 也能保存本次 gate 的 `not-required` / `pass` / `fail` 决策。

## 不做什么

本版不改变默认 seed handoff 行为，不改变 `--execute`，不改变 `--require-clean-evidence` 的退出码策略，不新增新的独立报告。

它只是把已有 CLI gate 决策写入现有 seed handoff outputs。

## 前置路线

本版承接：

```text
v214 clean-evidence readiness
v215 status-domain contract
v216 opt-in CLI gate
v217 structured gate diagnostics
v218 persisted gate artifacts
```

这是从“可读字段”到“可执行 gate”再到“可审计 artifact”的闭环。

## `scripts/execute_promoted_training_scale_seed.py`

### `_clean_evidence_requirement()`

新增 helper：

```python
def _clean_evidence_requirement(summary: dict[str, object], *, required: bool) -> dict[str, object]:
    ready = bool(summary.get("seed_handoff_clean_evidence_ready"))
    status = "pass" if required and ready else "fail" if required else "not-required"
    return {
        "required": bool(required),
        "status": status,
        "ready": ready,
        "readiness_status": summary.get("seed_handoff_clean_evidence_status"),
        "detail": summary.get("seed_handoff_clean_evidence_detail"),
    }
```

这段逻辑只消费已有 summary，不重新计算 suite alignment。

### 写出顺序

CLI 现在先构建 report，再计算：

```python
clean_evidence_requirement = _clean_evidence_requirement(summary, required=args.require_clean_evidence)
report["clean_evidence_requirement"] = clean_evidence_requirement
```

然后再调用 `write_promoted_training_scale_seed_handoff_outputs()`。

这保证了即使 `--require-clean-evidence` 最终失败，artifact 也已经带有 failure reason。

## `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增字段：

```text
clean_evidence_requirement_required
clean_evidence_requirement_status
clean_evidence_requirement_ready
clean_evidence_requirement_readiness_status
```

Markdown 新增：

```text
Clean evidence requirement
Clean evidence requirement detail
```

HTML stats 新增：

```text
Clean evidence gate
```

这些输出都是最终 handoff artifact 的一部分。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 扩展三类场景：

1. 默认不传 `--require-clean-evidence` 时，JSON 中 `clean_evidence_requirement.status` 为 `not-required`。
2. execute 后 suite alignment consistent 时，requirement 为 `pass`，`required=True`，`ready=True`。
3. pending-plan 场景显式要求 clean evidence 时，requirement 为 `fail`，`required=True`，`ready=False`，并且 CSV/Markdown/HTML 都包含 gate artifact 字段。

这些断言保护的是“gate 失败也留下可审计 evidence”。

## 运行证据

本版运行证据归档在 `c/218`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-gate-artifact-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-gate-artifact-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、CLI smoke 覆盖 not-required/pass/fail、artifacts 都持久化 gate 结果、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v218 让 seed handoff 的 clean-evidence gate 可以被后续 registry、maturity summary 或 CI job 直接读取 artifact，而不是依赖终端 stdout。

## 一句话总结

v218 把 clean-evidence CLI gate 的结果从临时 stdout 推进到最终 artifacts，让 gate 决策具备可追溯证据。
