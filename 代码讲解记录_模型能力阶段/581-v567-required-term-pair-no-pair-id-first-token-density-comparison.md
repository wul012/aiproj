# v567 required-term pair no-pair-id first-token density comparison

## 本版目标和边界

v567 接在 v562、v564、v566 之后，目标是回答一个很具体的问题：first-token hint 加得多、加得少，是否真的让 equals-surface no-pair-id 方向更稳定。

这一版不新增 corpus mode，不重新训练，也不扩大模型。它复用已有 comparison builder，把三份真实训练稳定性报告合成一个可审计报告，用来约束后续路线。

## 前置能力

- v562：`equals_surface_no_pair_id_loss_balanced_repair`，三 seed 中只有 seed `1535` pair-full。
- v564：加入 full first-token prefix rows，仍然只有 seed `1535` pair-full。
- v566：改成 light bridge hints，退化为 `0/3` pair-full。
- v555：已经提供 equals-surface repair comparison 的只读报告生成能力。

v567 的价值不是新算法，而是把这些零散结论放到同一张证据表里，避免继续凭单版现象调语料。

## 关键输入输出

输入是三个稳定性报告目录：

- `e/562/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability/`
- `e/564/解释/model-capability-required-term-pair-no-pair-id-loss-balanced-first-token-stability/`
- `e/566/解释/model-capability-required-term-pair-no-pair-id-loss-balanced-light-first-token-stability/`

输出写入：

- `e/567/解释/model-capability-required-term-pair-no-pair-id-first-token-density-comparison/`

核心输出文件包括：

- `model_capability_required_term_pair_equals_surface_repair_comparison.json`
  - 机器可读主报告。
- `model_capability_required_term_pair_equals_surface_repair_comparison.csv`
  - term 行明细，方便继续统计。
- `model_capability_required_term_pair_equals_surface_repair_comparison.md`
  - 人工审阅版。
- `model_capability_required_term_pair_equals_surface_repair_comparison.html`
  - Playwright 截图来源。

## 核心字段解释

- `compared_report_count=3`
  - 表示这次确实比较了 v562、v564、v566 三份报告。
- `term_case_row_count=36`
  - 三份报告各有三 seed、两个 profile、两个 term，共 36 行 term 证据。
- `pair_full_profile_seed_count=1`
  - 所有路线加起来只有一个 profile/seed 层面的 pair-full 信号。
- `branch_competition_seed_count=0`
  - 这里没有新的 branch competition 分类，主要问题是覆盖迁移和退化。
- `source_reports`
  - 保留每份源报告的路径、corpus mode、seed_count 和 pair_full_seed_count。
- `term_rows`
  - 展开每个 seed/profile/term 的命中状态和生成片段，供后续人工复核。

## 运行流程

脚本入口是：

```powershell
python scripts\run_model_capability_required_term_pair_equals_surface_repair_comparison.py ...
```

运行流程是：

1. 对每个输入目录定位稳定性 JSON。
2. 读取每份报告的 seed rows 与 term rows。
3. 按 label 记录 source report。
4. 汇总 term 命中、pair-full profile 和 seed 级覆盖迁移。
5. 写出 JSON、CSV、text、Markdown、HTML 五类证据。

这一流程是只读复核：源报告不会被改写，v567 只增加新归档。

## 证据解读

三条路线结果如下：

```text
v562-loss-balanced      -> 1/3 pair-full
v564-full-first-token   -> 1/3 pair-full
v566-light-first-token  -> 0/3 pair-full
```

seed 层面的变化更关键：

- seed `1535` 是 v562/v564 的唯一 pair-full，到了 v566 退化为 fixed-only。
- seed `535` 在 v564 出现 fixed-only，但没有形成 pair-full。
- seed `2535` 在 v562/v566 出现 loss-only，在 v564 退化为 all-miss。

所以 first-token hint 没有把能力从单 seed 推到多 seed，只是在不同 seed 和不同 term 之间迁移覆盖。

## 测试和验证

本版复用已有 comparison 模块和测试，不新增代码路径。验证重点放在真实输入报告和产物可读性：

- comparison CLI 返回 `status=pass`、`failed_count=0`。
- Playwright MCP 打开 HTML 报告并截图，确认 source reports 和 summary 字段可见。
- 后续全量测试会继续覆盖 comparison builder、artifact writer 和既有 corpus tests。

## 链路角色

v567 是路线收口证据，不是模型提升证据。它把 v562-v566 的探索压缩成一个判断：

```text
不要继续微调 first-token hint 密度。
```

后续如果继续推进，应选择更明确的方向：要么对 v562/v564 的 seed `1535` 做 held-out replay，要么回到 seed/config policy，而不是继续添加近似的 prefix hint 变体。

## 一句话总结

v567 把 first-token hint 方向从“可能有用”收束为“覆盖迁移但不稳定”，为下一版路线决策提供了可复核证据。
