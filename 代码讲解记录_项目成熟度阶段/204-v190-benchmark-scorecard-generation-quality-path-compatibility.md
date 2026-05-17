# v190 benchmark scorecard generation quality path compatibility

## 本版目标

v190 的目标是修掉 v189 真实链路里暴露出的一个小但实际的摩擦：`build_benchmark_scorecard.py` 读取 generation quality 时，历史上主要识别 `generation-quality/`；而真实 smoke 中 `analyze_generation_quality.py --out-dir runs/<run>/generation_quality` 产出了 underscore 目录，导致需要手动复制一份目录再 build scorecard。

本版解决的问题是：真实训练链路不应该靠人工 copy glue 才能从 generation quality 进入 benchmark scorecard。

本版明确不做：

- 不改变 benchmark scorecard 的评分权重和评分规则。
- 不改变 generation quality report schema。
- 不改变 training portfolio 的既有输出路径。
- 不扩大模型训练规模。

## 前置路线

v188 把 generation quality 摘要接入 training run evidence。

v189 把 benchmark scorecard 摘要接入 training run evidence，但真实 smoke 为了让 scorecard 找到 quality report，临时把 `generation_quality/` 复制成 `generation-quality/`。v190 就是把这个摩擦收掉。

## 关键文件

### `src/minigpt/benchmark_scorecard.py`

本版修改两个位置。

第一处是 `_read_generation_quality()`。

现在按顺序识别四个候选路径：

```text
run_dir/generation_quality/generation_quality.json
run_dir/generation-quality/generation_quality.json
run_dir/eval_suite/generation_quality/generation_quality.json
run_dir/eval_suite/generation-quality/generation_quality.json
```

读取到的 report 会继续补 `source_path`，所以 scorecard 的 Generation Quality component 仍能展示实际证据来源。

第二处是 `_evidence_completeness_component()`。

它现在也把这四个位置都视为有效 generation quality evidence，避免出现“scorecard 能读到 quality，但 evidence completeness 仍判定 quality 缺失”的不一致。

### `tests/test_benchmark_scorecard.py`

新增 `test_build_benchmark_scorecard_accepts_underscore_generation_quality_dir()`。

测试先用原有 fixture 生成 `generation-quality/generation_quality.json`，再把内容搬到 `generation_quality/generation_quality.json` 并删除原文件，然后构建 scorecard。

关键断言包括：

- `generation_quality_total_flags` 仍能读到。
- `generation_quality_dominant_flag` 仍是 `low_diversity`。
- Generation Quality component 的 `evidence_path` 指向 underscore 路径。
- Evidence Completeness component 的 `generation_quality` 为 true。

这证明兼容性不仅影响 summary，也影响 evidence completeness。

## 运行流程

v190 后，真实链路可以直接运行：

```text
scripts/train.py
 -> scripts/eval_suite.py
 -> scripts/analyze_generation_quality.py --out-dir run_dir/generation_quality
 -> scripts/build_benchmark_scorecard.py
 -> scripts/build_training_run_evidence.py
```

不再需要：

```text
Copy-Item run_dir/generation_quality run_dir/generation-quality
```

## 测试和证据

v190 的截图归档在 `c/190`。

关键验证包括：

- focused scorecard tests：覆盖原有 hyphen 路径和新增 underscore 路径。
- real PyTorch no-copy smoke：真实训练、eval、generation quality、scorecard、training evidence 全链路运行，期间没有复制 generation quality 目录。
- training evidence smoke：确认 scorecard 摘要仍能被 v189 的 evidence 读取。
- Playwright/Chrome screenshot：确认 evidence HTML 仍能打开。
- source encoding hygiene 和 full unittest discovery：确认兼容性修改不破坏全局测试。

## 边界说明

v190 是路径兼容，不是评分政策变化。真实 scorecard 如果仍然因为 pair batch 缺失、rubric 弱项或 evidence completeness 不足而 fail，这是正常的。v190 只保证 scorecard 能正确消费已有 generation quality evidence。

## 一句话总结

v190 把真实 benchmark 链路里的目录命名摩擦收掉，让 train -> eval -> quality -> scorecard -> training evidence 可以无手工 copy 地连起来。
