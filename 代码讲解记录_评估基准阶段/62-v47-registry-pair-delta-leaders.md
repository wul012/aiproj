# 第四十七版代码讲解：registry pair delta leaders

## 本版目标、来源和边界

v46 已经把 pair batch/trend 的摘要和 HTML 链接接进 run registry。它能回答“哪些 run 有 pair 报告”。v47 继续往评估可读性推进一层：registry 需要直接告诉评审者，多个 run 里哪些 prompt case 的左右 checkpoint 生成长度差异最大。

本版只读取已有的 `pair_batch/pair_generation_batch.json`，不改变 pair batch 生成脚本，不改变 trend 报告格式，也不重新推理模型。它把已有 case-level comparison 字段聚合到 registry JSON 和 HTML。

## 所在链路

```text
fixed prompt pair batch comparison
 -> pair batch trend comparison
 -> dashboard/playground report links
 -> registry pair report links
 -> registry pair delta leaders
```

这一层从“能打开报告”升级为“能先看到最值得打开的 case”。

## 关键文件

- `src/minigpt/registry.py`：新增 pair delta 行收集、summary、leaderboard 和 HTML 面板。
- `tests/test_registry.py`：新增跨 run delta 聚合测试，并扩展 registry 输出测试。
- `README.md`：记录 v47 当前能力、tag、截图和下一步。
- `b/47/解释/说明.md`：保存本版运行截图解释和 tag 含义。

## pair delta 行如何收集

`_collect_pair_delta_rows` 会遍历传入 registry 的每个 run：

```text
<run>/pair_batch/pair_generation_batch.json
```

每个 `results[]` 里的 `comparison` 字段会被抽成一行：

- `run_name`、`run_path`
- `case`、`task_type`、`difficulty`
- `generated_equal`、`continuation_equal`
- `generated_char_delta`、`continuation_char_delta`
- `abs_generated_char_delta`、`abs_continuation_char_delta`
- `suite_name`、`suite_version`
- `left_checkpoint_id`、`right_checkpoint_id`
- `report_path`

如果某个 case 没有 generated/continuation delta，它不会进入聚合榜，避免空数据污染排序。

## registry JSON 新增字段

`build_run_registry` 现在会写出：

```json
{
  "pair_delta_summary": {
    "case_count": 4,
    "run_count": 2,
    "max_abs_generated_char_delta": 9,
    "max_abs_continuation_char_delta": 10
  },
  "pair_delta_leaderboard": []
}
```

`pair_delta_summary` 用来判断覆盖量和最大差异；`pair_delta_leaderboard` 默认保留 top 10 case，按 `abs_generated_char_delta` 和 `abs_continuation_char_delta` 排序。

## HTML 面板如何读

`render_registry_html` 新增两个可见入口：

- `Pair deltas` 统计卡：显示 case 数、最大 generated delta、最大 continuation delta。
- `Pair Delta Leaders` 面板：列出 run/case、abs gen delta、原始 delta、equal 状态、task/difficulty、checkpoint pair 和 `pair batch` 报告链接。

这样评审者打开 `registry.html` 后，可以先看最大差异，再点回对应 run 的 pair batch 报告复查原始输出。

## 测试和证据

本版测试覆盖以下风险：

- 跨 run 聚合漏 case：`test_pair_delta_leaderboard_aggregates_runs` 检查 case_count 和 run_count。
- 排序错误：同一测试用 `-9` delta 确认 `abs_generated_char_delta=9` 的 run 排第一。
- HTML 漏面板：`test_write_registry_outputs` 检查 `Pair Delta Leaders`、`Abs Gen Delta` 和 case 名。
- 报告链接错误：测试检查 registry HTML 里相对 `pair_generation_batch.json` 链接。

运行证据保存在 `b/47/图片`，包括全量测试、smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v47 把 registry 从“多 run 报告入口”推进成“多 run pair 差异优先级列表”，更接近真实评估时先定位问题 case 的工作流。
