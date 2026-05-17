# v214 promoted seed handoff clean evidence readiness 代码讲解

## 本版目标

v214 的目标是把 promoted seed handoff 的 suite alignment verdict，继续落成可机器消费的 clean-evidence readiness。

v212 给出了 verdict：

```text
pending-plan
consistent
mismatch
missing
```

v213 把 verdict 转成 review recommendations。v214 再补一层稳定字段，让下游工具不用解析自然语言建议，也能知道这份 seed handoff 是否适合作为 clean comparison evidence。

## 不做什么

本版不改变 `_handoff_allowed()`，不改变 planned mode，不改变 `--execute`，不把 suite mismatch 或 missing evidence 变成 blocker。

readiness 只回答“是否适合作为干净比较证据”，不回答“命令能不能运行”。

## 前置路线

这版承接的是 promoted training-scale 证据链：

```text
promotion acceptance
-> promotion index
-> promoted comparison
-> promoted baseline decision
-> promoted seed
-> promoted seed handoff
```

v211 把上游 handoff suite guard 接到 seed handoff。v212 生成 alignment verdict。v213 生成 review recommendations。v214 把同一个 verdict 转成 summary/artifact/CLI 都能读取的 readiness 字段。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

### `_summary()`

`_summary()` 现在在生成 suite alignment 后调用：

```python
clean_evidence_readiness = _clean_evidence_readiness(execution.get("status"), suite_alignment)
```

然后把结果写入 summary：

```text
seed_handoff_clean_evidence_ready
seed_handoff_clean_evidence_status
seed_handoff_clean_evidence_detail
```

这样 JSON summary、CSV 行、Markdown、HTML 和 CLI 都可以消费同一组字段。

### `_clean_evidence_readiness()`

这个 helper 按 handoff execution status 和 suite alignment status 映射 readiness：

- alignment 为 `consistent` 且 handoff 为 `completed`：`ready=true`，状态为 `ready`。
- alignment 为 `pending-plan`：状态为 `pending-plan`，提醒先执行 seed handoff。
- alignment 为 `mismatch`：状态为 `review`，要求复核 suite mismatch。
- alignment 为 `missing`：状态为 `incomplete`，说明 suite alignment evidence 不完整。
- 其他状态：回退到 `review`。

它不读取文件、不启动训练、不修改执行状态，只做 summary 派生。

## `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增：

```text
seed_handoff_clean_evidence_ready
seed_handoff_clean_evidence_status
```

Markdown 新增 clean-evidence readiness 的 status、ready 和 detail。

HTML stats 新增 `Clean evidence` 卡片，方便人工打开页面时直接看到这份 handoff 是否可作为 clean comparison evidence。

这些输出都是最终证据，不是临时 fixture；后续工具可以从 JSON 或 CSV 中读取稳定字段。

## `scripts/execute_promoted_training_scale_seed.py`

CLI 新增两行 stdout：

```text
seed_handoff_clean_evidence_status=...
seed_handoff_clean_evidence_ready=...
```

这样 smoke、CI 或人工终端不用打开 JSON，也能快速判断 readiness。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 覆盖四类关键状态：

1. planned handoff 且 plan 未生成：alignment 为 `pending-plan`，readiness 为 `pending-plan`，ready 为 `False`。
2. execute 后 selected handoff、seed、plan suite 一致：readiness 为 `ready`，ready 为 `True`。
3. selected handoff 和 seed suite 不一致：readiness 为 `review`，ready 为 `False`，但 planned handoff 仍不被阻断。
4. 缺少 selected handoff suite evidence：readiness 为 `incomplete`，ready 为 `False`，但 execute 仍可完成。

这些断言保护的是“机器字段更清楚，但执行语义不变”。

## 运行证据

本版运行证据归档在 `c/214`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-clean-evidence-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-clean-evidence-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、四类 readiness smoke 可见、JSON/CSV/Markdown/HTML 都导出字段、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v214 让 promoted seed handoff 的 clean evidence 判断从“读推荐语”升级为“读稳定字段”。它适合后续被 promotion review、registry 或 maturity summary 继续消费，但本身仍保持非阻断边界。

## 一句话总结

v214 把 promoted seed handoff 的 suite alignment 证据转成 clean-evidence readiness 字段，让下一轮训练规划入口既可人工审阅，也可被脚本稳定消费。
