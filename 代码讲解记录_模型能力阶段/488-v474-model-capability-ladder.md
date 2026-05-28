# v474：model capability ladder

## 本版目标和边界

v474 的目标是把模型能力观察从 v473 的“一组 baseline/candidate 对比”推进到“多训练预算阶梯”。前一版已经能比较 `max_iters=1` 和 `max_iters=4`，但它仍然只给出两个点；本版用 `max_iters=1,2,4` 三个 rung 形成一条 tiny training scale ladder。

本版不做大模型训练，不引入外部数据集，也不宣称 tiny CPU smoke 能证明真实生产模型质量。它只把训练步数、best validation loss、scorecard 分数和 generation-quality flags 放到同一份报告里，让“训练多一点是否有变化”变成可复核证据。

## 前置能力

本版复用已有链路：

- `scripts/run_tiny_standard_benchmark_smoke.py`
  - 单次 tiny 训练、eval suite、generation quality、pair batch、scorecard 的完整 smoke。
- v473 的能力指标思路
  - 把 `best_val_loss`、`final_val_loss`、scorecard、generation flags 一起视为模型能力观察字段。
- `report_utils`
  - 复用 `as_dict`、`number_or_none`、`write_json_payload`、`html_escape` 等公共工具，避免继续复制 renderer 细节。

## 关键新增文件

- `src/minigpt/model_capability_ladder.py`
  - 负责解析 `max_iters` 列表、读取 tiny smoke summary、构建 ladder report、计算趋势。
- `src/minigpt/model_capability_ladder_artifacts.py`
  - 负责 JSON/CSV/text/Markdown/HTML 输出。
- `scripts/run_model_capability_ladder.py`
  - CLI 入口，按 `max_iters` 阶梯依次调用真实 tiny benchmark smoke。
- `tests/test_model_capability_ladder.py`
  - 覆盖趋势判断、输出文件、失败 rung 和 CLI exit code。
- `e/474/解释/model-capability-ladder/`
  - 本版真实运行证据。

## 核心数据结构

最终报告是 `model_capability_ladder.json`，关键字段如下：

- `rows`
  - 每个训练步数一个 rung。
  - 记录 `max_iters`、`status`、`checkpoint_exists`、`best_val_loss`、`final_val_loss`、`scorecard_overall_score`、`generation_quality_total_flags`。
- `trend_summary`
  - 记录首尾差值和趋势判断。
  - `best_val_loss_delta_first_to_last` 小于 0 表示 loss 下降。
  - `score_delta_first_to_last` 大于 0 才表示 scorecard 分数提升。
  - `generation_flags_delta_first_to_last` 小于 0 才表示 flags 减少。
- `interpretation`
  - 固定写明 `model_quality_claim=not_claimed`。
  - 防止把 tiny smoke 误写成成熟模型质量证明。

## 核心流程

```text
run_model_capability_ladder.py
  -> parse max_iters_list
  -> for each max_iters:
       run_tiny_standard_benchmark_smoke.py
       read tiny_standard_benchmark_smoke_summary.json
  -> build_model_capability_ladder_report()
  -> write_model_capability_ladder_outputs()
```

`build_model_capability_ladder_report()` 只处理 summary，不直接启动训练；这样单测可以用 fixture 覆盖趋势逻辑，CLI 则负责真实 subprocess 执行。这个边界让功能更容易维护，也避免把 runner、renderer、判断逻辑塞进一个巨型文件。

## 趋势判断

本版提供几个最小但清楚的判断：

- `training_signal_and_eval_signal_improved`
  - loss 下降，并且 score 或 flags 也改善。
- `loss_improved_without_eval_improvement`
  - loss 下降，但 score 和 flags 没有改善。
- `eval_signal_improved_without_loss_improvement`
  - score 或 flags 改善，但 loss 没有下降。
- `no_observed_capability_gain`
  - 没有观察到明确收益。

v474 的真实结果是 `loss_improved_without_eval_improvement`。

## 真实运行结果

本版运行配置：

- Suite：`standard-zh`
- Case token cap：`4`
- Max iters：`1,2,4`
- Seed：`1337`
- Tiny model：`n_layer=1`、`n_head=1`、`n_embd=8`

结果：

| Max iters | Best val loss | Scorecard | Generation flags |
| ---: | ---: | ---: | ---: |
| 1 | 5.345132350921631 | 81.67 | 0 |
| 2 | 5.345132350921631 | 81.67 | 0 |
| 4 | 5.3419880867004395 | 81.67 | 0 |

解释：训练到 4 步时 loss 有轻微下降，但 scorecard 和 generation flags 没变，所以不能说模型能力明显提升。

## 测试覆盖

新增测试覆盖：

- loss、score、flags 同时改善时的趋势判断。
- 单个 rung 失败或缺少 loss 时报告失败。
- JSON/CSV/text/Markdown/HTML 输出全部生成。
- `max_iters` 列表必须非空、唯一、正整数。
- loss-only improvement 会被标记为 `loss_improved_without_eval_improvement`。

本版还跑了真实 ladder 命令，证据写入 `e/474`，并用 Playwright MCP 检查 HTML 报告。

## 一句话总结

v474 让 MiniGPT 从“能比较一个候选模型”推进到“能观察训练预算阶梯趋势”，但本次真实 tiny 结果仍然只显示轻微 loss 改善，没有出现可宣称的模型能力提升。
