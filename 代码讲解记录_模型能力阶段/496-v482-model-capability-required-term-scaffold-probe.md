# v482：model capability required-term scaffold probe

## 本版目标和边界

v482 的目标是做一个最小真实生成实验：v481 已经证明 required terms 存在于 expected behavior，但 archived tiny generation 从未生成这些词；v482 进一步问，如果把 required term 直接放进 prompt 尾部，当前 tiny checkpoint 能不能在 continuation 中复现它？

本版不重训模型，不修改 benchmark，不扩大数据，也不宣称模型能力提升。它只加载 v478 归档 checkpoint/tokenizer 做短 prompt 推理，验证 prompt scaffold 是否足以改变 required-term uptake。

## 前置能力

本版承接三层证据：

- v480 的 coverage audit
  - 证明 required terms 已在 suite/tiny corpus 中可见。
- v481 的 uptake audit
  - 证明 212 个 archived generation observation 中，required terms 没有进入 continuation。
- v478 的 cap-12 ladder archive
  - 提供两个 seed 的 `max-iters-4` checkpoint、tokenizer 和 eval-suite 输出。

v482 不复制这些分析，只新增一个真实 generation probe。

## 关键新增文件

- `src/minigpt/model_capability_required_term_scaffold_probe.py`
  - 核心 probe 逻辑。
  - 输入 v481 uptake report，选择每个 case 最新 rung 的一个最短 required term。
  - 解析对应 eval-suite、checkpoint 和 tokenizer。
  - 调用 `MiniGPTGenerator` 做真实生成。
  - 统计 baseline/scaffold continuation required-term hits。
- `src/minigpt/model_capability_required_term_scaffold_probe_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright MCP 截图。
- `scripts/run_model_capability_required_term_scaffold_probe.py`
  - CLI 入口。
  - 支持 `--max-new-tokens`、`--temperature`、`--top-k`、`--generation-seed`、`--term-limit`、`--device`。
- `tests/test_model_capability_required_term_scaffold_probe.py`
  - 覆盖 no-uptake、partial uptake、缺 checkpoint、输出产物和路径定位。

## 核心数据结构

最终报告是：

```text
model_capability_required_term_scaffold_probe.json
```

关键字段：

- `settings`
  - 记录生成参数：`max_new_tokens`、`temperature`、`top_k`、`generation_seed`、`term_limit` 和 `device`。
- `source_rows`
  - 每个 eval-suite source 一行。
  - 记录 checkpoint/tokenizer 路径、是否存在，以及 checkpoint 的 `block_size`。
- `case_groups`
  - 每个 seed/case 一行。
  - 记录选中的 required term、token cap、max iters 和 eval-suite 路径。
- `probe_rows`
  - 每个 scaffold generation 一行。
  - 记录 `scaffold_prompt`、baseline continuation preview、scaffold continuation preview、prompt 是否截断、prompt 是否超过 block size、baseline/scaffold 命中数。
- `summary`
  - `baseline_continuation_hit_count`：原始 continuation 的 required-term 命中。
  - `scaffold_continuation_hit_count`：scaffold 后 continuation 的 required-term 命中。
  - `scaffold_generated_hit_count`：全文命中，包含 prompt 本身，不等同模型续写能力。
  - `prompt_truncated_count` 和 `prompt_over_block_count`：确保 prompt scaffold 没有被 context window 污染。
  - `probe_decision`：将结果分为 partial improvement、still no uptake、context blocked 或缺输出。

## v482 真实运行结果

真实输入：

```text
source=e/481/解释/model-capability-required-term-uptake
checkpoint=e/478/解释/model-capability-token-budget-stability/seeds/*/token-cap-12/ladder/rungs/max-iters-4/run/checkpoint.pt
term-limit=1
max-new-tokens=24
temperature=0.7
top-k=30
```

结果：

```text
status=pass
probe_decision=explicit_scaffold_still_no_required_term_uptake
case_group_count=20
probe_count=20
required_term_count=20
baseline_continuation_hit_count=0
scaffold_continuation_hit_count=0
scaffold_generated_hit_count=20
case_with_scaffold_hit_count=0
prompt_truncated_count=0
prompt_over_block_count=0
source_ready_count=2
```

解释：`block_size=8` 的 tiny checkpoint 无法承载长任务说明，所以本版选择每个 case 一个最短 required term，prompt 形如 `data:`、`text:`、`loss:`。报告显示 prompt 没有被截断，也没有超过 block size。尽管 required term 出现在 prompt 本身，continuation 仍然 0 命中，说明这个 tiny checkpoint 还不能通过显式词提示稳定续写 required terms。

## 测试覆盖

新增测试覆盖：

- fake generator 不输出 required term 时，probe 必须输出 `explicit_scaffold_still_no_required_term_uptake`。
- fake generator 输出一个 required term 时，probe 必须转为 `scaffold_prompt_partially_improves_required_term_uptake`。
- checkpoint/tokenizer 源材料缺失时，报告必须失败，并让 `--require-pass` 返回非零。
- JSON/CSV/text/Markdown/HTML 五类输出必须全部生成。
- 输入路径必须支持文件和目录。

这些测试保证 v482 既能跑真实 checkpoint，也能在单测里用 fake generator 稳定覆盖决策分支。

## 运行证据

运行证据位于：

```text
e/482/解释/model-capability-required-term-scaffold-probe/
e/482/图片/01-model-capability-required-term-scaffold-probe.png
e/482/解释/playwright-model-capability-required-term-scaffold-probe-snapshot.md
```

这些产物是 v478 checkpoint 的真实生成 probe，不是治理链的格式堆叠。它们说明下一步应转向 targeted micro-training repeat，而不是继续只做只读归档分析。

## 一句话总结

v482 证明当前 tiny checkpoint 即使看到不截断的 required-term scaffold，也没有把 required term 续写出来，下一步应做定向微训练验证。
