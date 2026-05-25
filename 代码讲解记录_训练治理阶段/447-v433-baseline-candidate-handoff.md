# v433 baseline-candidate handoff 代码讲解

## 本版目标与边界

v433 的目标是承接 v432 的 baseline-candidate eval loop，把 loop 报告里的接收/拒绝结果转成一个明确的 next-baseline handoff。v432 已经回答“候选是否满足接收条件”，v433 继续回答“下一轮 baseline 应该来自 candidate 还是继续沿用 current baseline”。

本版不重新跑训练，也不修改模型结构。它读取已有 `baseline_candidate_eval_loop.json`，生成 handoff JSON/text/Markdown/HTML，并通过 `--require-accepted` 提供严格交接 gate。当前真实证据来自 v432 strict loop：loop 执行通过，但 candidate 没有达到 `min_overall_score_delta=1.0`，所以 v433 正确选择 `keep_current_baseline`。

## 前置链路

本版直接依赖 v432：

- v432 运行 tiny scorecard comparison smoke，产出 baseline/candidate scorecard、delta、control checks、acceptance criteria、promotion decision 和 execution metadata。
- v432 在 strict gate 下因为 `overall_score_delta=0.0` 小于 `min_overall_score_delta=1.0` 而拒绝 candidate。
- v433 不重算这些判断，只读取 v432 loop 报告并固化下一轮 baseline 选择。

这让链路从“评估候选”继续走到“交接候选”，但仍保持同一条训练治理主线。

## 关键文件

### `src/minigpt/baseline_candidate_handoff.py`

这是 v433 的核心模块。它的主入口是：

```text
build_baseline_candidate_handoff(loop_report_path)
```

输入可以是 `baseline_candidate_eval_loop.json` 文件，也可以是包含该文件的目录。模块先通过 `resolve_baseline_candidate_loop_report()` 统一定位输入，再由 `load_baseline_candidate_loop_report()` 读取 JSON，并把实际路径写入 `_source_path`，方便后续追溯。

核心判定由 `_candidate_accepted()` 完成。候选只有同时满足以下条件才可以交接为下一轮 baseline：

- loop 顶层 `status == pass`
- loop 顶层 `decision == accept_candidate`
- control summary 为 `pass`
- acceptance criteria 为 `pass`
- promotion decision 里的 `accepted is True`

如果这些条件不全满足，`_handoff_decision()` 会给出保守结论：

```text
keep_current_baseline
```

如果 loop 自身失败，则结论是：

```text
fix_loop_before_handoff
```

输出报告分成几个稳定区域：

- `next_baseline`
  - 写清楚下一轮 baseline 名称、来源、ready 状态、checkpoint 路径和是否存在。
- `baseline`
  - 记录当前 baseline 的状态、scorecard 状态、overall score 和 checkpoint。
- `candidate`
  - 记录候选名称、selected name、score、accepted 状态、checkpoint、scorecard 和 pair batch。
- `delta`
  - 记录 overall score delta、最小分差、case delta 和 regression count。
- `guardrails`
  - 记录 control/acceptance/promotion 状态、rejected reasons 和 model quality claim 边界。
- `execution`
  - 保留 v432 的 source mode、gate mode、expected exit code 和 loop decision。
- `source_evidence`
  - 从 v432 的 `source_smoke_summary` 解析 baseline/candidate 目录、checkpoint、candidate scorecard、pair batch 和 benchmark history。
- `actions`
  - 根据结果给出后续动作，例如 `keep_current_baseline`、`fix_candidate_before_next_loop`。
- `boundary`
  - 明确当前只证明 tiny benchmark handoff readiness，不宣称生产模型质量。

模块还提供四种渲染函数：

```text
render_baseline_candidate_handoff_text()
render_baseline_candidate_handoff_markdown()
render_baseline_candidate_handoff_html()
write_baseline_candidate_handoff_outputs()
```

JSON 是机器消费主证据；TXT 适合 CI/shell；Markdown 适合人工 review；HTML 用于截图和浏览检查。

### `scripts/build_baseline_candidate_handoff.py`

这是命令入口。核心流程很短：

```text
parse_args -> prepare_output_dir -> build_baseline_candidate_handoff -> write outputs -> resolve_exit_code
```

关键参数：

```text
loop_report
--out-dir
--require-accepted
--force
```

`--require-accepted` 是本版最重要的 gate 行为：如果 handoff 报告本身 `status=pass`，但 `handoff_ready=False`，脚本返回 `2`。这和 v432 的 strict gate 语义一致，表示“流程跑通，但候选不能晋升”。如果 loop 本身失败，则返回 `1`。

