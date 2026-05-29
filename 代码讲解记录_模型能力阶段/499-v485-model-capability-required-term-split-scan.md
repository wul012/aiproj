# v485：model capability required-term split scan

## 本版目标和边界

v485 的目标是复核 v484 的“训练侧也没有复现”问题。v484 使用一个默认 term-level split，结果 train/holdout 两侧都没有 required-term continuation hit；v485 不扩大 benchmark，而是扫描多个 held-out term split，确认训练侧 uptake 是否可以在某些拆分下复现，以及是否出现 held-out uptake。

本版不宣称模型质量提升。只要 holdout hit 仍为 0，就只能说训练侧信号可复现，不能说模型学会了泛化。

## 关键新增文件

- `src/minigpt/model_capability_required_term_split_scan.py`
  - 核心扫描逻辑。
  - 输入 v483 micro-training report。
  - 自动生成多个 split specs。
  - 对每个 split 调用 v484 的 holdout builder，真实训练一个子 checkpoint。
  - 汇总 train/holdout hit count、最佳 split 和下一步建议。
- `src/minigpt/model_capability_required_term_split_scan_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright MCP 截图。
- `scripts/run_model_capability_required_term_split_scan.py`
  - CLI 入口，暴露训练参数和生成参数。
- `tests/test_model_capability_required_term_split_scan.py`
  - 用 monkeypatch fake holdout builder 覆盖 train-only、held-out、缺输入、输出产物和 split specs。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_split_scan.json
```

关键字段：

- `split_specs`
  - 每个 split 的 `id` 和 `holdout_terms`。
- `scan_rows`
  - 每个 split 一行。
  - 记录 holdout terms、train/holdout example 数、train/holdout continuation hit count、hit rate 和子报告路径。
- `summary`
  - `train_repro_split_count`：训练侧复现 required-term continuation hit 的 split 数。
  - `holdout_hit_split_count`：held-out 侧出现 required-term continuation hit 的 split 数。
  - `best_train_continuation_hit_count` 和 `best_split_id`：用于下一版稳定性复测。
  - `split_scan_decision`：区分 no uptake、train-slice only、held-out uptake。

## 运行流程

1. 读取 v483 micro-training report。
2. 从 examples 中抽取 unique required terms。
3. 构造多个 split：

```text
split-1 holdout=because,fixed,real
split-2 holdout=chain,four,text
split-3 holdout=data,loss,while
split-4 holdout=four,while
```

4. 对每个 split 调用 v484 holdout builder。
5. 每个 split 都训练一个独立 tiny checkpoint，并输出子报告。
6. 汇总所有 split 的 train/holdout continuation hit。

## v485 真实运行结果

真实配置：

```text
max_iters=800
eval_iters=1
batch_size=16
block_size=8
n_layer=1
n_head=1
n_embd=64
learning_rate=0.02
term_repeat=80
max_new_tokens=16
temperature=0.2
top_k=1
```

结果：

```text
status=pass
decision=required_term_split_scan_train_slice_only
split_scan_decision=train_slice_uptake_reproduced_without_holdout
split_count=4
train_repro_split_count=2
holdout_hit_split_count=0
best_train_continuation_hit_count=4
best_holdout_continuation_hit_count=0
best_split_id=split-4
model_quality_claim=not_claimed
```

解释：v485 证明训练侧 uptake 不是完全随机消失，部分 split 可以复现；但 held-out 仍然没有命中，所以 v483-v485 还处在“训练样本/拆分敏感信号”阶段。

## 测试覆盖

新增测试覆盖：

- fake split 中只训练侧命中时，报告必须输出 `required_term_split_scan_train_slice_only`。
- fake split 中 held-out 命中时，报告必须输出 `required_term_split_scan_holdout_uptake_observed`。
- source 没有 examples 时，报告必须 fail。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。
- 默认 split specs 必须去重。
- 空 rows summary 必须稳定输出 no rows decision。

这些测试保护 v485 的扫描决策，不依赖真实 PyTorch 训练速度。

## 运行证据

运行证据位于：

```text
e/485/解释/model-capability-required-term-split-scan/
e/485/图片/01-model-capability-required-term-split-scan.png
e/485/解释/model-capability-required-term-split-scan-snapshot.md
```

其中 `splits/` 下保存每个子 split 的完整 holdout report 和训练产物。

## 一句话总结

v485 证明 required-term 训练侧信号可以在部分 split 中复现，但 held-out 泛化仍为 0，下一步应对最佳 split 做多 seed 稳定性复测。
