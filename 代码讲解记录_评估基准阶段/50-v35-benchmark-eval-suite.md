# 50-v35-benchmark-eval-suite

## 本版目标、来源和边界

v35 的目标是把原来的 fixed prompt eval suite 升级成更像 benchmark 的评估层。v16 已经能让同一个 checkpoint 跑固定 prompts，并输出 JSON/CSV/SVG；但这些 prompt 缺少任务类型、难度、预期行为和浏览器可读报告，所以它更像“固定生成样例”，还不足以支撑后续模型能力横向比较。

本版新增 suite metadata、case metadata、task/difficulty 汇总和 HTML 报告，让一次 eval suite 结果能说明：

```text
这套评估叫什么？
版本是多少？
包含哪些任务类型？
每个 prompt 的预期行为是什么？
不同任务类型下的 continuation 长度和 unique chars 如何？
```

本版不做三件事：

- 不引入外部大模型评分器。
- 不声称 tiny MiniGPT 已经具备真实 benchmark 能力。
- 不改变训练目标，只增强固定任务评估的结构化表达。

## 本版处在评估基准阶段的哪一环

当前评估链路是：

```text
data/eval_prompts.json
 -> PromptSuite / PromptCase
 -> scripts/eval_suite.py
 -> eval_suite.json / eval_suite.csv / eval_suite.svg / eval_suite.html
 -> dashboard / playground / registry artifact links
 -> generation quality analysis
```

v35 的作用是把“固定 prompt”变成“固定 benchmark suite”。后续 v36/v37 才适合继续做 dataset versioning 和 baseline model comparison。

## 关键文件

```text
data/eval_prompts.json
src/minigpt/eval_suite.py
scripts/eval_suite.py
src/minigpt/dashboard.py
src/minigpt/playground.py
src/minigpt/manifest.py
src/minigpt/registry.py
tests/test_eval_suite.py
README.md
b/35/解释/说明.md
```

核心仍在 `src/minigpt/eval_suite.py`。其余文件负责把新产物接入 CLI、artifact inventory、dashboard/playground 链接、registry 计数和文档。

## PromptSuite 和 PromptCase 字段语义

v35 新增 `PromptSuite`：

```text
name
version
description
language
cases
```

`PromptCase` 新增：

```text
task_type
difficulty
expected_behavior
tags
```

旧字段继续保留：

```text
name
prompt
max_new_tokens
temperature
top_k
seed
```

这保证旧的 suite JSON 仍然可读：如果某个 case 没有 `task_type`，默认是 `general`；没有 `difficulty`，默认是 `medium`。这样 v35 是兼容升级，而不是打断已有脚本。

## 默认中文 benchmark suite

`data/eval_prompts.json` 现在包含 5 类任务：

```text
continuation
qa
summary
structured
factual-consistency
```

每个 case 都带固定 seed、temperature、top_k 和 expected behavior。这里的 expected behavior 不是自动判分标准，而是给人类评审、后续规则检查和模型对比报告提供参照。

## eval_suite report 输出

`build_eval_suite_report` 现在保留原有顶层字段：

```text
case_count
avg_continuation_chars
avg_unique_chars
results
```

并新增 benchmark 区域：

```json
{
  "benchmark": {
    "suite_name": "minigpt-zh-benchmark",
    "suite_version": "1",
    "description": "...",
    "language": "zh-CN",
    "task_type_counts": {},
    "difficulty_counts": {},
    "task_type_summary": [],
    "difficulty_summary": []
  }
}
```

为了方便旧代码读取，`task_type_counts` 和 `difficulty_counts` 也保留在顶层。

## 输出产物

v35 的 eval suite 输出为：

```text
eval_suite.json
eval_suite.csv
eval_suite.svg
eval_suite.html
```

CSV 新增 task metadata 列：

```text
task_type
difficulty
expected_behavior
tags
```

SVG 继续作为轻量图表，但标题会显示 suite name/version，并在每行标签里显示 task/difficulty。HTML 是本版新增的浏览器报告，包含 summary cards、task summary 和 prompt results 表格。

## CLI 行为

`scripts/eval_suite.py` 现在用 `load_prompt_suite` 读取 suite，而不是只读取 cases。命令输出新增：

```text
suite_name=...
suite_version=...
task_types=...
```

这让截图、CI 日志和归档说明不用打开 JSON，也能知道本次跑的是哪套 benchmark。

## 下游 artifact 链路

本版把 `eval_suite.html` 接入：

```text
manifest artifact inventory
dashboard artifact list
playground artifact list
registry artifact paths
```

Dashboard 的 eval suite 区域也会展示 task counts 和 difficulty counts。这样 benchmark 不只是一个孤立文件，而能继续被现有实验治理链路发现。

## 测试覆盖链路

`tests/test_eval_suite.py` 覆盖：

- 默认 suite 至少包含 5 个 case，并含 `qa`、`medium` 等 metadata。
- 新 JSON 对象格式能读取 suite name/version/language/case tags。
- 旧 list payload 仍然兼容，缺省为 `general`/`medium`。
- `PromptResult` 会携带 task_type 和 difficulty。
- report 会生成 benchmark summaries。
- 输出会生成 JSON/CSV/SVG/HTML，CSV 包含 task metadata，HTML 包含 `Prompt Results`。

同时回归跑了 dashboard、manifest、playground、registry 相关测试，确认新增 HTML artifact 没有破坏现有链路。

## 归档和截图证据

本版运行证据放在：

```text
b/35/图片
b/35/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-benchmark-eval-suite-smoke.png
03-benchmark-eval-suite-structure-check.png
04-playwright-benchmark-eval-suite.png
05-docs-check.png
```

其中 `02` 证明 benchmark suite fixture 能导出四类产物；`03` 证明 JSON、CSV、SVG、HTML 和下游 artifact 链路结构正确；`04` 证明新增 HTML 报告可以用真实 Chrome 打开；`05` 证明 README、b/35 归档和评估基准阶段讲解索引已经闭环。

## 一句话总结

v35 把 MiniGPT 的 fixed prompt eval suite 从“固定生成样例”推进到“带任务语义和浏览器报告的 benchmark prompt suite”，为后续 dataset versioning 和 baseline model comparison 铺路。
