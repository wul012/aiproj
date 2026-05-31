# v546 required-term pair loss-calibrated top-k2 t0.8 代码讲解

## 本版目标和边界

v545 排除了短前缀 first-token boost。v546 新增一个更轻的 `colon_immediate_loss_calibrated` corpus mode：它不继续堆 `loss:l` 这类短 token，而是增加少量完整 `loss:loss` 映射和对比句，测试是否能修复 seed `1535` 的 fixed 偏置。

本版新增一个 corpus mode，并运行真实三 seed 实验；不修改模型结构和 replay 判断逻辑。

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 在 `PAIR_COEXISTENCE_CORPUS_MODES` 中加入 `colon_immediate_loss_calibrated`。
  - 在 `build_pair_coexistence_refresh_corpus()` 中加入新分支。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增测试，确认 loss-calibrated corpus 的 loss 映射多于 fixed 映射，且仍保持 colon-immediate 无空格格式。

## 新 corpus 结构

核心重复块保留 direct mapping：

```text
fixed:fixed
loss:loss
loss:loss
comparison-baseline|fixed:fixed
factual-val-loss|loss:loss
prompt=fixed:target=fixed
prompt=loss:target=loss
```

同时加入轻量对比句：

```text
loss prompt selects loss
fixed prompt selects fixed
when prefix is loss: continue loss
when prefix is fixed: continue fixed
```

bridge 部分加入：

```text
loss prompt should not continue fixed
fixed prompt should not continue loss
```

它的目标不是单纯增加短前缀，而是校准 loss 分支和 fixed 分支的选择边界。

## 真实结果

v546 使用 v544 的最佳解码配置：

```text
top_k=2
temperature=0.8
max_new_tokens=12
```

结果：

```text
pair_full_seed_count=1/3
535  -> pair_full=False
1535 -> pair_full=True
2535 -> pair_full=False
```

这说明 loss 校准确实把 seed `1535` 拉回来了，但破坏了原本在 v544 已恢复的 `535` 和 `2535`。

## 链路角色

v546 的价值是暴露校准权衡。当前 fixed/loss pair 不是简单“多加 loss”或“多加 first-token”就能稳定的任务；不同 seed 对数据分布很敏感。后续应先做跨版本覆盖对比，再决定是否做混合 corpus、seed-aware fallback 或更明确的 contrastive objective。

## 验证覆盖

验证包括：

- 新 corpus mode 单测。
- 真实三 seed 训练和 replay。
- missed-seed diagnostic。
- Playwright MCP HTML 截图和 snapshot。
- 全量 pytest、source encoding、`git diff --check` 和 GitHub Actions。

一句话总结：v546 证明 loss 校准能修复 seed `1535`，但也证明当前目标需要更系统的覆盖对比，而不是单点调参。
