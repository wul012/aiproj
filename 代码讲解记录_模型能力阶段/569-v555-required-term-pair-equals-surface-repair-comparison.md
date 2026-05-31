# v555 required-term pair equals-surface repair comparison 代码讲解

## 本版目标和边界

v552 和 v554 都是围绕 seed `1535` 的 equals surface 修复：前者偏 fixed，后者做 balanced。两个版本都没有 pair-full，但命中项正好互补。v555 的目标是把这种互补现象做成可复核诊断，防止下一步继续凭印象训练。

本版不训练、不改 tokenizer、不宣称模型能力提升。它只读取已有归档，判断 repair 之间是否出现 branch competition。

## 前置链路

- v550：held-out replay 找到 `equals + seed 1535` 的唯一缺口。
- v551：把缺口定位为 fixed term surface gap。
- v552：fixed-biased repair 命中 fixed，但 loss 失败。
- v554：balanced repair 命中 loss，但 fixed 失败。

v555 接在这两次真实训练之后，承担“比较与决策收口”的角色。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_equals_surface_repair_comparison.py`
  - 核心诊断模块。
  - 提供报告定位、JSON 读取、comparison report 构建和 exit code 解析。
- `src/minigpt/model_capability_required_term_pair_equals_surface_repair_comparison_artifacts.py`
  - 负责 JSON/CSV/text/Markdown/HTML 输出。
  - 不参与判定逻辑，避免报告渲染和诊断规则混在一个大文件里。
- `scripts/run_model_capability_required_term_pair_equals_surface_repair_comparison.py`
  - 命令行入口。
  - 接收多个 report 或 report 目录，输出 v555 多格式证据。
- `tests/test_model_capability_required_term_pair_equals_surface_repair_comparison.py`
  - 用最小 fixture 覆盖 branch competition、pair-full found、无效输入和 artifacts。

## 核心数据结构

`source_reports` 保存输入报告摘要：

```json
{
  "source_label": "v552-fixed-repair",
  "status": "pass",
  "corpus_mode": "equals_surface_fixed_repair",
  "pair_full_seed_count": 0
}
```

`term_rows` 是 case 级证据：

```json
{
  "source_label": "v554-balanced-repair",
  "seed": 1535,
  "profile_id": "default",
  "term": "loss",
  "prompt": "loss=",
  "continuation_hit": true
}
```

`branch_rows` 是本版的判断核心：

```json
{
  "seed": "1535",
  "fixed_hit_reports": ["v552-fixed-repair"],
  "loss_hit_reports": ["v554-balanced-repair"],
  "pair_full_profile_reports": [],
  "branch_competition": true
}
```

判断条件很克制：fixed/loss 两个目标项必须跨 report 都有命中，同时没有任何单个 report/profile 同时命中 fixed 和 loss，才标记为 branch competition。

## 运行流程

1. CLI 将输入路径规范化为 `model_capability_required_term_pair_colon_immediate_stability.json`。
2. builder 读取每个 stability report 的 `settings`、`summary`、`seed_rows` 和内嵌 `seed_reports[*].replay_report.case_rows`。
3. 诊断模块按 seed 聚合 fixed/loss 的命中 report。
4. 如果 union 覆盖 `fixed,loss` 但 pair-full profile 为空，则输出 `required_term_pair_equals_surface_branch_competition_detected`。
5. artifacts 模块写出 JSON、CSV、text、Markdown 和 HTML，供 README、截图和后续版本消费。

## 真实结果

v555 对 v552/v554 的真实归档输出：

```text
status=pass
decision=required_term_pair_equals_surface_branch_competition_detected
branch_competition_seed_count=1
pair_full_profile_seed_count=0
union_hit_terms=fixed,loss
```

这说明两个修复方向都不是“完全没学到”，而是 tiny 模型在 equals surface 上无法同时稳定保住两个分支。

## 测试覆盖

测试不是只检查文件能写出，而是覆盖三类行为：

- `fixed` 只在第一个 report 命中、`loss` 只在第二个 report 命中时，必须判定 branch competition。
- 如果某个 report/profile 同时命中 fixed/loss，必须改判 pair-full found，避免把好结果误判为竞争。
- 输入少于两个 report 或 corpus mode 不是 equals surface 时，`--require-pass` 会返回失败。

## 归档角色

`e/555` 保存 HTML 报告、JSON/CSV/text/Markdown 输出、Playwright snapshot 和截图。它不是训练产物，而是一个决策检查点：下一版应围绕“把 fixed/loss 绑定在同一个目标里”或“先隔离 prompt 分支”推进，而不是继续随机调样本比例。

一句话总结：v555 把 v552/v554 的摆动负结果变成可测试的 branch-competition 诊断，为后续能力实验收紧了方向。
