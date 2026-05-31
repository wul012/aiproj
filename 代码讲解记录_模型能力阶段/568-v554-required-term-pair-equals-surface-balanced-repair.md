# v554 required-term pair equals-surface balanced repair 代码讲解

## 本版目标和边界

v552 的 `equals_surface_fixed_repair` 是单边 fixed 修复，真实结果是 fixed 命中了、loss 没命中。v554 改为 balanced repair：fixed/loss 在 equals surface 上对称出现，测试 seed `1535` 是否能同时保持两个分支。

本版不扩 seed，不做大 sweep，也不把负结果藏起来。它只检验 v552 之后最自然的修复假设：把 fixed/loss 样本做对称，是否就能 pair-full。

## 前置链路

- v551：定位 `fixed=` surface 的 fixed miss。
- v552：fixed-biased repair 让 fixed 命中，但 loss miss。
- v553：先拆出 corpus 模块，降低继续新增 corpus mode 的维护风险。

v554 在 v553 的新模块上新增 balanced mode。

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - `PAIR_COEXISTENCE_CORPUS_MODES` 加入 `equals_surface_balanced_repair`。
  - `build_pair_coexistence_refresh_corpus()` 分派到 `_extend_equals_surface_balanced_repair()`。
  - `source_prompts()` 对该 mode 返回 `fixed=` / `loss=`。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 balanced mode 测试，使用逐行精确计数保护 `fixed=fixed` 与 `loss=loss` 对称。

## Corpus 设计

balanced mode 的核心片段：

```text
fixed=fixed
loss=loss
fixed=f
loss=l
fixed=fi
loss=lo
fixed=fix
loss=los
fixed=fixed
loss=loss
prompt=fixed=target=fixed
prompt=loss=target=loss
```

它比 v552 少了 fixed 偏置，增加了“不要串到另一分支”的负向提示。

## 真实结果

真实运行：

```text
pair_full_seed_count=0
pair_full_seed_rate=0.0
```

case rows 显示：

```text
fixed= -> generated loss-like continuation, continuation_hit=False
loss=  -> generated loss continuation, continuation_hit=True
```

所以 balanced corpus 没有解决问题，只是把 v552 的 loss miss 转成了 fixed miss。

## 测试覆盖

测试覆盖：

- balanced corpus mode 可生成。
- `fixed=fixed` 与 `loss=loss` 精确行数对称。
- 防止该 mode 混入 colon-immediate 形式。
- 既有 refresh/stability 测试继续通过，证明新增 mode 没破坏旧模式。

## 归档角色

`e/554` 保存真实训练输出、seed `1535` checkpoint、tokenizer、metrics、generation-profile replay sidecar、HTML 截图和 snapshot。它是第二个修复负结果，用于证明 equals surface 的 pair-full 不能靠简单样本比例解决。

一句话总结：v554 把 equals-surface 修复从单边 fixed 推到 balanced，但真实结果仍失败，下一步应比较 v552/v554 的分支摆动并考虑更强的分支隔离。
