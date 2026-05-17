# v198 standard Chinese benchmark suite 代码讲解

## 本版目标

v198 的目标是给评估链路补一个真实可用的小功能：标准中文 benchmark prompt suite。

前两版 v196-v197 主要在 benchmark scorecard 周边做 helper 收束，本版回到“模型能力评估输入”的建设。它不训练新模型、不改变 scorecard 评分、不改默认 5 条 suite，而是在现有 eval/pair-batch 工作流上增加一个可显式选择的 10 条中文标准套件。

## 为什么需要

现有 `data/eval_prompts.json` 是一个轻量默认套件，适合 smoke 和学习演示，但覆盖面有限。后续如果要比较真实 checkpoint，最好有一套更稳定、更广一点的 prompts，减少每次临时拼 prompt 导致的比较漂移。

v198 解决的是“评估输入标准化”问题：

- 默认 suite 继续保留，避免破坏旧命令。
- 新增标准 suite，覆盖更多任务类型。
- 同时提供内置 API 和 JSON 文件，方便代码调用和命令行调用。
- eval 和 pair-batch 都能通过同一个 `--suite-name standard-zh` 使用它。

## 关键文件

### `src/minigpt/eval_suites.py`

这是本版新增的标准套件模块。

核心函数是：

```python
def standard_zh_prompt_suite() -> PromptSuite:
    ...
```

它返回一个 `PromptSuite`，名称为 `minigpt-standard-zh-benchmark`，版本为 `2`，包含 10 个 `PromptCase`。

10 个任务类型分别是：

- `continuation`
- `qa`
- `summary`
- `structured`
- `factual-consistency`
- `classification`
- `rewrite`
- `safety-boundary`
- `self-check`
- `comparison`

这些任务不是为了证明 MiniGPT 已经具备大模型能力，而是给后续真实训练/对比提供固定输入。

模块还提供：

```python
def named_prompt_suite(name: str) -> PromptSuite:
    ...
```

它把 `default`、`small-zh`、`standard-zh` 等名字解析成对应内置套件。

### `src/minigpt/eval_suite.py`

新增：

```python
def load_builtin_prompt_suite(name: str) -> PromptSuite:
    from minigpt.eval_suites import named_prompt_suite
    return named_prompt_suite(name)
```

这里使用函数内部 import，是为了避免 `eval_suite.py` 和 `eval_suites.py` 之间形成模块加载循环。

`load_prompt_suite()` 也新增了 `builtin:` URI：

```python
if str(path).startswith("builtin:"):
    return load_builtin_prompt_suite(str(path).split(":", 1)[1])
```

因此后续可以直接写：

```python
load_prompt_suite("builtin:standard-zh")
```

### `data/standard_zh_eval_prompts.json`

这是文件版标准套件。它和 `standard_zh_prompt_suite().to_dict()` 保持一致。

保留文件版的原因是很多现有命令已经习惯用 `--suite data/xxx.json`，文件版也更适合人工查看、复制、修改或提交给外部脚本。

### `scripts/eval_suite.py`

新增 CLI 参数：

```python
parser.add_argument("--suite-name", choices=["default", "standard-zh"], default=None, ...)
```

当用户传入 `--suite-name standard-zh` 时，脚本用内置套件；否则继续读取 `--suite` 指定的 JSON 文件。

report 中的 suite path 会记录为：

```text
builtin:standard-zh
```

这能让后续证据链知道本次 eval 用的是内置标准套件，而不是某个临时文件。

### `scripts/pair_batch.py`

同样新增 `--suite-name standard-zh`，让左右 checkpoint pair batch 可以使用完全相同的标准套件。

这点很重要，因为 pair-batch 是后续模型能力比较的主要入口之一。固定 prompt、采样参数和 seed 后，左右 checkpoint 的输出差异更容易解释。

### `tests/test_eval_suite.py`

新增三类测试：

- 标准套件覆盖测试：确认 suite name/version/case count/task type/difficulty/seed 范围。
- `builtin:` URI 测试：确认 `load_prompt_suite("builtin:standard-zh")` 能工作。
- 数据文件一致性测试：确认 `data/standard_zh_eval_prompts.json` 和内置 suite 的 `to_dict()` 完全一致。

## 使用方式

运行 eval suite：

```powershell
python scripts/eval_suite.py --checkpoint runs/minigpt/checkpoint.pt --suite-name standard-zh
```

运行 pair batch：

```powershell
python scripts/pair_batch.py --left-checkpoint runs/base/checkpoint.pt --right-checkpoint runs/candidate/checkpoint.pt --suite-name standard-zh
```

代码中加载：

```python
from minigpt.eval_suite import load_prompt_suite

suite = load_prompt_suite("builtin:standard-zh")
```

或者：

```python
from minigpt import standard_zh_prompt_suite

suite = standard_zh_prompt_suite()
```

## 验证

本版验证包括：

- focused tests：`tests.test_eval_suite`、`tests.test_pair_batch`、`tests.test_training_portfolio`。
- syntax：`eval_suite.py`、`eval_suites.py`、两个脚本和测试文件编译通过。
- smoke：内置 suite 和文件 suite 均为 10 条，task type 覆盖 10 类。
- CLI help：`eval_suite.py` 和 `pair_batch.py` 都暴露 `--suite-name {default,standard-zh}`。
- source encoding：`scripts/check_source_encoding.py` 通过。
- full unittest：全量 `python -B -m unittest discover -s tests` 通过。

截图证据放在 `c/198/图片`，说明文件放在 `c/198/解释/说明.md`。

## 边界说明

v198 不声称模型能力提升。它提升的是评估输入的标准化程度。真正的模型能力提升还需要后续用这个标准套件跑多个真实 checkpoint，并把 eval suite、generation quality、benchmark scorecard 和 pair-batch 结果串起来比较。

一句话总结：v198 把 MiniGPT 的中文评估输入从默认 5 条 smoke suite 扩展出一个可复用的 10 条标准 suite，让后续 checkpoint 比较更稳定、更可解释。
