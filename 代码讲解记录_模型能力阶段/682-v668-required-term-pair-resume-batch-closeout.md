# v668 required-term pair resume batch closeout

## 本版目标和边界

v668 是 v659-v668 十版推进的收尾版本。它把本批次的真实 checkpoint continuation、路线矩阵、分支 closeout 和 constrained decode feasibility 汇总成一个可检查的批次结论。

本版不新增训练，不声称模型质量提升；它的角色是验证和收口。

## 本批次完成了什么

### 真实 resume 能力

v659 让 `model_capability_required_term_pair_coexistence_refresh` 支持 `--resume-checkpoint`，并把 `training_mode`、`resume_checkpoint`、`resume_checkpoint_exists` 写入报告。

这让后续不再只是单语料近似 schedule，而能真正从已有 checkpoint 继续训练。

### 两条 continuation 负证据

v660 从 v630 pair-full checkpoint 继续到 internal-repair corpus，但自由生成退化为 loss-only。

v662 使用 lower-rate light-merge continuation，仍然退化为 loss-only。

v661/v663 的 forced-choice 诊断证明这两条 continuation 没有恢复 aligned internal preference。

### 路线矩阵和决策

v664 修正 comparison 边界，让 `internal_expected_best_terms=[]` 成为有效负样本，而不是输入错误。

v665 route decision 确认：

- `selected_generation_route=loss-internal-joint-cycle`
- `internal_anchor_route=joint-cycle-internal-repair`
- `direct_promotion_ready=False`

### 分支 closeout

v666 泛化 closeout 输出，使自定义 `next_route` 真正进入 decision 和 next action，并在包含 resume source 时记录 `resume_routes_rejected`。

### constrained decode 边界

v667 验证 v630 上的 constrained decode 只带来 partial gain：

- `constrained_hit_count=1`
- `constrained_pair_full=False`
- `fixed_constrained_hit=False`

这说明当前 decode-only profile 不能 promotion。

## v668 归档角色

v668 新增 `e/668/解释/v659-v668-batch-closeout.html`，把版本角色、批次决策和证据边界放在一个可截图页面里。

它的核心判断是：

- 停止 naive checkpoint continuation variants。
- 不把工程 resume 能力误报成模型质量提升。
- 下一步转向 explicit dual-objective boundary 或更细的 constrained decode 分析。

## 验证计划

本版收尾需要运行：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v668-full
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v668
git diff --check
```

截图通过 Playwright MCP 完成，归档到 `e/668/图片/v668-batch-closeout.png`。

一句话总结：v668 把 v659-v668 从“持续尝试”收束成“resume 能力已建立，但模型路线仍需新目标设计”的清晰结论。
