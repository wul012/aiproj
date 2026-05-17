# v213 promoted seed handoff alignment recommendations 代码讲解

## 本版目标

v213 的目标是把 v212 的 promoted seed handoff suite alignment verdict，继续落成具体的 review recommendations。

v212 已经能判断：

```text
pending-plan
consistent
mismatch
missing
```

但 verdict 只回答“现在是什么状态”，还没有直接告诉审阅者下一步该怎么处理。v213 补上这一步，让 seed handoff 的 recommendation 区域消费 alignment verdict。

## 不做什么

本版不改变 `_handoff_allowed()`，不改变 planned-mode review，不改变 `--execute` 命令运行，不把 `mismatch` 或 `missing` 变成 blocker。

recommendations 是审阅指导，不是执行策略。这样可以提升报告可读性，同时保留 v212 的边界：alignment verdict 仍然只是证据链判断。

## 前置路线

v211 把 handoff suite guard 接到 seed handoff。

v212 把 selected handoff、seed 和 plan suite path 变成 alignment verdict。

v213 再推进一小步：

```text
alignment verdict -> review recommendation
```

这不是新的模型能力，也不是新的训练流程，而是让审阅入口更好用。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

### `_recommendations()`

`_recommendations()` 现在先调用：

```python
alignment_recommendations = _suite_alignment_recommendations(summary)
```

然后把 alignment recommendation 放在原有 handoff recommendation 前面。

这样 planned、blocked、timeout、failed、completed 都会先说明 suite alignment 风险，再说明对应执行状态下的下一步动作。

### `_suite_alignment_recommendations()`

新增 helper 按状态生成审阅语：

- `pending-plan`：提醒先执行 seed handoff，再确认 plan suite。
- `consistent`：说明 selected handoff、seed、plan 三者一致。
- `mismatch`：提示先复核 suite mismatch，再把该 handoff 当作 clean model-quality evidence。
- `missing`：提示补齐 suite alignment evidence，再把它当作 clean comparison。
- 其他状态：回退为通用 suite alignment review。

这个 helper 只读 summary 字段，不读取文件、不启动进程、不影响 artifact rows。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 增加和强化断言：

1. `consistent` 状态时，第一条 recommendation 说明 suite alignment consistent。
2. `mismatch` 状态时，第一条 recommendation 要求 review mismatch，第二条仍保留 planned-mode 的原有“review command then execute”建议。
3. `missing` 状态时，execute 仍可完成，但第一条 recommendation 要求补齐 suite alignment evidence，第二条仍保留 completed handoff 的原有“use generated plan report”建议。

这些断言保护的是“建议更聪明，但执行语义不变”。

## Artifact 影响

本版没有新增 artifact 字段。原因是 JSON 已经包含 `recommendations`，Markdown/HTML 已经渲染 Recommendations 区块。

所以 v213 只要改变 recommendation 内容，JSON/Markdown/HTML 就自然携带 alignment-aware review actions。

## 运行证据

本版运行证据归档在 `c/213`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-recommendation-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-recommendation-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些证据分别证明：聚焦测试通过、smoke 能展示四类 recommendation、artifact 输出保留 review actions、source encoding 仍干净、全量 unittest 通过、README 和归档说明已经对齐。

## 证据链角色

v213 处在 promoted seed handoff 的审阅层。它让 v212 的 verdict 不停留在状态字段，而是进入 recommendation 区域，帮助后续人员判断是否该执行下一轮 plan、复核 mismatch，或补齐缺失证据。

## 一句话总结

v213 把 promoted seed handoff 的 alignment verdict 转成 review recommendations，让下一轮训练规划入口不只显示 suite 状态，也说明对应处理动作。
