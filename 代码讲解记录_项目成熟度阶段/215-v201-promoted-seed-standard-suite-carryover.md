# v201 promoted seed standard suite carryover 代码讲解

## 本版目标

v201 的目标是把 v200 已经进入 training scale workflow 的标准中文 benchmark suite 继续带到 promoted seed 和 seed handoff。

v198 新增 `standard-zh` 内置评测集，v199 把它接到 training portfolio / batch，v200 把它接到 scale plan、gated run 和 consolidated workflow。剩下的断点在 promoted baseline 之后：当项目从一个已 promoted 的 scale run 生成下一轮 seed 时，旧逻辑只生成 `plan_training_scale.py` 命令，不读取已选基线的 suite 信息，下一轮可能静默回到默认 `data/eval_prompts.json`。

本版解决这个断点：promoted seed 从 selected training scale run 继承 `suite_path=builtin:standard-zh`，生成的下一轮 plan 命令保留 `--suite-name standard-zh`，seed handoff 执行后也会确认生成的 plan report 仍然使用同一套 suite。

## 不做什么

本版不新增评测题，不训练模型，不改变 promotion 选择策略，不改变 benchmark 分数计算，也不把 `standard-zh` 设为全局默认。

它只让“已选 promoted baseline 用过什么评测集”成为下一轮 seed 的显式输入，避免跨轮比较时评测基准悄悄变化。

## 关键文件

### `src/minigpt/promoted_training_scale_seed.py`

`build_promoted_training_scale_seed()` 新增：

```python
suite_path: str | Path | None = None
suite_name: str | None = None
```

这两个参数是人工覆盖入口。没有覆盖时，seed 会读取 selected training scale run 的：

```text
scale_plan_summary.suite_mode
scale_plan_summary.suite_name
scale_plan_summary.suite_path
```

必要时也会从 `batch_summary` 读取同名字段作为兼容来源。

新增 helper：

```python
_suite_ref_from_selected_run()
_next_suite_ref()
_suite_args()
```

`_suite_ref_from_selected_run()` 把 selected run 的 suite 字段整理成 seed 里的 baseline evidence：

```json
{
  "mode": "builtin",
  "name": "standard-zh",
  "path": "builtin:standard-zh",
  "source": "selected_run"
}
```

`_next_suite_ref()` 决定下一轮 plan 使用哪套 suite：

- CLI 传 `--suite-name standard-zh`：使用人工覆盖的 builtin suite。
- CLI 传 `--suite <path>`：使用人工覆盖的文件 suite。
- CLI 传 `--suite-name default`：回到默认 `data/eval_prompts.json`。
- 没有 CLI 覆盖但 selected run 有 suite：继承 selected run 的 suite。
- selected run 也没有 suite：使用默认 `data/eval_prompts.json`。

`_suite_args()` 把这个结构转换成命令行：

```text
--suite-name standard-zh
```

或：

```text
--suite path/to/prompts.json
```

默认文件 suite 不额外追加参数，保持旧命令兼容。

## Seed 报告字段

`baseline_seed` 新增：

```json
"suite": {
  "mode": "builtin",
  "name": "standard-zh",
  "path": "builtin:standard-zh",
  "source": "selected_run"
},
"suite_path": "builtin:standard-zh"
```

它表示被选中的 promoted baseline 原本来自哪套评测集。

`next_plan` 新增：

```json
"suite": {
  "mode": "builtin",
  "name": "standard-zh",
  "path": "builtin:standard-zh",
  "source": "inherited"
},
"suite_path": "builtin:standard-zh",
"suite_source": "inherited"
```

它表示下一轮计划命令实际会使用哪套评测集。

`summary` 新增：

```json
"baseline_suite_path": "builtin:standard-zh",
"next_suite_path": "builtin:standard-zh",
"next_suite_source": "inherited"
```

这些字段是给 CSV、Markdown、HTML 和人工审阅使用的快速证据，不替代完整 JSON。

## `src/minigpt/promoted_training_scale_seed_artifacts.py`

promoted seed 的 CSV、Markdown 和 HTML 现在都会显示：

```text
baseline_suite_path
next_suite_path
next_suite_source
```

