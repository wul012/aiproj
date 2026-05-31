# v560 required-term pair equals-surface no-pair-id repair 代码讲解

## 本版目标和边界

v559 把 `n_embd` 加到 `96` 之后仍然失败，并且输出里反复出现 `fixed=01=...`。这提示我们：问题未必只是容量不够，`equals_surface_tied_repair` 里的 `pair=01` 可能让模型在看到任意 `=` 后都倾向补数字 ID。

v560 因此做一个目标函数层面的轻量修正：保留 fixed/loss 在同一条记录里共同出现，但删除 `pair=01` 这种 numeric id。它不是新治理链，也不是大改架构，只是把 v559 的错误形态转成可验证的语料假设。

## 前置链路

- v556：tied repair 没能恢复 pair-full。
- v557：forced-choice 发现 `fixed=` 内部偏向 `loss`。
- v558：decode constraint 不可行。
- v559：加宽 embedding 后出现 `=01` 干扰，且两个分支都未命中。

v560 接在 v559 之后，专门处理 `pair=01` 对 equals surface 的竞争。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - 新增 `equals_surface_no_pair_id_repair`。
  - 新增 `_extend_equals_surface_no_pair_id_repair()`。
  - `source_prompts()` 把新模式纳入 equals replay surface。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 corpus 结构测试。
  - 新增 replay prompt 测试。
- `e/560/解释/model-capability-required-term-pair-equals-surface-no-pair-id-repair/`
  - 保存真实训练报告、checkpoint、replay 报告和 Playwright snapshot。

## 核心语料设计

旧 tied repair 的关键记录包含 numeric pair id：

```text
pair=01 fixed=fixed loss=loss
pair=01 loss=loss fixed=fixed
```

v560 新模式改成：

```text
record fixed=fixed loss=loss
record loss=loss fixed=fixed
fixed=fixed
loss=loss
fixed=fixed loss=loss
loss=loss fixed=fixed
```

这样仍然保留 fixed/loss 同记录绑定，但不会在 corpus 中反复出现 `=01`。测试明确断言 `pair=01` 不存在，防止之后误把数字 ID 重新放回来。

## 运行流程

1. CLI 使用 `equals_surface_no_pair_id_repair` 生成 corpus。
2. 用 seed `1535` 训练一个 `n_embd=64` tiny checkpoint。
3. 对 `fixed=` 和 `loss=` 运行 default 与 `suppress_newline_tokens` replay。
4. 汇总 pair-full、profile hit count 和稳定性 decision。
5. 写出 JSON、CSV、text、Markdown、HTML，并用 Playwright 截图。

## 真实结果

真实稳定性结果：

```text
pair_full_seed_count=0/1
stable_pair_full=False
default_continuation_hit_count=1
suppression_continuation_hit_count=1
```

case rows 显示：

```text
fixed= -> fixed=fixed\nfixed=      hit=True
loss=  -> loss= filoixed\nfi       hit=False
```

这说明 v560 没有解决 pair-full，但它确实改变了失败形态：v559 是两个分支都未命中，v560 恢复了 `fixed=`，剩余失败集中在 `loss=`。

## 测试覆盖

新增测试保护三件事：

- 新模式包含 paired fixed/loss records。
- 新模式不包含 `pair=01`。
- 新模式仍然使用 `fixed=` / `loss=` 作为 replay prompt。

本版还运行了目标测试，确保 corpus builder 和 refresh 报告路径没有回归。

## 归档角色

`e/560` 是一个目标设计分叉的真实训练证据。它不是成功版，而是把“equals surface 失败”从模糊的容量/解码问题缩小到一个更明确的分支不平衡问题：去掉 numeric id 后 fixed 可回归，但 loss 仍缺少足够稳定的目标表达。

一句话总结：v560 移除了 `pair=01` equals 竞争并恢复 fixed 分支，但 pair-full 仍被 loss 分支卡住，下一版应做 no-pair-id 的 loss-balanced 修正。

