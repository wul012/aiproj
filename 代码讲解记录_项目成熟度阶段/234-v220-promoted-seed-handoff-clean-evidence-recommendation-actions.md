# v220 promoted seed handoff clean evidence recommendation actions 代码讲解

## 本版目标

v220 的目标是把 clean-evidence requirement 的 pass/fail 结果补进 seed handoff recommendations。

v219 已经完成库级契约：

```text
clean_evidence_requirement.status = not-required / pass / fail
```

但调用方如果只看 recommendations，还需要自己再读 requirement 字段才能知道下一步动作。v220 解决这个小断点：当调用方显式要求 clean evidence 时，report 的 recommendations 会直接出现通过或失败提示。

## 不做什么

本版不改变默认行为。

`require_clean_evidence=False` 时，不新增 clean-evidence recommendation，避免普通 handoff 报告变吵。

本版不改变 CLI 退出码，不改变 artifact schema 的既有字段，不重新设计 suite alignment 或 clean-evidence readiness。

## 前置路线

本版承接：

```text
v214 clean-evidence readiness
v215 readiness status-domain contract
v216 opt-in CLI gate
v217 structured gate diagnostics
v218 persisted gate artifacts
v219 library-level requirement contract
v220 recommendation actions
```

这条路线把 clean-evidence 从字段、gate、artifact、库契约继续推进到人可读动作提示。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

### `_recommendations()`

本版让 `_recommendations()` 接收：

```python
clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None = None
```

然后在原有 suite alignment recommendations 后追加 requirement recommendations：

```python
alignment_recommendations + clean_evidence_recommendations + [...]
```

这样顺序保持稳定：

1. 先说明 suite alignment 状态。
2. 再说明 clean-evidence requirement 是否通过。
3. 最后给出原来的 seed handoff 执行动作。

### `_clean_evidence_requirement_recommendations()`

新增 helper：

```python
def _clean_evidence_requirement_recommendations(
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None,
) -> list[str]:
```

核心规则：

```text
required=False -> []
status=pass -> Clean-evidence requirement passed...
status=fail -> Clean-evidence requirement failed... + detail
other -> Review clean-evidence requirement status...
```

其中失败分支会带上 readiness detail，例如：

```text
execute the seed handoff before treating clean comparison evidence as ready
```

这让 pending-plan 场景不只是 fail，还能告诉调用方应该先执行 seed handoff。

## `tests/test_promoted_training_scale_seed_handoff.py`

测试扩展了三处：

1. builder 级别：`require_clean_evidence=True` 的 planned report 包含 failed recommendation，execute report 包含 passed recommendation。
2. CLI pass 场景：`--execute --require-clean-evidence` 写出的 JSON artifact 里包含 passed recommendation。
3. CLI fail 场景：只传 `--require-clean-evidence` 而不 execute 时，JSON artifact 里包含 failed recommendation，并带有 `execute the seed handoff` detail。

这些断言保护的是“recommendation 和 requirement status 一致”。

## 输入输出

输入不变，仍然是 promoted seed handoff summary 和 requirement object。

输出变化只在：

```text
report["recommendations"]
```

因此 JSON、Markdown、HTML 会自然带上新增 action，因为 artifact writer 已经渲染 recommendations。

## 运行证据

本版运行证据归档在 `c/220`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-seed-handoff-recommendation-smoke.png`
- `图片/03-promoted-seed-handoff-cli-recommendation-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、库级 recommendations 正确、CLI artifact recommendations 正确、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v220 让 clean-evidence gate 的读法更直接。

过去下游需要读取：

```text
clean_evidence_requirement.status
clean_evidence_requirement.detail
```

现在下游也可以直接读取：

```text
recommendations[]
```

这对 CI summary、registry 展示、人工复盘都更友好。

## 一句话总结

v220 把 clean-evidence requirement 的 pass/fail 结果转成 recommendation action，让 seed handoff artifact 同时具备机器状态和人可读下一步。
