# v440 baseline-candidate threshold boundary diagnosis gate 代码讲解

## 本版目标与边界

v440 的目标是把 v439 的 `review_diagnosis` 从“解释字段”推进为“可选 gate”。默认情况下，baseline-candidate threshold boundary smoke 仍然适合本地探索：只要 smoke 和 matrix 链路正常就可以输出 `status=pass`。但当调用方传入 `--require-diagnosis-pass` 时，如果诊断还是 `review`，脚本会返回退出码 `2`。

本版不改变候选是否晋升，不新增训练，不声称模型质量提升。它只把已有诊断接入命令退出语义，让 CI 或晋升脚本可以选择严格模式。

## 前置链路

v440 承接 v438-v439：

- v438 证明 live smoke 可以重新推导 threshold matrix。
- v439 支持复用已有 smoke summary，并把全阈值拒绝转成 `candidate_not_accepted` 诊断。
- v440 在这个诊断上加严格 gate，要求诊断必须 `pass` 才能在严格模式下退出 `0`。

因此 v440 是执行语义增强，不是新的治理链。

## 关键文件

### `scripts/run_baseline_candidate_threshold_boundary_smoke.py`

本版新增 CLI 参数：

```text
--require-diagnosis-pass
```

默认情况下，`review_diagnosis.status=review` 不会让脚本失败，因为本地探索需要保留“候选未被接受”这个事实。但当开启该参数后：

- `review_diagnosis.status=pass`：退出 `0`。
- `review_diagnosis.status=review`：退出 `2`。
- `review_diagnosis.status=fail`：退出 `1`。

这一区分很重要：`1` 表示链路或 contract 坏了；`2` 表示链路没坏，但严格 gate 不接受当前候选。

本版还新增 `annotate_execution_summary()`，在写出产物前把执行语义嵌入 JSON：

```json
{
  "gate_mode": "diagnosis_strict",
  "require_boundary_pass": false,
  "require_diagnosis_pass": true,
  "expected_exit_code": 2,
  "strict_gate_active": true
}
```

这样后续只读 JSON 时，不需要从命令行日志反推这次为什么退出 `2`。

### `src/minigpt/baseline_candidate_threshold_boundary_smoke.py`

渲染层新增 `execution` 展示：

- text 输出增加 `execution_gate_mode`、`execution_require_boundary_pass`、`execution_require_diagnosis_pass`、`execution_expected_exit_code`。
- Markdown 输出增加 gate mode、require diagnosis pass 和 expected exit code。
- HTML 摘要卡片增加 `Gate mode` 和 `Expected exit`。

这些字段让截图能直接证明严格 gate 生效，而不只是看 JSON。

### `tests/test_baseline_candidate_threshold_boundary_smoke.py`

本版测试覆盖：

- `resolve_exit_code()` 在 diagnosis strict 模式下区分 `pass`、`review`、`fail`。
- `annotate_execution_summary()` 正确写入 `diagnosis_strict`、`require_diagnosis_pass` 和 `expected_exit_code`。
- CLI 在 `--require-boundary-pass` 下继续写入 `boundary_strict` 执行信息。
- CLI 在 `--smoke-summary` 复用模式下继续保持 exploratory 执行信息。
- CLI 在 `--require-diagnosis-pass` 且诊断为 review 时抛出 `SystemExit(2)`，同时仍写出 summary JSON。

测试保护的是退出码语义，而不是只检查文件生成。

## 输入输出格式

真实运行命令：

```text
python -B scripts\run_baseline_candidate_threshold_boundary_smoke.py --smoke-summary d\438\解释\baseline-candidate-threshold-boundary-smoke\tiny-scorecard-comparison-smoke\tiny_scorecard_comparison_smoke_summary.json --out-dir d\440\解释\baseline-candidate-threshold-boundary-diagnosis-gate --thresholds 0:1:0.5 --require-diagnosis-pass --force
```

关键输出：

```text
execution_gate_mode=diagnosis_strict
execution_require_diagnosis_pass=True
execution_expected_exit_code=2
review_diagnosis_decision=candidate_not_accepted
captured_exit=2
```

这说明 v440 没有把候选拒绝当成脚本错误，也没有让它在严格 gate 下悄悄通过。

## 运行证据

运行证据归档在 `d/440`：

- `d/440/解释/baseline-candidate-threshold-boundary-diagnosis-gate/`：严格 diagnosis gate 输出产物。
- `d/440/解释/baseline_candidate_threshold_boundary_diagnosis_gate_stdout.txt`：命令输出。
- `d/440/解释/baseline_candidate_threshold_boundary_diagnosis_gate_exit.txt`：捕获退出码，结果为 `2`。
- `d/440/图片/01-baseline-candidate-threshold-boundary-diagnosis-gate.png`：HTML 截图。
- `d/440/解释/baseline_candidate_threshold_boundary_diagnosis_gate_snapshot.md`：页面结构说明。

截图显示 `Gate mode=diagnosis_strict`、`Expected exit=2`、`Diagnosis=candidate_not_accepted`、`Accept count=0`、`Reject count=3`，说明严格 gate 的行为已经进入可视化证据。

## 测试覆盖

本版验证命令：

```text
python -m py_compile src\minigpt\baseline_candidate_threshold_boundary_smoke.py scripts\run_baseline_candidate_threshold_boundary_smoke.py tests\test_baseline_candidate_threshold_boundary_smoke.py
python -m pytest tests\test_baseline_candidate_threshold_boundary_smoke.py tests\test_baseline_candidate_threshold_matrix.py -q -o cache_dir=runs\pytest-cache-v440-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v440
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

聚焦测试覆盖严格 gate 的退出码和 execution 元数据；全量测试确认 baseline-candidate 链路其它版本没有被破坏。

结果：

- py_compile：通过。
- 聚焦测试：`14 passed`。
- 全量测试：`765 passed`。
- source encoding：`status=pass`，`source_count=344`。
- `git diff --check`：通过，仅出现 Git 对 Markdown/Python 文件的 CRLF 提示。

## 证据边界

v440 证明的是 gate 语义，不证明 candidate 模型质量提升。当前严格 gate 返回 `2` 是合理结果，因为所有阈值都拒绝 candidate。

## 一句话总结

v440 把 baseline-candidate threshold boundary diagnosis 从“可读解释”推进到“可选严格阻断”，让同一份候选未接受证据既能归档，也能在晋升路径里可靠停住。
