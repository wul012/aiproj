# v499 model capability required-term pair prompt separation audit

## 本版目标和边界

v499 的目标是解释 v498 的负结果。v498 已经复用 v497 的 partial checkpoints，扫过短生成、长生成、top-k sampling 和 open sampling，但 `fixed/loss` 仍然没有恢复 full-hit。继续加训练预算或继续加解码 profile 的收益已经很低，所以本版回到训练语料本身，检查 prompt 和 target 是否真的分离。

本版不训练新 checkpoint，不修改 v497/v498 的历史产物，也不声明模型质量提升。它只是新增一个只读 audit：从 v498 decoding sweep 反查 v497 capacity sweep，再读取真实 capacity corpus，量化同一 prompt 后是否出现了另一个 required term。

## 前置路线

- v492 证明单目标 tiny checkpoint 可以学到 `fixed/loss/four/chain`。
- v493 证明单目标能力在 seed 间相对稳定。
- v494 进入两目标 pair 后变成 partial-only。
- v495 出现一次 `fixed/loss` full-hit，但 v496 证明它不稳定。
- v497 扫训练步数、embedding 和 corpus density，仍没有恢复 full-hit。
- v498 扫解码策略，仍没有恢复 full-hit。
- v499 开始检查 corpus row design，而不是继续盲目调参数。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_prompt_separation_audit.py`
  - 负责定位 v498 JSON，读取 v497 capacity report，解析 capacity corpus。
  - 输出 target rows 和 term rows。
  - 核心判断是 `prompt_separation_ready` 与 `corpus_revision_recommended`。
- `src/minigpt/model_capability_required_term_pair_prompt_separation_audit_artifacts.py`
  - 输出 JSON、CSV、text、Markdown 和 HTML。
  - HTML 把 summary、target summary、term rows 放在同一页，方便截图审阅。
- `scripts/run_model_capability_required_term_pair_prompt_separation_audit.py`
  - CLI 入口。
  - 支持传入 v498 JSON 或目录，支持 `--source-capacity-sweep` 覆盖 v497 report，支持 `--require-pass` 和 `--force`。
- `tests/test_model_capability_required_term_pair_prompt_separation_audit.py`
  - 覆盖泄露语料、干净语料、坏输入、summary helper 和 CLI require-pass。
- `e/499/`
  - 保存真实运行产物、Playwright MCP snapshot 和截图。

## 核心数据结构

输入是 v498：

```text
model_capability_required_term_pair_decoding_sweep.json
```

其中最重要的是：

```text
summary.pair_decoding_sweep_decision = pair_decoding_sweep_partial_only
targets[].capacity_run_id
targets[].terms[].scaffold_prompt
targets[].terms[].term
source_required_term_pair_capacity_sweep
```

builder 会用 `source_required_term_pair_capacity_sweep` 继续读取 v497：

```text
capacity_rows[].capacity_run_id
capacity_rows[].capacity_corpus_path
```

然后每个 term row 会统计：

- `prompt_prefix_line_count`：以该 scaffold prompt 开头的训练行数量。
- `target_after_prompt_line_count`：prompt 后包含目标 term 的行数量。
- `other_after_prompt_line_count`：prompt 后包含另一个 required term 的行数量。
- `negative_contrast_leak_count`：类似 `not loss` / `not fixed` 的 contrast 负例数量。
- `pair_header_shared_context_count`：pair header 里同时出现两个 term 和该 prompt 的数量。
- `prompt_separation_ready`：是否没有直接泄露，并且仍有目标行。

## 运行流程

1. CLI 定位 v498 decoding sweep report。
2. builder 校验 v498 是 `pass`，且仍是 `pair_decoding_sweep_partial_only`。
3. 从 v498 读取 v497 capacity sweep 路径。
4. 根据 `capacity_run_id` 找到真实 capacity corpus。
5. 对每个 target、每个 term 扫描训练行。
6. 汇总 target rows、term rows 和 summary。
7. 写出 JSON/CSV/text/Markdown/HTML，并用 Playwright MCP 截图。

## 真实结果解释

真实 v499 结果是：

```text
status=pass
decision=required_term_pair_prompt_separation_revision_needed
prompt_separation_ready=False
direct_prompt_other_term_leak_count=960
negative_contrast_leak_count=960
pair_header_shared_context_count=960
corpus_revision_recommended=True
```

这不是测试夹具里的假数，而是从 v497 的两个真实 capacity corpora 里扫出来的。每个 target 有两个 term，每个 term 都出现 240 行 direct leak：

```text
fixed:fixed not loss
loss:loss not fixed
```

这些行原意是做 contrast，但对 char-level tiny GPT 来说，它们也把另一个 term 放进了同一 prompt 的 continuation 区域。于是模型很容易学到 pair 共现或偏向一个高频 continuation，而不是学会 `fixed:` 只续 `fixed`、`loss:` 只续 `loss`。

## 测试覆盖

测试不是只检查函数能跑，而是保护几个关键边界：

- leaky corpus 必须被判定为 `required_term_pair_prompt_separation_revision_needed`。
- separated corpus 必须能得到 `required_term_pair_prompt_separation_ready`。
- source decoding sweep 失败、source capacity report 缺失、corpus 缺失都必须进入 `fail` 或 require-pass 失败。
- summary helper 必须把 direct leak、negative leak、shared context 计入对应计数。
- CLI 在 `--require-pass` 下遇到缺失 corpus 必须返回 `1`。

## 证据角色

`e/499` 是只读诊断证据，不是训练产物。JSON/CSV 用于后续脚本消费，Markdown/HTML 用于人工审阅，截图证明 HTML 报告可打开且关键数字可见。

本版最重要的结论不是“模型变好了”，而是“下一版该怎么训练更合理”：先生成 contrast-free pair corpus，再跑一个小型 retraining check。

## 一句话总结

v499 把 `fixed/loss` 的失败原因从“可能是解码问题”推进到“已有训练语料存在 prompt-target 泄露证据”，为下一版 contrast-free pair corpus 提供了明确依据。
