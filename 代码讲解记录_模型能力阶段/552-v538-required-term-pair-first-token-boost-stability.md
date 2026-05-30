# v538 required-term pair first-token boost stability 代码讲解

## 本版目标和边界

v537 已经证明 v536 的 missed seeds 主要卡在 first-token preference。v538 不继续堆诊断，而是修改训练 corpus，加入 `colon_immediate_first_token_boost`，用真实三 seed 训练验证短前缀增强是否能改善稳定性。

本版不改变模型结构，不增加训练预算，不把负结果包装成能力提升。它只比较“同预算下换 corpus 形态”是否能减少 first-token gap。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 `PAIR_COEXISTENCE_CORPUS_MODES` 和 `colon_immediate_first_token_boost`。
- `src/minigpt/model_capability_required_term_pair_colon_immediate_stability.py`
  - 新增 `corpus_mode` 参数，三 seed stability 不再硬编码 `colon_immediate`。
- `scripts/run_model_capability_required_term_pair_coexistence_refresh.py`
  - CLI 的 `--corpus-mode` 复用统一常量。
- `scripts/run_model_capability_required_term_pair_colon_immediate_stability.py`
  - 新增 `--corpus-mode`，可直接跑 first-token boost 三 seed。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 覆盖 boost corpus 中的短前缀目标。
- `tests/test_model_capability_required_term_pair_colon_immediate_stability.py`
  - 覆盖 stability builder 对非默认 corpus mode 的透传。
- `e/538/解释/`
  - 保存真实三 seed stability 和 missed-seed diagnostic。

## 核心 corpus 改动

新增 mode 会生成以下更短的 prompt-target 片段：

```text
fixed:f
loss:l
fixed:fi
loss:lo
fixed:fix
loss:los
prefix=fixed:next=fixed
prefix=loss:next=loss
```

它的意图是让字符级 tokenizer 在 `fixed:` 后更偏向 `f`，在 `loss:` 后更偏向 `l`。这直接回应 v537 的结论。

## 运行流程

v538 的 stability runner 现在接受：

```text
--corpus-mode colon_immediate_first_token_boost
```

每个 seed 内部仍调用 refresh builder：

```text
build_model_capability_required_term_pair_coexistence_refresh(
    corpus_mode="colon_immediate_first_token_boost",
    seed=<535/1535/2535>,
)
```

训练完成后仍用 generation profile replay 判断 pair-full，再用 v537 的 missed-seed diagnostic 复查 first-token rank。

## 真实结果

stability 结果：

```text
pair_full_seed_count=1/3
stable_pair_full=False
```

seed 明细：

```text
535  -> no pair-full
1535 -> no pair-full
2535 -> pair-full
```

first-token 诊断：

```text
535  -> fixed rank=2, loss rank=1
1535 -> fixed rank=1, loss rank=2
2535 -> fixed rank=1, loss rank=2
```

这说明短前缀增强并没有让两个词同时稳定 top-ranked。

## 测试覆盖

单测保护两类行为：

- `colon_immediate_first_token_boost` 必须包含短前缀目标，且不能回到 `fixed: fixed` 这种带空格形态。
- stability builder 传入非默认 corpus mode 后，报告 `settings.corpus_mode` 必须真实记录该模式。

真实 PyTorch 训练由 `e/538` 证据覆盖，截图由 Playwright MCP 生成。

## 链路角色

v538 是一次必要的负结果：它证明“简单短前缀增强”还不足以修复 first-token gap。后续应转向更强的 prompt 分离 corpus，而不是继续增加同类短片段。

一句话总结：v538 用真实训练证明 first-token boost 的简单形态不足，下一步需要更强的分离式数据设计。
