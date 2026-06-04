# v838：bounded objective training run

## 本版目标和边界

v838 的目标是用 v837 的 direct-only seed corpus 真跑一次小型训练，生成一个可以被后续 replay 消费的 checkpoint。v837 只生成了训练文本；v838 让这批文本进入真实 `scripts/train.py` 流程，产出 checkpoint、tokenizer、metrics、manifest、sample 和 prepared corpus。

本版不做 replay，也不声称模型质量提升。它只证明“bounded objective seed 可以被训练成一个完整 checkpoint”。

## 前置链路

输入来自 v837：

- `bounded_objective_seed_ready=True`
- `example_count=18`
- `direct_example_count=18`
- `carry_forward_example_count=0`
- `proposed_next_artifact=model_capability_route_promotion_bounded_objective_training_run`

这意味着 v838 的训练输入是 direct objective corpus，而不是之前失败路线里的 carry-forward 或 forced-prefix 样本。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_training_run.py`
  - 读取 v837 seed summary 和真实 run 目录，检查 checkpoint、metrics、manifest 等训练产物。
- `src/minigpt/model_capability_route_promotion_bounded_objective_training_run_artifacts.py`
  - 渲染 JSON、CSV、TXT、Markdown 和 HTML 报告。
- `scripts/build_model_capability_route_promotion_bounded_objective_training_run.py`
  - CLI 入口，支持 run 目录保留、`--require-training-ready` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_training_run.py`
  - 用 fake run 覆盖正常训练证据、缺 checkpoint、seed 含 carry-forward、输出和 CLI。
- `e/838/解释/model-capability-route-promotion-bounded-objective-training-run/run/`
  - 真实训练产物目录。
- `e/838/图片/v838-bounded-objective-training-run-html.png`
  - Playwright MCP 截图。

## 训练输入和参数

训练输入是 v837 的 corpus：

```text
e/837/解释/model-capability-route-promotion-bounded-objective-seed/model_capability_route_promotion_bounded_objective_seed_corpus.txt
```

核心训练参数：

```text
tokenizer=char
batch_size=8
block_size=64
max_iters=40
eval_interval=10
eval_iters=5
learning_rate=0.001
n_layer=2
n_head=2
n_embd=64
seed=1838
device=cpu
```

这是一个受控 tiny run，不追求大模型能力，只追求产生可复核 checkpoint 并为下一步 replay 提供输入。

## 训练产物校验

builder 检查 11 类条件：

- objective seed 必须 pass。
- `bounded_objective_seed_ready` 必须为 True。
- direct examples 必须覆盖所有 examples。
- `carry_forward_example_count` 必须为 0。
- `checkpoint.pt` 必须存在。
- `tokenizer.json` 必须存在。
- `metrics.jsonl` 必须存在。
- `run_manifest.json` 必须存在。
- `prepared_corpus.txt` 必须存在。
- metrics 至少有首尾两条记录。
- train config 必须记录正数 `max_iters`。

这些检查保证 v838 不是只跑了一条命令，而是完整形成了后续 replay 可以依赖的训练证据。

## 关键结果

真实训练输出：

```text
step=1  train_loss=3.0520 val_loss=3.1011
step=40 train_loss=1.4958 val_loss=1.7003
```

报告摘要：

```text
bounded_objective_training_ready=True
final_step=40
final_train_loss=1.4957764148712158
final_val_loss=1.7002859115600586
train_loss_delta=-1.556213
objective_example_count=18
direct_example_count=18
model_quality_claim=training_artifact_only
```

loss 下降说明训练过程有效完成，但模型是否真的能在 bounded replay 中输出 `fixed/loss`，还必须由下一版 replay/comparison 判断。

## 测试覆盖

聚焦测试覆盖：

- fake run 产物完整时，training evidence ready。
- 删除 checkpoint 时失败。
- seed summary 出现 carry-forward 时失败。
- artifact writer 和 CLI 能输出全部格式。

本版聚焦测试结果是 `4 passed`。

## 运行证据

HTML 证据截图保存到：

```text
e/838/图片/v838-bounded-objective-training-run-html.png
```

页面展示 artifact 表，并明确写出该 checkpoint 仍需要 bounded replay comparison 才能形成模型能力结论。

## 一句话总结

v838 把 v837 的 direct-only objective seed 训练成了真实 checkpoint，但仍把能力判断关在下一步 bounded replay 之后。
