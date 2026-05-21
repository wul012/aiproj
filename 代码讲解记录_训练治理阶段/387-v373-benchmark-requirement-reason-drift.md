# 387-v373-benchmark-requirement-reason-drift

## 本版目标与边界

v373 的目标是补齐一个成熟度评审盲点：benchmark-history readiness requirement 的状态和 exit code 没变时，如果 failed reasons 新增，成熟度层也应该能看到并进入 review。

这一版不增加训练能力，不新增治理链，不改变命令入口，也不把它做成新的独立报告。它只沿已有 release readiness comparison -> registry -> maturity summary -> maturity narrative 链路传递更细的失败原因变化。

## 前置路线

v364-v371 已经把 benchmark-history readiness requirement 从 benchmark history 传到了 release gate、release readiness、registry、maturity summary 和 maturity narrative。v373 继续同一条链，但补的不是 status，而是 reason drift：为什么失败这件事本身也会变化。

## 关键文件与链路角色

- `src/minigpt/release_readiness_comparison.py`
  - 在 delta 中新增 failed reason added/removed count。
  - 输出 failed reason added/removed 列表。
  - 当 failed reason 只新增、status 和 exit code 不变时，也视为 benchmark history delta/regression。

- `src/minigpt/release_readiness_comparison_artifacts.py`
  - CSV、Markdown、HTML 中展示 failed reason additions。
  - 这些产物是 release readiness comparison 的最终证据之一，会被 registry 继续消费。

- `src/minigpt/registry_rankings.py`
  - Registry row 和 release readiness delta summary 承接 failed reason additions。
  - 对旧 comparison JSON 做兼容：如果没有新增字段，就从 baseline/compared failed reasons 推导。

- `src/minigpt/maturity.py`
  - Maturity summary 增加 `release_readiness_benchmark_requirement_failed_reason_added_count`。
  - 新增 failed reason 会让趋势变为 `benchmark-regressed`，避免被 status-stable 的表象掩盖。

- `src/minigpt/maturity_narrative_summary.py`
  - 组合 portfolio status 时把 reason-only drift 作为 review 条件。
  - recommendations 会提示 review newly added benchmark-history readiness failed reasons。

- `src/minigpt/maturity_narrative_sections.py`
  - Release Quality Trend claim 中直接写出新增 failed reasons。

- `scripts/build_maturity_summary.py`
- `scripts/build_maturity_narrative.py`
  - CLI 输出 failed reason addition count/list，方便日志和 CI 读者不用打开 JSON。

## 核心数据结构

新增字段包括：

```text
benchmark_history_readiness_requirement_failed_reason_added_count
benchmark_history_readiness_requirement_failed_reason_removed_count
benchmark_history_readiness_requirement_failed_reason_added
benchmark_history_readiness_requirement_failed_reason_removed
```

在 maturity summary / narrative 层对应为：

```text
release_readiness_benchmark_requirement_failed_reason_added_count
release_readiness_benchmark_requirement_failed_reason_removed_count
release_readiness_benchmark_requirement_failed_reason_added
```

这些字段不是新的模型质量指标，而是 release readiness evidence 的稳定性诊断：同样失败，也要知道失败原因是否变多。

## 测试覆盖

本版定向测试覆盖四层：

- `tests/test_release_readiness_comparison.py`
  - 覆盖 requirement status 变为 fail 时的 failed reason addition。
  - 覆盖 status/exit code 不变、只新增 failed reason 时仍然 regression。

- `tests/test_registry.py`
  - 覆盖 registry delta summary 和 leaderboard 承接 failed reason additions。

- `tests/test_maturity.py`
  - 覆盖 maturity summary 对 reason-only drift 的 `benchmark-regressed` 判定。

- `tests/test_maturity_narrative.py`
  - 覆盖 maturity narrative portfolio status 和 release section claim。

验证命令：

```powershell
python -m py_compile src/minigpt/release_readiness_comparison.py src/minigpt/release_readiness_comparison_artifacts.py src/minigpt/registry_rankings.py src/minigpt/maturity.py src/minigpt/maturity_artifacts.py src/minigpt/maturity_narrative_summary.py src/minigpt/maturity_narrative_sections.py scripts/build_maturity_summary.py scripts/build_maturity_narrative.py
python -m pytest tests/test_release_readiness_comparison.py tests/test_registry.py tests/test_maturity.py tests/test_maturity_narrative.py -q
```

测试结果：`51 passed`。

## 运行证据

运行截图和解释归档到 `d/373`：

- `d/373/解释/说明.md`：说明本版目标、链路、验证命令和 tag 含义。
- `d/373/解释/v373-benchmark-reason-drift-evidence.html`：本地证据页，汇总 signal path 和验证结果。
- `d/373/图片/01-benchmark-reason-drift-evidence.png`：Playwright 打开的本地证据页截图。

## 一句话总结

v373 让 release readiness 到 maturity narrative 的评审从“失败状态是否变化”推进到“失败原因是否新增”。
