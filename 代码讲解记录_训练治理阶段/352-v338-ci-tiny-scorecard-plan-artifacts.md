# v338 CI tiny scorecard plan artifacts

## 本版目标和边界
v337 把 CI tiny scorecard smoke 收束成稳定 wrapper，但一次 CI 运行结束后，固定预算和实际命令主要还藏在日志里。v338 的目标是让 wrapper 自己写出 invocation plan artifact，把“这次 CI tiny smoke 以什么配置、什么 sidecar 路径、什么命令、什么 return code 执行”保存成 JSON 和文本。

本版不做的事：
- 不改变底层 tiny scorecard comparison 的训练、比较和 decision 逻辑
- 不改变 CI workflow 步骤顺序
- 不新增新的评分报告
- 不把 tiny smoke 输出解释成模型质量提升

## 前置路线

```text
v336 CI enforced inline smoke
  -> v337 stable wrapper
  -> v338 wrapper invocation plan artifacts
```

## 关键文件

- `scripts/run_ci_tiny_scorecard_comparison_smoke.py`
  - 新增 `PLAN_JSON_FILENAME` 和 `PLAN_TEXT_FILENAME`
  - 新增 `build_invocation_plan()`
  - 新增 `render_invocation_plan()`
  - 新增 `write_invocation_plan()`
  - wrapper 在底层 smoke 运行后写出 plan，并记录 `returncode`
- `tests/test_ci_tiny_scorecard_smoke.py`
  - 覆盖纯 plan 构造与文本渲染
  - 覆盖真实 wrapper smoke 会留下 plan、summary 和 summary-check sidecar
- `README.md`
  - 更新当前版本、v338 checkpoint 和 tag 说明
- `d/338/`
  - 保存本版运行截图和解释

## 核心数据结构

`ci_tiny_scorecard_smoke_plan.json` 的核心字段：

```text
schema_version
wrapper
out_dir
summary_check_out_dir
config
flags
command
command_text
returncode
```

其中 `config` 保存 CI 固定预算：

```text
suite_name=standard-zh
case_token_cap=3
baseline_max_iters=1
candidate_max_iters=2
decision_min_rubric_score=60.0
eval_iters=1
batch_size=2
block_size=8
n_embd=8
baseline_seed=1337
candidate_seed=2026
```

`flags` 保存 wrapper 层参数：

```text
summary_check_allow_gate_stop
summary_check_no_fail
force
```

`returncode` 在底层 smoke 完成后写入。这个设计是 v338 中刻意调整的：如果先写 plan，底层 smoke 带 `--force` 时会清空输出目录，反而删除 plan。现在 plan 在运行后写出，既不会被清掉，也能记录最终退出码。

## 输入输出

输入仍是 wrapper 的 CI 入口参数：

```text
--out-dir
--summary-check-out-dir
--summary-check-allow-gate-stop
--summary-check-no-fail
--force
```

新增输出：

```text
ci_tiny_scorecard_smoke_plan.json
ci_tiny_scorecard_smoke_plan.txt
```

这些产物和原来的 smoke summary、summary-check sidecar 放在同一条证据链里。它们不是新的模型评估结果，而是本次 CI wrapper invocation 的审计记录。

## 测试覆盖

`tests/test_ci_tiny_scorecard_smoke.py` 新增两类保护：

1. `test_invocation_plan_records_wrapper_config_and_command`
   - 直接构造 plan
   - 验证固定预算、flags、command_text 和 returncode
   - 验证文本格式中保留关键字段
2. `test_wrapper_writes_invocation_plan_after_running_smoke`
   - 运行真实 wrapper smoke
   - 验证 plan JSON/text、smoke summary、summary-check sidecar 同时存在
   - 验证 plan 中的 sidecar 路径和固定预算正确

第二个测试保护的是“wrapper 运行后必须留下 invocation plan”。本版修复了测试最初暴露的 `--force` 删除 plan 风险。

## 链路角色

v338 让 CI tiny scorecard wrapper 的证据链变成：

```text
CI wrapper command
  -> bottom tiny scorecard comparison smoke
  -> smoke summary
  -> inline summary-check sidecar
  -> wrapper invocation plan JSON/text
```

排查 CI 时，可以先看 plan，确认 wrapper 用了哪套固定预算和路径，再看 smoke summary 与 summary-check 输出。

## 一句话总结
v338 把 CI tiny scorecard wrapper 从“稳定入口”推进到“入口本身也有机器可读审计证据”，让 tiny benchmark CI 运行更容易复查和追踪。
