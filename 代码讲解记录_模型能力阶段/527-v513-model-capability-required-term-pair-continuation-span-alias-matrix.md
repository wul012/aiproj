# v513 required-term pair continuation-span alias matrix 代码讲解

## 本版目标与边界

v513 的目标是把 v512 的 held-out probe 从两个 alias 扩展成一个小矩阵。v512 只看到 `alpha:` 能触发 `fixed`，还不能判断这是偶然还是稳定别名信号。v513 增加 `gamma:`、`delta:`、`theta:`、`omega:` 等 alias，继续复用 v511 的两个 seed checkpoint 做 generation-only 检查。

本版不训练新 checkpoint，不调整参数，不改变 v511 的模型产物。它只做更密的泛化检查。

## 前置链路

前置版本：

- v510：训练 continuation-span checkpoint，`fixed` prefix boundary 改善。
- v511：双 seed 复现 prefix gain。
- v512：`alpha:` -> `fixed` 出现 held-out 信号，但 `loss` 未泛化。

v513 的问题是：`fixed` alias 信号是不是只在一个 alias 上偶然出现。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_continuation_span_heldout.py`
  - 扩展 `build_heldout_prompt_cases()`，增加 alias matrix。
  - 增加 `heldout_hit_term_count`、`heldout_full_term_coverage` 和 `alias_group_rows`。
- `src/minigpt/model_capability_required_term_pair_continuation_span_heldout_artifacts.py`
  - CSV/HTML/text/Markdown 输出新增 alias group 和 heldout term coverage 字段。
- `tests/test_model_capability_required_term_pair_continuation_span_heldout.py`
  - 更新测试，确认 held-out cases 从 2 个扩到 6 个，fixed/loss 各 4 个 case。

## 核心数据结构

`cases` 现在分两类：

source:

- `fixed:` -> `fixed`
- `loss:` -> `loss`

heldout:

- `alpha:` -> `fixed`
- `gamma:` -> `fixed`
- `delta:` -> `fixed`
- `beta:` -> `loss`
- `theta:` -> `loss`
- `omega:` -> `loss`

`summary` 新增：

- `heldout_term_count`
- `heldout_hit_term_count`
- `heldout_hit_terms`
- `heldout_full_term_coverage`
- `alias_group_rows`

这些字段让报告能区分“有任意 alias 命中”和“两类目标词都泛化”。

## 真实结果解释

真实结果：

- `fixed`: source 和三个 held-out alias 都是 2/2 命中。
- `loss`: source 和三个 held-out alias 都是 0/2 命中。

因此 v513 可以说明 `fixed` alias signal 已经比 v512 更稳定，但不能说明 fixed/loss pair 整体恢复。下一步应该针对 `loss` 做 alias-aware objective。

## 输出证据

v513 输出位置：

```text
e/513/解释/model-capability-required-term-pair-continuation-span-alias-matrix/
```

截图和说明归档在：

```text
e/513/图片
e/513/解释/说明.md
```

## 测试覆盖

测试覆盖：

- source-only fake generation 下 held-out hit terms 仍为 0。
- 前置 stable prefix gain 缺失时报告失败。
- seed sources 和 expanded alias cases 的数量、目标词分布保持稳定。

## 一句话总结

v513 把 held-out 检查从单 alias 扩展成矩阵：`fixed` 泛化信号清楚，`loss` 成为下一步必须补的目标。
