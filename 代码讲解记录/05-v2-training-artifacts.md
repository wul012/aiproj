# 05 v2 训练产物和 resume 讲解

这一篇讲的是 v2 新增的 `src/minigpt/history.py`、`scripts/plot_history.py`，以及 `scripts/train.py` 里的训练产物和恢复训练逻辑。

v2 的目标是把训练从“跑一次、看控制台”升级成“可恢复、可追踪、可复盘”。

核心流程是：

```text
训练 step
 -> eval 得到 train_loss / val_loss
 -> 写入 metrics.jsonl
 -> 训练结束生成 history_summary.json
 -> 根据 metrics.jsonl 画 loss_curve.svg
 -> 用当前 checkpoint 生成 sample.txt
 -> 保存 model + optimizer + config
 -> 下次用 --resume 继续训练
```

先看训练记录：

```python
@dataclass(frozen=True)
class TrainingRecord:
```

它表示一次评估点，不是每个 batch 的记录。字段包括 `step`、`train_loss`、`val_loss` 和 `last_loss`。这样可以用很小的文件记录训练趋势。

写 JSONL：

```python
f.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")
```

JSONL 的好处是每一行都是一个独立 JSON 对象。训练中断时，前面已经写入的记录仍然容易读取；后续也可以一行一行追加。

读取历史：

```python
records.append(TrainingRecord(...))
```

读取时会把 JSON 字段重新转成 `TrainingRecord`。如果缺少必要字段，会抛出带行号的错误，便于定位损坏记录。

历史摘要：

```python
best = min(records, key=lambda record: record.val_loss)
```

`history_summary.json` 记录总评估次数、起止 step、最佳验证集 loss 和最后一次 loss。它适合被 README、看板或后续控制台读取。

loss 曲线：

```python
write_loss_curve_svg(records, args.out_dir / "loss_curve.svg")
```

这里选择 SVG 而不是依赖 matplotlib，是为了保持项目轻量。SVG 是文本文件，可以直接在浏览器或 GitHub 中查看，也方便版本管理。

resume 入口：

```python
parser.add_argument("--resume", type=Path, default=None)
```

`--resume` 接收上一次的 `checkpoint.pt`。训练脚本会从 checkpoint 旁边读取 `tokenizer.json`，避免 token id 和字符映射错位。

恢复模型和优化器：

```python
model.load_state_dict(checkpoint["model"])
optimizer.load_state_dict(checkpoint["optimizer"])
```

只恢复模型参数还不够。AdamW 优化器内部有动量状态，如果一起恢复，继续训练会更接近“同一场训练被暂停后继续”的语义。

继续 step：

```python
start_step = resume_step + 1
```

v2 把 `--max-iters` 理解成目标 step，而不是“额外再跑多少步”。例如 checkpoint 在 step 2，传 `--max-iters 4`，就会继续跑 step 3 和 step 4。

一句话总结：v2 让 MiniGPT 不再只是能训练，而是开始具备模型工程项目需要的运行记录、恢复训练和产物归档能力。
