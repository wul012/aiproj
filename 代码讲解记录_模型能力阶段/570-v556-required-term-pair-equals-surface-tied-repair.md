# v556 required-term pair equals-surface tied repair 代码讲解

## 本版目标和边界

v555 已经把 v552/v554 的结果收束成 branch competition：fixed/loss 跨运行都能命中，但没有一个运行能同时保住两个分支。v556 选择最小的能力实验：把 fixed/loss 绑定进同一条或同一组训练记录，测试 tiny GPT 是否能把这两个分支一起记住。

本版不新增诊断链，不扩大 seed，不改变训练脚本；它只新增一个 corpus mode，并跑同样预算下的 seed `1535`。

## 前置链路

- v552：`equals_surface_fixed_repair` 偏 fixed，fixed 命中但 loss 失败。
- v554：`equals_surface_balanced_repair` 对称化，loss 命中但 fixed 失败。
- v555：比较两者，判定为 branch competition。

v556 的 tied repair 是 v555 `next_action` 中“tie fixed/loss branches in one objective”的最小实现。

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - `PAIR_COEXISTENCE_CORPUS_MODES` 增加 `equals_surface_tied_repair`。
  - `build_pair_coexistence_refresh_corpus()` 分派到 `_extend_equals_surface_tied_repair()`。
  - `source_prompts()` 对 tied mode 返回 `fixed=` / `loss=`。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增测试，确保 tied mode 真的包含 pair-level 绑定记录，并且不会回退到 colon prompt surface。

## Corpus 设计

核心样本是把两个分支放在同一 pair record 里：

```text
pair=01 fixed=fixed loss=loss
pair=01 loss=loss fixed=fixed
prompt=fixed=target=fixed pair=01
prompt=loss=target=loss pair=01
fixed= continues fixed while loss= continues loss
loss= continues loss while fixed= continues fixed
```

bridge 样本再明确说明：

```text
pair=01 means fixed=fixed and loss=loss together.
do not trade fixed for loss; keep both branches.
fixed=fixed|loss=loss
```

这和 v554 的 balanced repair 不同：balanced 只是行数对称，v556 则显式把两个分支绑定到同一 pair id。

## 真实结果

真实运行输出：

```text
status=pass
decision=required_term_pair_colon_immediate_not_stable
pair_full_seed_count=0
pair_full_seed_rate=0.0
```

内嵌 replay case rows 显示：

```text
fixed= -> continuation_hit=False
loss=  -> continuation_hit=True
```

也就是说 tied repair 仍然没有恢复 pair-full，且结果和 v554 类似：模型继续偏向 `loss=` 分支。

## 测试覆盖

测试覆盖了 tied mode 的三个关键约束：

- `pair=01 fixed=fixed loss=loss` 和 `pair=01 loss=loss fixed=fixed` 会按 repeat 数出现。
- bridge hint 包含 `fixed=fixed|loss=loss` 和“不把 fixed 交换成 loss”的说明。
- corpus 不包含 `fixed:fixed`，避免误用旧 colon surface。

既有 refresh/stability 测试继续通过，说明新增 mode 没破坏旧训练链路。

## 归档角色

`e/556` 保存真实训练输出、seed `1535` checkpoint、tokenizer、metrics、replay sidecar、HTML 截图和 snapshot。它是第三个 equals-surface 负结果，价值在于排除“只要把 fixed/loss 放在同一条样本里就能 pair-full”的假设。

一句话总结：v556 把 branch competition 的最小绑定修复跑成真实负结果，下一步应转向约束解码、评分诊断或目标函数层面的更强验证。
