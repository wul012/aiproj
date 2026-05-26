# v434 baseline-candidate handoff contract check 代码讲解

## 本版目标与边界

v434 的目标是在 v433 baseline-candidate handoff 后面补一个 contract check。v433 已经能读取 v432 eval loop，产出下一轮 baseline 交接单；v434 继续验证这份交接单是否还能从原始 loop report 重新推导出来。

本版不新增训练流程，也不改变 baseline/candidate 判定逻辑。它只做一致性验证：如果 handoff 记录的 `source_loop_report` 存在，check 会重新调用 v433 的 builder 生成 expected handoff，再比较关键契约字段。candidate 被拒绝不是失败；只有 handoff 与源 loop 不一致、路径丢失或字段被篡改才失败。

## 前置链路

本版承接 v432-v433：

- v432 产出 `baseline_candidate_eval_loop.json`，其中包含 control checks、acceptance criteria、promotion decision 和 strict gate metadata。
- v433 读取 v432 loop，产出 `baseline_candidate_handoff.json`，把 next baseline 固定为 current baseline 或 candidate。
- v434 读取 v433 handoff，再从 `source_loop_report` 重建 expected handoff，验证 v433 产物没有漂移。

这不是新治理链，而是给 v433 交接产物加一个可复核入口。

## 关键文件

### `src/minigpt/baseline_candidate_handoff_check.py`

这是 v434 的核心模块。主入口是：

```text
build_baseline_candidate_handoff_check(handoff_path)
```

输入可以是 `baseline_candidate_handoff.json`，也可以是包含该文件的目录。模块先用 `resolve_baseline_candidate_handoff()` 定位 JSON，再由 `load_baseline_candidate_handoff()` 读取 handoff，并记录 `_source_handoff_path`。

随后模块读取 handoff 里的 `source_loop_report`，并重新调用：

```text
build_baseline_candidate_handoff(source_loop_report)
```

得到 expected handoff。v434 不比较 `generated_at` 这类运行时字段，只比较计划中定义的关键契约字段：

```text
status
decision
handoff_ready
next_baseline
baseline.checkpoint_exists
candidate.checkpoint_exists
guardrails.rejected_reasons
execution.expected_exit_code
```

如果字段一致，输出：

```text
status=pass
decision=continue_with_valid_handoff
failed_count=0
```

如果字段不一致，`issues` 会记录：

- `id`
- `field`
- `expected`
- `actual`
- `detail`

这样后续 CI 或人工审阅能直接知道哪一段 handoff 发生了漂移。

模块提供四种输出：

```text
baseline_candidate_handoff_check.json
baseline_candidate_handoff_check.txt
baseline_candidate_handoff_check.md
baseline_candidate_handoff_check.html
```

JSON 是机器消费主证据；TXT 适合 CI/shell；Markdown 适合 review；HTML 用于截图和浏览检查。

### `scripts/check_baseline_candidate_handoff.py`

这是独立检查入口。核心参数是：

```text
handoff
--out-dir
--require-pass
--force
```

`--require-pass` 只在 contract check 本身失败时返回 `1`。如果 handoff 合法地拒绝 candidate，例如 v433 的 `keep_current_baseline`，check 仍然返回 `0`。这点很重要：v434 检查的是“产物是否可信”，不是“candidate 是否应该晋升”。

### `scripts/build_baseline_candidate_handoff.py`

v434 给 v433 builder 增加可选参数：

```text
--check-out-dir
```

当该参数存在时，builder 会在写出 handoff 后立即对刚生成的 JSON 运行同一套 contract check，并把 sidecar 写入指定目录。默认不传这个参数时，v433 的行为保持不变。

### `tests/test_baseline_candidate_handoff_check.py`

测试覆盖五类契约：

- 合法 handoff 即使拒绝 candidate，也会 check pass。
- 篡改 `next_baseline.source` 后，check fail。
- 删除或改错 `source_loop_report` 后，check fail。
- `--require-pass` 对失败 check 返回 `1`。
- builder 的 `--check-out-dir` 会生成 check sidecar。

这些测试保护的是 handoff contract，而不是 PyTorch 训练效果。

## 输入输出格式

v434 的真实运行命令归档在 `d/434`：

```text
python -B scripts\check_baseline_candidate_handoff.py d\433\解释\baseline-candidate-handoff --out-dir d\434\解释\baseline-candidate-handoff-check --require-pass --force
```

关键输出：

```text
status=pass
decision=continue_with_valid_handoff
failed_count=0
source_handoff=d\433\解释\baseline-candidate-handoff\baseline_candidate_handoff.json
source_loop_report=d\432\解释\baseline-candidate-eval-loop\baseline_candidate_eval_loop.json
handoff_decision=keep_current_baseline
expected_decision=keep_current_baseline
handoff_ready=False
expected_handoff_ready=False
issues=
```

这说明 v433 的拒绝候选结论和 v432 loop 可重建结果一致。

## 运行证据

运行证据归档在 `d/434`：

- `d/434/解释/baseline-candidate-handoff-check/`：完整 check 输出。
- `d/434/图片/01-baseline-candidate-handoff-check.png`：Playwright MCP 渲染 HTML 报告截图。
- `d/434/解释/baseline_candidate_handoff_check_snapshot.md`：Playwright MCP 页面快照。
- `d/434/解释/baseline_candidate_handoff_check_stdout.txt`：check 命令输出。
- `d/434/解释/baseline_candidate_handoff_check_exit.txt`：`--require-pass` 退出码。

截图证明 HTML 报告能直观看到 `pass`、`failed_count=0`、`keep_current_baseline`、`Handoff ready=False`、`Expected ready=False` 和 `Issues=none`。

## 测试覆盖

本版验证包括：

```text
python -m py_compile src\minigpt\baseline_candidate_handoff_check.py scripts\check_baseline_candidate_handoff.py scripts\build_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff_check.py
python -m pytest tests\test_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff_check.py -q -o cache_dir=runs\pytest-cache-v434-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v434
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- 聚焦单测：`9 passed`
- 全量测试：`749 passed`
- source encoding：`status=pass`，`clean_count=338`
- `git diff --check`：通过，仅有 CRLF 提示
- handoff contract check：按设计返回 `exit_code=0`
- Playwright MCP 截图：已归档到 `d/434/图片/01-baseline-candidate-handoff-check.png`

说明：仓库旧 `.pytest_cache` 存在 ACL 权限异常，默认 cache 会阻止 pytest 初始化；本轮全量测试显式使用 `-o cache_dir=runs\pytest-cache-v434`，该临时缓存会在提交前清理。

## 证据边界

v434 证明的是 handoff contract consistency，不是模型能力提升。candidate 仍然没有通过 v432 的 `min_overall_score_delta=1.0`，因此 `keep_current_baseline` 是正确的保守结论。v434 只保证这份保守结论可以被源 loop 重新推导出来。

## 一句话总结

v434 把 baseline-candidate handoff 从“可交接”推进到“可重建验证”，让下一轮 baseline 选择具备轻量 contract check。
