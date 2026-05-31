# v561 required-term pair equals-surface no-pair-id loss-balanced repair 代码讲解

## 本版目标和边界

v560 去掉 `pair=01` 后，`fixed=` 恢复但 `loss=` 仍失败。这个结果很有用：它说明数字 ID 是一个干扰项，但剩余问题变成了 loss 分支权重不足。v561 于是只做一个定向修正：在 no-pair-id 设计上给 loss 分支额外样本，不再回到模型加宽或 decode trick。

本版不做 held-out、不做多 seed，也不宣称模型已泛化。它只回答一个问题：seed `1535` 是否能在 no-pair-id + loss-balanced 目标下恢复 fixed/loss pair-full。

## 前置链路

- v559：加宽 embedding 失败，且输出中出现 `=01` 干扰。
- v560：去掉 `pair=01` 后 `fixed=` 命中，`loss=` 仍失败。

v561 是 v560 的自然下一步：不改变模型，只平衡剩余失败分支。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - 新增 `equals_surface_no_pair_id_loss_balanced_repair`。
  - 新增 `_extend_equals_surface_no_pair_id_loss_balanced_repair()`。
  - 保持 replay prompt 为 `fixed=` / `loss=`。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增测试，确认 loss evidence 多于 fixed evidence。
  - 确认 `pair=01` 没有被重新引入。
- `e/561/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-repair/`
  - 保存真实训练输出、主报告、replay 报告和截图旁证。

## 核心语料设计

v561 继承 v560 的 no-pair-id records：

```text
record fixed=fixed loss=loss
record loss=loss fixed=fixed
fixed=fixed loss=loss
loss=loss fixed=fixed
```

同时给 loss 分支增加轻量权重：

```text
loss=loss
prompt loss= target loss
loss=next loss
loss= should not continue fixed
select loss=loss fixed=fixed
```

这不是盲目重复全部语料，而是针对 v560 剩余 miss 的局部目标平衡。

## 运行流程

1. CLI 生成 `equals_surface_no_pair_id_loss_balanced_repair` corpus。
2. seed `1535` 训练一个 `n_embd=64` tiny checkpoint。
3. replay `fixed=` 和 `loss=`。
4. 同时检查 default 与 `suppress_newline_tokens` 两个 profile。
5. 写出 JSON、CSV、text、Markdown、HTML，并用 Playwright 归档截图。

## 真实结果

真实命令返回：

```text
decision=required_term_pair_colon_immediate_stably_pair_full
pair_full_seed_count=1/1
pair_full_seed_rate=1.0
stable_pair_full=True
```

replay 汇总：

```text
default_continuation_hit_count=2
suppression_continuation_hit_count=2
default_pair_full_variant_count=1
suppression_pair_full_variant_count=1
```

case rows 中，`fixed=` 和 `loss=` 都命中目标项。虽然生成仍有重复和混合片段，但 required-term pair-full 指标在这个 seed 上已经恢复。

## 测试覆盖

本版新增测试保护：

- 新 corpus 模式确实增加 loss 分支证据。
- 新 corpus 模式没有重新加入 `pair=01`。
- 既有 refresh corpus 测试仍全部通过。

完整收口还需要全量 pytest、source encoding hygiene、`git diff --check` 和 CI。

## 归档角色

`e/561` 是当前 equals-surface objective 的正向候选证据。它把 v552-v560 的一串负结果推进到一个可复核的单 seed pair-full recovery，但仍必须经过多 seed 和 held-out aliases 才能升级成更强基线。

一句话总结：v561 用 no-pair-id + loss-balanced 目标恢复 seed `1535` 的 fixed/loss pair-full，下一步应验证稳定性和泛化边界。

