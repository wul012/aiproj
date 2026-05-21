# v364 benchmark history readiness gate

## 本版目标

这一版把注意力从 governance routing 收口转回模型评估证据链：给 `benchmark_history` 增加 readiness requirement，判断当前 benchmark history 是否足够支持“进入下一步训练推广/模型质量讨论”。

它不做新训练，不新增 benchmark suite，也不把 tiny smoke 说成真实模型质量证据。v364 做的是一个 preflight：历史证据不够时，可以让 CLI 明确 stop。

## 本版来自哪里

v343-v351 已经把 benchmark history 接进成熟度、审计、release bundle、release gate、readiness、registry 和 maturity review。

但当用户问“后续是否该扩功能、是否该跑更真实训练”时，项目还缺一个更直接的入口来回答：

```text
现在的 benchmark history 是否已经 ready？
```

v364 就补这个判断。

## 关键文件

- `src/minigpt/benchmark_history.py`
  - 新增 `build_benchmark_history_readiness_requirement()`。
  - `build_benchmark_history()` 现在把结果写入 `readiness_requirement`。
- `src/minigpt/benchmark_history_artifacts.py`
  - Markdown 增加 readiness status、decision、exit code、failed reasons。
  - HTML 增加 `Readiness Requirement` 区块。
- `scripts/build_benchmark_history.py`
  - 新增 `--require-ready-history`。
  - 新增 `--min-ready-entries`。
  - 新增 `--allow-tiny-smoke-readiness`。
  - 当 requirement 失败且开启 require 时，脚本退出 1。
- `tests/test_benchmark_history.py`
  - 覆盖 real benchmark pass。
  - 覆盖 tiny-smoke fail。
  - 覆盖 JSON/Markdown/HTML 持久化。

## 核心数据结构

### `readiness_requirement`

字段包括：

- `status`
  - `pass` 或 `fail`
- `decision`
  - `continue` 或 `stop`
- `exit_code`
  - `0` 或 `1`
- `min_ready_entries`
  - 要求至少多少条 ready history
- `ready_count`
  - 当前历史里 ready 的数量
- `evidence_kind`
  - `real-benchmark` 或 `tiny-smoke`
- `require_real_benchmark`
  - 是否要求真实 benchmark
- `failed_reasons`
  - `missing_history_entries`
  - `insufficient_ready_entries`
  - `not_real_benchmark_evidence`
  - `case_regression_entries`
  - `generation_quality_flag_regressions`

这些字段是 preflight 判断，不是新的模型评分。

## 运行流程

1. `scripts/build_benchmark_history.py` 读取 comparison 和 decision artifacts。
2. `build_benchmark_history()` 生成 entries 和 summary。
3. `build_benchmark_history_readiness_requirement()` 根据 summary、`evidence_kind` 和门槛参数生成 requirement。
4. JSON/Markdown/HTML 同步写入 requirement。
5. CLI stdout 输出 requirement 状态。
6. 如果传入 `--require-ready-history` 且 `exit_code=1`，命令失败。

## 输入输出边界

### real benchmark ready

当 `evidence_kind=real-benchmark`，且至少有一条 `promotion_readiness=ready`，没有 case regression 和 generation-quality flag regression 时：

```text
readiness_requirement_status=pass
readiness_requirement_decision=continue
readiness_requirement_exit_code=0
```

### tiny smoke review

当 `evidence_kind=tiny-smoke`，ready count 为 0，且存在 regression 时：

```text
readiness_requirement_status=fail
readiness_requirement_decision=stop
readiness_requirement_exit_code=1
```

失败原因会明确说明不是 real benchmark evidence。

## 测试覆盖

本版测试保护了四件事：

- real benchmark ready 历史可以通过 requirement
- tiny-smoke review 历史不能冒充 ready history
- `--require-ready-history` 会让 CLI 失败退出
- JSON/Markdown/HTML 都包含 readiness requirement

## 一句话总结

v364 让 benchmark history 从“模型评估历史账本”升级成“进入下一步训练/推广前的 readiness preflight”，更贴近真实 AI 工程节奏。
