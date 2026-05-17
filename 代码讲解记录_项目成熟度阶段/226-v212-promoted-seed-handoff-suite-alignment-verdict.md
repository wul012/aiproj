# v212 promoted seed handoff suite alignment verdict 代码讲解

## 本版目标

v212 的目标是把 promoted seed handoff 里已经存在的 suite guard 证据，整理成一个更直接的审阅结论。

v211 已经让 seed handoff 能看到 seed 继承来的 `selected_handoff_selected_suite_path`、`selected_handoff_suite_consistency` 和 `handoff_suite_mismatch_total`。但这些字段仍然偏“原始证据”，审阅者需要自己比较它们和 `seed_suite_path`、`plan_suite_path` 是否一致。

本版新增 `seed_handoff_suite_alignment_status`，让 seed handoff 直接回答：

```text
selected handoff suite path
seed suite path
generated plan suite path
```

这三者在当前阶段是否对齐。

## 不做什么

本版不重新计算 suite consistency，不改变 `_handoff_allowed()`，不改变 planned-mode review，也不改变 `--execute` 命令运行方式。

`seed_handoff_suite_alignment_status` 是审阅证据，不是 blocker。即使状态是 `mismatch` 或 `missing`，seed handoff 的放行仍然由 seed 状态、source 是否存在、command 是否可用、review flag 和子进程返回码决定。

## 前置路线

v202-v211 已经把 suite guard 一路带到 seed handoff：

```text
comparison -> decision -> workflow -> handoff -> promotion
  -> promotion index -> promoted comparison -> promoted decision
  -> promoted seed -> promoted seed handoff
```

v212 不再往下一层传字段，而是在 seed handoff 入口处增加明确判断，帮助人工审阅更快识别 suite 边界是否还干净。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

### `_summary()`

`_summary()` 现在先提取三条 suite path：

```python
seed_suite_path = _dict(next_plan.get("suite")).get("path")
selected_handoff_suite_path = handoff_guard.get("selected_handoff_selected_suite_path")
plan_suite_path = plan_suite.get("path") or plan_summary.get("suite_path")
```

然后调用 `_suite_alignment()`，把结果写入 summary：

```text
seed_handoff_suite_alignment_status
seed_handoff_suite_alignment_detail
seed_handoff_suite_alignment_mismatch_count
seed_handoff_suite_alignment_missing_count
```

### `_suite_alignment()`

`_suite_alignment()` 的状态语义是：

- `pending-plan`：selected handoff 和 seed suite 已对齐，但 plan 还没生成。
- `consistent`：selected handoff、seed 和 plan 三条路径都一致。
- `mismatch`：至少有两条已知路径不一致。
- `missing`：缺少 selected handoff 或 seed suite path，无法判断。

这里有一个刻意边界：plan path 是可选的，因为 planned-mode 本来就不执行命令，不能要求 plan artifact 已经存在。

## `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 新增：

```text
seed_handoff_suite_alignment_status
seed_handoff_suite_alignment_mismatch_count
seed_handoff_suite_alignment_missing_count
```

Markdown summary 新增：

```text
Seed handoff suite alignment
Seed handoff suite alignment detail
```

HTML stats 新增 `Suite alignment` 卡片，方便打开 HTML 时先看 verdict，再看详细 artifact rows。

## `scripts/execute_promoted_training_scale_seed.py`

CLI stdout 新增：

```text
seed_handoff_suite_alignment_status
seed_handoff_suite_alignment_mismatch_count
```

这样 smoke 或 CI 日志不用解析整段 JSON，也能判断 seed handoff 的 suite alignment 状态。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 增强了 seed handoff 测试：

1. 不带 upstream guard 的旧 seed，执行后仍能完成，但 alignment 是 `missing`。
2. 带 guard 的 planned seed handoff，alignment 是 `pending-plan`。
3. 带 guard 并执行生成 plan 后，alignment 是 `consistent`。
4. selected handoff suite 和 seed suite 不一致时，alignment 是 `mismatch`，但 handoff 仍保持 planned，不被这个审阅 verdict 自动阻断。
5. CSV、Markdown、HTML 和 CLI stdout 都暴露 alignment 字段。

这些断言保护的是“审阅判断增强，但执行语义不变”。

## 运行证据

本版运行证据归档在 `c/212`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-alignment-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-alignment-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些证据分别证明：聚焦测试通过、CLI 能看到 alignment verdict、四类 artifact 都带 alignment 字段、source encoding 仍干净、全量 unittest 通过、README 和归档说明已经对齐。

## 证据链角色

v212 处在 promoted seed handoff 的审阅入口。它不扩展训练能力，也不改变执行控制，而是把 suite guard 证据变成明确 verdict，让后续人员更容易判断这次 next-plan handoff 是否仍沿用同一条 clean-comparison 边界。

## 一句话总结

v212 把 promoted seed handoff 的 suite path 证据升级成 alignment verdict，让下一轮训练规划入口能一眼看出 selected handoff、seed 和 plan suite 是否仍然对齐。
