# v23 Experiment Cards 代码讲解

## 这一版解决什么问题

v22 已经能在 registry 里比较多个 run，知道谁的 `best_val_loss` 最低、其他 run 差多少。
但如果要把某一个 run 交给别人看，仍然要打开很多文件：

```text
run_manifest.json
history_summary.json
dataset_quality.json
eval_suite.json
run_notes.json
registry.json
dashboard.html
```

v23 增加 `experiment_card`，把这些信息压缩成一张“实验卡”：

```text
单个 run 目录
 -> 读取训练、数据、评估、备注、registry 排名
 -> 生成 experiment_card.json
 -> 生成 experiment_card.md
 -> 生成 experiment_card.html
 -> dashboard / playground / registry 能识别并链接它
```

## 核心文件

```text
src/minigpt/experiment_card.py
scripts/build_experiment_card.py
tests/test_experiment_card.py
```

同时集成到：

```text
src/minigpt/manifest.py
src/minigpt/dashboard.py
src/minigpt/playground.py
src/minigpt/registry.py
```

## build_experiment_card 的输入

主函数是：

```python
build_experiment_card(run_dir, registry_path=None, title="MiniGPT experiment card")
```

它主要读取这些文件：

```text
train_config.json
history_summary.json
dataset_report.json
dataset_quality.json
eval_report.json
eval_suite/eval_suite.json
run_manifest.json
run_notes.json
registry.json（可选）
```

`registry_path` 是可选的。如果传入 registry，它会尝试根据 run 路径找到对应行，然后拿到：

```text
best_val_loss_rank
best_val_loss_delta
is_best_val_loss
registry note/tags
```

## 输出结构

实验卡 JSON 分成几块：

```text
summary
notes
data
training
evaluation
registry
artifacts
recommendations
warnings
```

`summary` 是最适合快速浏览的一层，例如：

```text
run_name
status
checkpoint_exists
best_val_loss
best_val_loss_rank
best_val_loss_delta
dataset_quality
eval_suite_cases
git_commit
total_parameters
```

## 状态判断

`_overall_status` 用很朴素的规则给 run 一个状态：

```text
缺 checkpoint 或 loss -> incomplete
缺 dataset quality -> needs-data-quality
数据质量不是 pass -> review
缺 eval suite -> needs-eval
否则 -> ready
```

这不是模型质量的最终判断，只是帮助你快速判断这个 run 是否“资料齐全，能进入复盘”。

## Recommendations

`_build_recommendations` 会根据当前资料给下一步建议。

例如：

```text
当前是 best-val 第一名 -> 建议作为当前参考 run
没有 dataset_quality -> 建议先生成数据质量报告
没有 eval_suite -> 建议跑固定 prompt 评估
没有 dashboard -> 建议生成 dashboard.html
```

这让实验卡不只是静态摘要，也能告诉你下一步该补什么。

## Markdown 和 HTML

`render_experiment_card_markdown` 面向 README、笔记、报告粘贴场景。

`render_experiment_card_html` 面向浏览器查看，页面包含：

```text
顶部统计卡
Notes
Data
Training
Evaluation
Registry
Recommendations
Artifacts
Warnings
```

HTML 输出会对文本做转义，避免 run note 里出现 `<script>` 这类内容时污染页面。

## CLI 脚本

新增脚本：

```powershell
python scripts/build_experiment_card.py --run-dir runs/minigpt --registry runs/registry/registry.json
```

默认输出到 run 目录：

```text
experiment_card.json
experiment_card.md
experiment_card.html
```

终端会打印：

```text
status
best_val_loss
rank
recommendations
outputs
```

## 与旧功能的关系

v23 没有替代 dashboard、playground 或 registry，而是补了一个“单个 run 的可交付摘要”：

```text
dashboard: 看一个 run 的所有产物
playground: 本地交互和命令入口
registry: 多个 run 横向比较
experiment card: 一个 run 的复盘/交付卡片
```

为了让它成为正式产物，v23 还把它加入了：

```text
manifest artifact spec
dashboard artifact list
playground link list
registry artifact count / card link
```

## 一句话总结

v23 把“这个 run 做得怎么样、数据和评估是否完整、它在 registry 里排第几、下一步该补什么”汇成一张实验卡，方便复盘、展示和继续迭代。
