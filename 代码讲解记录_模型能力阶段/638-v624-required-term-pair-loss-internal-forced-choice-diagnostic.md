# v624 required-term pair loss-internal forced-choice diagnostic

## 本版目标和边界

v624 对 v620-v622 的真实 checkpoint 做 teacher-forced forced-choice scoring。它不生成新样本、不训练模型，而是直接比较 `fixed=` / `loss=` 后候选 `fixed` 与 `loss` 的负对数似然。

本版的边界很重要：forced-choice full match 是内部偏好证据，不等于模型已经能稳定生成 pair-full。

## 输入和输出

输入：

```text
e/620/解释/model-capability-required-term-pair-loss-internal-preference-seed-3535/
e/621/解释/model-capability-required-term-pair-loss-internal-first-token-seed-3535/
e/622/解释/model-capability-required-term-pair-loss-internal-ranked-choice-seed-3535/
```

输出：

```text
e/624/解释/model-capability-required-term-pair-loss-internal-forced-choice-diagnostic/
e/624/图片/v624-loss-internal-forced-choice-diagnostic.png
```

## 核心流程

`scripts/run_model_capability_required_term_pair_refresh_forced_choice_diagnostic.py` 加载每个 checkpoint 和 tokenizer，然后对每个 prompt/candidate 计算 teacher-forced NLL。

每个 source 会得到两个 prompt summary：

- `fixed=` 下 candidate `fixed` 是否最佳。
- `loss=` 下 candidate `loss` 是否最佳。

当两个 prompt 都 expected-best 时，该 source 被记为 `forced_choice_full_match`。

## 运行结果

```text
decision=refresh_forced_choice_internal_pair_match
expected_best_prompt_count=4
forced_choice_full_match_source_count=1
best_internal_sources=loss-internal-first-token
```

v621 的 first-token checkpoint 虽然生成上是 loss-only，但内部 scoring 同时偏好 `fixed` 和 `loss`。

## 证据解释

这不是生产能力提升证据，而是训练机理证据：模型已经在内部学到 pair preference，问题转移到了 decoding/generation path。

后续版本应该比较内部偏好和生成失败之间的差距，而不是继续无约束增加语料模板。

## 一句话总结

v624 发现 v621 已经具备内部 pair match，下一步要把内部偏好桥接到生成表现。