HTML 的 baseline table 也显示 selected run 的 source suite mode/name/path。这样审阅者不用打开嵌套 JSON，就能看到“上一轮基线”和“下一轮命令”是否使用同一套 benchmark suite。

这些 artifact 是只读证据，不是执行器。真正执行来源仍是 seed JSON 里的 `next_plan.command`。

## `src/minigpt/promoted_training_scale_seed_handoff.py`

seed handoff 在执行或验证 seed 命令后，会读取生成的：

```text
training_scale_plan.json
```

并把 seed 中的 suite 与 plan report 中的 suite 放到同一个 summary：

```json
"seed_suite_path": "builtin:standard-zh",
"seed_suite_source": "inherited",
"plan_suite_mode": "builtin",
"plan_suite_name": "standard-zh",
"plan_suite_path": "builtin:standard-zh"
```

这里的含义是：

- `seed_suite_path`：seed 打算让下一轮用什么 suite。
- `plan_suite_path`：实际生成的 training scale plan 使用了什么 suite。

两者一致，才说明 seed handoff 没有在执行时丢失 suite。

## `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

handoff 的 CSV、Markdown 和 HTML 加入 seed suite 与 plan suite 字段。HTML 的 Plan Report 区域也显示：

```text
Suite mode
Suite name
Suite path
```

这样 handoff 报告可以作为下一轮训练规模计划的入口证据。

## CLI 入口

### `scripts/build_promoted_training_scale_seed.py`

新增：

```text
--suite <path>
--suite-name {default,standard-zh}
```

默认行为是继承 selected run 的 suite。显式 `--suite-name default` 表示人工选择回到默认文件 suite。

脚本输出也新增：

```text
baseline_suite_path=...
next_suite_path=...
next_suite_source=...
```

### `scripts/execute_promoted_training_scale_seed.py`

执行 seed 后新增打印：

```text
seed_suite_path=...
plan_suite_path=...
```

它们用于快速确认生成的 plan 是否保留了 seed 里的 suite。

## 默认 suite 语义修正

`training_scale_plan.py` 和 `training_portfolio.py` 都把：

```python
suite_name="default"
```

解释为默认文件 suite，而不是：

```text
builtin:default
```

这是一个小的契约硬化。`default` 是 CLI 选择项，代表“回到默认 suite”，不应该被写成不存在的 builtin suite 名称。

## 测试覆盖

### `tests/test_promoted_training_scale_seed.py`

新增：

- selected run 使用 `suite_path=builtin:standard-zh` 时，seed 会继承它。
- `next_plan.command` 包含 `--suite-name standard-zh`。
- `--suite-name default` 不会产生 `builtin:default`。

### `tests/test_promoted_training_scale_seed_handoff.py`

新增真实执行覆盖：

1. 构造带 `standard-zh` 的 seed。
2. `execute=True` 执行 seed 里的 `plan_training_scale.py` 命令。
3. 读取生成的 `training_scale_plan.json`。
4. 断言 plan 仍然是：

```json
{"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"}
```

同时断言下一条 batch command 也包含 `--suite-name standard-zh`。

### `tests/test_training_scale_plan.py`

新增默认 suite-name 行为测试，保护 `suite_name="default"` 不会被写成 `builtin:default`。

### `tests/test_training_portfolio.py`

新增同样的 default suite 测试，确保 portfolio API 和 scale API 的语义一致。

## 运行证据

v201 的运行截图和解释放在：

```text
c/201/图片
c/201/解释/说明.md
```

截图覆盖：

- focused promoted seed/handoff、portfolio、batch、training-scale 测试。
- promoted seed build smoke。
- promoted seed handoff execute smoke。
- source encoding hygiene。
- full unittest discovery。
- README、代码讲解、AGENTS 规则和关键词检查。

## 边界说明

本版证明的是 suite 选择在 seed 和 seed handoff 中没有丢失，不证明 `standard-zh` 上的模型质量提升。真正的模型能力判断仍需要后续真实 checkpoint、固定 suite、多轮 scorecard 和 promoted comparison。

一句话总结：v201 把标准中文评测集选择从 training scale workflow 延伸到 promoted baseline 的下一轮 seed，让跨轮训练规模实验能继续使用同一个 benchmark 基准。
