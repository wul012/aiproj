# 第六十三版代码讲解：release readiness comparison

## 本版目标、来源和边界

v63 的目标是给 v62 的 release readiness dashboard 增加跨版本比较层。v62 已经能把 registry、release bundle、project audit、release gate、request history summary 和 maturity summary 汇总成单个 `release_readiness.json`；但它只能回答“这一版是否 ready”，不能回答“这一版相对上一版是改善、退化，还是只是 panel 有变化”。

所以 v63 新增 release readiness comparison：读取多个 `release_readiness.json`，把第一个输入或 `--baseline` 指定的文件作为基线，生成 JSON、CSV、delta CSV、Markdown 和 HTML 产物。它解决的是发布治理证据的横向比较问题。

本版不做三件事：

- 不新增 release gate policy，也不改变 v62 的 readiness 判定规则。
- 不训练模型，不比较 checkpoint 的真实语言能力。
- 不把比较结果接入 registry，这一步留给后续版本做 release quality trend。

## 本版来自哪条路线

这一版属于项目成熟度阶段的发布治理路线：

```text
v60 request history summary context
 -> v61 request history audit gates
 -> v62 release readiness dashboard
 -> v63 release readiness comparison
```

前两版把本地推理请求历史变成可审计证据，v62 把分散证据汇成发布就绪 dashboard，v63 则把多个 dashboard 横向比较，让项目能说明发布质量是否真的变好。

## 关键新增和修改文件

- `src/minigpt/release_readiness_comparison.py`
  - 核心比较模块。
  - 负责读取 readiness JSON、抽取 summary/panel 字段、计算 baseline delta、渲染 Markdown/HTML，并写出 JSON/CSV 证据文件。
- `scripts/compare_release_readiness.py`
  - 命令行入口。
  - 支持重复传入 `--readiness`，也支持 `--baseline` 覆盖默认基线，便于本地 smoke、版本比较和后续自动化调用。
- `tests/test_release_readiness_comparison.py`
  - 单元测试。
  - 覆盖改善、退化、输出文件、HTML escape 和 Windows 路径安全等关键风险。
- `README.md`
  - 更新当前版本到 v63，加入 release readiness comparison 能力、tag、截图索引和下一步方向。
- `b/63/解释/说明.md`
  - 运行截图说明。
  - 解释每张截图对应的验证证据，而不只是罗列文件名。
- `代码讲解记录_项目成熟度阶段/78-v63-release-readiness-comparison.md`
  - 本篇讲解。
  - 把新增比较层放回 MiniGPT 的治理路线里说明。

## 核心数据结构

`build_release_readiness_comparison()` 返回一个字典，主要字段是：

```text
schema_version
title
generated_at
baseline_path
readiness_paths
summary
rows
deltas
recommendations
```

`rows` 是每个 `release_readiness.json` 被归一化后的表格行。它不是完整复制原始 dashboard，而是抽取跨版本比较最需要的字段：

```text
readiness_path
release_name
readiness_status
decision
readiness_score
gate_status
audit_status
audit_score_percent
request_history_status
maturity_status
ready_runs
missing_artifacts
fail_panel_count
warn_panel_count
action_count
panel_statuses
```

其中 `readiness_score` 来自固定顺序：

```python
STATUS_ORDER = {
    "blocked": 0,
    "incomplete": 1,
    "review": 2,
    "ready": 3,
}
```

这个分数只用于比较状态方向，不代表模型能力评分。比如 `blocked -> ready` 是 `+3`，`ready -> blocked` 是 `-3`。

`deltas` 是基线和每个后续 release 的差异说明。关键字段包括：

```text
status_delta
delta_status
audit_score_delta
missing_artifact_delta
fail_panel_delta
warn_panel_delta
changed_panels
explanation
```

`delta_status` 的语义是：

- `improved`：readiness 状态分数升高。
- `regressed`：readiness 状态分数降低。
- `panel-changed`：总体状态未变，但某些 panel 状态变化。
- `same`：总体状态和 panel 都没有变化。

`changed_panels` 使用 `panel_key:before->after` 的形式，例如：

```text
release_gate:fail->pass
request_history:warn->pass
```

这样 delta CSV 和 HTML 中既能显示变化，也能被后续脚本消费。

## 运行流程

CLI 的典型流程是：

```text
compare_release_readiness.py
 -> parse_args()
 -> build_release_readiness_comparison()
 -> write_release_readiness_comparison_outputs()
 -> print summary counts and output paths
```

模块内部流程是：

```text
读取 readiness_paths
 -> 如果指定 baseline_path，则把 baseline 放到第一位并去重
 -> 读取每个 release_readiness.json
 -> _row_from_report() 抽取 summary 和 panels
 -> _delta_from_baseline() 计算每个版本相对基线的变化
 -> _summary() 汇总 ready/blocked/improved/regressed 数量
 -> _recommendations() 生成操作建议
 -> 写出 JSON/CSV/delta CSV/Markdown/HTML
```

默认第一个 `--readiness` 是 baseline；如果传入 `--baseline`，就用它作为真正基线。这一点对发布复盘很重要，因为你可能想用当前已发布版本作为基线，再检查候选版本是否退化。

## 输出产物的作用

`release_readiness_comparison.json` 是主证据。它保留 summary、rows、deltas 和 recommendations，适合后续自动化读取。

`release_readiness_comparison.csv` 是版本矩阵。它适合表格查看每个 release 的 readiness status、gate/audit/request history 状态和 panel 数量。

`release_readiness_deltas.csv` 是差异表。它面向后续治理脚本和人工 review，重点记录 status delta、panel changes 和 explanation。

`release_readiness_comparison.md` 是轻量人工阅读版，可直接放入 release note 或版本归档。

`release_readiness_comparison.html` 是浏览器报告，适合截图和演示。它不是交互式服务，也不启动后台进程。

## 测试覆盖了什么

`tests/test_release_readiness_comparison.py` 覆盖四个核心判断：

- blocked baseline 对 ready current 时，`improved_count=1`，delta 为 `improved`，并能看到 `release_gate:fail->pass`。
- ready baseline 对 blocked current 时，`regressed_count=1`，验证 `--baseline` 类似的基线覆盖逻辑。
- 输出函数会同时生成 JSON、CSV、delta CSV、Markdown 和 HTML，并且 CSV/Markdown 中含有关键字段。
- HTML 渲染会 escape release name 和 title，避免 `<baseline>` 这类文本被当成 HTML 标签。

其中 Windows 路径安全也被纳入测试：fixture 目录名会过滤 `<`、`>` 等非法字符，避免本地测试在 Windows 上因为文件名失败。

## README、截图和归档的证明作用

README 证明 v63 已进入项目总能力列表、tag 列表、截图索引、代码讲解索引和学习路线图。

`b/63/图片` 保存真实运行证据：单测、CLI smoke、结构检查、Playwright 浏览器渲染和文档检查。

`b/63/解释/说明.md` 说明这些截图分别证明什么，避免截图只是“看起来跑过”。

本篇代码讲解负责把代码、产物、测试、README 和截图串成一条证据链。

## 和后续版本的关系

v63 还没有把 comparison 输出写入 run registry，也没有做长期趋势图。后续可以做：

```text
release_readiness_comparison -> registry release quality trend -> maturity summary release trend context
```

这样 release quality 就能像 benchmark scorecard 一样进入长期追踪。

## 一句话总结

v63 把 MiniGPT 的发布治理从“单版就绪总览”推进到“跨版本发布质量变化解释”，让项目能说明一版 release 相对基线到底是改善、退化，还是只是局部 panel 变化。
