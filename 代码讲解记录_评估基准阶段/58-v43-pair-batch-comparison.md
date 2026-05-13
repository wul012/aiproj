# 58-v43-pair-batch-comparison

## 本版目标、来源和边界

v43 的目标是把 v42 的“单次 pair generation artifact”推进到“固定 prompt suite 的批量左右 checkpoint 对比”。v42 能保存一次 prompt 的左右输出；v43 要回答更接近评估的问题：

```text
同一套 prompts 能不能稳定地跑两个 checkpoint？
每个 prompt 的左右输出是否相同、长度差异是多少？
这批结果能不能保存成 JSON/CSV/Markdown/HTML，供人工扫描和后续版本继续比较？
```

本版不做三件事：

- 不做自动打分或胜负判定；`generated_equal` 和 delta 只描述差异，不代表质量好坏。
- 不替代 v16/v35 的 eval suite；这里关注“两个 checkpoint 的横向生成差异”，不是单 checkpoint benchmark。
- 不把报告接入 registry 或 release gate；v43 先把本地批量证据链打稳。

## 本版处在评估链路的哪一环

当前链路是：

```text
benchmark prompt suite
 -> checkpoint selector / comparison
 -> single /api/generate-pair
 -> persisted pair artifact
 -> scripts/pair_batch.py
 -> pair_generation_batch.json
 -> pair_generation_batch.csv
 -> pair_generation_batch.md
 -> pair_generation_batch.html
 -> Playwright browser evidence
```

v43 的作用是把“人工点一次保存”升级成“按固定任务集批量保存”。这让后续做 pair batch trend、checkpoint family 对比、人工巡检清单时有稳定输入。

## 关键文件

```text
src/minigpt/pair_batch.py
scripts/pair_batch.py
src/minigpt/__init__.py
tests/test_pair_batch.py
README.md
b/43/解释/说明.md
```

`pair_batch.py` 是报告层；`scripts/pair_batch.py` 是真实 checkpoint 的 CLI；`tests/test_pair_batch.py` 保护字段、summary 和输出格式；`b/43` 保存运行截图和版本说明。

## 报告数据结构

`build_pair_batch_case_result` 输入一个 `PromptCase` 和左右两个 `GenerationResponse`，输出单个 case 结果：

```text
name
prompt
task_type
difficulty
expected_behavior
tags
max_new_tokens / temperature / top_k / seed
left
right
comparison
```

其中 `left` 和 `right` 保存：

```text
checkpoint_id
checkpoint
tokenizer
generated
continuation
generated_chars
continuation_chars
unique_continuation_chars
```

`comparison` 保存：

```text
same_checkpoint
generated_equal
continuation_equal
generated_char_delta
continuation_char_delta
unique_continuation_char_delta
```

delta 沿用 v41/v42 的方向：`right - left`。这样正数表示右侧更长，负数表示左侧更长。

## Batch Summary

`build_pair_batch_report` 把多个 case result 汇总成完整报告：

```text
schema_version = 1
kind = minigpt_pair_generation_batch
suite
left
right
case_count
generated_equal_count
continuation_equal_count
generated_difference_count
continuation_difference_count
avg_abs_generated_char_delta
avg_abs_continuation_char_delta
task_type_counts
difficulty_counts
task_type_summary
difficulty_summary
results
```

这里的核心不是“谁赢”，而是“差异是否稳定可见”。如果两个 checkpoint 在固定 prompts 上经常输出完全相同，可能说明模型差异小、seed/采样设置太稳定，或者 checkpoint 实际相同；如果 delta 很大，就需要人工再看 HTML/Markdown 里的具体 continuation。

## CLI 流程

新增命令：

```powershell
python scripts/pair_batch.py --left-checkpoint runs/minigpt/checkpoint.pt --right-checkpoint runs/minigpt-wide/checkpoint.pt --left-id base --right-id wide --suite data/eval_prompts.json --out-dir runs/pair_batch
```

脚本流程是：

```text
load_prompt_suite
 -> MiniGPTGenerator(left checkpoint)
 -> MiniGPTGenerator(right checkpoint)
 -> each PromptCase builds left/right GenerationRequest
 -> generate left/right responses
 -> build_pair_batch_case_result
 -> build_pair_batch_report
 -> write_pair_batch_outputs
```

输出包括：

```text
pair_generation_batch.json
pair_generation_batch.csv
pair_generation_batch.md
pair_generation_batch.html
```

命令行还会打印 cases、suite version、左右 checkpoint id、generated_equal_count、difference count 和 outputs 路径，方便截图证明脚本跑通。

## 为什么四种输出都是证据

JSON 是最完整的机器可读记录，后续 trend comparison 可以直接读取它。

CSV 适合快速筛选：看哪些 case 相同、哪些 case delta 最大。

Markdown 适合提交、讲解和人工 review，把关键 continuation 放在表格里。

HTML 适合浏览器打开，作为本地可视化证据；v43 用 Playwright 打开它并截图，证明报告不是只存在于 JSON 里。

## 测试覆盖链路

`tests/test_pair_batch.py` 覆盖：

- `build_pair_batch_case_result` 是否正确写入左右 checkpoint id、相等标记和 delta。
- `build_pair_batch_report` 是否写入 `kind=minigpt_pair_generation_batch`、suite、case count、summary 和 task counts。
- `write_pair_batch_outputs` 是否生成 JSON、CSV、Markdown 和 HTML。

v43 还用一个极小 PyTorch checkpoint smoke 跑 `scripts/pair_batch.py`，确认真实 CLI 可以加载 tokenizer、checkpoint、suite，并写出四类报告。

## 归档和截图证据

本版运行证据放在：

```text
b/43/图片
b/43/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-pair-batch-cli-smoke.png
03-pair-batch-structure-check.png
04-playwright-pair-batch-html.png
05-docs-check.png
```

其中 `02` 证明真实 CLI 跑通，`03` 证明输出结构可复核，`04` 证明 HTML 报告可在真实 Chrome 中打开，`05` 证明 README、b/43 和讲解索引闭环。

## 一句话总结

v43 把 MiniGPT 的 checkpoint 对比从“单 prompt 可保存”推进到“固定 prompt suite 可批量横向比较并形成稳定本地报告”的阶段。
