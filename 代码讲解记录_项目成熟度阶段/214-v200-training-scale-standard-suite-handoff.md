# v200 training scale standard suite handoff 代码讲解

## 本版目标

v200 的目标是把 v199 已经接入 training portfolio / batch 的标准中文 benchmark suite 继续向上接到 training scale 工作流。

v198 提供了 `standard-zh` 内置评测集，v199 让单条 portfolio 和 batch variants 能使用 `--suite-name standard-zh`。但 scale 规划链路仍然只负责生成 variants 和 batch handoff，没有记录或传递评测集选择。这样后续从 `plan_training_scale.py` 或 `run_training_scale_workflow.py` 起步时，仍可能掉回默认 `data/eval_prompts.json`。

本版解决这个断点：scale plan、gated scale run、consolidated workflow 都能接收并展示 `suite_name="standard-zh"`，并把它传给下游 portfolio batch。

## 不做什么

本版不训练新模型，不修改标准中文评测集内容，不改变 gate policy，不改变 portfolio batch 的执行语义，也不证明模型在标准 suite 上变好。

它只负责把“训练规模链路选择哪个评测集”变成可记录、可传递、可审计的计划证据。

## 关键文件

### `src/minigpt/training_scale_plan.py`

`build_training_scale_plan()` 新增：

```python
suite_path: str | Path | None = None
suite_name: str | None = None
```

内部新增两个 helper：

```python
def _suite_ref(root: Path, *, suite_path: str | Path | None, suite_name: str | None) -> dict[str, Any]:
    ...


def _suite_args(root: Path, suite_ref: dict[str, Any]) -> list[str]:
    ...
```

`_suite_ref()` 把用户输入规范化为计划证据：

- 文件模式：`{"mode": "file", "name": None, "path": ".../data/eval_prompts.json"}`
- 内置模式：`{"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"}`

它会拒绝同时传入 `suite_path` 和 `suite_name`，避免计划 JSON 出现“既像文件、又像内置 suite”的歧义。

`_suite_args()` 把计划证据转成下游 batch 命令参数：

- `mode == "builtin"` 时生成 `["--suite-name", "standard-zh"]`
- 显式文件 suite 时生成 `["--suite", path]`
- 默认 `data/eval_prompts.json` 时保持旧命令不额外增加参数

这个默认保持旧命令的处理是刻意的：v200 只在用户明确选择 suite 时改变 handoff command，降低对旧脚本和旧测试的扰动。

计划报告新增：

```python
"suite": suite_ref,
"suite_path": suite_ref["path"],
```

`batch.command` 在内置 suite 场景中会包含：

```text
--suite-name standard-zh
```

### `src/minigpt/training_scale_run.py`

`run_training_scale_plan()` 是 scale plan 进入 portfolio batch 的实际执行入口。本版读取 plan 中的 `suite` 对象，并按模式传给 `build_training_portfolio_batch_plan()`：

```python
suite = _dict(scale_plan.get("suite"))
suite_path=None if suite.get("mode") == "builtin" else suite.get("path")
suite_name=suite.get("name") if suite.get("mode") == "builtin" else None
```

这里不能把 `suite_path="builtin:standard-zh"` 和 `suite_name="standard-zh"` 同时传下去，因为 portfolio 计划会把这视为互斥冲突。v200 明确把兼容展示字段和真正执行参数分开：

- JSON 证据里保留 `suite_path="builtin:standard-zh"`
- 下游执行参数只传 `suite_name="standard-zh"`

`_scale_plan_summary()` 新增：

```python
"suite_mode": ...,
"suite_name": ...,
"suite_path": ...,
```

`_batch_summary()` 读取 batch 第一个 variant 的 portfolio plan，确认最终 portfolio batch 也确实继承了同一个 suite。

### `src/minigpt/training_scale_workflow.py`

`run_training_scale_workflow()` 新增 `suite_path` / `suite_name` 参数，并传给 `build_training_scale_plan()`。

workflow 的 `plan_summary` 和 `summary` 都新增 suite 字段。这样总览 JSON、Markdown、HTML 不需要再打开嵌套 plan 才知道本次 workflow 用的是哪个评测集。

### `src/minigpt/training_scale_plan_artifacts.py`

计划 Markdown 和 HTML 现在会展示 suite path：

- Markdown 顶部加入 `Suite`
- HTML stats 加入 `Suite`
- Batch Handoff 面板显示 `Suite`

这些输出是人读证据，不是下游执行源。真正的机器消费字段仍然是 JSON 里的 `suite` 和 `batch.command`。

### `src/minigpt/training_scale_workflow_artifacts.py`

