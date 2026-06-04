# v859：bounded objective curriculum patch profile sweep

## 本版目标和边界

v859 的目标是回答 v858 留下的问题：v856 checkpoint 没有恢复 `fixed loss`，究竟是模型完全没有 `loss` 能力，还是 v857 的单一解码 profile 没有把 `loss` 释放出来。

边界：

- 不训练。
- 不修改 v855 patch corpus。
- 不修改 v836 bounded objective contract。
- 不把某个 profile 命中 `loss` 当作 promotion。
- 不使用 decoder anchor。

这版是解码边界验证，不是能力宣传。

## 前置链路

```text
v857 curriculum patch replay comparison
 -> v858 case-level shape migration diagnostic
 -> v859 curriculum patch profile sweep
```

v858 的 next action 是：

```text
run_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_profile_sweep_before_more_training
```

v859 正是这一步。

## 关键新增文件

- `src/minigpt/bounded_objective_curriculum_patch_profile_sweep.py`
  - v859 builder。读取 contract、training run、shape diagnostic，运行多个 profile 的 replay。
- `src/minigpt/bounded_objective_curriculum_patch_profile_sweep_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/run_bounded_objective_curriculum_patch_profile_sweep.py`
  - CLI 入口。
- `tests/test_bounded_objective_curriculum_patch_profile_sweep.py`
  - 覆盖 loss signal、diagnostic not ready、writer 和 CLI。
- `e/859/解释/bounded-objective-curriculum-patch-profile-sweep/`
  - 保存真实 profile sweep 产物。
- `e/859/图片/v859-bounded-objective-curriculum-patch-profile-sweep-html.png`
  - Playwright MCP 截图。

## 命名收敛

这版没有继续使用完整路线名作为文件名，而是采用：

```text
bounded_objective_curriculum_patch_profile_sweep.py
```

原因是 v858 已经真实暴露过 Windows 路径长度问题。后续模型能力阶段继续保持短文件名和清晰职责，比机械延续超长命名更利于维护。

## 核心数据结构

默认 profile：

```text
v857-baseline
top1-low-temp
top3-low-temp
longer-top20
longer-open
```

每条 `sweep_rows` 记录：

```text
profile_id
case_id
continuation
required_terms
hit_terms
missed_terms
case_pass
loss_hit
fixed_hit
max_new_tokens
temperature
top_k
seed
```

每条 `profile_summaries` 记录：

```text
profile_id
case_count
passed_case_count
any_hit_case_count
zero_hit_case_count
loss_hit_case_count
fixed_hit_case_count
objective_contract_recovered
```

## 核心流程

`build_bounded_objective_curriculum_patch_profile_sweep()` 做五步：

1. 读取 v836 contract cases。
2. 读取 v856 checkpoint/tokenizer。
3. 检查 v858 shape diagnostic 已 ready。
4. 对每个 profile、每个 case 运行生成。
5. 聚合 profile summary 并选择 best profile。

best profile 的排序优先级：

```text
passed_case_count
loss_hit_case_count
any_hit_case_count
zero_hit_case_count
profile_id
```

因此它不会被“只命中 fixed”误导，而会优先寻找 `loss` 桥接信号。

## 真实结果

```text
status=pass
decision=bounded_objective_curriculum_patch_profile_sweep_found_loss_signal_bridge_required
profile_count=5
sweep_row_count=15
any_profile_recovered=False
profile_with_loss_hit_count=2
max_loss_hit_case_count=2
best_profile_id=longer-open
next_action=build_loss_signal_bridge_without_promotion
```

关键行：

```text
longer-top20 / minimal_direct_completion -> hit loss, missed fixed
longer-open / canonical_direct_completion -> hit loss, missed fixed
longer-open / completion_label_surface -> hit loss, missed fixed
```

这说明 `loss` 可以出现，但和 `fixed` 没有稳定共现。

## 测试覆盖

focused pytest 覆盖：

- fake profile 中出现 `loss` signal 但没有恢复 contract。
- shape diagnostic 不 ready 时阻断 sweep。
- JSON/CSV/TXT/Markdown/HTML writer 和 CLI。

```text
3 passed
```

运行证据：

```text
e/859/解释/bounded-objective-curriculum-patch-profile-sweep/
e/859/图片/v859-bounded-objective-curriculum-patch-profile-sweep-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Profiles=5
Rows=15
Recovered=False
Loss profiles=2
Max loss hits=2
Best profile=longer-open
```

## 一句话总结

v859 把问题从“是否能生成 loss”推进到“如何让 fixed 和 loss 在同一 contract 输出中稳定共现”。
