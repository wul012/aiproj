# v337 CI tiny scorecard wrapper

## 本版目标和边界
v336 已经把 tiny scorecard inline summary-check smoke 放进 GitHub Actions，但 workflow 里直接写了一整条长命令。v337 的目标是把这条 CI 专用命令收束成一个稳定 wrapper：workflow 只调用 `scripts/run_ci_tiny_scorecard_comparison_smoke.py`，具体 tiny benchmark 预算留在脚本和测试里维护。

本版不做的事：
- 不改变 tiny scorecard comparison 的训练、比较或 decision 逻辑
- 不改变 summary checker 的结构
- 不新增更重的 benchmark
- 不把 tiny smoke 结果解释成模型质量提升

## 前置路线

```text
v334 standalone summary checker
  -> v335 inline summary-check sidecars
  -> v336 GitHub Actions hygiene enforcement
  -> v337 stable CI wrapper
```

## 关键文件

- `scripts/run_ci_tiny_scorecard_comparison_smoke.py`
  - 新增 CI 专用 wrapper
  - 固定 `standard-zh`、`case_token_cap=3`、baseline 1 iter、candidate 2 iter、decision threshold 60
  - 继续要求 `--summary-check-out-dir`
  - 支持透传 `--summary-check-allow-gate-stop`、`--summary-check-no-fail` 和 `--force`
- `.github/workflows/ci.yml`
  - tiny scorecard CI step 改为调用 wrapper
  - workflow 不再保存长串 benchmark 参数
- `src/minigpt/ci_workflow_hygiene.py`
  - required command fragment 改为 wrapper 入口
  - required order 仍然要求 tiny smoke 在 coverage 前运行
- `tests/test_ci_tiny_scorecard_smoke.py`
  - 新增 wrapper 单测
  - 保护固定预算、summary-check sidecar 和可选 gate flags
- `tests/test_ci_workflow.py`
  - 测试 fixture 改为 wrapper 命令
  - 保持 CI hygiene 对 wrapper、sidecar 和顺序的约束

## 核心结构

wrapper 里的核心配置是 `CI_TINY_SCORECARD_CONFIG`：

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

这些字段原本散在 `.github/workflows/ci.yml` 的一行命令里。v337 把它们集中到 Python 脚本中，测试可以直接断言配置和最终命令文本，避免以后 workflow 改动时遗漏关键预算。

## 输入输出

输入：

```text
--out-dir
--summary-check-out-dir
--summary-check-allow-gate-stop
--summary-check-no-fail
--force
```

输出仍来自底层 `run_tiny_scorecard_comparison_smoke.py`：

```text
tiny_scorecard_comparison_smoke_summary.json
tiny_scorecard_comparison_smoke_summary.txt
tiny_scorecard_comparison_smoke_check.json
tiny_scorecard_comparison_smoke_check.txt
```

wrapper 自己不生成新的报告格式，它只是把 CI 入口稳定下来。

## CI 链路角色

v337 后的 CI 顺序仍然是：

```text
source encoding
  -> CI workflow hygiene
  -> promoted seed handoff assurance smoke
  -> CI tiny scorecard wrapper
  -> test coverage
```

CI hygiene 检查的是 wrapper 是否存在、`--summary-check-out-dir` 是否存在，以及 wrapper 是否在 coverage 前运行。这样它守的是自动化质量门入口，而不是散落的一长串参数。

## 测试覆盖

测试覆盖三层：

1. `tests/test_ci_tiny_scorecard_smoke.py`
   - 断言 wrapper 生成的底层命令包含固定 tiny budget
   - 断言 summary-check sidecar 参数存在
   - 断言 optional summary-check flags 能透传
2. `tests/test_ci_workflow.py`
   - 断言当前 workflow 通过 hygiene
   - 断言旧 workflow 缺失必要命令会失败
   - 断言 wrapper 放在 coverage 后会产生 order violation
3. 真实 wrapper smoke
   - 运行 `scripts/run_ci_tiny_scorecard_comparison_smoke.py`
   - 证明底层 scorecard comparison、decision 和 summary-check sidecar 都能跑通

## 运行证据

本版证据归档在 `d/337`：

- wrapper 单测和 CI workflow 单测
- CI hygiene 输出
- workflow 中的 wrapper step
- wrapper 固定配置
- 真实 wrapper smoke 输出
- source encoding、py_compile、diff check

这些证据说明 v337 是一次 CI 入口收束，不是模型能力提升。

## 一句话总结
v337 把 tiny scorecard CI smoke 从“workflow 里的长命令”推进为“有测试保护的稳定入口”，让后续 CI 参数维护更可控。
