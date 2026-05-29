# v486：model capability required-term split seed stability

## 本版目标和边界

v486 的目标是复测 v485 的最佳 split 是否稳定。v485 的 `split-4` 训练侧可以达到 `4` 个 required-term continuation hit，但 held-out hit 为 `0`；v486 固定这个 split，只改变 seed，观察训练侧信号是否能稳定复现。

本版不换 benchmark、不扩大模型、不宣称模型质量提升。它只回答：v485 的最佳训练侧信号是否跨 seed 稳定。

## 前置能力

本版承接：

- v483
  - 全量 scaffold-to-term 微训练出现 `4/20` continuation hit。
- v484
  - 默认 held-out split 下 train/holdout 都没有命中。
- v485
  - 多 split 扫描发现 `split-4` 训练侧最好，train hit 为 `4`，held-out hit 为 `0`。

v486 只复测最佳 split，不引入新训练目标。

## 关键新增文件

- `src/minigpt/model_capability_required_term_split_seed_stability.py`
  - 核心 seed stability 逻辑。
  - 输入 v485 split-scan report。
  - 找到 `summary.best_split_id` 对应的 scan row。
  - 解析 v483 micro-training report。
  - 对多个 seed 调用 v484 holdout builder。
  - 汇总训练侧是否复现、held-out 是否仍为 0。
- `src/minigpt/model_capability_required_term_split_seed_stability_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_required_term_split_seed_stability.py`
  - CLI 入口。
  - 支持 `--seed` 重复传入，也支持覆盖训练参数。
- `tests/test_model_capability_required_term_split_seed_stability.py`
  - 用 fake holdout builder 覆盖稳定训练侧、部分训练侧、held-out 命中、缺 source、输出产物和路径定位。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_split_seed_stability.json
```

关键字段：

- `best_split`
  - 来自 v485 的最佳 split row。
  - 本次真实运行中是 `split-4`，holdout terms 为 `four/while`。
- `settings`
  - 继承 v485 的训练参数，并记录 seed 列表。
- `seed_rows`
  - 每个 seed 一行。
  - 记录 train/holdout example count、train/holdout continuation hit count、hit rate 和子报告路径。
- `summary`
  - `train_repro_seed_count`：训练侧出现 required-term continuation hit 的 seed 数。
  - `holdout_hit_seed_count`：held-out 出现 required-term continuation hit 的 seed 数。
  - `stable_train_repro`：所有 seed 是否都复现训练侧命中。
  - `stable_holdout_zero`：所有 seed 是否都保持 held-out 0。

## 运行流程

1. 读取 v485 split-scan JSON。
2. 找到最佳 split：

```text
best_split_id=split-4
holdout_terms=four, while
```

3. 解析 v483 micro-training report 路径。
4. 对 `785/1785/2785` 三个 seed 分别调用 v484 holdout builder。
5. 每个 seed 都训练一个独立 tiny checkpoint。
6. 汇总 seed rows，判断训练侧信号是否稳定。

## v486 真实运行结果

真实结果：

```text
status=pass
decision=required_term_seed_stability_train_slice_partial
seed_stability_decision=train_slice_uptake_partial_without_holdout
seed_count=3
train_repro_seed_count=1
holdout_hit_seed_count=0
min_train_continuation_hit_count=0
max_train_continuation_hit_count=4
stable_train_repro=False
stable_holdout_zero=True
model_quality_claim=not_claimed
```

seed 行：

```text
785  -> train_hits=4 holdout_hits=0
1785 -> train_hits=0 holdout_hits=0
2785 -> train_hits=0 holdout_hits=0
```

解释：训练侧 signal 只在一个 seed 上复现，不稳定；held-out 始终为 0。这个结果把 v485 的边界继续收紧：当前需要先改善语料构造，而不是继续做更大的 held-out claim。

## 测试覆盖

新增测试覆盖：

- 所有 seed 都训练侧命中、held-out 为 0 时，输出 stable train-slice decision。
- 只有部分 seed 训练侧命中时，输出 partial decision。
- 任一 seed 出现 held-out 命中时，输出 holdout uptake seen。
- micro source 缺失时报告失败，`--require-pass` 返回非零。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。
- 输入路径支持文件和目录。

这些测试确保 v486 的结论来自 seed 级汇总，而不是单个最佳 run 的偶然结果。

## 运行证据

运行证据位于：

```text
e/486/解释/model-capability-required-term-split-seed-stability/
e/486/图片/01-model-capability-required-term-split-seed-stability.png
e/486/解释/model-capability-required-term-split-seed-stability-snapshot.md
```

`seeds/` 下保存每个 seed 的完整 holdout report 和训练产物。

## 一句话总结

v486 证明 v485 的最佳 split 训练侧信号只在部分 seed 上复现，held-out 始终为 0，因此下一步应改微训练语料，而不是扩大模型能力结论。
