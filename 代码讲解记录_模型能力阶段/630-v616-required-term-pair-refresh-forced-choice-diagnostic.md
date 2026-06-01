# v616 required-term pair refresh forced-choice diagnostic

## 本版目标和边界

v616 新增 refresh forced-choice diagnostic。它不生成文本、不训练新模型，而是对 checkpoint 做 teacher-forced 候选打分：给 `fixed=` prompt 比较 `fixed` 和 `loss` 的 NLL，给 `loss=` prompt 也做同样比较。

本版只交付诊断能力；真实 v611-v613 checkpoint 运行放到 v617。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_refresh_forced_choice_diagnostic.py
src/minigpt/model_capability_required_term_pair_refresh_forced_choice_diagnostic_artifacts.py
scripts/run_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py
tests/test_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py
```

## 核心数据结构

`score_rows` 记录每个 prompt/candidate：

```text
source_label
prompt_term
prompt
candidate_term
is_expected_candidate
total_nll
avg_nll
first_token_rank
```

`prompt_summaries` 再判断每个 prompt 的 expected candidate 是否是最低 NLL。

`source_summaries` 判断一个 checkpoint 是否同时在 `fixed=` 和 `loss=` 上内部偏好正确 term。

## 测试覆盖

测试覆盖：

- 双 prompt 都 expected-best 时输出 internal pair match。
- 单 prompt expected-best 时输出 partial internal match。
- checkpoint 缺失会失败。
- JSON/CSV/text/Markdown/HTML 输出可生成。
- locator 支持 output directory。

## 一句话总结

v616 给后续实验增加了“看模型内部偏好”的入口，避免只凭采样文本继续猜语料方向。
