# v173 training scale run decision artifact split 代码讲解

## 本版目标

v173 的目标是把 `training_scale_run_decision.py` 中的 artifact 输出层拆到 `training_scale_run_decision_artifacts.py`，让训练规模运行决策继续向“决策逻辑”和“证据发布”分离。原模块同时做了三件事：读取 run comparison、筛选可执行候选、把决策写成 JSON/CSV/Markdown/HTML。前两者是训练规模推进链路的语义，后者是发布和展示层。随着后续可能调整 HTML 展示、CSV 字段或 Markdown 口径，把输出层拿出来可以避免决策模块继续膨胀。

本版明确不做这些事：不改变候选选择算法，不改变拒绝原因，不改变 `min_readiness`、`require_gate_pass`、`require_batch_started` 的含义，不改变 execute command 格式，不改变 `scripts/decide_training_scale_run.py` 用法，也不改变旧的 `minigpt.training_scale_run_decision` writer/render 导出入口。

## 前置路线

v173 接在训练规模工作流和项目维护收口路线后面。v70-v75 建立了 training scale plan -> gate -> run -> comparison -> decision -> workflow 的基本链路；v160 拆出 training scale promotion artifacts；v165 拆出 training scale plan artifacts；v168-v169 拆出 promoted seed 和 promoted seed handoff artifacts。这些版本的共同思路是：训练规模链路中的“判断和语义”留在主模块，“证据文件写出和页面渲染”放到 artifact 模块。

因此 v173 不是新增一个报告层，而是把已经存在的 run decision 产物写出职责收到对应位置。这也符合当前仓库规则：经过 3-4 个功能版本后，用一版做契约不变的去重和模块压力收束。

## 关键文件

- `src/minigpt/training_scale_run_decision.py`：运行决策主模块。它继续负责加载 comparison、建立 candidates/rejected、选择 selected run、生成 execute command、计算 decision status 和 recommendations。
- `src/minigpt/training_scale_run_decision_artifacts.py`：新增 artifact 模块。它只消费已经构造好的 decision report，把它写成 JSON、CSV、Markdown 和 HTML。
- `tests/test_training_scale_run_decision.py`：保留原有决策、拒绝、输出文件测试，并新增 facade identity 测试。
- `README.md`、`c/173/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录本版在项目成熟度阶段的位置、证据目录和讲解索引。

## 决策主模块

`build_training_scale_run_decision()` 是主入口。它的输入是 training scale run comparison JSON 路径和一组控制阈值：

- `min_readiness`：运行候选需要达到的 readiness 分数下限。
- `require_gate_pass`：是否要求 gate status 必须为 `pass`。
- `require_batch_started`：是否要求 batch status 已经从 `skipped` 推进到 planned/completed 等状态。
- `execute_out_root` 和 `python_executable`：用来构造后续真正执行 selected run 的命令。

函数先通过 `load_training_scale_run_comparison()` 读取 comparison，再把 `runs` 规范化为 list[dict]。每个 run 都会经过 `_rejection_reasons()`：如果不允许执行、readiness 不足、gate 未达标或 batch 未启动，就进入 `rejected`；否则进入 `candidates`。

`_select_candidate()` 是选择策略的核心，它依次考虑 `readiness_score`、gate 状态排序、batch 状态排序和 run name。这保证候选选择不是“遇到第一个就用”，而是有稳定、可重复的排序规则。`_decision_status()` 把 selected run 和阈值组合成 `ready`、`review` 或 `blocked`，`_recommendations()` 则生成人可读的下一步推荐。

## Artifact 模块

`training_scale_run_decision_artifacts.py` 接管的是产物层：

- `write_training_scale_run_decision_json()`：将完整 report 写为 JSON，这是机器可消费的主证据。
- `write_training_scale_run_decision_csv()`：把决策状态、selected run、gate/batch/readiness、candidate/rejected 数量和 execute command 压成单行 CSV，便于 registry 或人工对比。
- `render_training_scale_run_decision_markdown()`：生成人可读 Markdown，展示 summary、execute command、rejected runs 和 recommendations。
- `render_training_scale_run_decision_html()`：生成浏览器可读 HTML，用 card 和 table 展示状态、被拒运行和建议。
- `write_training_scale_run_decision_outputs()`：统一调用 JSON/CSV/Markdown/HTML writer，并返回四个路径的字典。

这个 artifact 模块只消费 report，不读 comparison，不选候选，不生成 execute command，也不判断是否应该执行。这个边界很重要：如果以后调整页面展示，应该改 artifact 模块；如果调整选择策略，应该改主决策模块。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.training_scale_run_decision import write_training_scale_run_decision_outputs
```

原因是 `training_scale_run_decision.py` 从 `training_scale_run_decision_artifacts.py` 重新导入并导出了 writer/render 函数。这样 `scripts/decide_training_scale_run.py` 和其他旧消费方不需要同步改路径。

`tests/test_training_scale_run_decision.py` 新增了直接 identity 断言：

```python
self.assertIs(
    training_scale_run_decision.write_training_scale_run_decision_outputs,
    training_scale_run_decision_artifacts.write_training_scale_run_decision_outputs,
)
self.assertIs(
    training_scale_run_decision.render_training_scale_run_decision_html,
    training_scale_run_decision_artifacts.render_training_scale_run_decision_html,
)
```

这个断言保护的不是文本相似，而是函数对象本身相同。如果未来有人在旧模块里重新复制一份 writer 实现，测试会提醒新旧入口已经分叉。

## 测试覆盖

v173 的测试分五层：

- `tests.test_training_scale_run_decision`：覆盖决策构建、candidate/rejected 结构、execute command、JSON/CSV/Markdown/HTML 输出和 facade identity。
- 直接 smoke：检查旧 facade 与新 artifact 模块 writer/render 函数是同一对象，并记录主模块行数从 513 降到 308。
- 全量 unittest discovery：确认其他训练规模、registry、server、benchmark 和 release governance 消费方不受影响。
- source encoding hygiene：确认没有 BOM、语法错误或 Python 3.11 兼容问题。
- maintenance batching：确认模块压力状态为 `pass`，没有新 warn/critical 模块。

## 运行证据

v173 的运行截图归档在 `c/173`：

- `01-training-scale-run-decision-tests.png`：定向运行决策测试通过。
- `02-training-scale-run-decision-artifact-smoke.png`：旧 facade 和新 artifact 函数对象一致，且行数收束符合预期。
- `03-maintenance-smoke.png`：module pressure 为 `pass`，没有 warn 模块。
- `04-source-encoding-smoke.png`：编码、语法和目标 Python 兼容检查通过。
- `05-full-unittest.png`：全量 395 个测试通过。
- `06-docs-check.png`：README、`c/173`、讲解索引、source/test 关键词对齐。

这些截图是版本证据，临时 `tmp_v173_*` 日志和 `runs/*v173*` 输出会在提交前按 AGENTS 清理门禁删除。

## 边界说明

`training_scale_run_decision_artifacts.py` 不是新的决策器。它不知道什么 run 可以执行，也不解释 gate 或 batch 状态。它只把决策器交给它的 report 发布为文件。这意味着后续修改时的责任归属更清楚：策略变更找 `training_scale_run_decision.py`，输出格式变更找 `training_scale_run_decision_artifacts.py`。

## 一句话总结

v173 把 training scale run decision 的 JSON/CSV/Markdown/HTML 输出层独立成 `training_scale_run_decision_artifacts.py`，让 `training_scale_run_decision.py` 从 513 行降到 308 行，同时保持候选选择、拒绝理由、execute command、CLI 和旧 facade 导出不变。
