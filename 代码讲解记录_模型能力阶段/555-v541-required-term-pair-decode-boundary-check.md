# v541 required-term pair decode boundary check 代码讲解

## 本版目标和边界

v540 用更高训练预算仍得到 `pair_full_seed_count=0/3`，说明继续盲目加 `repeat` 和 `max_iters` 不是好路线。v541 增加一层轻量 decode boundary check：读取 v540 stability report 内嵌的三个 seed checkpoint，不重训，只改变 replay 时的 `top_k`、`max_new_tokens` 等解码边界，检查 fixed/loss pair 是否能被重新表达出来。

本版不新增训练目标，不改变模型结构，也不把单个 seed 的恢复解释成稳定模型能力。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_decode_boundary_check.py`
  - 核心 builder。负责读取 stability report、为每个 seed 重建 generation profile replay 输入、运行多组 decode spec，并汇总 pair-full 是否改善。
- `src/minigpt/model_capability_required_term_pair_decode_boundary_check_artifacts.py`
  - 产物渲染层。输出 JSON、CSV、text、Markdown、HTML，并把每个 seed/spec 的 replay sidecar 写到 `replay-reports/`。
- `scripts/run_model_capability_required_term_pair_decode_boundary_check.py`
  - CLI 入口。接受 v540 JSON 或目录，支持 `--out-dir`、`--force`、`--require-pass`。
- `tests/test_model_capability_required_term_pair_decode_boundary_check.py`
  - 单测覆盖改善、无改善、缺 seed report 失败、sidecar 输出四类路径。

## 核心数据结构

`DEFAULT_DECODE_SPECS` 是本版的解码边界矩阵：

```text
greedy-k1-t020-n12
wider-k2-t020-n12
wider-k4-t020-n12
greedy-k1-t020-n20
```

每个 spec 固定三类字段：

```text
top_k
temperature
max_new_tokens
```

builder 从 v540 stability report 中取出两类输入：

- `seed_rows`：每个 seed 在原 stability 下是否 pair-full。
- `seed_reports`：每个 seed 的真实 training report，其中包含 checkpoint 和 tokenizer 路径。

然后 `_source_report_for_seed()` 把每个 seed 转成 generation profile replay 能消费的最小 source report：

```text
targets        -> fixed/loss 两个 term
training_rows  -> 单 seed checkpoint/tokenizer
probe_rows     -> fixed 与 loss 的 generation seed
```

这样 v541 复用 v532 的 replay 能力，而不是重新写一套生成逻辑。

## 运行流程

`build_model_capability_required_term_pair_decode_boundary_check()` 的流程是：

1. 校验输入 report 状态、`seed_rows`、`seed_reports` 和 decode spec。
2. 对每个 `decode_spec x seed` 调用 `build_model_capability_required_term_pair_generation_profile_replay()`。
3. 从 replay summary 读取 default/suppression 的 pair-full 和 continuation hit。
4. 生成逐行 CSV 记录。
5. 汇总 baseline pair-full、最佳 spec、最佳 pair-full seed 数。
6. 给出决策：
   - `required_term_pair_decode_boundary_improves_pair_surface`
   - `required_term_pair_decode_boundary_partial_pair_surface`
   - `required_term_pair_decode_boundary_no_pair_surface_gain`
   - `fix_required_term_pair_decode_boundary_check`

## 真实结果

v541 读取 v540 高预算 stability 证据后得到：

```text
baseline_pair_full_seed_count=0
best_spec_id=wider-k2-t020-n12
best_pair_full_seed_count=1
decision=required_term_pair_decode_boundary_improves_pair_surface
```

明细上，seed `535` 在 `top_k=2` 和 `top_k=4` 下恢复 pair-full；seed `1535` 和 `2535` 没有恢复。因此本版结论是“存在解码边界收益”，不是“模型能力稳定”。

## 产物说明

- `e/541/解释/model-capability-required-term-pair-decode-boundary-check/`
  - 主报告 JSON/CSV/text/Markdown/HTML。
- `e/541/解释/model-capability-required-term-pair-decode-boundary-check/replay-reports/`
  - 每个 spec/seed 的 generation profile replay sidecar，可追溯 continuation。
- `e/541/图片/01-model-capability-required-term-pair-decode-boundary-check.png`
  - Playwright MCP 截图，证明 HTML 报告能展示状态、最佳 spec 和逐行复核结果。

这些都是最终证据，不是临时调试文件。

## 测试覆盖

单测覆盖四个关键断言：

- 当 fake generation 在宽解码下命中 fixed/loss 时，builder 报告改善。
- 当 fake generation 始终只返回 fixed 时，builder 报告无改善。
- 当 stability report 缺少 `seed_reports` 时，`status=fail`，`--require-pass` 对应退出码为 1。
- artifact writer 会写主报告，并为 replay 子报告写 sidecar。

真实验证还包括 v540 checkpoint 的实际 replay、Playwright MCP 截图、全量 pytest、source encoding 和 `git diff --check`。

一句话总结：v541 让 fixed/loss pair 的失败原因更细，从“训练预算不足”推进到“一个 seed 可由解码边界恢复，但整体稳定性仍待训练/数据修复”。
