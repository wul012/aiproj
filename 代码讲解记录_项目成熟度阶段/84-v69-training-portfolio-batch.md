# 第六十九版代码讲解：Training Portfolio Batch Matrix

## 本版目标、来源和边界

v69 的目标是把 v67 的单次 training portfolio 和 v68 的多 portfolio 对比，继续向前收成一个 batch matrix：一次声明多组训练 variant，统一生成每组的 portfolio 报告，并自动把这些 portfolio 交给 v68 comparison 做 baseline 对比。

它解决的问题是：后续真正跑“大语料 vs 小样本”“不同上下文长度”“不同模型宽度”“不同 seed”时，不再手工复制多条 `run_training_portfolio.py` 和 `compare_training_portfolios.py` 命令。

本版不做这些事情：

- 不自动下载或扩充训练语料。
- 不替代 v67 的单 run pipeline；每个 variant 仍然调用同一套 portfolio plan。
- 不替代 v68 的 comparison；batch 只是自动衔接 comparison。
- 默认 smoke 仍然可 dry-run，避免每次测试都进行耗时训练。

## 本版接在哪条链路后面

v67 提供单次端到端 portfolio：

```text
source -> prepare/train/eval/quality/scorecard/card/registry/maturity -> training_portfolio.json
```

v68 提供多个 portfolio 的 baseline comparison：

```text
training_portfolio.json x N -> training_portfolio_comparison.json/csv/md/html
```

v69 在两者上层加 batch matrix：

```text
variant matrix
 -> portfolio plan/result x N
 -> comparison/training_portfolio_comparison.*
 -> training_portfolio_batch.*
```

## 关键新增文件

### `src/minigpt/training_portfolio_batch.py`

这是 v69 的核心模块。

关键函数：

- `load_training_portfolio_batch_variants(path)`：读取 variant JSON。既支持顶层 list，也支持 `{ "variants": [...] }`。
- `build_training_portfolio_batch_plan(...)`：根据 sources、out_root 和 variants 生成 batch plan。每个 variant 内部都会调用 `build_training_portfolio_plan`。
- `run_training_portfolio_batch_plan(...)`：按 variant 顺序 dry-run 或 execute，并为每个 variant 写出 `training_portfolio.json/md/html`。如果未禁用 comparison，则继续调用 v68 的 `build_training_portfolio_comparison`。
- `write_training_portfolio_batch_outputs(...)`：输出 batch 级 JSON/CSV/Markdown/HTML。

核心字段：

- `variants`：计划中的 variant 列表，每项包含 `name`、`description`、`out_root`、`portfolio_path`、`config` 和 `portfolio_plan`。
- `variant_results`：运行后的 variant 摘要，包含状态、输出路径、artifact 数、完成 step 数。
- `comparison`：自动比较入口，记录 baseline、portfolio paths、out dir 和 CLI command。
- `comparison_outputs`：v68 comparison 写出的 JSON/CSV/Markdown/HTML 路径。
- `summary`：矩阵摘要，包括 variant 数、总 max iters、最大 block size、最大 n_embd、模型形状数量和 dataset version 数量。

### `scripts/run_training_portfolio_batch.py`

这是命令行入口。基础用法：

```powershell
python scripts/run_training_portfolio_batch.py data --out-root runs/training-portfolio-batch
```

可选参数：

- `--variants matrix.json`：读取自定义 variant 矩阵。
- `--baseline name`：指定 comparison 的 baseline。
- `--execute`：真正执行每个 portfolio pipeline；不加时只 dry-run。
- `--no-compare`：只生成 batch 和 per-variant portfolio，不写 comparison。

CLI 输出 `status`、`variant_count`、`comparison_status`、`summary`、`comparison_outputs` 和 batch 输出路径，方便截图和 CI/脚本检查。

### `tests/test_training_portfolio_batch.py`

测试覆盖：

- batch plan 能生成 variant matrix 和 comparison command。
- dry-run 能写出每个 variant 的 portfolio 报告，并自动生成 comparison。
- variant JSON 支持 list 和 `{variants: [...]}` 两种格式。
- 重复 variant 名称会报错，避免输出目录和 comparison 名称错位。
- HTML 渲染会转义 `<base>` 这类显示名。

这里还顺手处理了一个真实边界：Windows 路径不能包含 `< > : " / \ | ? *`。v69 的 `_safe_path_name` 会在派生目录名和默认 run_name 时替换非法字符，但报告里的展示名仍保留原始 variant name。

### `c/README.md` 和 `c/69`

用户要求从现在开始不再把运行截图和解释写入 `b/`，而是新建同级目录 `c/`。v69 已经按新规则归档：

```text
c/69/图片
c/69/解释/说明.md
```

同时 `AGENTS.md` 增加规则：`a/` 保留 v1-v31，`b/` 保留 v32-v68，v69 起使用 `c/`。

## 输入输出格式

variant JSON 可以写成：

```json
[
  {"name": "small", "max_iters": 50, "block_size": 64},
  {"name": "context", "max_iters": 50, "block_size": 96}
]
```

也可以写成：

```json
{
  "variants": [
    {"name": "small", "seed": 1},
    {"name": "wide", "n_embd": 96, "seed": 2}
  ]
}
```

每个 variant 可以覆盖训练参数，例如 `max_iters`、`batch_size`、`block_size`、`n_layer`、`n_head`、`n_embd`、`learning_rate`、`seed`、`sample_tokens` 等。没有覆盖的字段使用 batch 级默认值。

输出产物：

- `training_portfolio_batch.json`：机器可读 batch 证据。
- `training_portfolio_batch.csv`：variant matrix 表格。
- `training_portfolio_batch.md`：审阅说明。
- `training_portfolio_batch.html`：浏览器展示入口。
- `variants/<name>/training_portfolio.*`：每个 variant 自己的 v67 portfolio。
- `comparison/training_portfolio_comparison.*`：自动生成的 v68 portfolio comparison。

## 为什么这是收口而不是继续堆报告

v69 不是再做一个孤立 dashboard。它把已有能力串起来：

- v67 负责“每个实验怎么完整跑”。
- v68 负责“多个实验怎么比较”。
- v69 负责“多个实验怎么被统一声明、统一运行、统一进入比较”。

因此它更接近实际 AI 工程里的 experiment matrix：参数、数据、seed 和模型形状是变量，portfolio 和 comparison 是证据产物。

## 测试如何保护链路

单测不执行真实训练，而是检查 dry-run 链路：

- 每个 variant 都会落到独立 out_root。
- 每个 out_root 都写出 `training_portfolio.json`。
- batch 会收集这些 portfolio path 并生成 comparison。
- 重复名称会失败，避免 comparison baseline 指错。
- HTML 转义保护浏览器报告。

这类测试能快速发现 matrix 参数、路径推导、输出文件、comparison 衔接和 HTML 展示被改坏的问题。

## 一句话总结

v69 把 MiniGPT 从“能比较多份训练组合报告”推进到“能统一规划、运行和比较一组训练组合实验矩阵”。
