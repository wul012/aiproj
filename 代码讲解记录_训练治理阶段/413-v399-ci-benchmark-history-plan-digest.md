# v399 CI benchmark-history plan digest 代码讲解

## 本版目标和边界

v399 的目标是把 v398 新增的 benchmark history artifacts 纳入 CI tiny scorecard wrapper 的 plan digest 和 plan checker。这样 CI 不只确认 summary/check 文件没有漂移，也能确认 `benchmark-history/benchmark_history.json/csv/md/html` 没有在 wrapper 完成后被改动或丢失。

本版不新增治理链，不改变 tiny smoke 训练预算，不改变 benchmark history 的 readiness 判定，也不把 tiny-smoke 证据升级成模型质量声明。它只是把已有 CI 证据闭环补完整。

## 前置能力

v337-v341 建立 CI tiny scorecard wrapper、invocation plan、artifact digest、plan checker 和 GitHub Actions gate。v398 让 tiny scorecard comparison smoke 生成 benchmark history。

v399 把两条线接上：

```text
v398 benchmark history artifacts
        |
        +--> v399 wrapper summary_digest.artifacts
        |
        +--> v399 plan checker recomputes digests
        |
        +--> CI plan check catches post-run drift
```

## 关键文件

### `scripts/run_ci_tiny_scorecard_comparison_smoke.py`

`build_summary_digest()` 原来只记录四个 artifact：

```text
summary_json
summary_text
summary_check_json
summary_check_text
```

v399 扩展为八个 artifact：

```text
benchmark_history_json
benchmark_history_csv
benchmark_history_markdown
benchmark_history_html
```

每个 artifact 仍然使用同一个 digest 结构：

```text
path
exists
size_bytes
sha256
```

`render_invocation_plan()` 同步输出四个新的 shell-readable hash：

```text
benchmark_history_json_sha256
benchmark_history_csv_sha256
benchmark_history_markdown_sha256
benchmark_history_html_sha256
```

这让 CI 日志里可以直接看到 history 产物是否被纳入计划。

### `scripts/check_ci_tiny_scorecard_plan.py`

`REQUIRED_ARTIFACTS` 从四项扩展到八项。checker 会逐个读取计划里记录的路径，重新计算 exists、size 和 sha256，然后和 plan digest 对比。

如果 benchmark history 缺失、内容被改写、大小变化或 hash 变化，报告会出现：

```text
artifact_digest_mismatch
```

并且 `decision` 变为：

```text
fix-ci-tiny-scorecard-plan
```

### `tests/test_ci_tiny_scorecard_smoke.py`

测试覆盖：

- invocation plan 文本包含 history sha256 字段；
- digest helper 能记录 history JSON/CSV/Markdown/HTML；
- 真实 wrapper smoke 生成 plan 后，summary digest 中四个 history artifact 均存在；
- wrapper 输出仍保留原有 summary/check 行为。

### `tests/test_ci_tiny_scorecard_plan_check.py`

测试覆盖：

- 完整八项 artifact digest 匹配时 plan check 通过；
- 篡改 summary artifact 时仍能失败，证明原有保护不退化；
- 真实 wrapper smoke 后运行 plan checker，确认 `artifact_count=8`，并在 stdout 看到 `benchmark_history_json_status=pass`。

## 输入输出格式

输入仍然是 CI wrapper 生成的：

```text
ci_tiny_scorecard_smoke_plan.json
```

输出仍然是：

```text
ci_tiny_scorecard_smoke_plan_check.json
ci_tiny_scorecard_smoke_plan_check.txt
```

本版只是扩大 artifact map，不改变文件名和调用方式。

## 运行流程

```text
scripts/run_ci_tiny_scorecard_comparison_smoke.py
        |
        +--> run tiny scorecard comparison smoke
        +--> write summary/check artifacts
        +--> write benchmark-history artifacts
        +--> build_summary_digest(eight artifacts)
        +--> write ci_tiny_scorecard_smoke_plan.json/txt

scripts/check_ci_tiny_scorecard_plan.py
        |
        +--> read plan
        +--> recompute eight artifact digests
        +--> fail on any mismatch
```

## 测试覆盖

本版定向验证：

```text
python -m py_compile scripts/run_ci_tiny_scorecard_comparison_smoke.py scripts/check_ci_tiny_scorecard_plan.py tests/test_ci_tiny_scorecard_smoke.py tests/test_ci_tiny_scorecard_plan_check.py
python -m pytest tests/test_ci_tiny_scorecard_smoke.py tests/test_ci_tiny_scorecard_plan_check.py -q
```

全量收口继续执行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v399
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/399/图片
d/399/解释/说明.md
```

`d/399/解释/v399-ci-benchmark-history-plan-digest-evidence.html` 是给 Playwright MCP 截图的静态证据页。它展示八项 artifact digest 和 plan checker 的新保护范围。

## 一句话总结

v399 把 v398 的 benchmark history 从“生成了”推进到“CI wrapper plan 会记录并校验它”，让 tiny scorecard 证据链更闭合。