workflow Markdown 和 HTML 的 summary 区域加入 suite path。它让审阅者能在总报告第一屏看到本次 scale workflow 是否使用标准中文 benchmark suite。

### `scripts/plan_training_scale.py`

新增 CLI：

```text
--suite <path>
--suite-name {default,standard-zh}
```

`--suite-name standard-zh` 会生成带内置 suite 的 scale plan 和 batch handoff command。

### `scripts/run_training_scale_workflow.py`

同样新增：

```text
--suite <path>
--suite-name {default,standard-zh}
```

用户可以从 consolidated workflow 入口直接选择标准中文 suite，不必先手动生成 plan 再修改 batch 命令。

## 运行流程

从 scale plan 起步：

1. 用户运行 `scripts/plan_training_scale.py data --suite-name standard-zh`。
2. `build_training_scale_plan()` 写入 `suite={"mode":"builtin","name":"standard-zh","path":"builtin:standard-zh"}`。
3. `batch.command` 生成 `run_training_portfolio_batch.py ... --suite-name standard-zh`。
4. 后续 `run_training_scale_plan.py` 读取 plan JSON，按 builtin 模式把 `suite_name` 传给 portfolio batch。
5. batch 内部 variants 的 portfolio plan 继续把 `--suite-name standard-zh` 传给 eval-suite 和 pair-batch。

从 consolidated workflow 起步：

1. 用户运行 `scripts/run_training_scale_workflow.py data --suite-name standard-zh`。
2. workflow 先生成带 suite 的 plan。
3. review / standard profiles 分别进入 gated run。
4. 被 gate 允许的 profile 会把 suite 传给 portfolio batch dry-run。
5. workflow summary 显示 `suite_path=builtin:standard-zh`，decision 仍只负责选择可执行 profile，不改变 suite。

## 测试覆盖

### `tests/test_training_scale_plan.py`

新增：

- `test_build_training_scale_plan_accepts_builtin_standard_suite()`
  - 断言 plan 的 `suite` 对象是 builtin 模式。
  - 断言 `suite_path == "builtin:standard-zh"`。
  - 断言 batch command 包含 `--suite-name standard-zh`。
  - 断言 command 没有回退成 `--suite <path>`。
- `test_build_training_scale_plan_rejects_suite_name_and_path_together()`
  - 保护互斥规则。

### `tests/test_training_scale_run.py`

新增 `test_review_gate_can_handoff_builtin_standard_suite()`：

- 先生成带 `suite_name="standard-zh"` 的 scale plan。
- 再跑 review gate dry-run。
- 断言 run summary 仍记录 `suite_path=builtin:standard-zh`。
- 断言 batch summary 也继承了同一个 suite。

这个测试保护的是最关键的一跳：plan JSON 进入 gated batch 时不能丢失 suite。

### `tests/test_training_scale_workflow.py`

新增 `test_workflow_can_use_builtin_standard_suite()`：

- 从 consolidated workflow 入口传 `suite_name="standard-zh"`。
- 断言 `plan_summary` 和 `summary` 都带 builtin suite。
- 读取嵌套 `training_scale_plan.json`，断言 batch command 真正包含 `--suite-name` 和 `standard-zh`。

## 证据边界

v200 的 JSON/Markdown/HTML 产物证明的是：训练规模链路已经能保存并传递标准中文 suite 选择。

它不证明：

- 模型在标准中文 suite 上分数提升。
- 更大 corpus 训练已经执行。
- gate profile 本身更严格或更宽松。
- promotion decision 会自动因为使用标准 suite 而通过。

后续如果继续能力侧推进，应该从 `run_training_scale_workflow.py --suite-name standard-zh --execute` 或受控 handoff 开始，收集真实 checkpoint 的 eval-suite、generation quality、benchmark scorecard、pair-batch 和 promotion evidence。

## 验证

本版验证包括：

- focused tests：`tests.test_training_scale_plan`、`tests.test_training_scale_run`、`tests.test_training_scale_workflow`。
- syntax：training-scale plan/run/workflow、两个 CLI 和对应测试文件编译通过。
- plan smoke：`plan_training_scale.py data --suite-name standard-zh` 生成带 suite handoff 的计划。
- workflow smoke：`run_training_scale_workflow.py data --suite-name standard-zh` 生成 review/standard profile 总览。
- source encoding：`scripts/check_source_encoding.py` 通过。
- full unittest：全量 `python -B -m unittest discover -s tests` 通过。

截图证据放在 `c/200/图片`，说明文件放在 `c/200/解释/说明.md`。

一句话总结：v200 把标准中文 benchmark suite 从 portfolio 层继续接到 training scale plan / gated run / workflow，让下一阶段训练规模实验可以从入口开始就固定同一套评测输入。
