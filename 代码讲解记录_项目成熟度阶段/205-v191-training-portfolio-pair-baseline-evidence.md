# v191 training portfolio pair baseline evidence 代码讲解

## 本版目标

v191 的目标是补上真实 training portfolio 链路里最后一个明显的 benchmark 证据缺口：pair batch。

v190 之后，真实链路已经能从训练输出继续跑到 fixed eval suite、generation quality 和 benchmark scorecard，而且不再需要手工复制 `generation_quality` 目录。但 scorecard 仍然期待 `pair_batch/pair_generation_batch.json` 和 `pair_batch/pair_generation_batch.html`。如果不生成这组证据，scorecard 会把 pair consistency、pair delta stability 和 evidence completeness 视为缺口。

本版解决的问题是：

```text
训练组合执行时，能否自动产出 scorecard 需要的 pair batch 证据？
如果暂时没有第二个 checkpoint，能否先用同 checkpoint 自检证明可复现性？
同 checkpoint 自检会不会被误读为模型能力提升？
```

本版答案是：可以自动产出，但必须明确边界。v191 把 `scripts/pair_batch.py` 接进 training portfolio，默认用本次训练得到的同一个 checkpoint 做左右两侧，形成 `same_checkpoint_baseline`。这证明同 seed、同 prompt、同 checkpoint 下生成结果可复现，不证明新模型优于旧模型。

本版明确不做：

- 不新增新的 pair batch 算法。
- 不改变 `scripts/pair_batch.py` 的原有 CLI 契约。
- 不把 same-checkpoint 自检包装成 cross-checkpoint improvement。
- 不修改 eval suite、generation quality 或 rubric 评分规则。
- 不扩大训练规模，也不声称模型真实能力提升。

## 前置路线

v191 接在 v186-v190 的真实训练证据链后面：

```text
v186 real training run evidence
 -> v187 fixed eval suite summary
 -> v188 generation quality summary
 -> v189 benchmark scorecard summary
 -> v190 generation quality path compatibility
 -> v191 portfolio pair baseline evidence
```

这条路线的重点已经从早期 report 拆分回到真实执行链路。v191 做的是把已有 pair batch 能力放回训练组合，而不是继续新增一个孤立报告。

## 关键文件

```text
src/minigpt/training_portfolio.py
src/minigpt/benchmark_scorecard.py
src/minigpt/benchmark_scorecard_artifacts.py
tests/test_training_portfolio.py
tests/test_benchmark_scorecard.py
tests/test_benchmark_scorecard_artifacts.py
c/191/图片
c/191/解释/说明.md
```

`src/minigpt/training_portfolio.py` 是本版的主链路修改点。它负责生成训练组合计划，并在 `--execute` 时逐步运行每个命令。

`src/minigpt/benchmark_scorecard.py` 是本版的边界语义修改点。它不再只看 pair batch 是否相等，还会判断这是不是同 checkpoint baseline。

`src/minigpt/benchmark_scorecard_artifacts.py` 负责把 scorecard 的新字段写进 Markdown 和 HTML，让人工复核时能直接看到 pair comparison mode。

测试文件分别保护 plan 顺序、same-checkpoint 评分边界、路径优先判断和输出展示。

## training portfolio 新增了什么

v191 在 `build_training_portfolio_plan()` 中新增了两个 artifact：

```text
pair_batch
pair_batch_html
```

它们对应真实输出：

```text
<run_dir>/pair_batch/pair_generation_batch.json
<run_dir>/pair_batch/pair_generation_batch.html
```

同时新增一个 pipeline step：

```text
pair_batch
```

它的位置在：

```text
generation_quality
 -> pair_batch
 -> benchmark_scorecard
```

这个顺序很重要。scorecard 需要同时读取：

- `eval_suite/eval_suite.json`
- generation quality report
- `pair_batch/pair_generation_batch.json`
- `pair_batch/pair_generation_batch.html`

所以 pair batch 必须出现在 scorecard 之前。

## pair_batch step 的命令结构

新增 step 调用的是已有脚本：

```text
scripts/pair_batch.py
```

命令核心参数是：

```text
--left-checkpoint <run_dir>/checkpoint.pt
--right-checkpoint <run_dir>/checkpoint.pt
--left-tokenizer <run_dir>/tokenizer.json
--right-tokenizer <run_dir>/tokenizer.json
--left-id <run_name>
--right-id <run_name>
--suite <suite_path>
--out-dir <run_dir>/pair_batch
--device <device>
```

左右两侧 checkpoint 相同，所以这是 same-checkpoint baseline。这样做的工程价值是：

- 证明同一 checkpoint 在固定 prompt、固定 seed 下可复现。
- 给 scorecard 提供真实 pair batch artifact，不再靠手工补文件。
- 让后续 registry、dashboard、maturity 读取同一组标准路径。

