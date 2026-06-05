# v873：bounded objective loss signal bridge target-only memory training run

## 本版目标和边界

v873 的目标是把 v872 target-only memory patch corpus 训练成真实 checkpoint，并生成训练证据。上一版只是数据修补，本版才真正进入模型训练。

本版不修改 v836 objective contract，不做 replay，不把 loss 下降或 sample 变好解释成能力恢复。它只回答一个问题：`v872 corpus 能不能稳定训练出一个可被后续 replay 消费的 checkpoint`。

## 前置链路

```text
v871 persisted label echo diagnostic
 -> v872 target-only memory patch corpus
 -> v873 real CPU training run
 -> v874 target-only memory replay comparison
```

这条链路的工程意义是把“诊断 -> 修补语料 -> 真实训练 -> 同契约回放”拆清楚。v873 只负责第三步。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_training_run.py`
  - v873 的核心证据适配模块。
  - 读取 target-only memory patch summary 和真实 run 目录。
  - 将 v872 patch 的 ready、example count、decoder anchor 等字段映射到既有 loss-signal bridge training-run 证据模型。
  - 输出 `bounded_objective_loss_signal_bridge_target_only_memory_training_ready`、`final_step`、`final_train_loss`、`final_val_loss`、`train_loss_delta`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_training_run_artifacts.py`
  - 复用已有 training-run renderer。
  - 只做标题和 ready 字段替换，避免复制一套大 HTML/Markdown 渲染器。

- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_training_run.py`
  - CLI 入口。
  - 支持 `--target-only-memory-patch`、`--run-dir`、`--out-dir`、`--require-training-ready`、`--force`。
  - `prepare_output_dir()` 会保留 run 子目录，避免生成 evidence 时误删刚训练出的 checkpoint。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_training_run.py`
  - 覆盖 ready 报告、patch not ready 阻断、writer 和 CLI。

- `e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/`
  - v873 真实训练和证据目录。

## 核心数据结构

v873 输入不是裸 corpus，而是 v872 patch report：

```text
bounded_objective_loss_signal_bridge_target_only_memory_patch_ready=True
patch_example_count=24
target_only_example_count=14
prompt_target_memory_count=3
label_target_memory_count=3
decoder_anchor_example_count=0
```

`_adapt_patch()` 会把它映射成已有 training-run 模型能理解的字段：

```text
bounded_objective_loss_signal_bridge_ready
bridge_example_count
loss_signal_bridge_example_count
decoder_anchor_example_count
bridged_corpus_char_count
```

这个适配的好处是训练证据解析、checkpoint 检查、metrics 读取、artifact 表格都复用旧链路。新增模块只表达 v873 的语义差异，不制造第二套训练治理系统。

## 真实训练命令

```text
python scripts/train.py
  --prepared-data e/872/解释/bounded-objective-loss-signal-bridge-target-only-memory-patch/bounded_objective_loss_signal_bridge_target_only_memory_patch_corpus.txt
  --out-dir e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/run
  --tokenizer char
  --batch-size 8
  --block-size 64
  --max-iters 180
  --eval-interval 10
  --eval-iters 5
  --learning-rate 0.001
  --train-ratio 0.9
  --n-layer 2
  --n-head 2
  --n-embd 64
  --dropout 0.0
  --seed 1873
  --device cpu
  --sample-prompt "Answer with exactly two tokens: fixed loss answer:"
  --sample-tokens 12
  --sample-temperature 0.8
  --sample-top-k 20
```

训练输出：

```text
final_step=180
final_train_loss=0.9454461932182312
final_val_loss=0.8332666158676147
train_loss_delta=-2.710383
```

## 样本输出解释

v873 的 sample 是：

```text
Answer with exactly two tokens: fixed loss answer: fixed los
a
```

它比 v869 的 `fansweved l` 更接近目标词面，说明 target-only memory corpus 对短目标有学习信号。但它还没有证明 replay 通过：sample prompt 只是一个观察窗口，真正的能力判定必须由 v874 对 v836 contract 的三条 cases 做同口径 replay。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_training_run.py -q -o cache_dir=runs/pytest-cache-v873-focus
```

结果：

```text
3 passed
```

测试保护的点：

- patch ready 时 training run report 必须 pass。
- patch not ready 时必须 fail，不能用坏 patch 伪造训练证据。
- writer 和 CLI 必须输出 JSON、CSV、TXT、Markdown、HTML。
- summary 必须路由到 `bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison`。

## 运行证据

- 解释目录：`e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/`
- 真实 run 目录：`e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/run/`
- 截图目录：`e/873/图片/`
- Playwright MCP 截图：`e/873/图片/v873-bounded-objective-loss-signal-bridge-target-only-memory-training-run-html.png`

## 一句话总结

v873 把 target-only memory patch 变成真实可回放 checkpoint，但仍把能力判断留给下一版同契约 replay。
