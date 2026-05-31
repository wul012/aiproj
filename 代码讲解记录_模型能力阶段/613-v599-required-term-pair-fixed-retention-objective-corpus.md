# v599 required-term pair fixed-retention objective corpus

## 本版目标和边界

v599 承接 v598 closeout 的结论：loss-branch 已经不适合继续按原方向加权，下一步应转向 fixed-retention objective。

本版只新增可训练的 fixed-retention corpus modes，不宣称模型能力提升；能力提升要等真实 seed training 和 replay 结果。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fixed_retention_objective_corpus.py
src/minigpt/model_capability_required_term_pair_coexistence_corpus.py
tests/test_model_capability_required_term_pair_fixed_retention_objective_corpus.py
e/599/解释/fixed-retention-objective-corpus-contract/
```

## 语料模式

`equals_surface_no_pair_id_fixed_retention_balanced_repair`：

```text
fixed=fixed 行更多，但保留 loss=loss。
```

`equals_surface_no_pair_id_fixed_retention_first_token_repair`：

```text
补 fixed=f / fixed=fi / fixed=fix / fixed=fixed 前缀链，直接针对 v596 发现的 first-token gap。
```

`equals_surface_no_pair_id_fixed_retention_prompt_guard_repair`：

```text
用 guard fixed= not loss 和 guard loss= not fixed 分开 prompt 表面，减少互相覆盖。
```

## 接入方式

`model_capability_required_term_pair_coexistence_corpus.py` 只负责路由：

```text
extend_pair_fixed_retention_objective_corpus(...)
```

具体语料行放进独立模块，避免继续扩大主 corpus 文件。

## 测试覆盖

测试确认：

- 三个模式都注册进 `PAIR_COEXISTENCE_CORPUS_MODES`。
- 三个模式都使用 `fixed=` / `loss=` replay prompt。
- balanced 模式偏向 fixed 但保留 loss。
- first-token 模式增加 fixed 前缀链。
- prompt-guard 模式明确区分 fixed prompt 与 loss prompt。
- 所有模式都不引入 `pair=01`。

## 一句话总结

v599 把 fixed-retention 从路线判断推进为可训练的 corpus objective。
