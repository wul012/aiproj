# v627 required-term pair loss-internal fixed-bridge corpus

## 本版目标和边界

v627 把 v626 的诊断结论转成训练语料：v621 内部 fixed/loss 都匹配，但生成只命中 loss，缺口是 fixed。

本版不训练模型，不声明能力提升；它只新增 bridge corpus mode。

## 关键修改

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
e/627/解释/loss-internal-fixed-bridge-corpus-contract/
```

## 新增模式

```text
equals_surface_no_pair_id_loss_internal_fixed_bridge_repair
```

这个模式增加三类行：

- `fixed=fixed` / `fixed=fix` 一类 fixed generation bridge。
- `loss=loss` / `loss=los` 一类 loss internal anchor。
- `bridge fixed= fixed while loss= remains loss` 一类桥接说明行。

它仍保持 `fixed=` / `loss=` prompt surface，并且不引入 `pair=01`。

## 测试覆盖

新增测试确认：

- fixed bridge 关键行存在。
- loss internal preference anchor 仍然存在。
- 没有 pair-id 泄漏。

## 运行证据

`e/627/解释/loss-internal-fixed-bridge-corpus-contract/` 保存 contract JSON/CSV/text/Markdown/HTML。

`e/627/图片/v627-loss-internal-fixed-bridge-corpus-contract.png` 证明 contract 页面字段完整。

## 一句话总结

v627 把 v626 的 fixed generation gap 转成可训练的 bridge objective。
