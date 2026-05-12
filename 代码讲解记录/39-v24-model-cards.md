# v24 Model Cards 代码讲解

## 这一版解决什么问题

v23 可以给单个 run 生成 `experiment_card`。
但当项目里有多个 run 时，还需要一个更高层的页面回答这些问题：

```text
当前项目一共有多少 run？
哪个 run 是当前 best-val 最好？
有多少 run 已经有 experiment card？
有多少 run 有 dataset quality / eval suite？
哪些 run 还需要复查？
这个项目适合什么用途，又有什么限制？
```

v24 新增 `model_card`，从 registry 和多张 experiment card 汇总项目级说明：

```text
registry.json
 -> 自动寻找每个 run 的 experiment_card.json
 -> 汇总 top runs / coverage / limitations / recommendations
 -> 输出 model_card.json
 -> 输出 model_card.md
 -> 输出 model_card.html
```

## 核心文件

```text
src/minigpt/model_card.py
scripts/build_model_card.py
tests/test_model_card.py
```

## build_model_card 的输入

主函数是：

```python
build_model_card(registry_path, card_paths=None, title="MiniGPT model card")
```

`registry_path` 是必需的，它提供：

```text
run_count
runs
best_by_best_val_loss
loss_leaderboard
quality_counts
tag_counts
dataset_fingerprints
```

`card_paths` 是可选的。
如果不传，代码会根据 registry 里的 run path 自动寻找：

```text
<run_dir>/experiment_card.json
```

## 输出结构

`model_card.json` 的主要结构是：

```text
summary
intended_use
limitations
coverage
quality_counts
tag_counts
dataset_fingerprints
top_runs
runs
recommendations
warnings
```

这和 experiment card 的分工不同：

```text
experiment card: 单个 run 的复盘卡
model card: 一组 run / 一个实验系列的项目级说明
```

## Run 汇总逻辑

`_build_run_summaries` 会遍历 registry 中每个 run。

如果找到了对应的 experiment card，就优先使用 card 里的：

```text
summary.status
notes.note
notes.tags
recommendations
```

如果没有 experiment card，就从 registry 字段推断状态。

状态推断规则在 `_derive_status` 里：

```text
缺 checkpoint 或 best_val_loss -> incomplete
缺 dataset_quality -> needs-data-quality
dataset_quality 不是 pass -> review
缺 eval_suite -> needs-eval
否则 -> ready
```

## Coverage

`_build_coverage` 会计算项目覆盖度：

```text
experiment_cards_found
experiment_card_coverage
quality_checked_runs
eval_suite_runs
checkpoint_runs
dashboard_runs
dataset_fingerprint_count
```

这部分回答的是“这个实验系列的证据链是否完整”。

例如：

```text
experiment_card_coverage = 1.0
```

表示 registry 里的每个 run 都有对应的 experiment card。

## Top Runs

`_top_runs` 优先读取 registry 的 `loss_leaderboard`。
这样 model card 的 top runs 和 registry HTML 的排行榜保持一致。

每个 top run 会展示：

```text
rank
name
status
best_val_loss
best_val_loss_delta
dataset_quality
eval_suite_cases
experiment_card link
```

## Recommendations

`_build_recommendations` 生成项目级建议。

常见建议包括：

```text
补齐缺失的 experiment cards
至少准备一个 ready run
复查 dataset quality 非 pass 的 run
给所有 run 跑固定 prompt eval suite
修复不可读的 experiment_card.json
```

这和 v23 的单 run 建议不同，v24 看的是整个实验系列是否完整。

## CLI 脚本

新增脚本：

```powershell
python scripts/build_model_card.py --registry runs/registry/registry.json --out-dir runs/model-card
```

输出：

```text
model_card.json
model_card.md
model_card.html
```

终端会打印：

```text
run_count
best_run
ready_runs
experiment_cards
outputs
```

## HTML 页面

`render_model_card_html` 生成一个本地浏览器页面，包含：

```text
顶部统计卡
Intended Use
Limitations
Top Runs
Coverage
Quality Counts
Tag Counts
Recommendations
All Runs
Warnings
```

HTML 会对 run name、note、tag 等内容做转义，避免用户输入污染页面。

## 一句话总结

v24 把多个实验 run 从“散落的实验卡”汇总成“项目级模型卡”，让这个 MiniGPT 项目更像一个可以交付、展示和复盘的 AI 工程作品。
