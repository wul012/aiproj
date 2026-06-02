# v694 minimal prompt objective readiness

## 本版目标和边界

v694 的目标是把 v692/v693 留下的下一步建议落成一个可检查的入口：只有在 contextual surface-policy 分支已经关闭、promotion 明确禁止、推荐路线确实是 `minimal_prompt_surface_objective` 时，才允许进入下一版 corpus contract。

本版不做三件事：

- 不训练 checkpoint。
- 不新增语料模式。
- 不把 contextual decode aid 的成功解释成模型 baseline 能力。

这个边界很重要。上一批 v679-v693 的结论是“上下文提示可以作为演示和诊断辅助”，不是“模型在最小提示词下已经学会 fixed/loss 分支”。

## 前置链路

v694 读取 v692 的 surface branch closeout：

```text
e/692/解释/model-capability-required-term-pair-surface-branch-closeout/
```

这个 closeout 已经汇总了 v679、v681、v684、v685、v688、v690、v691 七个节点，并给出：

- `contextual_decode_aid_ready=True`
- `promotion_allowed=False`
- `recommended_next_route=minimal_prompt_surface_objective`

v694 的任务是检查这些字段是否同时成立，再输出下一版可消费的 objective contract。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_objective_readiness.py`
  - builder 模块。
  - 负责读取 closeout 字段、构造 check rows、生成 objective、summary 和 interpretation。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_objective_readiness_artifacts.py`
  - artifact writer。
  - 负责 JSON、CSV、text、Markdown、HTML 五种输出，避免 builder 文件继续膨胀。

- `scripts/run_model_capability_required_term_pair_minimal_prompt_objective_readiness.py`
  - CLI 入口。
  - 支持输入 JSON 文件或 closeout 输出目录，支持 `--require-pass` 和 `--force`。

- `tests/test_model_capability_required_term_pair_minimal_prompt_objective_readiness.py`
  - focused tests。
  - 覆盖 readiness 通过、promotion 被错误打开、route 错误、输出渲染、目录定位。

- `e/694/解释/...`
  - 本版运行证据。
  - 后续 v695 corpus contract 可以引用这里的 objective 字段。

## 核心数据结构

### check rows

`check_rows` 是本版最重要的可审计结构。每一行包含：

- `id`
- `status`
- `actual`
- `detail`

当前检查项包括：

- `closeout_passed`
- `contextual_aid_closed`
- `promotion_blocked`
- `minimal_prompt_route_selected`
- `model_quality_not_promoted`

这些检查保护的是路线边界，而不是训练效果。

### objective

`objective` 写清下一条路线的约束：

- `objective_id=minimal_prompt_surface_objective`
- `claim_boundary=minimal prompt only; no contextual answer-bearing anchor`
- `target_prompt_surface=fixed= / loss=`
- `blocked_prompt_surface=contextual variants that reveal the other answer before the target prompt`
- `success_criterion=both fixed= and loss= produce their exact terms without contextual anchor across selected seeds`
- `recommended_corpus_mode=minimal_prompt_equals_surface_objective`

这些字段把“下一版该做什么”和“什么不能算成功”同时固定下来。

## 输入输出流程

CLI 流程是：

1. 定位输入。如果传入目录，就在目录下寻找 `model_capability_required_term_pair_surface_branch_closeout.json`。
2. 读取 JSON。
3. 调用 `build_minimal_prompt_objective_readiness()`。
4. 写出 JSON、CSV、text、Markdown、HTML。
5. 如果传了 `--require-pass` 且检查失败，退出码为 1。

本版输出的 JSON 是后续版本最应该消费的机器入口；HTML 和截图主要用于人工检查。

## 测试覆盖

focused tests 保护了四类风险：

- 正常 closeout 能打开 minimal prompt objective。
- 如果上一分支错误允许 promotion，readiness 必须失败。
- 如果推荐路线不是 minimal prompt，readiness 必须失败。
- 输出文件和 HTML/Markdown/text 渲染都能生成。
- locator 能接受文件或真实目录。

这组测试防止后续代码把 contextual aid 路线误接到 baseline promotion 上。

## 运行证据

本版证据在：

```text
e/694/解释/model-capability-required-term-pair-minimal-prompt-objective-readiness/
e/694/图片/v694-minimal-prompt-objective-readiness.png
```

截图展示了 objective boundary、readiness checks 和 next action。它证明的是“路线入口已经可复核”，不是“模型能力已经提升”。

## 一句话总结

v694 把 minimal-prompt 后续路线从人工建议收束为可检查 contract，为 v695 的语料契约和后续真实训练铺路。
