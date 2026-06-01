# v675 required-term pair route decision with dual-boundary

## 本版目标和边界

v675 的目标是读取 v674 alignment comparison，给 required-term pair 路线一个明确下一步：既然出现 generation/internal 双对齐候选，就先重复 seed，而不是继续发明新的治理链或 corpus 变体。

本版不训练新模型，不改模型结构，不改变 v674 的 comparison 规则。它是路线控制层，产物可以被后续 seed stability 使用。

## 前置链路

v674 显示：

- `aligned_pair_full_count=1`
- `best_source_labels=dual-boundary-seed-3535`
- `best_alignment_class=generation_internal_pair_full`

这意味着 dual-boundary seed 3535 已经比旧路线更完整。但单 seed 可能是偶然结果，所以 v675 不能给出强模型能力结论，只能要求多 seed 复核。

## 输入输出

输入：

- `e/674/解释/model-capability-required-term-pair-alignment-comparison-with-dual-boundary/`

输出：

- `e/675/解释/model-capability-required-term-pair-route-decision-with-dual-boundary/`

输出包括 JSON、CSV、text、Markdown 和 HTML。它们是路线决策证据，不是训练产物。

## 核心字段语义

- `selected_generation_route`: 历史上最好的 generation pair-full anchor。
- `internal_anchor_route`: 历史上最好的 internal pair-full anchor。
- `aligned_route`: 当前同时满足 generation/internal pair-full 的路线。
- `direct_promotion_ready`: 是否已经出现可重复验证的直接候选。
- `requires_internal_repair`: 是否仍必须优先做内部偏好修复。
- `requires_generation_preservation`: 是否后续仍需保护自由生成 pair-full。

## 本版结果

v675 给出的核心判断是：

- `decision=repeat_aligned_pair_full_candidate_before_promotion`
- `aligned_route_label=dual-boundary-seed-3535`
- `direct_promotion_ready=True`
- `next_action=repeat the aligned candidate across seeds`

这说明 dual-boundary 当前不是最终推广结论，而是多 seed 稳定性实验的入口。

## 测试与证据

测试运行：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_generation_internal_alignment_route_decision.py -q -o cache_dir=runs\pytest-cache-v675
```

测试保护 route decision 在三种场景下的分支：无 aligned candidate 时选 split-anchor，有 aligned candidate 时转 repeat，多格式输出保持稳定。

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/675/解释/model-capability-required-term-pair-route-decision-with-dual-boundary/`
- 截图: `e/675/图片/v675-route-decision-with-dual-boundary.png`
- 解释: `e/675/解释/说明.md`

一句话总结：v675 把模型能力路线从“继续修补”切到“重复验证已对齐候选”。
