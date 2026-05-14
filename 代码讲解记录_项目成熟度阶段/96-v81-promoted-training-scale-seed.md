# v81 promoted training scale next-cycle seed 代码讲解

## 本版目标

v81 的目标是把 v80 选出的 promoted baseline 继续向下一轮训练规模规划交接。

v80 已经回答：

```text
promoted comparison 完成之后，哪一个 promoted run 可以作为下一阶段稳定 baseline？
如果上游 comparison 不完整，是否应该阻断？
如果候选 readiness、gate、batch 条件不足，是否应该进入 review 或 blocked？
```

v81 继续回答：

```text
baseline 已经选出来以后，下一轮 training scale plan 应该从哪里开始？
新的语料来源是否已经给出并存在？
如果 baseline decision 或下一轮 corpus 输入不完整，是否应该阻断下一轮计划命令？
```

本版明确不做：

- 不重新训练模型。
- 不重新执行 v75-v80 的 workflow/handoff/promotion/index/comparison/decision。
- 不读取 review/blocked baseline 强行启动下一轮。
- 不把 `plan_training_scale.py` 的真实执行结果伪装成本版产物。

v81 只生成 next-cycle seed：它是从上一个 promoted baseline 决策到下一轮训练规模规划之间的交接证据。

## 前置链路

本版接在 v75-v80 训练规模治理链路之后：

```text
v75 consolidated training scale workflow
 -> v76 controlled training scale handoff
 -> v77 training scale promotion acceptance
 -> v78 training scale promotion index
 -> v79 promoted training scale comparison
 -> v80 promoted training scale baseline decision
 -> v81 promoted training scale next-cycle seed
```

这条链路原本已经能从多次 gated scale run 中筛出 promoted baseline。v81 让它再往前走一步：把被选中的 baseline 变成下一轮 `plan_training_scale.py` 的输入依据，而不是停在“报告已经选出 baseline”这一层。

## 关键新增文件

```text
src/minigpt/promoted_training_scale_seed.py
scripts/build_promoted_training_scale_seed.py
tests/test_promoted_training_scale_seed.py
c/81/图片
c/81/解释/说明.md
```

README、`c/README.md` 和项目成熟度阶段讲解索引同步更新到 v81。

## 核心模块

### `load_promoted_training_scale_decision`

输入可以是：

```text
runs/training-scale-workflow/promoted-decision/promoted_training_scale_decision.json
runs/training-scale-workflow/promoted-decision
runs/training-scale-workflow
```

目录输入会查找：

```text
promoted_training_scale_decision.json
promoted-decision/promoted_training_scale_decision.json
decision/promoted_training_scale_decision.json
```

读到 JSON 后会附加 `_source_path`，后续报告用它记录 seed 来自哪一份 v80 decision。

### `build_promoted_training_scale_seed`

这是 v81 的主函数。它的输入有两类：

```text
1. v80 promoted_training_scale_decision.json
2. 下一轮 corpus sources，也就是 text 文件或目录
```

它执行的核心步骤是：

```text
1. 读取 v80 baseline decision
2. 解析 selected_baseline 和 training_scale_run_path
3. 检查 selected training_scale_run.json 是否存在
4. 检查下一轮 corpus sources 是否存在
5. 根据 decision_status、baseline、source 状态生成 seed_status
6. 在允许时生成 plan_training_scale.py 的下一步命令
```

这里的关键边界是：命令只在 blockers 为空时生成。也就是说，如果 v80 decision 是 `blocked`、没有 `selected_baseline`、selected run 路径缺失，或者下一轮语料不存在，v81 不会输出可执行命令。

## 状态语义

v81 输出三类状态：

```text
ready
review
blocked
```

含义如下：

- `ready`：v80 decision 是 `accepted`，selected run 存在，下一轮语料来源存在，可以进入下一轮 training scale plan。
- `review`：v80 decision 是 `review`，selected run 和语料来源都存在，但人需要先复核 warning，再决定是否执行命令。
- `blocked`：baseline decision、selected run 或 corpus sources 中至少有一项不完整。

