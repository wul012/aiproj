# v568 required-term pair first-token route decision

## 本版目标和边界

v568 的目标是把 v567 的人工判断沉淀成可复核的 route decision：在 v562、v564、v566 三条 first-token density 相关路线里，选择下一步最值得保留的 baseline，并明确哪些路线不再继续投入。

这一版不训练模型，不扩展 corpus，不声称 tiny GPT 能力已经稳定提升。它只把路线选择变成 JSON/CSV/Markdown/HTML 产物，避免后续继续重复做相近的 first-token hint 变体。

## 前置能力

- v562 提供 no-pair-id loss-balanced 的三 seed 稳定性报告。
- v564 提供 full first-token rows 的三 seed 稳定性报告。
- v566 提供 light first-token hints 的三 seed 稳定性报告。
- v567 把三者合并成 comparison JSON。

v568 的输入就是 v567 的 comparison 输出：

```text
e/567/解释/model-capability-required-term-pair-no-pair-id-first-token-density-comparison/model_capability_required_term_pair_equals_surface_repair_comparison.json
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_first_token_route_decision.py`
  - 负责读取 comparison 结构、选择 route、生成 selected/rejected 列表。
- `src/minigpt/model_capability_required_term_pair_first_token_route_decision_artifacts.py`
  - 负责渲染 text、Markdown、HTML，并写出 CSV/JSON。
- `scripts/run_model_capability_required_term_pair_first_token_route_decision.py`
  - 命令行入口，支持输入 comparison JSON 或目录。
- `tests/test_model_capability_required_term_pair_first_token_route_decision.py`
  - 单测覆盖正常选择、失败输入、输出格式和目录定位。

## 核心数据结构

主报告字段：

- `status`
  - 输入结构是否可用于路线决策。
- `decision`
  - 本版核心判断；真实运行结果为 `stop_first_token_density_and_replay_best_baseline`。
- `source_comparison`
  - 指向 v567 comparison JSON。
- `selected_route`
  - 保留的下一步路线。
- `rejected_routes`
  - 被拒绝路线和拒绝原因。
- `summary`
  - 汇总 source report 数量、first-token density route 数量、stable route 数量和最大 pair-full seed 数。
- `interpretation`
  - 人类可读边界说明和下一步建议。

## 选择逻辑

builder 的选择规则比较保守：

1. 输入 comparison 必须是 `status=pass`。
2. 至少要有两份 source report。
3. 找到 `pair_full_seed_count` 最高的路线。
4. 如果最高路线并列，优先选择非 first-token-density 的简单路线。
5. first-token-density route 如果没有稳定收益，就进入 rejected routes。

在 v567 的真实输入里：

```text
v562-loss-balanced      -> 1/3 pair-full, non-density
v564-full-first-token   -> 1/3 pair-full, density route
v566-light-first-token  -> 0/3 pair-full, density route
```

所以 v568 选择 `v562-loss-balanced`，拒绝 v564/v566 的 first-token density 方向。

## 产物角色

- JSON 是后续脚本可消费的主证据。
- CSV 用来快速查看 selected/rejected route。
- Markdown 用于代码审阅和归档。
- HTML 用于运行截图。
- Playwright snapshot 证明页面关键字段可读。

这些都是只读派生产物，不回写 v562/v564/v566 的源报告。

## 测试覆盖

新增测试覆盖：

- 三 route 输入时，选择 `v562-loss-balanced`。
- 失败输入在 `--require-pass` 语义下返回失败。
- 输出 JSON、CSV、text、Markdown、HTML 五类产物。
- 输入为目录时能自动定位 comparison JSON。

这组测试保护的是 route decision 的契约：后续即便 comparison 报告格式有小变化，也不能悄悄把 first-token density 路线错误地选为下一步。

## 链路角色

v568 是 v559-v567 的收口层。它不增加实验分支，而是把接下来要做的事情缩小到一条：

```text
replay held-out equals-surface prompts for v562-loss-balanced before adding more corpus variants
```

这比继续新增 `*_first_token_*` corpus mode 更稳，也符合项目规则里“几版功能后要做收口、去重和路线判断”的节奏。

## 一句话总结

v568 把 first-token density 实验从连续试错收束为可执行路线决策：停掉 hint 密度微调，回到 v562-loss-balanced 做 held-out 复核。
