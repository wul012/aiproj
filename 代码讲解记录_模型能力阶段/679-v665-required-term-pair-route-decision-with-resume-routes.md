# v665 required-term pair route decision with resume routes

## 本版目标和边界

v665 把 v664 的五路线 alignment matrix 转成 route decision。目标不是训练新模型，而是在真实 continuation 分支加入后重新确认路线选择。

本版不声称模型质量提升。它只回答：是否应该继续沿 naive checkpoint continuation 分支推进。

## 前置链路

v664 已经把五组 evidence 放入同一张矩阵：

- v621/v624: 内部 pair-full，但生成缺 fixed。
- v630/v631: 生成 pair-full，但内部只匹配 fixed。
- v640/v641: 内部 pair-full，但生成无命中。
- v660/v661: v630 到 internal-repair 的真实 resume，退化为 loss-only。
- v662/v663: v630 到 light-merge 的真实 resume，生成和内部都未恢复。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_generation_internal_alignment_route_decision.py e\664\解释\model-capability-required-term-pair-alignment-comparison-with-resume-routes --out-dir e\665\解释\model-capability-required-term-pair-route-decision-with-resume-routes --require-pass --force
```

## 核心输出字段

- `status=pass`: route decision 输入有效。
- `decision=repair_internal_preference_preserve_generation_pair_full`: 当前最佳策略仍是保护生成 pair-full，再修内部偏好。
- `selected_generation_route=loss-internal-joint-cycle`: v630 路线仍是生成锚点。
- `internal_anchor_route=joint-cycle-internal-repair`: v640 路线仍是内部锚点。
- `direct_promotion_ready=False`: 没有 aligned pair-full，不能晋升。

## 链路解释

v665 的价值在于让 continuation branch 的失败有正式位置。它不是只说“v660/v662 不行”，而是把它们放入已有决策器，证明即使纳入这些路线，最终选择仍然不变。

因此后续不应继续微调 lower-rate、bridge-repeat、light-merge 这类 naive continuation 参数。更合理的方向是：

- 做 continuation branch closeout。
- 对 constrained decode 或更明确的 dual-objective boundary 做独立评估。
- 保留 v630/v640 split anchors，而不是把它们强行合成一个 checkpoint。

## 运行证据

- JSON/CSV/text/Markdown/HTML: `e/665/解释/model-capability-required-term-pair-route-decision-with-resume-routes/`
- 解释: `e/665/解释/说明.md`
- 截图: `e/665/图片/v665-route-decision-with-resume-routes.png`

一句话总结：v665 把 resume branch 纳入路线决策后，确认最佳路线仍是“保留 v630 生成锚点，参考 v640 内部锚点”，而不是继续 naive continuation。
