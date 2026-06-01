# v610 required-term pair contrast-free objective corpus

## 本版目标和边界

v610 承接 v609 诊断结论：当前问题不是单边样本不够，而是 `fixed=` / `loss=` 首 token 选择和 repeated term loop 互相纠缠。本版新增三条 contrast-free objective corpus mode。

本版只新增语料设计和测试，不跑训练，不声明模型能力提升。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_contrast_free_objective_corpus.py
src/minigpt/model_capability_required_term_pair_coexistence_corpus.py
tests/test_model_capability_required_term_pair_contrast_free_objective_corpus.py
e/610/解释/contrast-free-objective-corpus-contract/
```

新增模块只负责 corpus extension，不把训练、比较、报告渲染塞进去。`coexistence_corpus.py` 只增加注册和 dispatch。

## 三条路线

`equals_surface_no_pair_id_fixed_retention_contrast_free_repair`：

```text
fixed rows 不直接提 loss，loss rows 不直接提 fixed，减少对侧 term 起始泄漏。
```

`equals_surface_no_pair_id_fixed_retention_delimiter_span_repair`：

```text
用 fixed=fixed; / loss=loss; 训练目标 span 的结束边界，减少 fixed=fixed=fixed= 这类循环。
```

`equals_surface_no_pair_id_fixed_retention_context_switch_repair`：

```text
用 [fixed-context] / [loss-context] 分离局部上下文，但 replay prompt 仍保持 fixed= / loss=。
```

## 测试覆盖

测试确认：

- 三个 mode 全部注册到 `PAIR_COEXISTENCE_CORPUS_MODES`。
- `source_prompts(mode)` 仍返回 `fixed=` / `loss=`。
- contrast-free mode 有分离 branch rows。
- delimiter mode 有停止 span。
- context-switch mode 有上下文隔离。
- 不引入 `pair=01`。

## 运行证据

```text
e/610/解释/contrast-free-objective-corpus-contract/
e/610/图片/v610-contrast-free-objective-corpus-contract.png
```

contract JSON/HTML 是本版语料能力的静态证据，后续 v611-v613 会分别跑真实 seed。

## 一句话总结

v610 把 first-token preference 诊断转成三条新的可训练 objective route。
