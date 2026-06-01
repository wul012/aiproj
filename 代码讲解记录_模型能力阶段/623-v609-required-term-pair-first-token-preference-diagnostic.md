# v609 required-term pair first-token preference diagnostic

## 本版目标和边界

v609 承接 v608 closeout 的下一步建议：检查 first-token preference。它读取 v600-v607 的真实训练报告，把 replay continuation 拆成首字母、对侧 term 起始、branch vote 和 hit 状态。

本版不训练，不修改语料，不把诊断结果解释成模型能力提升。它只为下一版 objective 设计提供证据。

## 前置链路

```text
v608: closeout 证明 fixed-retention/loss-rebalance 分支应停止
v609: 检查这些分支为何互相覆盖
```

v608 的核心结论是：v606 loss-only，v607 fixed-only。v609 继续往下看，确认它们不是单纯“没训练够”，而是首 token 和对侧 term 起始互相抢占。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_first_token_preference_diagnostic.py
src/minigpt/model_capability_required_term_pair_first_token_preference_diagnostic_artifacts.py
scripts/run_model_capability_required_term_pair_first_token_preference_diagnostic.py
tests/test_model_capability_required_term_pair_first_token_preference_diagnostic.py
e/609/解释/model-capability-required-term-pair-first-token-preference-diagnostic/
```

判定模块负责读取 refresh reports、生成 prompt rows、统计冲突。artifact 模块负责报告渲染，避免把 HTML/CSV 写入判定模块。

## 核心字段

每个 prompt row 包含：

```text
source_label
profile_id
term
expected_first_char
observed_first_char
first_char_expected
expected_term_at_start
other_term_at_start
branch_vote
continuation_hit
continuation_preview
```

`other_term_at_start` 是本版最关键字段。它表示 prompt 期望 `fixed` 时 continuation 是否从 `loss` 开始，或者 prompt 期望 `loss` 时是否从 `fixed` 开始。

## 运行结果

真实 v600-v607 输入输出：

```text
status=pass
decision=first_token_preference_tradeoff_confirmed
source_report_count=5
first_token_conflict_confirmed=True
mixed_branch_tradeoff_confirmed=True
other_term_start_count=8
```

这说明同一 `fixed=` / `loss=` surface 并没有稳定选择正确 branch，而是在不同语料路线里被拉向对侧 term。

## 测试覆盖

测试覆盖：

- fixed-only 与 loss-only 输入会产生 `first_token_preference_tradeoff_confirmed`。
- 如果输入里已有 pair-full，会转成 pair-full candidate 判定。
- checkpoint 缺失会失败。
- JSON/CSV/text/Markdown/HTML 五种输出都能生成。
- locator 支持 output directory。

## 运行证据

```text
e/609/解释/model-capability-required-term-pair-first-token-preference-diagnostic/
e/609/图片/v609-first-token-preference-diagnostic.png
```

JSON 是机器可读源证据；HTML 和截图用于人工审查。

## 一句话总结

v609 证明当前问题是 first-token preference 与 repeated term loop 纠缠，下一版应设计 contrast-free objective。
