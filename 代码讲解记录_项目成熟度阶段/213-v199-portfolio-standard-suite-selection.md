# v199 portfolio standard suite selection 代码讲解

## 本版目标

v199 的目标是把 v198 的标准中文 benchmark suite 接入训练 portfolio 和 batch 工作流。

v198 已经提供了 `standard_zh_prompt_suite()`、`builtin:standard-zh`、`data/standard_zh_eval_prompts.json`，并让 `scripts/eval_suite.py`、`scripts/pair_batch.py` 支持 `--suite-name standard-zh`。但是训练 portfolio 计划仍然只会把 suite 当文件路径传给 eval-suite 和 pair-batch。这样在真实训练链路里使用标准套件仍然要手动绕一下。

本版解决这个断点：portfolio 和 batch 计划可以直接接收 `suite_name="standard-zh"`，并把它传给下游 eval-suite/pair-batch 步骤。

## 不做什么

本版不训练新模型，不改变 eval-suite 评分逻辑，不修改标准 suite 的 10 条 prompt，也不改变默认 `data/eval_prompts.json` 行为。

它只负责把“选择标准 suite”这件事接入训练工作流。

## 关键文件

### `src/minigpt/training_portfolio.py`

`build_training_portfolio_plan()` 新增参数：

```python
suite_name: str | None = None
```

内部新增两个 helper：

```python
def _suite_ref(root: Path, *, suite_path: str | Path | None, suite_name: str | None) -> dict[str, Any]:
    ...


def _suite_args(suite_ref: dict[str, Any]) -> list[str]:
    ...
```

`_suite_ref()` 负责把 suite 选择转换成计划证据：

- 文件模式：`{"mode": "file", "name": None, "path": ".../data/eval_prompts.json"}`
- 内置模式：`{"mode": "builtin", "name": "standard-zh", "path": "builtin:standard-zh"}`

它还会拒绝同时传 `suite_path` 和 `suite_name`，防止计划里出现“既是文件又是内置套件”的歧义。

`_suite_args()` 负责生成下游命令参数：

- 文件模式生成 `["--suite", path]`
- 内置模式生成 `["--suite-name", name]`

因此 eval-suite 步骤和 pair-batch 步骤都复用同一组 suite 参数，避免一个步骤用标准 suite、另一个步骤仍用默认文件。

### `src/minigpt/training_portfolio_batch.py`

batch 公共配置新增：

```python
suite_name: str | None = None
```

`VARIANT_OVERRIDE_KEYS` 新增：

```python
"suite_path",
"suite_name",
```

这样 variant 可以单独覆盖 suite 选择。

这里有一个重要细节：如果 batch 全局设置了 `suite_name="standard-zh"`，而某个 variant 显式设置了 `suite_path`，那 variant 必须清掉继承来的 `suite_name`。否则 `build_training_portfolio_plan()` 会同时收到 `suite_path` 和 `suite_name` 并拒绝。

所以 `_variant_config()` 新增了互斥清理：

```python
if "suite_path" in variant and "suite_name" not in variant:
    config["suite_name"] = None
if "suite_name" in variant and "suite_path" not in variant:
    config["suite_path"] = None
```

这个行为让 batch 支持两种实际使用方式：

- 全部 variants 继承 `standard-zh`。
- 某个 variant 显式回到文件 suite。

### `scripts/run_training_portfolio.py`

新增 CLI：

```python
--suite-name {default,standard-zh}
```

如果传了 `--suite-name`，脚本调用 plan builder 时传：

```python
suite_path=None
suite_name=args.suite_name
```

否则保持旧行为，继续传 `--suite data/eval_prompts.json`。

### `scripts/run_training_portfolio_batch.py`

同样新增 `--suite-name {default,standard-zh}`，并把它传给 batch plan builder。

### `tests/test_training_portfolio.py`

新增两类测试：

- `test_build_training_portfolio_plan_accepts_builtin_standard_suite()`
  - 断言 plan 的 `suite` 对象是 built-in 模式。
  - 断言 `suite_path == "builtin:standard-zh"`。
  - 断言 eval-suite 和 pair-batch command 都包含 `--suite-name standard-zh`。
  - 断言 command 不再包含 `--suite <path>`。
- `test_build_training_portfolio_plan_rejects_suite_name_and_path_together()`
  - 保护互斥规则，避免计划证据歧义。

### `tests/test_training_portfolio_batch.py`

新增 `test_build_batch_plan_passes_standard_suite_to_variants()`。

它覆盖：

- batch 全局 `suite_name="standard-zh"` 能传进 variants。
- 默认继承的 variant 使用 `--suite-name standard-zh`。
- 明确指定 `suite_path` 的 variant 能覆盖全局 suite_name，回到 `--suite <path>`。

这个测试在开发中实际抓到了两个问题：`suite_path` 一开始没有进入 `VARIANT_OVERRIDE_KEYS`，以及 variant 文件 suite 没有正确清掉继承的 suite_name。修正后测试才通过。

## 运行流程

单条 portfolio：

1. 用户运行 `scripts/run_training_portfolio.py data --suite-name standard-zh`。
2. 脚本传入 `suite_name="standard-zh"`。
3. `build_training_portfolio_plan()` 生成 `suite={"mode":"builtin","name":"standard-zh","path":"builtin:standard-zh"}`。
4. eval-suite step 使用 `scripts/eval_suite.py --suite-name standard-zh`。
5. pair-batch step 使用 `scripts/pair_batch.py --suite-name standard-zh`。

batch：

1. 用户运行 `scripts/run_training_portfolio_batch.py data --suite-name standard-zh`。
2. batch common config 带上 `suite_name`。
3. 每个 variant 的 portfolio plan 继承这个 suite。
4. 如果 variant 显式设置 `suite_path`，它可以覆盖全局内置 suite。

## 验证

本版验证包括：

- focused tests：`tests.test_training_portfolio`、`tests.test_training_portfolio_batch`、`tests.test_eval_suite`。
- syntax：portfolio、batch、两个脚本和对应测试文件编译通过。
- dry-run smoke：`run_training_portfolio.py --suite-name standard-zh` 生成 planned portfolio。
- batch dry-run smoke：`run_training_portfolio_batch.py --suite-name standard-zh --no-compare` 生成 planned batch。
- source encoding：`scripts/check_source_encoding.py` 通过。
- full unittest：全量 `python -B -m unittest discover -s tests` 通过。

截图证据放在 `c/199/图片`，说明文件放在 `c/199/解释/说明.md`。

## 边界说明

v199 不证明模型在标准 suite 上表现更好。它只是把标准 suite 接入训练后的评估链路。下一步如果继续往能力侧推进，应该用 `--execute` 跑真实 checkpoint，再把 eval suite、generation quality、benchmark scorecard 和 pair-batch 结果一起比较。

一句话总结：v199 把标准中文 benchmark suite 从单独评估入口接进训练 portfolio 和 batch 计划，让后续真实训练比较能直接用同一套标准 prompt 闭环。
