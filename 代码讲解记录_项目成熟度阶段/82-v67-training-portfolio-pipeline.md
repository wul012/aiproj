# 第六十七版代码讲解：training portfolio pipeline

## 本版目标、来源和边界

v67 的目标是把 v66 的成熟度叙事报告反向接回真实训练链路。v66 已经能把 maturity summary、registry、request history summary、benchmark scorecard 和 dataset card 合成一份 portfolio 叙事，但这份叙事仍依赖用户手动把训练、评估、数据卡和成熟度报告逐个跑出来。

所以本版新增 training portfolio pipeline：用一个入口把数据准备、训练、固定 prompt 评估、生成质量分析、benchmark scorecard、dataset card、registry、maturity summary 和 maturity narrative 串成一条可 dry-run、也可 `--execute` 的端到端流程。

本版不做三件事：

- 不引入新模型结构，也不改变 Transformer/GPT 的训练目标。
- 不把 smoke 训练结果包装成真实大模型能力，真实能力仍取决于语料规模、训练步数和评估集质量。
- 不替代各个底层脚本；pipeline 只是编排已有脚本，并记录命令、状态和产物。

## 本版来自哪条路线

这一版来自“从治理收口回到真实训练”的路线：

```text
v13-v16 数据准备、质量和 eval suite
 -> v49-v54 benchmark scorecard / dataset card
 -> v60-v66 request history / release readiness / maturity narrative
 -> v67 training portfolio pipeline
```

前面版本已经有很多报告和证据，但项目要继续成熟，不能只靠静态展示。v67 把这些证据重新绑定到一个真实可执行的训练组合跑。

## 关键新增和修改文件

- `src/minigpt/training_portfolio.py`
  - 新增 pipeline plan 构建器、执行器、JSON/Markdown/HTML 渲染和写出函数。
  - 负责把每一步命令、预期产物、执行结果和 artifact 状态组织成结构化报告。
- `scripts/run_training_portfolio.py`
  - 新增命令行入口。
  - 默认 dry-run，只写计划和报告；加 `--execute` 才真正跑训练、评估和后续证据生成。
- `tests/test_training_portfolio.py`
  - 覆盖步骤顺序、dry-run 状态、通用执行记录、输出写入和 HTML 转义。
- `README.md`
  - 更新 v67 当前版本、能力说明、CLI 用法、tag、截图索引、学习路线和下一步方向。
- `b/67/解释/说明.md`
  - 解释本版运行截图、真实 smoke 和 tag 含义。

## 核心数据结构

`build_training_portfolio_plan()` 输出的是一个 plan：

```text
schema_version
title
project_root
out_root
run_name
dataset_name
dataset_version
suite_path
request_log_path
artifacts
steps
```

`artifacts` 是本次组合跑的关键产物索引：

```text
corpus
dataset_version
dataset_quality
dataset_card
checkpoint
run_manifest
eval_suite
generation_quality
benchmark_scorecard
registry
maturity_summary
maturity_narrative
request_history_summary  # 仅在传入 request log 时存在
```

`steps` 是可执行步骤列表，每一项包含：

```text
key
title
command
expected_outputs
```

固定步骤顺序是：

```text
prepare_dataset
train
eval_suite
generation_quality
benchmark_scorecard
dataset_card
registry
maturity_summary
request_history_summary  # 可选
maturity_narrative
```

## 执行流程

默认运行：

```powershell
python scripts/run_training_portfolio.py data --out-root runs/training-portfolio
```

只生成 dry-run 计划和 `training_portfolio.json/md/html`，不训练模型。

真实执行：

```powershell
python scripts/run_training_portfolio.py data --out-root runs/training-portfolio --execute --device cpu --max-iters 100
```

执行器按步骤调用已有脚本。每个步骤会记录：

```text
returncode
started_at
finished_at
stdout
stderr
stdout_tail
stderr_tail
```

如果某一步失败，pipeline 会停止，`execution.status` 变为 `failed`，并记录 `failed_step`。如果全部成功，状态为 `completed`。

## 输出产物的角色

`training_portfolio.json` 是机器可读执行证据，保留命令、产物路径、执行状态和 stdout/stderr。

`training_portfolio.md` 是仓库内可读的 pipeline 说明，适合查看步骤、命令和产物表。

`training_portfolio.html` 是浏览器展示和截图入口，适合把一次训练组合跑作为 portfolio evidence 打开。

这些文件是最终证据；临时训练 fixture、临时 run 目录和临时日志仍按 AGENTS 清理门禁删除，不进入版本库。

## 测试覆盖了什么

`tests/test_training_portfolio.py` 覆盖四类风险：

- 步骤顺序：确保 pipeline 按数据准备、训练、评估、质量、scorecard、数据卡、registry、maturity 和 narrative 的顺序执行。
- dry-run：确保默认不会误触发训练，只写计划和 expected artifacts。
- 执行记录：用一个轻量命令验证执行器能记录 return code、stdout tail 和 artifact 存在状态。
- 输出和 HTML 转义：确保 JSON/Markdown/HTML 都写出，并且标题中的 `<Portfolio>` 被安全转义。

这些测试不跑真实训练，避免单测变慢；真实训练闭环用 v67 的 smoke 截图证明。

## README、截图和归档如何证明本版闭环

README 记录 v67 能力、CLI 用法、tag 和截图索引。

`b/67/图片/` 保存 dry-run、真实 execute smoke、artifact 检查、Playwright/Chrome HTML 截图和文档检查。

`b/67/解释/说明.md` 说明每张截图证明什么，避免证据只是图片堆积。

本篇代码讲解解释 pipeline 为什么存在、如何执行、字段语义是什么、测试保护哪些边界。

## 一句话总结

v67 把 MiniGPT 从“能解释已有证据”推进到“能用一个命令重新生产训练、评估、数据卡、scorecard、registry 和成熟度叙事证据”的训练组合跑阶段。
