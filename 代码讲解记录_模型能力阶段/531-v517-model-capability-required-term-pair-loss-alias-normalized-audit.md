# v517 required-term pair loss-alias normalized audit 代码讲解

## 本版目标与边界

v517 的目标是解释 v516 的 focused repair 为什么严格命中为 0。v516 的 generation preview 出现 `los\ns\ns` 这类文本，说明模型可能生成了目标字符序列，但被换行或分隔符拆开。本版新增 normalization-aware audit，只读 v516 输出，不训练新 checkpoint。

本版不把 normalized hit 当作 strict hit，也不改变 v516 的原始判断。它只是新增一层诊断：严格命中失败时，是否存在格式分隔导致的 hidden signal。

## 前置链路

前置版本：

- v516：focused corpus 对 seed `515` 没有产生 strict hit。
- v517：读取 v516 的 generation rows，重新计算 strict vs normalized hit。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_normalized_audit.py`
  - 新增 normalized audit builder。
  - 展开 v516 `seed_reports[].generation_rows`。
  - 计算 strict hit、normalized hit、normalization gain。
- `src/minigpt/model_capability_required_term_pair_loss_alias_normalized_audit_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 显示 strict/normalized/gain 对照。
- `scripts/run_model_capability_required_term_pair_loss_alias_normalized_audit.py`
  - CLI 入口，只读 v516 focus report。
- `tests/test_model_capability_required_term_pair_loss_alias_normalized_audit.py`
  - 覆盖 hidden full signal、no hidden signal、缺少 generation rows、normalization helper。

## 核心规则

`normalize_for_required_term()` 的规则：

```text
casefold + remove non-alphanumeric characters
```

例如：

```text
lo s\ns! -> loss
```

这能识别字符被空格、换行或标点打散的 required term。但它不替代 strict metric，因为真实生成质量仍需要连续、可读的目标词。

## 输出字段

`normalized_rows` 每行包含：

- `strict_hit`
- `normalized_hit`
- `normalization_gain`
- `continuation_preview`
- `normalized_continuation_preview`

`summary` 包含：

- `strict_hit_count`
- `normalized_hit_count`
- `normalization_gain_count`
- `focus_normalized_hit_count`
- `normalized_full_coverage`
- `focus_normalized_full_coverage`

本版真实运行结果是 strict `0/4`，normalized `4/4`。

## 真实结果解释

v517 说明 v516 的 “no repair” 不是“模型完全没有靠近 loss”，而是“输出形状不满足严格 required-term substring”。这对后续路线很重要：

- 继续加 repeat 不一定有效。
- 应先把 strict-vs-normalized 指标并列到下一层评估。
- 再决定是否用 corpus 排版、token 约束或 decoding path 修复换行分隔。

## 测试覆盖

测试覆盖：

- `los\ns` 和 `lo s\ns` 能变成 normalized hit。
- 完全无目标字符时不会误报。
- 缺少 generation rows 会结构失败。
- 输出 artifact 的五种格式都能生成。

## 运行证据

运行证据归档在：

```text
e/517/解释/model-capability-required-term-pair-loss-alias-normalized-audit/
e/517/图片/
```

截图：

```text
e/517/图片/01-model-capability-required-term-pair-loss-alias-normalized-audit.png
```

## 一句话总结

v517 把 loss-alias 失败从训练密度问题推进到指标与输出格式问题：strict miss 背后存在 normalized full signal。
