# v697 minimal prompt branch-bias diagnostic

## 本版目标和边界

v697 的目标是解释 v696 为什么失败。它不重新训练，不改 corpus，不新增模型能力声明，只读取 v696 的真实 replay rows，判断 `loss=` 是否被竞争分支 `fixed` 吸走。

本版输出的是 diagnostic evidence，不是 promotion evidence。

## 前置链路

v696 的真实训练结果是：

```text
fixed= -> fixed=fixed=fixed=
loss=  -> loss=fixed=fixed=
```

这说明 fixed 命中，loss 未命中。v697 在这个基础上把 case rows 转成 branch-bias rows。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.py`
  - builder。
  - 读取 coexistence refresh report，提取 replay case rows，统计 branch vote。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic_artifacts.py`
  - 输出层。
  - 生成 JSON、CSV、text、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.py`
  - CLI。
  - 接受 refresh JSON 或 refresh 输出目录。

- `tests/test_model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic.py`
  - focused tests。

## 核心数据结构

### diagnostic rows

每个 replay case 转成一行：

- `profile_id`
- `term`
- `prompt`
- `expected_first_char`
- `observed_first_char`
- `expected_term_at_start`
- `other_term_at_start`
- `continuation_hit`
- `branch_vote`
- `continuation_preview`

`branch_vote` 是本版关键字段：如果 continuation 以 `fixed` 开头，就是 `fixed-start`；以 `loss` 开头，就是 `loss-start`。

### summary

summary 聚合：

- `fixed_hit_count`
- `loss_hit_count`
- `loss_prompt_fixed_start_count`
- `fixed_prompt_loss_start_count`
- `expected_first_char_match_count`
- `dominant_bias`
- `training_status`
- `checkpoint_exists`

这些字段把“有没有训练产物”和“输出偏向哪条分支”分开。

## 判定逻辑

如果输入 report 不 pass、训练不 pass、checkpoint 缺失或没有 case rows，本版 fail。

正常情况下：

- pair-full 已经观察到：`minimal_prompt_branch_bias_pair_full_observed`
- `loss=` 以 `fixed` 开头：`minimal_prompt_branch_bias_fixed_absorbs_loss`
- `fixed=` 以 `loss` 开头：`minimal_prompt_branch_bias_loss_absorbs_fixed`
- 否则只是记录诊断：`minimal_prompt_branch_bias_recorded`

v696 的真实输入落在第二种。

## 运行证据

命令输出：

```text
decision=minimal_prompt_branch_bias_fixed_absorbs_loss
fixed_hit_count=2
loss_hit_count=0
loss_prompt_fixed_start_count=2
dominant_bias=fixed
```

截图：

```text
e/697/图片/v697-minimal-prompt-branch-bias-diagnostic.png
```

## 测试覆盖

focused tests 覆盖：

- fixed absorbs loss 的主路径。
- pair-full 候选时不误判为失败。
- checkpoint missing 时 fail。
- 五种输出格式都能渲染。
- locator 支持目录输入。

## 下一步

v698 应该基于这个诊断修 corpus，而不是盲目加训练轮数。最合理的是加入更强的 loss first-token 和 branch separation 行，再重新训练。

## 一句话总结

v697 把 minimal-prompt 首轮失败定位为 fixed-dominant branch bias，给下一版 loss-first-token 修复提供了明确靶点。
