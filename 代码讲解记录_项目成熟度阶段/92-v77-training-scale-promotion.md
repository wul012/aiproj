# v77 training scale promotion acceptance 代码讲解

## 本版目标

v77 的目标是把 v76 完成后的 handoff 结果再验收一次，判断这次真实训练执行能不能进入后续项目证据链。

v76 已经能读取 workflow decision，并在显式 `--execute` 后真实运行选中的训练命令。但 handoff 的重点是“命令有没有跑、关键产物有没有出现”。v77 往后推进一层：读取 handoff 背后的 gated scale run、batch、per-variant portfolio 和变体内的训练证据，给出：

```text
promoted: 可以作为后续对比或成熟度证据
review: 主链路完成，但缺少部分应检查证据
blocked: 执行、gate、batch 或变体失败，不能继续推广
```

本版明确不做：

- 不重新训练模型。
- 不修改 handoff、batch 或 portfolio 产物。
- 不把临时训练 checkpoint 提交进仓库。
- 不绕过 v75/v76 的 workflow/decision/handoff 边界。

## 前置链路

v77 接在 v75 和 v76 后面：

```text
v75 training_scale_workflow
 -> v76 training_scale_handoff
 -> gated training_scale_run
 -> training_portfolio_batch
 -> variant training_portfolio
 -> v77 training_scale_promotion
```

这让项目从“能受控执行建议”推进到“能判断执行结果是否值得推广”。

## 关键新增文件

```text
src/minigpt/training_scale_promotion.py
scripts/build_training_scale_promotion.py
tests/test_training_scale_promotion.py
c/77/图片
c/77/解释/说明.md
```

README、`c/README.md` 和项目成熟度阶段 README 也同步加入 v77 索引。

## 核心模块

### `load_training_scale_handoff`

输入可以是：

```text
runs/training-scale-workflow/handoff-executed/training_scale_handoff.json
runs/training-scale-workflow/handoff-executed/
```

传入目录时会自动寻找 `training_scale_handoff.json`。读取后附加 `_source_path`，用于定位同目录输出和后续报告里的来源。

### `build_training_scale_promotion`

这是 v77 主函数。它先解析 handoff 里的 command：

- `--project-root`：用于解析相对路径。
- `--out-root`：用于定位 `training_scale_run.json` 和 batch 输出。

然后读取这些证据：

```text
training_scale_handoff.json
training_scale_run.json
batch/training_portfolio_batch.json
batch/variants/*/training_portfolio.json
```

每个 variant portfolio 继续检查关键训练证据：

```text
checkpoint
run_manifest
eval_suite
generation_quality
benchmark_scorecard
dataset_card
registry
maturity_summary
maturity_narrative
```

这些字段不是装饰字段，而是决定 promotion 状态的证据：checkpoint 说明训练确实落盘，run manifest 说明训练可复现，eval/generation/scorecard 说明模型输出被评估，dataset card 说明数据可追溯，registry/maturity/narrative 说明它能进入项目级证据链。

## 状态判定

v77 的输出状态有三种：

```text
blocked
review
promoted
```

判定规则：

- handoff 没有完成、return code 非 0、scale run 没完成、batch 没完成，进入 `blocked`。
- 主执行完成但 variant 缺少 checkpoint、manifest、scorecard、dataset card、registry 或 maturity evidence，进入 `review`。
- handoff、scale run、batch 和所有 required variant artifacts 都齐全，进入 `promoted`。

这比 v76 更严格：v76 只确认执行命令和几个关键路径；v77 会继续向 variant 内部看，确认这次训练是否能被后续对比和成熟度模块消费。

## 输出产物

CLI：

```powershell
python scripts/build_training_scale_promotion.py runs/training-scale-workflow/handoff-executed --out-dir runs/training-scale-workflow/promotion
```

输出：

```text
training_scale_promotion.json
training_scale_promotion.csv
training_scale_promotion.md
training_scale_promotion.html
```

JSON 是后续脚本最稳定的输入；CSV 方便扫多次 promotion；Markdown 适合代码讲解；HTML 用于浏览器验收和截图归档。

CLI 默认在 `blocked` 时返回非零退出码；需要只写报告时可以用 `--no-fail`。

## 测试覆盖

`tests/test_training_scale_promotion.py` 覆盖：

- 完整 handoff、scale run、batch 和 variant evidence 会得到 `promoted`。
- handoff 失败会得到 `blocked`，并生成阻断建议。
- 主链路完成但缺少 registry 或 maturity narrative 会得到 `review`。
- JSON/CSV/Markdown/HTML 输出会落盘，HTML 对 `<Promotion>` 做转义。

测试里的训练树是轻量 fixture，不跑真实 PyTorch；真实 tiny workflow -> handoff execute -> promotion smoke 放在 `c/77` 证据链里完成。

## 运行归档

`c/77` 保存本版截图和解释：

```text
c/77/图片
c/77/解释/说明.md
```

截图中既有单元测试和结构检查，也有真实 tiny workflow/handoff/promotion smoke。真实训练产物在 `tmp/v77-smoke` 下生成，并在提交前按 cleanup gate 删除，仓库只保留截图和说明。

## 一句话总结

v77 把 MiniGPT 从“能受控执行训练建议”推进到“能验收执行结果是否可以进入项目级证据链”。
