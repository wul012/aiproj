# v559 required-term pair equals-surface tied wider embedding 代码讲解

## 本版目标和边界

v556 的 `equals_surface_tied_repair` 没能修复 seed `1535`，v557 证明 `fixed=` 的内部偏好会滑向 `loss`，v558 又否定了简单 constrained decoding。v559 继续沿着同一条证据链，检查一个更朴素的问题：是不是模型太小，导致 tied equals-surface 目标放不下。

本版不新增模型结构，不新增治理链，也不把单次结果包装成模型质量提升。它只做一次真实训练对照：保持 v556 的语料模式、seed、训练步数和 decode 设置，把 `n_embd` 从 `64` 提到 `96`。

同时，按用户最新要求，本版把仓库规则中的自动持续推进默认目标从 8 个中/大版本修正为 10 个。这个修改是协作节奏规则，不参与模型能力结论。

## 前置链路

- v555：比较 v552/v554，确认 equals-surface repair 存在 branch competition。
- v556：新增 tied repair，`loss=` 可命中但 `fixed=` 仍失败。
- v557：teacher-forced forced-choice 说明 `fixed=` 内部评分更偏向 `loss`。
- v558：decode-only constraint 不可行，甚至破坏 `loss=` 默认命中。

v559 的位置是容量验证：如果加宽 embedding 能恢复 pair-full，说明后续可以考虑容量路线；如果不能，就要回到目标函数或语料结构。

## 关键文件

- `e/559/解释/model-capability-required-term-pair-equals-surface-tied-wider-embd/model_capability_required_term_pair_colon_immediate_stability.json`
  - 主稳定性报告。
  - 记录 `n_embd=96`、seed `1535`、训练预算、pair-full 汇总和最终 decision。
- `e/559/解释/model-capability-required-term-pair-equals-surface-tied-wider-embd/seed-runs/seed-1535/`
  - 真实训练产物，包括 corpus、checkpoint、tokenizer 和 metrics。
- `e/559/解释/model-capability-required-term-pair-equals-surface-tied-wider-embd/seed-reports/seed-1535/pair-generation-profile-replay/`
  - replay 证据，说明 default 与 newline suppression 都没有命中 `fixed` 或 `loss`。
- `e/559/图片/01-model-capability-required-term-pair-equals-surface-tied-wider-embd.png`
  - Playwright 截图，证明 HTML 报告可打开且核心指标可见。
- `AGENTS.md`
  - 协作规则更新：未来默认持续推进 10 个中等或较大版本。

## 输入输出格式

输入仍然是现有稳定性 runner 的 CLI 参数：

```text
corpus_mode=equals_surface_tied_repair
seed=1535
n_embd=96
top_k=2
temperature=0.8
max_iters=1400
```

主报告输出的核心字段是：

```json
{
  "status": "pass",
  "decision": "required_term_pair_colon_immediate_not_stable",
  "summary": {
    "seed_count": 1,
    "pair_full_seed_count": 0,
    "pair_full_seed_rate": 0.0
  }
}
```

replay 报告继续保存每个 prompt/profile 的生成结果。v559 的关键行可以概括为：

```text
default fixed -> fixed=01=fixxed=01
default loss  -> loss=01s fixxed p
suppress_newline_tokens fixed -> fixed=01=fixxed=01
suppress_newline_tokens loss  -> loss=01s fixxed p
```

也就是说，加宽后没有出现“隐藏命中”，newline suppression 也没有救回任一分支。

## 运行流程

1. runner 生成 `equals_surface_tied_repair` corpus。
2. 用 seed `1535` 训练一个 `n_embd=96` 的 tiny checkpoint。
3. 保存训练 metrics、checkpoint 和 tokenizer。
4. 对 `fixed=`、`loss=` prompt 分别运行 default 与 `suppress_newline_tokens` replay。
5. 汇总 pair-full seed count、profile hit count 和稳定性 decision。
6. 用 Playwright 打开 HTML 报告并归档截图。

## 真实结果

真实命令返回：

```text
status=pass
decision=required_term_pair_colon_immediate_not_stable
pair_full_seed_count=0/1
stable_pair_full=False
```

replay 汇总为：

```text
default_continuation_hit_count=0
suppression_continuation_hit_count=0
suppression_hit_delta=0
suppression_pair_full_delta=0
```

这个结果弱于 v556。v556 的 tied repair 至少还保留一个 `loss=` 命中；v559 扩大 embedding 后，`fixed=` 与 `loss=` 都没有命中。

## 验证覆盖

本版复用了已测试的稳定性 runner 和 artifact writer，没有新增 Python 模块。收口验证应覆盖：

- 全量 pytest，确认既有训练治理和模型能力测试没有回归。
- source encoding hygiene，防止中文文档和脚本编码破坏 CI。
- `git diff --check`，防止 Markdown、Python 和归档文件出现尾随空白。
- Playwright screenshot，证明 HTML 证据不是只写文件、不可查看。

## 归档角色

`e/559` 是容量假设的负证据归档，不是新功能链路的起点。它的作用是把“再加宽一点也许就好了”的直觉变成可复核数据：至少在 seed `1535`、`n_embd=96`、同等训练预算下，这条路没有改善。

一句话总结：v559 证明 tied equals-surface 的 seed `1535` 问题不能靠简单加宽 embedding 修复，下一步应转向目标函数和语料结构。

