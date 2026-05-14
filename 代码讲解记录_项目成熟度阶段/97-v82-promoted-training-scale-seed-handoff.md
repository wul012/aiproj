# v82 promoted training scale seed handoff 代码讲解

## 本版目标

v82 的目标是把 v81 的 promoted training scale next-cycle seed 继续往下交接一步：把 seed 里生成的 `plan_training_scale.py` 命令变成可验证、可执行、可归档的 plan handoff。

v81 已经解决了：

```text
baseline decision 选出来后，下一轮训练规模规划该从哪里开始？
next-cycle corpus source 是否存在？
如果 seed 不完整，是否应该阻断？
```

v82 继续解决：

```text
这个 seed 生成的 plan 命令是否真的可以运行？
运行后是否会落出 plan 证据？
是否能继续读取 plan 产物里的 next batch command，作为下一层证据继续往后传？
```

本版明确不做：

- 不训练模型。
- 不执行 training portfolio batch 或更重的训练命令。
- 不重新生成 v81 seed。
- 不把 plan 产物伪装成训练产物。

v82 只负责把 seed 命令 materialize 成 plan 产物，并检查下一层 batch command 是否已经显现出来。

## 前置链路

v82 接在 v81 之后：

```text
v80 promoted training scale baseline decision
 -> v81 promoted training scale next-cycle seed
 -> v82 promoted training scale seed handoff
```

它保留了 v76 handoff 的思想，但输入从 workflow decision 变成了 v81 seed。也就是说，这里不是“执行训练”，而是“把下一轮 plan 先跑出来，并把 plan 的批量入口再往后暴露一层”。

## 关键新增文件

```text
src/minigpt/promoted_training_scale_seed_handoff.py
scripts/execute_promoted_training_scale_seed.py
tests/test_promoted_training_scale_seed_handoff.py
c/82/图片
c/82/解释/说明.md
```

这些文件共同构成 v82 的闭环：一个可执行的 CLI、一个可验证的核心模块、一组覆盖边界和落盘的单测，以及归档截图和说明。

## 核心模块

### `load_promoted_training_scale_seed`

输入可以是：

```text
runs/training-scale-workflow/promoted-seed/promoted_training_scale_seed.json
runs/training-scale-workflow/promoted-seed
runs/training-scale-workflow
```

目录输入会查找：

```text
promoted_training_scale_seed.json
promoted-seed/promoted_training_scale_seed.json
seed/promoted_training_scale_seed.json
```

读到 JSON 后会附加 `_source_path`，报告据此标注 seed 的来源路径。

### `build_promoted_training_scale_seed_handoff`

这是 v82 的核心函数。它做的事情是：

```text
1. 读取 v81 seed
2. 提取 next_plan.command 和 next_plan.plan_out_dir
3. 检查 seed_status 是否允许继续
4. 默认只验证命令，显式 --execute 时才运行 plan 命令
5. 读取生成出来的 training_scale_plan.json
6. 从 plan 里提取下一层 batch command
```

这一步的关键不是“执行得多重”，而是“把 seed 的下一步真正落成证据”。v81 给的是 command，v82 给的是 command 运行后的 plan 证据和下一层 batch command。

## 状态语义

v82 输出的 handoff 状态有：

```text
planned
completed
blocked
failed
timeout
```

含义如下：

- `planned`：命令可用，但这次只做验证，没有实际执行。
- `completed`：命令执行成功，plan 产物全部落盘。
- `blocked`：seed 状态或命令前提不足，无法继续。
- `failed`：命令执行了，但返回了非零退出码。
- `timeout`：命令执行超时。

seed 本身仍然有自己的 `seed_status`，但 v82 关注的是 seed 是否成功被转化为 plan handoff。

## 核心字段

### `command`

`command` 是从 v81 seed 的 `next_plan.command` 直接读取的结构化命令列表。

这部分是 seed 到 plan 的关键交接点。它不是字符串拼接日志，而是后续可以直接执行的命令参数数组。

### `plan_report`

`plan_report` 是执行后读取的 `training_scale_plan.json`。它不是新训练结果，而是训练规模计划证据。里面最关键的字段有：

```text
dataset.scale_tier
dataset.source_count
dataset.char_count
dataset.quality_status
variants[]
batch.command
```

v82 会把这些字段继续提取到自己的 summary 中，并把 `batch.command` 暴露为 `next_batch_command`。

### `artifact_rows`

`artifact_rows` 对应 plan 产物的五个文件：

```text
training_scale_plan.json
training_scale_variants.json
training_scale_plan.csv
training_scale_plan.md
training_scale_plan.html
```

这些不是临时日志，而是最终证据。只要计划执行成功，它们就应该可见。

## CLI

入口命令：

```powershell
python scripts/execute_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-seed --execute --out-dir runs/training-scale-workflow/promoted-seed-handoff
```

常用参数：

```text
--execute
--no-allow-review
--timeout-seconds
--title
```

默认情况下它只验证 seed 和 plan 命令；加上 `--execute` 才会真正运行 plan 命令。

## 输出产物

v82 输出：

```text
promoted_training_scale_seed_handoff.json
promoted_training_scale_seed_handoff.csv
promoted_training_scale_seed_handoff.md
promoted_training_scale_seed_handoff.html
```

JSON 适合后续模块消费；CSV 便于快速扫描状态；Markdown 适合人审；HTML 适合浏览器截图和归档。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 覆盖：

- ready seed 在不执行时会得到 `planned`。
- review seed 在 `allow_review=False` 时会被阻断。
- ready seed 在 `--execute` 时会真正运行 plan 命令并落出 plan 产物。
- 失败命令会返回 `failed` 并保留 return code。
- JSON/CSV/Markdown/HTML 都能落盘，HTML 会转义 `<Handoff>`。

这些断言保护的是 v82 的边界：seed 并不是自动可执行训练指令，只有命令和来源都完整时，plan handoff 才能继续往下走。

## 运行归档

`c/82` 保存本版截图和解释：

```text
c/82/图片
c/82/解释/说明.md
```

它们记录了 focused tests、full regression、compileall、ready smoke、blocked smoke、结构检查、Playwright/Chrome HTML 验收和文档索引检查。

## 一句话总结

v82 把 MiniGPT 的 promoted training scale 链路从“能生成下一步 plan 命令”推进到“能把 plan 命令执行成可复查的计划证据，并暴露下一层 batch command”。
