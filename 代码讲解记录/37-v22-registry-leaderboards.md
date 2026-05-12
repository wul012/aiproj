# v22 Registry Leaderboards 代码讲解

## 这一版解决什么问题

v21 以后，registry 已经能记录每个实验 run 的人工备注和 tags。
但是只看表格时，还要人自己比较 `best_val_loss`，判断哪个 run 当前最好、其他 run 差多少。

v22 做的是一个很小但很实用的工程增强：

```text
多个 run
 -> 读取每个 run 的 best_val_loss
 -> 按 loss 从小到大排序
 -> 给每个 run 写入 rank
 -> 计算它与最佳 run 的 delta
 -> 输出 loss_leaderboard
 -> 同步到 JSON/CSV/SVG/HTML/CLI
```

这让 registry 从“实验清单”更进一步变成“实验排行榜”。

## 核心文件

```text
src/minigpt/registry.py
scripts/register_runs.py
tests/test_registry.py
```

## 数据结构变化

`build_run_registry` 现在不再直接把 `RegisteredRun.to_dict()` 塞进结果，而是先转成可补充字段的字典列表：

```python
run_rows = [run.to_dict() for run in runs]
loss_leaderboard = _annotate_loss_leaderboard(run_rows)
```

之后 registry 顶层新增：

```python
"loss_leaderboard": loss_leaderboard
```

每个 run 字典也会新增三个字段：

```text
best_val_loss_rank
best_val_loss_delta
is_best_val_loss
```

含义分别是：

```text
rank: 当前 run 按 best_val_loss 排第几
delta: 当前 run 的 best_val_loss - 最佳 run 的 best_val_loss
is_best: 是否就是当前 best_val_loss 最低的 run
```

## 排名逻辑

核心函数是 `_annotate_loss_leaderboard`。

它先给每个 run 设置默认值：

```python
run["best_val_loss_rank"] = None
run["best_val_loss_delta"] = None
run["is_best_val_loss"] = False
```

这样即使某个 run 没有 `best_val_loss`，输出结构也稳定，不会因为字段缺失导致 CSV 或 HTML 报错。

然后筛出有 loss 的 run：

```python
candidates = [
    run
    for run in runs
    if _as_optional_float(run.get("best_val_loss")) is not None
]
```

排序规则是：

```python
candidates.sort(key=lambda run: (_as_optional_float(run.get("best_val_loss")) or float("inf"), str(run.get("name") or "")))
```

先按 loss 小的排前面，如果 loss 一样，再按名字排序，保证结果稳定。

最后以第一名的 loss 作为基准：

```python
best_loss = _as_optional_float(candidates[0].get("best_val_loss")) or 0.0
```

每个 run 的 delta 就是：

```python
delta = loss - best_loss
```

所以第一名的 delta 总是 `0.0`，第二名以后表示“比最佳 loss 高多少”。

## 输出到 CSV

`write_registry_csv` 新增了这些列：

```text
best_val_loss_rank
best_val_loss_delta
is_best_val_loss
```

这让 registry 的 CSV 可以直接拿去做表格筛选或画图。

## 输出到 SVG

`write_registry_svg` 原来只画 loss bar 和 artifact bar。
v22 额外把 rank 和 delta 写到每一行：

```text
#1
0.95 (+0)
```

这样即使只看静态 SVG，也能快速知道谁是当前最佳 run。

## 输出到 HTML

HTML 表格新增 `Rank` 列，并在 `Best Val` 单元格下方显示 delta。

每一行还新增排序用的 data 属性：

```text
data-rank
data-delta
```

排序下拉框新增：

```text
Rank
Loss Delta
```

默认排序也从 `Best Val` 改为 `Rank`，因为对用户来说 `#1`、`#2` 比原始 loss 数值更直观。

## Leaderboard 面板

v22 新增 `_loss_leaderboard_html`，在表格后面生成一个简短的排行榜：

```text
Loss Leaderboard
1. #1 low-loss-review 0.95 / +0 / quality=warn / eval=3
2. #2 clean-candidate 1.1 / +0.15 / quality=pass / eval=3
```

这个面板只展示前 8 个 run，避免实验很多时页面太长。

## 命令行输出

`scripts/register_runs.py` 新增：

```python
print("loss_leaderboard=" + json.dumps(registry.get("loss_leaderboard", []), ensure_ascii=False))
```

所以跑完注册脚本后，终端马上能看到排行榜摘要，不一定要打开 HTML。

## 测试覆盖

`tests/test_registry.py` 覆盖了这些点：

```text
build_run_registry 会生成 loss_leaderboard
最佳 run 排名为 1
非最佳 run 有正确 delta
CSV 包含 rank/delta 字段
SVG 包含 #1 和 +0
HTML 包含 Rank 列、Loss Leaderboard、rank/delta 排序项和 data 属性
```

## 一句话总结

v22 把 registry 从“把实验都列出来”推进到“直接告诉你当前谁最好，以及其他实验差多少”，这是实验复盘和模型迭代非常关键的一层。