`prepare_output_dir()` 负责输出目录保护：目录非空时必须显式传 `--force` 才会替换，避免误覆盖证据。

### `tests/test_baseline_candidate_handoff.py`

测试用临时目录构造两类 loop bundle：

- accepted candidate
  - 断言 decision 为 `promote_candidate_to_next_baseline`
  - next baseline source 为 `candidate`
  - candidate checkpoint 存在
- rejected candidate
  - 断言 decision 为 `keep_current_baseline`
  - next baseline source 为 `current_baseline`
  - rejected reason 保留最小分差失败原因
  - `resolve_exit_code(..., require_accepted=True)` 返回 `2`

测试还覆盖四类输出文件都会写出，以及 CLI 在 `--require-accepted` 下会抛出 `SystemExit(2)` 并保留 JSON 报告。这里保护的是 handoff 契约、checkpoint evidence 和退出码语义，而不是 PyTorch 训练效果。

## 输入输出格式

v433 的真实运行命令归档在 `d/433`：

```text
python -B scripts\build_baseline_candidate_handoff.py d\432\解释\baseline-candidate-eval-loop --out-dir d\433\解释\baseline-candidate-handoff --require-accepted --force
```

关键输出为：

```text
status=pass
decision=keep_current_baseline
handoff_ready=False
next_baseline_name=tiny-baseline
next_baseline_source=current_baseline
next_baseline_checkpoint_exists=True
candidate_name=tiny-candidate
candidate_accepted=False
overall_score_delta=0.0
min_overall_score_delta=1.0
control_status=pass
acceptance_status=fail
promotion_status=promote
execution_source_mode=rerun_smoke
execution_gate_mode=strict
execution_expected_exit_code=2
rejected_reasons=min_overall_score_delta expected >= 1.0, got 0.0
```

这说明 v432 loop 可以被复用，且 v433 handoff 对拒绝候选保持保守：候选没有通过接收条件，下一轮 baseline 继续指向 `tiny-baseline`，但报告仍记录 candidate 的路径、失败原因和后续动作。

## 运行证据

运行证据归档在 `d/433`：

- `d/433/解释/baseline-candidate-handoff/`：完整 handoff 输出。
- `d/433/图片/01-baseline-candidate-handoff.png`：Playwright MCP 渲染 HTML 报告截图。
- `d/433/解释/baseline_candidate_handoff_snapshot.md`：Playwright MCP 页面快照。
- `d/433/解释/baseline_candidate_handoff_stdout.txt`：handoff 命令输出。
- `d/433/解释/baseline_candidate_handoff_exit.txt`：`--require-accepted` 退出码。

截图和文本证据共同证明：v433 的 handoff 能看见 `keep_current_baseline`、`Ready=False`、`current_baseline`、`Acceptance=fail` 和 rejected reason。

## 测试覆盖

本版验证包括：

```text
python -m py_compile src\minigpt\baseline_candidate_handoff.py scripts\build_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff.py
python -m pytest tests\test_baseline_candidate_handoff.py -q
python -B scripts\build_baseline_candidate_handoff.py d\432\解释\baseline-candidate-eval-loop --out-dir d\433\解释\baseline-candidate-handoff --require-accepted --force
```

结果：

- 单测：`4 passed`
- v432/v433 组合测试：`15 passed`
- 全量测试：`744 passed`
- source encoding：`status=pass`，`clean_count=335`
- handoff strict gate：按设计返回 `exit_code=2`
- Playwright MCP 截图：已归档到 `d/433/图片/01-baseline-candidate-handoff.png`

说明：仓库旧 `.pytest_cache` 存在 ACL 权限异常，默认 cache 会阻止 pytest 初始化；本轮全量测试显式使用 `-o cache_dir=runs\pytest-cache-v433`，该临时缓存会在提交前清理。

## 证据边界

v433 证明的是交接契约，不是模型效果。当前 candidate 的 tiny benchmark 分数没有超过 baseline，`overall_score_delta=0.0`，因此 handoff 拒绝晋升是正确行为。报告里的 checkpoint path 证明“继续用哪个 baseline”，rejected reasons 证明“为什么不能换 candidate”，这两者共同服务后续训练治理。

## 一句话总结

v433 把 baseline-candidate eval loop 的结果变成 next-baseline handoff，让 MiniGPT 的训练治理从“能评估候选”推进到“能保守交接下一轮 baseline”。
