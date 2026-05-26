# v435 baseline-candidate handoff embedded check 代码讲解

## 本版目标与边界

v435 的目标是在 v434 contract check 基础上，把 check 结果嵌回 baseline-candidate handoff 主产物。v434 已经能通过 sidecar 证明 handoff 与源 loop 一致；v435 让 handoff JSON/TXT/Markdown/HTML 自己也能显示这份检查状态。

本版不改变候选接受逻辑，不新增训练，不把 rejected candidate 说成 accepted candidate。当前 tiny candidate 仍因 `min_overall_score_delta expected >= 1.0, got 0.0` 被拒绝；`--require-accepted` 仍返回 `2`。v435 只是在拒绝候选的同时，记录这份拒绝型 handoff 的 contract check 是 `pass`。

## 前置链路

本版承接 v432-v434：

- v432 产出 baseline-candidate eval loop，并因最小分差不足拒绝 candidate。
- v433 把 loop 结果转成 next-baseline handoff，保守选择 current baseline。
- v434 从 handoff 的 `source_loop_report` 重建 expected handoff，并验证关键字段一致。
- v435 把 v434 check 的摘要和输出路径嵌回 v433 handoff 主报告。

这是一版收口型增强，不是新治理链。

## 关键文件

### `src/minigpt/baseline_candidate_handoff_check.py`

本版新增：

```text
embed_baseline_candidate_handoff_check(handoff, check, outputs)
```

这个函数不会改动 handoff 的核心决策字段，而是返回一份带两个新字段的 handoff：

```text
handoff_check
handoff_check_outputs
```

`handoff_check` 是 compact summary，包含：

- `schema_version`
- `status`
- `decision`
- `failed_count`
- `source_handoff`
- `source_loop_report`
- `handoff_decision`
- `expected_decision`
- `handoff_ready`
- `expected_handoff_ready`

`handoff_check_outputs` 保存 JSON/text/Markdown/HTML sidecar 路径。这样后续消费者只读 handoff 主 JSON，就能知道 check 是否通过，以及完整 check 证据在哪里。

### `src/minigpt/baseline_candidate_handoff.py`

本版让 handoff 渲染器识别可选的 `handoff_check`：

- TXT 新增：
  - `handoff_check_status`
  - `handoff_check_failed_count`
- Markdown 新增 `Embedded Handoff Check` 小节。
- HTML 在 Decision 指标区新增：
  - `Handoff check`
  - `Check failures`

如果 handoff 没有嵌入 check，HTML 会显示 `not-run`；这保证旧行为仍可兼容。

### `scripts/build_baseline_candidate_handoff.py`

v434 已经支持：

```text
--check-out-dir
```

v435 调整了这个参数的行为：当 check pass 后，脚本会调用 `embed_baseline_candidate_handoff_check()`，再重新写一次 handoff JSON/TXT/Markdown/HTML。输出中会出现：

```text
saved_embedded_json
saved_embedded_text
saved_embedded_markdown
saved_embedded_html
```

如果 check fail，脚本仍会返回 `1`，不会继续到 accepted gate。check pass 后，再按原有 `--require-accepted` 判断候选是否可晋升。因此当前真实运行仍返回 `2`，因为 candidate 没有被接受。

### `tests/test_baseline_candidate_handoff_check.py`

本版新增两类测试：

- builder 使用 `--check-out-dir --require-accepted` 时，即使命令最终因 candidate 未接受返回 `2`，handoff JSON 仍写入 `handoff_check.status=pass` 和 `handoff_check_outputs`。
- `embed_baseline_candidate_handoff_check()` 不改变 `decision` 和 `next_baseline` 等核心契约字段，只追加 check summary 和 sidecar paths。

这些测试保护的是“嵌入 check 不改变 handoff 判定”。

## 输入输出格式

v435 的真实运行命令归档在 `d/435`：

```text
python -B scripts\build_baseline_candidate_handoff.py d\432\解释\baseline-candidate-eval-loop --out-dir d\435\解释\baseline-candidate-handoff-embedded-check --check-out-dir d\435\解释\baseline-candidate-handoff-embedded-check\handoff-check --require-accepted --force
```

最终 handoff TXT 包含：

```text
status=pass
decision=keep_current_baseline
handoff_ready=False
handoff_check_status=pass
handoff_check_failed_count=0
rejected_reasons=min_overall_score_delta expected >= 1.0, got 0.0
```

这说明 handoff 合法拒绝 candidate，同时 contract check 已嵌入并通过。

## 运行证据

运行证据归档在 `d/435`：

- `d/435/解释/baseline-candidate-handoff-embedded-check/`：带 embedded check 的 handoff 主输出。
- `d/435/解释/baseline-candidate-handoff-embedded-check/handoff-check/`：v434 check sidecar 输出。
- `d/435/图片/01-baseline-candidate-handoff-embedded-check.png`：Playwright MCP 渲染 HTML 报告截图。
- `d/435/解释/baseline_candidate_handoff_embedded_check_snapshot.md`：Playwright MCP 页面快照。
- `d/435/解释/baseline_candidate_handoff_embedded_check_stdout.txt`：builder 命令输出。
- `d/435/解释/baseline_candidate_handoff_embedded_check_exit.txt`：`--require-accepted` 退出码。

截图证明主 handoff HTML 已经直接显示 `Handoff check = pass` 和 `Check failures = 0`。

## 测试覆盖

本版验证包括：

```text
python -m py_compile src\minigpt\baseline_candidate_handoff.py src\minigpt\baseline_candidate_handoff_check.py scripts\build_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff_check.py
python -m pytest tests\test_baseline_candidate_handoff.py tests\test_baseline_candidate_handoff_check.py -q -o cache_dir=runs\pytest-cache-v435-focus
python -m pytest -q -o cache_dir=runs\pytest-cache-v435
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local
git diff --check
```

结果：

- 聚焦单测：`11 passed`
- 全量测试：`751 passed`
- source encoding：`status=pass`，`clean_count=338`
- `git diff --check`：通过，仅有 CRLF 提示
- embedded handoff smoke：按设计返回 `exit_code=2`，同时 embedded check 为 `pass`
- Playwright MCP 截图：已归档到 `d/435/图片/01-baseline-candidate-handoff-embedded-check.png`

说明：仓库旧 `.pytest_cache` 存在 ACL 权限异常，默认 cache 会阻止 pytest 初始化；本轮全量测试显式使用 `-o cache_dir=runs\pytest-cache-v435`，该临时缓存会在提交前清理。

## 证据边界

v435 证明的是 embedded check visibility，不是模型能力提升。candidate 仍未通过 v432 的最小分差条件，因此继续保留 current baseline 是正确行为。v435 只是让这个保守 handoff 自带契约检查状态，便于后续 CI、审计和人工 review。

## 一句话总结

v435 把 baseline-candidate handoff 从“旁边有 check sidecar”推进到“主 handoff 自带 check 状态和证据路径”。
