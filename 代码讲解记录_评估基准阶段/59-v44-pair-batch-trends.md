# 59-v44-pair-batch-trends

## 本版目标、来源和边界

v44 的目标是把 v43 的“单份固定 prompt pair batch 报告”推进到“多份 pair batch 报告之间的趋势比较”。v43 能回答同一套 prompts 在两个 checkpoint 上的左右差异；v44 继续回答：

```text
多份 pair_generation_batch.json 之间，哪些 case 的相等状态发生变化？
哪些 case 的 generated / continuation 字符长度 delta 最大？
不同版本或不同 checkpoint pair 的 summary 能不能放在一个 HTML/CSV 里横向看？
```

本版不做三件事：

- 不重新调用模型；它只读取已经保存的 `pair_generation_batch.json`。
- 不自动判断模型质量；趋势报告只描述 equality variants 和 delta。
- 不接入 release gate；v44 先把 pair batch 的跨报告证据格式稳定下来。

## 本版处在评估链路的哪一环

当前链路是：

```text
benchmark prompt suite
 -> scripts/pair_batch.py
 -> pair_generation_batch.json
 -> multiple saved pair batch reports
 -> scripts/compare_pair_batches.py
 -> pair_batch_trend.json
 -> pair_batch_trend.csv
 -> pair_batch_trend.md
 -> pair_batch_trend.html
 -> Playwright browser evidence
```

v44 的意义是让 pair batch 从“单次实验输出”变成“可以跨版本复盘的时间线材料”。后续如果把 trend 链接进 dashboard、registry 或 playground，就能更自然地查看模型能力变化。

## 关键文件

```text
src/minigpt/pair_trend.py
scripts/compare_pair_batches.py
src/minigpt/__init__.py
tests/test_pair_trend.py
README.md
b/44/解释/说明.md
```

`pair_trend.py` 负责读取和汇总多份 batch report；`compare_pair_batches.py` 是命令行入口；`tests/test_pair_trend.py` 保护 schema、summary、case trends 和输出格式；`b/44` 保存运行截图和版本说明。

## 输入格式

v44 读取 v43 生成的：

```text
pair_generation_batch.json
```

每份 report 至少包含：

```text
kind = minigpt_pair_generation_batch
suite
left
right
case_count
generated_equal_count
generated_difference_count
avg_abs_generated_char_delta
results[].name
results[].task_type
results[].difficulty
results[].comparison
```

`load_pair_batch_report` 会校验 JSON object 和 `kind`，并给 payload 附上 `_source_path`，让默认 report name 可以从路径推出来。

## Trend Report Schema

`build_pair_batch_trend_report` 输出：

```text
schema_version = 1
kind = minigpt_pair_batch_trend
report_count
case_count
changed_generated_equal_cases
max_abs_generated_char_delta
max_abs_continuation_char_delta
reports
case_trends
largest_generated_delta_cases
```

`reports` 是每份 batch 的 summary：

```text
name
path
suite_name / suite_version
left_checkpoint_id / right_checkpoint_id
case_count
generated_equal_count
generated_difference_count
avg_abs_generated_char_delta
```

`case_trends` 按 case name 聚合：

```text
name
task_type
difficulty
appearances
generated_difference_reports
continuation_difference_reports
generated_equal_variants
continuation_equal_variants
max_abs_generated_char_delta
max_abs_continuation_char_delta
entries
```

如果某个 case 在一份报告里 `generated_equal=True`，另一份报告里 `False`，它会进入 changed generated-equal cases。

## CLI 流程

新增命令：

```powershell
python scripts/compare_pair_batches.py runs/pair_batch_v1/pair_generation_batch.json runs/pair_batch_v2/pair_generation_batch.json --name v1 --name v2 --out-dir runs/pair_batch_trend
```

脚本流程是：

```text
load_pair_batch_report for each path
 -> build_pair_batch_trend_report
 -> write_pair_batch_trend_outputs
```

输出包括：

```text
pair_batch_trend.json
pair_batch_trend.csv
pair_batch_trend.md
pair_batch_trend.html
```

命令行会打印 reports、cases、changed_generated_equal_cases、max_abs_generated_char_delta 和 outputs 路径，方便截图证明脚本跑通。

## 为什么四种输出都是证据

JSON 是完整趋势记录，后续可以被 dashboard 或 registry 读取。

CSV 是扁平化的 case/report 明细，适合筛选某个 case 在不同报告里的 delta。

Markdown 适合提交和人工 review，能快速看到 report summary 和 case trends。

HTML 适合浏览器打开，v44 用 Playwright 打开它并截图，证明趋势报告不是只存在于 JSON 中。

## 测试覆盖链路

`tests/test_pair_trend.py` 覆盖：

- `build_pair_batch_trend_report` 能发现同一 case 的 generated equality 变化。
- `load_pair_batch_report` 能读取 report 并保留 source path。
- `--name` 数量与 report 数量不一致时会报错。
- `write_pair_batch_trend_outputs` 会生成 JSON、CSV、Markdown 和 HTML。

v44 的 smoke 还会生成两份小型 pair batch JSON，再通过真实 CLI `scripts/compare_pair_batches.py` 输出趋势报告，并检查四类产物。

## 归档和截图证据

本版运行证据放在：

```text
b/44/图片
b/44/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-pair-trend-cli-smoke.png
03-pair-trend-structure-check.png
04-playwright-pair-trend-html.png
05-docs-check.png
```

其中 `02` 证明真实 CLI 跑通，`03` 证明输出结构可复核，`04` 证明 HTML 报告可在真实 Chrome 中打开，`05` 证明 README、b/44 和讲解索引闭环。

## 一句话总结

v44 把 MiniGPT 的 pair batch 从“单份固定 prompt 横向比较报告”推进到“多份 batch report 可以跨版本、跨 checkpoint pair 做趋势复盘”的阶段。
