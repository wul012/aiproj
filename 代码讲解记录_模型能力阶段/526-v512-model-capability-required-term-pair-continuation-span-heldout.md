# v512 required-term pair continuation-span heldout 代码讲解

## 本版目标与边界

v512 接着 v511 的结论：prefix gain 已经跨 seed 稳定，但还不知道能不能离开原始 `fixed:` / `loss:` scaffold。于是本版读取 v511 的两个 seed checkpoint，直接做 held-out prompt 生成检查。

本版不训练，不调整 checkpoint，不扩大目标词。它只是一个泛化探针：source scaffold 和 alias scaffold 是否都能触发对应 required term。

## 前置链路

前置版本：

- v510：continuation-span objective 让 `fixed` 的 prefix boundary 从 4 降到 1。
- v511：seed 510 和 511 都复现 prefix gain，但自由生成 full pair 未恢复。

v512 的问题是：这种稳定信号是否只会在原始 prompt 上出现。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_continuation_span_heldout.py`
  - 主流程：读取 v511、选择 seed checkpoint、构造 source/heldout prompt cases、运行生成并汇总。
- `src/minigpt/model_capability_required_term_pair_continuation_span_heldout_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
- `scripts/run_model_capability_required_term_pair_continuation_span_heldout.py`
  - CLI 入口，输入 v511 report 或目录。
- `tests/test_model_capability_required_term_pair_continuation_span_heldout.py`
  - 覆盖 source-only、缺稳定前置失败、seed/case 选择。

## 核心数据结构

`cases` 固定为四个 prompt：

- `source-fixed`: `fixed:` -> `fixed`
- `source-loss`: `loss:` -> `loss`
- `heldout-alpha-fixed`: `alpha:` -> `fixed`
- `heldout-beta-loss`: `beta:` -> `loss`

`generation_rows` 每行代表一个 seed/case 生成结果：

- `seed`
- `case_id`
- `case_type`
- `prompt`
- `expected_term`
- `generated`
- `continuation`
- `continuation_hit`
- `continuation_preview`

`case_rows` 汇总每个 case 在两个 seed 上的命中率。

## 核心函数流程

`build_model_capability_required_term_pair_continuation_span_heldout()` 是主入口：

1. `select_heldout_seed_sources()` 从 v511 `seed_reports` 中抽取通过且有 checkpoint 的 seed。
2. `build_heldout_prompt_cases()` 构造 source 和 heldout prompt cases。
3. `_run_heldout_generations()` 使用每个 seed checkpoint 逐 case 生成。
4. `summarize_heldout_seed_rows()` 汇总 seed 级别 source/heldout 命中。
5. `summarize_heldout_case_rows()` 汇总 case 级别命中率。
6. `summarize_continuation_span_heldout()` 判断是否出现 held-out generalization。

## 真实结果解释

真实结果：

- `source-fixed`: 2/2 命中 `fixed`
- `source-loss`: 0/2 命中 `loss`
- `heldout-alpha-fixed`: 2/2 命中 `fixed`
- `heldout-beta-loss`: 0/2 命中 `loss`

因此本版 decision 是 `required_term_pair_continuation_span_heldout_signal`，但解释必须保守：held-out 信号只出现在 `fixed`，`loss` 尚未恢复。

## 输出证据

v512 输出位置：

```text
e/512/解释/model-capability-required-term-pair-continuation-span-heldout/
```

截图和说明归档在：

```text
e/512/图片
e/512/解释/说明.md
```

## 测试覆盖

测试覆盖：

- source prompt 有命中、heldout prompt 无命中时，报告为 source-only。
- v511 前置没有 stable prefix gain 时，报告失败。
- seed sources 和 heldout cases 的选择保持稳定。

测试中的 fake generation 不模拟真实模型质量，只保护 v512 的结构契约和边界判断。

## 一句话总结

v512 证明 continuation-span 信号开始在 `fixed` 的 alias prompt 上出现，但 `loss` 仍未泛化，下一步应扩大 alias 集做更严格检查。
