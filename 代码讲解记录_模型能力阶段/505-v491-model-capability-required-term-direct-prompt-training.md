# v491 model capability required-term direct prompt training

## 本版目标和边界

v491 的目标是把 v490 暴露的问题继续缩小：v490 已经证明 prompt-leading 对齐后仍没有 required-term continuation uptake，本版进一步去掉训练语料中的 metadata 和额外模板，只保留最直接的两种行：

```text
prompt+term
prompt term
```

本版不改变 GPT 结构，不扩大到真实大模型，也不把 generated 全文包含 prompt 当作能力证据。唯一有效指标仍然是 `continuation_hit_count`：模型在 prompt 之后新生成的文本是否包含当前 prompt 对应的完整 required term。

## 前置路线

- v489：把 corpus 修成 prompt-leading，解决 v488 的 prefix shape 不一致。
- v490：用 prompt-leading corpus 训练，checkpoint 生成成功，但 `continuation_hit_count=0`。
- v491：移除 metadata 和多模板变体，测试“更直接的 prompt-to-term 语料”是否足以让 tiny 模型按 prompt 输出目标词。

## 关键文件

- `src/minigpt/model_capability_required_term_direct_prompt_training.py`
  - 读取 v490 report。
  - 从 `term_rows` 生成 direct prompt corpus。
  - 复用 `_train_micro_checkpoint` 训练 tiny checkpoint。
  - 复用 `_generation_row` 做 required-term continuation probe。
  - 统计当前结果与 v490 baseline 的 delta。
- `src/minigpt/model_capability_required_term_direct_prompt_training_artifacts.py`
  - 写出 JSON、CSV、text、Markdown 和 HTML。
- `scripts/run_model_capability_required_term_direct_prompt_training.py`
  - CLI 入口，支持 repeat、训练参数、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_direct_prompt_training.py`
  - 覆盖 direct corpus、fake improvement、no uptake、坏 source、产物写出和定位函数。
- `e/491/`
  - 保存真实训练产物、报告、CLI 输出和运行截图。

## 核心数据结构

`term_rows` 来自 v490，每行保留：

- `case`：原 benchmark case。
- `term`：当前 prompt 期待续写出的 required term。
- `scaffold_prompt`：probe 使用的短 prompt，例如 `data:`。

`build_required_term_direct_prompt_corpus()` 生成两类训练行：

- `direct`：`data:data`
- `spaced`：`data: data`

它刻意不写 `pattern=...`、`cycle=...`、`case=...` 这类 metadata。这样 v491 测的是最小条件下的 prompt-conditioned copy，而不是复杂模板记忆。

## 输出字段语义

report 的关键字段：

- `corpus.path`：本版生成的 direct prompt corpus。
- `corpus.pattern_boundary`：说明本版只保留 direct/spaced，没有 metadata。
- `previous_baseline.continuation_hit_count`：v490 baseline。
- `summary.continuation_hit_count`：v491 当前 continuation hit。
- `summary.continuation_hit_delta`：v491 相对 v490 的变化。
- `summary.direct_prompt_ready`：每个 term 是否都有 direct prompt 行。
- `interpretation.model_quality_claim`：是否允许提出模型能力信号。真实结果为 `not_claimed`。

## 运行流程

1. CLI 定位 v490 的 `model_capability_required_term_prompt_leading_training.json`。
2. builder 从 v490 读取 9 个 term row。
3. 生成 `required_term_direct_prompt_corpus.txt`，最终真实运行使用 `repeat=160`，共 `2880` 条 direct prompt 行。
4. 调用训练脚本产生 checkpoint、tokenizer、metrics、run manifest 和 sample。
5. 对 9 个 scaffold prompt 逐个生成短 continuation。
6. 统计 target continuation hit，并与 v490 的 `0` 做 delta。
7. 写出 JSON/CSV/text/Markdown/HTML 和截图证据。

## 真实结果

```text
status=pass
decision=required_term_direct_prompt_training_completed_without_uptake
direct_prompt_training_decision=direct_prompt_training_completed_without_uptake
term_count=9
generation_count=9
continuation_hit_count=0
previous_continuation_hit_count=0
continuation_hit_delta=0
training_status=pass
checkpoint_exists=True
direct_prompt_ready=True
direct_prompt_line_count=2880
model_quality_claim=not_claimed
```

生成预览显示，模型会输出类似 `fixecauseca` 的片段，但没有输出当前 prompt 对应的完整 term。例如多个 prompt 都趋向同一类片段，这说明它更像在学习局部字符分布，而不是按 prompt 条件选择目标词。

## 测试覆盖

测试重点保护了五个边界：

- fake generation 命中 term 时，必须报告 `required_term_direct_prompt_training_improved`。
- fake generation 不命中时，结构仍然通过，但能力结论必须是 no-uptake。
- direct corpus 不能包含 `pattern=` 或 `case=` metadata。
- source training 状态异常时，报告必须 fail。
- JSON/CSV/text/Markdown/HTML 必须全部写出。

这些测试确保 v491 的结论不会被“训练成功”“prompt 本身包含 term”或“generated 全文回显 prompt”误导。

## 证据角色

- JSON 是后续 one-term isolation 可以读取的结构化证据。
- CSV 用于逐 term 检查 generation 和 continuation preview。
- HTML 与截图用于人工复核报告可读性。
- `checkpoint.pt` 是真实训练产物，但不是能力提升证明。
- `说明.md` 说明本版是负结果，并给出下一步实验边界。

## 一句话总结

v491 证明去掉 metadata 和额外模板后，tiny 模型仍没有学到 target-specific required-term continuation，下一步应做 one-term capacity isolation。
