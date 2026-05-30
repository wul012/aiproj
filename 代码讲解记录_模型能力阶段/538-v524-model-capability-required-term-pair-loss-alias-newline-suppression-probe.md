# v524 required-term pair loss-alias newline suppression probe 代码讲解

## 本版目标与边界

v524 的目标是验证 v523 的 newline cleanup signal 是否可以通过解码策略转成 strict surface hit。v523 已经证明只去掉换行就能看到 `loss`，但那仍然是后处理层面的观察；v524 直接在采样时屏蔽 newline token，看同一个 checkpoint 是否会生成不带换行的 `loss`。

本版不训练、不改 checkpoint、不改服务 API，也不把 newline suppression 直接写入默认生成逻辑。它只是一个可复核的能力 probe。

## 前置链路

前置版本：

- v522：确认 remove-newlines 是最小恢复策略。
- v523：把 newline cleanup metrics 接回主线 focus report。

v524 顺着 v523 的 next action，比较 baseline 解码与 newline-suppressed 解码。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_newline_suppression_probe.py`
  - 新增 probe builder。
  - 定义 `baseline_rerun` 与 `suppress_newline_tokens` 两个 profile。
  - 在本地 sampling 中对包含 `\n` 或 `\r` 的 tokenizer entries 施加 logits mask。
- `src/minigpt/model_capability_required_term_pair_loss_alias_newline_suppression_probe_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 展示 profile-level strict hit 对比和每个 case 的 strict gain。
- `scripts/run_model_capability_required_term_pair_loss_alias_newline_suppression_probe.py`
  - CLI 接收 v523 focus JSON 或目录。
- `tests/test_model_capability_required_term_pair_loss_alias_newline_suppression_probe.py`
  - 用 fake generator 覆盖 baseline miss 与 newline suppression recovery。

## 核心数据结构

profile row 字段：

- `profile_id`
- `case_count`
- `focus_case_count`
- `strict_hit_count`
- `focus_strict_hit_count`
- `strict_full_coverage`
- `focus_strict_full_coverage`
- `strict_gain_count`
- `exclude_token_texts`

case row 字段：

- `profile_id`
- `case_id`
- `source_strict_hit`
- `source_newline_cleanup_hit`
- `source_normalized_hit`
- `strict_hit`
- `newline_cleanup_hit`
- `normalized_hit`
- `strict_gain`
- `excluded_token_count`
- `continuation_preview`

这些字段把“原始生成失败”“cleanup 能看见目标词”“屏蔽 newline 后直接生成目标词”三层证据分开。

## 核心流程

1. CLI 定位 v523 focus report。
2. Builder 读取 seed report、checkpoint path、tokenizer path 和原始 generation rows。
3. `baseline_rerun` 走原有 `MiniGPTGenerator`。
4. `suppress_newline_tokens` 走本地逐 token sampling。
5. `_excluded_token_ids()` 找到 tokenizer 中包含 newline 的 token id。
6. 采样时把这些 token 的 logits 设为 `-inf`。
7. 生成后复用 `required_term_hit_metrics()` 计算 strict/newline/normalized 命中。
8. artifact writer 输出报告和可视化证据。

## 真实结果解释

v524 真实运行结果：

```text
baseline_strict_hit_count=0
suppressed_strict_hit_count=4
suppressed_focus_strict_hit_count=2
suppressed_strict_gain_count=4
```

这说明同一个 seed-515 checkpoint 并不是完全不能输出 strict `loss`。在 newline token 被屏蔽后，四个 loss-alias prompts 都直接命中 strict surface。这个结果更支持“解码边界问题”而不是“必须先大改训练数据”。

## 测试覆盖

测试覆盖：

- fake baseline 生成 `lo\ns\ns` 时 strict miss。
- fake newline suppression 生成 `loss` 时 strict full recovery。
- artifact writer 输出五类文件。
- 缺少 generation rows 时结构失败，`--require-pass` 会返回失败。

这些断言保护本版边界：suppression 是 probe profile，不是默认生成策略。

## 运行证据

运行证据归档在：

```text
e/524/解释/model-capability-required-term-pair-loss-alias-newline-suppression-probe/
e/524/图片/
```

截图：

```text
e/524/图片/01-model-capability-required-term-pair-loss-alias-newline-suppression-probe.png
```

## 一句话总结

v524 把 focused loss-alias 的 newline surface 问题推进到真实解码实验，证明屏蔽 newline token 可以把严格命中从 0/4 提升到 4/4。
