# v75 consolidated training scale workflow 代码讲解

## 本版目标

v75 的目标是把 v70-v74 的训练规模治理链收口到一个统一入口里：

```text
plan -> gated profile runs -> comparison -> decision -> workflow summary
```

它解决的问题是：v70-v74 每一层都合理，但用户需要手工串多条命令，版本看起来也偏碎。v75 不再继续拆一个新的小 report，而是把已有能力合并为“执行前一键审阅工作流”。

本版明确不做：

- 不直接扩大训练语料。
- 不自动执行真实训练。
- 不删除 v70-v74 的独立脚本；它们仍然可单独调试。
- 不把 warn profile 当作生产通过，只把它标记为需要 review 的候选。

## 前置能力

v75 消费并编排这些既有模块：

- v70 `training_scale_plan`：扫描语料、判断规模、生成 variant matrix。
- v72 `training_scale_run`：按 gate profile 运行 dry-run 或 execute。
- v73 `training_scale_run_comparison`：比较多个 profile run。
- v74 `training_scale_run_decision`：选择下一步可执行候选。

v75 的价值不是多做一个展示层，而是减少治理链的人工拼接成本。

## 关键新增文件

```text
src/minigpt/training_scale_workflow.py
scripts/run_training_scale_workflow.py
tests/test_training_scale_workflow.py
c/75/图片
c/75/解释/说明.md
```

README、`c/README.md` 和本目录 README 同步加入 v75，表示这条收口路线已经进入项目主结构。

## 核心模块

### `run_training_scale_workflow`

这是 v75 的主函数。它的输入包括：

- `sources`：训练文本文件或目录。
- `profiles`：要比较的 gate profiles，默认 `review`、`standard`。
- `baseline_profile`：comparison baseline，默认第一个 profile。
- `dataset_name`、`dataset_version_prefix`、`dataset_description`：传给 scale plan。
- `execute`：是否真实执行 profile batch，默认 false。
- `allow_warn`、`allow_fail`：传给 gated runner。
- `decision_min_readiness`、`decision_require_gate_pass`、`decision_require_batch_started`：传给 decision。

主流程是：

```text
1. build_training_scale_plan
2. write_training_scale_plan_outputs
3. 对每个 profile 调 run_training_scale_plan
4. build_training_scale_run_comparison
5. write_training_scale_run_comparison_outputs
6. build_training_scale_run_decision
7. write_training_scale_run_decision_outputs
8. 写出 training_scale_workflow.* 总览产物
```

这样，用户不需要手工记住五条命令，也不容易把 plan、profile、comparison baseline 或 decision 参数串错。

## 输出结构

默认输出目录类似：

```text
runs/training-scale-workflow/
  plan/
    training_scale_plan.json
    training_scale_variants.json
  runs/
    review/
      training_scale_run.json
    standard/
      training_scale_run.json
  comparison/
    training_scale_run_comparison.json
  decision/
    training_scale_run_decision.json
  training_scale_workflow.json
  training_scale_workflow.csv
  training_scale_workflow.md
  training_scale_workflow.html
```

`plan/`、`runs/<profile>/`、`comparison/` 和 `decision/` 是下游证据；根目录下的 `training_scale_workflow.*` 是总览证据。

## 核心字段

`training_scale_workflow.json` 的关键字段：

- `profiles`：参与比较的 gate profiles。
- `baseline_profile`：comparison baseline。
- `plan_summary`：语料规模、字符数、variant 数量。
- `runs`：每个 profile 的 status、allowed、gate_status、batch_status、readiness_score 和产物路径。
- `comparison_summary`：来自 v73 的比较摘要。
- `decision_summary`：来自 v74 的选择摘要。
- `execute_command_text`：最终 handoff 命令。
- `summary`：面向人审阅的统一结论。

这里的 `execute_command_text` 仍然只是 handoff，不会自动执行。这个边界很重要：v75 收口的是审阅链，不是绕开人工确认去跑更贵的训练。

## CLI

入口脚本是：

```powershell
python scripts/run_training_scale_workflow.py data --out-root runs/training-scale-workflow --profile review --profile standard --baseline-profile review
```

常用参数：

- `--profile`：可重复，用于选择 review/standard/strict。
- `--baseline-profile`：指定 comparison baseline。
- `--execute`：真实执行 profile batch，默认不开。
- `--decision-require-gate-pass`：让 decision 只接受 pass，不接受 warn。
- `--decision-min-readiness`：设置最低 readiness。

当 decision 结果为 `blocked` 时，CLI 返回非零退出码，让自动化流程能够停住。

## 测试覆盖

`tests/test_training_scale_workflow.py` 覆盖四类风险：

- 默认 workflow 能真实写出 plan、profile run、comparison、decision 和 workflow HTML。
- 严格 decision 模式会阻断 warn-only 候选。
- 重复 profiles 或 baseline 不在 profiles 中会抛出 `ValueError`。
- Markdown/HTML 渲染可用，HTML 会转义标题里的 `<workflow>`。

这些测试不是只看函数返回值，而是检查实际文件落盘，防止统一入口看似成功但中间产物缺失。

## 运行归档

`c/75` 保存本版截图和解释：

```text
c/75/图片
c/75/解释/说明.md
```

截图包含 focused tests、全量 tests、compileall、默认 workflow smoke、严格 blocked smoke、结构检查、文档检查和 Playwright/Chrome HTML 截图。它们用于证明 v75 的“收口”不是口头路线，而是已经变成可执行入口。

## 一句话总结

v75 把 MiniGPT 从“训练规模治理链很完整但偏碎”推进到“一个命令生成训练前审阅闭环”的收口阶段。