这和 v80 的 `accepted/review/blocked` 不完全一样。v81 的 `ready` 代表“下一轮计划命令已经具备执行前提”，而不是说模型能力已经提升。

## 核心字段

### `baseline_seed`

`baseline_seed` 是 v80 选出的 baseline 在 v81 中的交接摘要：

```text
selected_name
decision_status
gate_status
batch_status
readiness_score
training_scale_run_path
training_scale_run_exists
comparison_path
selected_run_summary
```

`selected_run_summary` 会读取 selected `training_scale_run.json`，提取上一轮的 scale tier、字符数、variant 数、gate/batch 状态等信息。它不是重新计算训练结果，只是让下一轮 seed 能解释“这个 baseline 来自什么样的训练规模证据”。

### `next_plan`

`next_plan` 描述下一轮 training scale plan 的入口：

```text
project_root
dataset_name
dataset_version_prefix
dataset_description
sample_prompt
max_variants
plan_out_dir
batch_out_root
sources
command
command_text
command_available
execution_ready
```

`command` 是结构化列表，适合后续脚本消费；`command_text` 是给人复查的 PowerShell 形式。

当 `seed_status=ready` 时，`execution_ready=true`。当 `seed_status=review` 时，命令可以存在，但 `execution_ready=false`，提醒用户先复核。

### `blockers`

`blockers` 是本版很重要的证据字段。它可能包含：

```text
decision status is blocked
decision does not contain selected_baseline
selected baseline does not include training_scale_run_path
selected training_scale_run.json is missing
no corpus sources provided for the next training scale plan
missing corpus sources: ...
```

这些不是调试日志，而是最终报告的一部分。它们解释为什么 v81 没有把上一轮 baseline 转成下一轮训练规模计划命令。

## CLI

命令入口：

```powershell
python scripts/build_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-decision data --out-dir runs/training-scale-workflow/promoted-seed --plan-out-dir runs/training-scale-workflow/next-plan
```

常用参数：

```text
--project-root
--plan-out-dir
--batch-out-root
--dataset-name
--dataset-version-prefix
--dataset-description
--sample-prompt
--max-variants
--require-ready
```

`--require-ready` 适合自动化链路：如果最终 `seed_status` 不是 `ready`，命令返回非零退出码。

## 输出产物

v81 输出：

```text
promoted_training_scale_seed.json
promoted_training_scale_seed.csv
promoted_training_scale_seed.md
promoted_training_scale_seed.html
```

JSON 是最稳定的后续消费入口；CSV 方便扫描状态字段；Markdown 用于审查记录；HTML 用于浏览器验收和截图归档。

这些产物都是最终证据，不是临时日志。临时 fixture 和 smoke 输出只放在 `tmp/`，提交前按 cleanup gate 删除。

## 测试覆盖

`tests/test_promoted_training_scale_seed.py` 覆盖：

- `accepted` decision + 存在的 corpus source 会生成 `ready` seed 和 `plan_training_scale.py` 命令。
- `review` decision 会保留命令，但把 `execution_ready` 标为 `false`。
- `blocked` decision 或缺少 `selected_baseline` 会阻断命令。
- 下一轮 corpus source 缺失时会阻断，并记录 missing source blocker。
- JSON/CSV/Markdown/HTML 能落盘，HTML 会转义 `<Seed>`。

这些断言保护的是 v81 的核心边界：不能因为 v80 选过 baseline，就忽略下一轮语料是否存在；也不能在 blocked decision 上生成误导性的下一步命令。

## 运行归档

`c/81` 保存本版截图和解释：

```text
c/81/图片
c/81/解释/说明.md
```

截图覆盖新单测、完整回归、compileall、ready smoke、blocked smoke、结构检查、Playwright/Chrome HTML 验收和 README/讲解/c 归档索引检查。

## 一句话总结

v81 把 MiniGPT 的 promoted training scale 链路从“选出稳定 baseline”推进到“把稳定 baseline 转成下一轮训练规模规划的可审查入口”。
