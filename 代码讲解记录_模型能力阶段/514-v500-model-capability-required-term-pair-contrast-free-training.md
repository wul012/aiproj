# v500 model capability required-term pair contrast-free training

## 本版目标和边界

v500 的目标是把 v499 的语料诊断变成一次真实训练实验。v499 已经确认：v497 pair corpus 中存在 `fixed:fixed not loss` 和 `loss:loss not fixed` 这类行，它们把另一个 required term 放在同一个 scaffold prompt 后面。v500 因此构建 contrast-free pair corpus，再训练新的 tiny checkpoints，观察 `fixed/loss` 是否能恢复 full-hit。

本版不扩展到三词组，不增加大型模型，也不把 partial signal 宣称为生产级能力。它只验证一个具体修正：去掉 prompt-target 泄露后，pair 训练是否更稳定。

## 前置路线

- v497：增加训练步数、embedding 宽度和 corpus density，仍未恢复 full-hit。
- v498：复用 v497 checkpoints 扫 decoding profile，仍未恢复 full-hit。
- v499：从真实 capacity corpus 中找到 960 次 direct other-term leak 和 960 次 negative contrast leak。
- v500：基于 v499 结论构建 contrast-free corpus，并重新训练 3 个 tiny variants。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_contrast_free_training.py`
  - 主 builder，负责串联 source audit、pair selection、variant training、generation probe 和最终 report。
  - 文件保持在 orchestration 角色，不再塞入所有 summary 和 corpus helper。
- `src/minigpt/model_capability_required_term_pair_contrast_free_training_components.py`
  - 承接 pair 选择、variant 归一化、contrast-free corpus 构建和 summary helper。
  - 这样避免继续制造难维护的大文件。
- `src/minigpt/model_capability_required_term_pair_contrast_free_training_artifacts.py`
  - 输出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 用于 Playwright MCP 截图归档。
- `scripts/run_model_capability_required_term_pair_contrast_free_training.py`
  - CLI 入口，支持 `--variant-preset default|fast`、`--pair-limit`、`--force` 和 `--require-pass`。
- `tests/test_model_capability_required_term_pair_contrast_free_training.py`
  - 覆盖 full-hit、partial、坏输入、clean corpus、summary helper 和 artifact 输出。
- `e/500/`
  - 保存真实训练产物、报告、截图和说明。

## 核心数据结构

输入是 v499：

```text
model_capability_required_term_pair_prompt_separation_audit.json
```

其中关键字段是：

```text
summary.prompt_separation_audit_decision = prompt_separation_corpus_revision_needed
summary.corpus_revision_recommended = True
targets[].pair_id
targets[].terms[].scaffold_prompt
targets[].terms[].term
```

`select_contrast_free_pairs()` 会按 `pair_id` 去重，避免 v499 中 `baseline-repeat` 和 `longer-iters` 两个 target 对同一 `01-fixed-loss` pair 重复训练。

`build_required_term_pair_contrast_free_corpus()` 只写目标自身 continuation：

```text
fixed:fixed
fixed: fixed
comparison-baseline|fixed:fixed
loss:loss
loss: loss
factual-val-loss|loss:loss
```

它明确不写：

```text
fixed:fixed not loss
loss:loss not fixed
pair fixed loss prompt fixed: target fixed
```

## 运行流程

1. CLI 定位 v499 prompt-separation audit report。
2. builder 校验 source 是 `pass` 且 `corpus_revision_recommended=True`。
3. 选择唯一的 `01-fixed-loss` pair。
4. 构建 3 个 contrast-free variants。
5. 每个 variant 写出独立 corpus，并调用现有 `_train_micro_checkpoint()` 训练真实 checkpoint。
6. 每个 checkpoint 对 `fixed:` 和 `loss:` 运行固定 probe。
7. 汇总 variant summary、pair summary 和 overall summary。
8. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果

```text
status=pass
decision=required_term_pair_contrast_free_training_partial
contrast_free_training_decision=contrast_free_training_partial_only
selected_pair_count=1
variant_count=3
training_run_count=3
training_pass_count=3
probe_count=6
probe_hit_count=3
variant_pair_full_hit_count=0
variant_pair_partial_hit_count=3
contrast_free_full_hit_observed=False
best_variant_id=contrast-longer
model_quality_claim=contrast_free_pair_partial_signal_only
```

三个 variant 的共同现象是：

```text
hit_terms = fixed
missed_terms = loss
pair_full_hit = False
```

这说明去掉 direct leakage 后，模型没有继续偏向 v497/v498 里的 `loss`，而是偏向 `fixed`。语料修正改变了输出偏向，但还没有让 tiny checkpoint 同时保住两个 prompt-target 映射。

## 测试覆盖

测试覆盖了几个关键边界：

- fake full-hit variant 必须得到 `required_term_pair_contrast_free_training_recovered`。
- 只命中一个词时只能是 partial，不能误报 recovered。
- source audit 失败或没有推荐 corpus revision 时必须进入 fail。
- contrast-free corpus 必须不包含 `not loss` / `not fixed`。
- summary helper 必须优先选择 full-hit variant，再按 hit count 选择 best variant。
- artifact 输出覆盖 JSON/CSV/text/Markdown/HTML。

## 证据角色

`e/500` 是真实训练证据，不是只读审计。它包含新训练出来的 contrast-free corpora、checkpoints、tokenizer、metrics、train config、probe rows 和 HTML 报告。虽然本版没有恢复 full-hit，但它把“语料泄露修正”从建议变成了可复核实验。

## 一句话总结

v500 把 v499 的 prompt-target 泄露诊断推进成真实 contrast-free tiny training；结果证明明显语料泄露已被移除，但 `fixed/loss` 仍停在 partial signal，下一步应检查 seed 稳定性和 `loss:` 分支。
