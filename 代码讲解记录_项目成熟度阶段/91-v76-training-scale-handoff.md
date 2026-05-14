# v76 controlled training scale handoff 代码讲解

## 本版目标

v76 的目标是把 v75 workflow 生成的 `--execute` handoff command 变成可验证、可执行、可记录的受控执行证据。

v75 已经能把 v70-v74 收口成一个 workflow，并生成下一步命令。但命令仍然只是文本，人需要自己复制执行。v76 增加一个边界清晰的执行器：

```text
默认：只验证 handoff，不执行训练
显式 --execute：执行 handoff command，并记录执行结果与产物状态
```

本版明确不做：

- 不自动跑大规模训练。
- 不绕过 v75 decision。
- 不在 decision blocked 时强行执行。
- 不把临时训练产物提交进仓库；真实 smoke 产物在 cleanup gate 中删除。

## 前置链路

v76 接在 v75 后面：

```text
v75 training_scale_workflow
 -> decision/training_scale_run_decision.json
 -> selected execute command
 -> v76 training_scale_handoff
```

这让项目从“建议执行”推进到“可以受控执行并留下证据”。

## 关键新增文件

```text
src/minigpt/training_scale_handoff.py
scripts/execute_training_scale_handoff.py
tests/test_training_scale_handoff.py
c/76/图片
c/76/解释/说明.md
```

README、`c/README.md` 和项目成熟度阶段 README 也同步加入 v76 索引。

## 核心模块

### `load_training_scale_workflow`

输入可以是：

```text
runs/training-scale-workflow/training_scale_workflow.json
runs/training-scale-workflow/
```

传入目录时会自动寻找 `training_scale_workflow.json`。读取后附加 `_source_path`，用于定位同目录下的 decision 产物。

### `build_training_scale_handoff`

这是 v76 的主函数。关键参数：

- `workflow_path`：v75 workflow JSON 或目录。
- `execute`：是否真实执行，默认 false。
- `allow_review`：是否允许 decision_status=`review` 的候选进入 handoff，默认 true。
- `timeout_seconds`：执行超时。

主流程：

```text
1. 读取 workflow
2. 根据 workflow.decision_outputs.json 读取 decision
3. 提取 decision.execute_command
4. 判断 decision_status 是否允许执行
5. execute=false 时只记录 planned
6. execute=true 时运行命令并捕获 returncode/stdout/stderr/elapsed
7. 检查训练规模执行产物是否存在
8. 写出 handoff JSON/CSV/Markdown/HTML
```

## 执行边界

v76 的关键边界是“不默认执行”。没有 `--execute` 时，输出状态是：

```text
handoff_status=planned
```

它只证明命令存在且 decision 允许 handoff。加上 `--execute` 后才会运行 command：

```powershell
python scripts/execute_training_scale_handoff.py runs/training-scale-workflow --execute
```

如果 decision 是 `blocked`，或 `review` 但用户传了 `--no-allow-review`，handoff 会停在 blocked，不运行命令。

## 产物检查

执行后 v76 检查这些路径：

```text
training_scale_run.json
training_scale_run.html
batch/training_portfolio_batch.json
batch/training_portfolio_batch.html
batch/variants/*/training_portfolio.json
batch/variants/*/runs/*/checkpoint.pt
```

这些不是全部训练证据，但足够判断 selected profile 是否真的进入了 gated run、batch runner、portfolio pipeline 和 checkpoint 生成阶段。

## CLI

入口脚本：

```powershell
python scripts/execute_training_scale_handoff.py runs/training-scale-workflow
python scripts/execute_training_scale_handoff.py runs/training-scale-workflow --execute --timeout-seconds 900
```

输出：

```text
training_scale_handoff.json
training_scale_handoff.csv
training_scale_handoff.md
training_scale_handoff.html
```

CLI 在 `blocked`、`failed` 或 `timeout` 时返回非零退出码，方便后续自动化停住。

## 测试覆盖

`tests/test_training_scale_handoff.py` 覆盖：

- review 状态默认可以生成 planned handoff，但不执行。
- `allow_review=false` 时 review 会被阻断。
- `execute=true` 时能运行轻量命令并检查产物。
- 命令失败时记录 failed 和 returncode。
- HTML 转义 `<handoff>`，避免报告被输入文本破坏。

测试里执行的是轻量 artifact command，不跑真实训练；真实训练 smoke 放在 `c/76` 证据链里完成。

## 运行归档

`c/76` 保存本版截图和解释：

```text
c/76/图片
c/76/解释/说明.md
```

截图中既有 validation smoke，也有 tiny/max-variants=1 的真实 execute smoke。真实训练产物在 `tmp/v76-smoke` 下生成，并在提交前按 cleanup gate 删除，仓库只保留截图和说明。

## tiny corpus execution fix

真实 v76 execute smoke 首次暴露了一个计划源头问题：样例语料只有 507 个字符，原计划的 `block_size=64` 会让默认 90/10 split 后的验证集短于 `get_batch` 要求，训练脚本按设计报错。

所以本版同时修改 `src/minigpt/training_scale_plan.py`：

- `safe_block_size_for_char_count` 根据语料长度和默认 split 估算可训练的最大 context。
- `_fit_variant_contexts` 在生成 variant 时把过大的 `block_size` 降到安全范围。
- variant 和 matrix 写入 `context_adjustment`，让后续报告知道这不是隐藏改参，而是为了可执行性做的有证据调整。

本次真实 smoke 中，`scale-smoke` 从 `block_size=64` 降到 `block_size=48`，随后 handoff execute 返回 `returncode=0`，6 个预期 artifact 检查全部可用。

## 一句话总结

v76 把 MiniGPT 从“有训练执行建议”推进到“能受控执行建议并记录真实训练产物状态”。