它的边界也很明确：

- 不能说明 candidate 比 baseline 好。
- 不能替代两个不同 checkpoint 的 pair comparison。
- 只能作为真实训练链路的自检基线。

## scorecard 如何识别 same-checkpoint baseline

v191 在 scorecard 中新增两个 summary 字段：

```text
pair_same_checkpoint_baseline
pair_comparison_mode
```

当 pair batch 的每个 case 都带有：

```text
comparison.same_checkpoint = true
```

或者 pair batch 的左右 checkpoint 路径相同，scorecard 会标记：

```text
pair_same_checkpoint_baseline = true
pair_comparison_mode = same_checkpoint_baseline
```

这里还有一个小边界：判断时优先比较 checkpoint 路径，只有路径缺失时才退回比较 checkpoint id。这样即使用户把两个不同 checkpoint 都命名成同一个 id，也不会误判成自检基线。

## 为什么 pair 组件最高只给 90 分

同 checkpoint pair 如果 seed 固定，理想情况下输出应该完全一样。原先公式会给：

```text
Pair Consistency = 100
Pair Delta Stability = 100
```

这在数学上没错，但在项目语义上容易误导。100 分看起来像“跨模型对比很强”，实际只是“同模型可复现”。所以 v191 对 same-checkpoint baseline 增加上限：

```text
score = min(score, 90.0)
```

这个上限只作用于：

- `pair_consistency`
- `pair_delta_stability`

它不影响 eval coverage、generation quality、rubric correctness 或 evidence completeness。

## 输出产物的语义

pair batch 输出仍然是标准四件套：

```text
pair_generation_batch.json
pair_generation_batch.csv
pair_generation_batch.md
pair_generation_batch.html
```

这些是最终证据，不是临时文件。它们被后续模块消费：

- benchmark scorecard 读取 JSON 和 HTML 是否存在。
- registry 可以统计 pair report counts。
- dashboard/playground 可以展示 pair batch 链接。
- maturity 和 narrative 可以继续引用 scorecard 里的 pair summary。

scorecard 输出中会出现：

```text
Pair comparison mode: same_checkpoint_baseline
```

recommendations 也会提醒：

```text
Run a different candidate checkpoint pair before using pair metrics as model improvement evidence.
```

这条提醒就是本版最关键的边界说明。

## 测试如何覆盖链路

`tests/test_training_portfolio.py` 覆盖 plan 层：

- step 顺序包含 `pair_batch`。
- `pair_batch` 位于 `generation_quality` 和 `benchmark_scorecard` 之间。
- artifact map 包含 `pair_generation_batch.json` 和 `pair_generation_batch.html`。
- 命令里包含左右 checkpoint、左右 id 和 pair batch 脚本。

`tests/test_benchmark_scorecard.py` 覆盖 scorecard 语义：

- 普通 pair batch 仍然是 `cross_checkpoint_or_unknown`。
- same-checkpoint pair batch 会被标记为 `same_checkpoint_baseline`。
- same-checkpoint pair 两个组件最高 90 分。
- recommendation 会提示需要不同 checkpoint 才能作为模型提升证据。
- 当左右 checkpoint 路径不同但 id 相同，优先按路径判断，不误判为 same-checkpoint。

`tests/test_benchmark_scorecard_artifacts.py` 覆盖输出层：

- Markdown 包含 `Pair comparison mode`。
- HTML stats 包含 pair mode。
- artifact facade 仍然委托给 artifact 模块。

真实 smoke 还跑了完整 CPU PyTorch portfolio：

```text
status=completed
completed_steps=11/11
available_artifacts=18/18
pair_comparison_mode=same_checkpoint_baseline
pair component scores=90
```

这说明本版不是只改 plan 文本，而是真能跑出 checkpoint、eval、quality、pair batch、scorecard、registry、maturity 和 narrative。

## README 和运行证据

README 的 Current version 更新到 v191，强调：

- portfolio 已经自动生成 pair batch。
- same-checkpoint pair 是 reproducibility baseline。
- scorecard 不再把它夸成 cross-checkpoint improvement。

运行截图和解释放在：

```text
c/191/图片
c/191/解释/说明.md
```

这些截图证明：

- 聚焦测试通过。
- 真实 portfolio 执行完成。
- scorecard summary 能看到 pair mode 和 90 分上限。
- Playwright 能打开 scorecard HTML。
- source encoding 和全量 unittest 通过。

## 一句话总结

v191 把真实 training portfolio 的 pair evidence 缺口补上，同时把 same-checkpoint 自检的边界写进 scorecard，让项目从“缺 pair 证据”推进到“有可复现基线但仍诚实区分模型提升证据”。
