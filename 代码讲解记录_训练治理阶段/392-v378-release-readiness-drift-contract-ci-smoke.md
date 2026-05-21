# v378 release readiness drift contract CI smoke 代码讲解

## 本版目标和边界

v378 的目标是把 v377 的 release readiness drift contract 检查器从“可手工运行”推进到“CI 会固定运行”。

v377 已经能重新推导 failed-reason additions、removals、drift status 和 summary counts。v378 解决的是执行入口问题：CI 不能依赖开发机上临时存在的 `runs/release-readiness-comparison`，所以本版新增一个稳定 smoke fixture，每次都生成最小 mixed-drift comparison，再调用 v377 检查器。

本版不重新跑完整 release readiness comparison，不新增 drift 语义，不改变模型训练流程，也不把治理 evidence 当作模型质量证明。

## 前置能力

本版承接 v377：

```text
release_readiness_comparison.json
        |
        v
release_readiness_drift_contract checker
        |
        v
pass/fail + JSON/TXT sidecars
```

v378 在它外面包了一层 CI smoke：

```text
write deterministic mixed fixture
        |
        v
run checker against fixture
        |
        v
write smoke summary
        |
        v
CI workflow hygiene requires smoke before coverage
```

## 关键文件

### `scripts/check_release_readiness_drift_contract_smoke.py`

这是本版核心新增脚本。它做四件事：

1. 创建最小 `release_readiness_comparison.json`。
2. 调用 `scripts/check_release_readiness_drift_contract.py`。
3. 校验 checker JSON/TXT sidecar 存在且状态为 `pass`。
4. 写出 smoke summary JSON/TXT，供 CI 日志和后续人工检查读取。

fixture 的关键输入是：

```text
baseline reasons: insufficient_ready_entries, legacy_fixture_gap
compared reasons: insufficient_ready_entries, tiny_smoke_only
```

因此 expected contract 是：

```text
added  : tiny_smoke_only
removed: legacy_fixture_gap
status : mixed
```

smoke summary 暴露：

```text
status
decision
checker_returncode
check_status
check_delta_count
check_delta_fail_count
check_expected_mixed_delta_count
check_actual_mixed_delta_count
outputs
```

这些字段让 CI 日志不用打开完整 JSON，也能看到核心结果。

### `.github/workflows/ci.yml`

新增 step：

```text
Release readiness drift contract smoke
```

命令为：

```powershell
python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-ci
```

它放在 coverage 前面，原因是 drift contract 是治理字段契约。如果契约坏了，CI 应该更早失败，而不是先跑较重的覆盖率测试。

### `src/minigpt/ci_workflow_hygiene.py`

新增 required command：

```text
release_readiness_drift_contract_smoke
```

新增 required order：

```text
release_readiness_drift_contract_smoke_before_coverage
```

这样后续如果有人删掉 CI smoke 或把它挪到 coverage 后面，`scripts/check_ci_workflow_hygiene.py` 会失败。

### `tests/test_release_readiness_drift_contract_smoke.py`

测试真实调用 smoke 脚本，断言：

- summary JSON/TXT 存在。
- checker JSON/TXT 存在。
- comparison fixture 存在。
- summary status 为 `pass`。
- expected/actual mixed delta count 都为 `1`。

### `tests/test_ci_workflow.py`

测试当前 workflow 包含新 command 和新 order check，并更新 old-runtime / wrong-order fixture 的预期数量。

## 输入输出

输入：无外部输入，smoke 自己生成 fixture。

输出目录结构：

```text
runs/release-readiness-drift-contract-smoke-ci/
  comparison/release_readiness_comparison.json
  check/release_readiness_drift_contract_check.json
  check/release_readiness_drift_contract_check.txt
  release_readiness_drift_contract_smoke_summary.json
  release_readiness_drift_contract_smoke_summary.txt
  checker_stdout.txt
  checker_stderr.txt
```

这些都是 CI 运行产物，不作为长期仓库 source 文件提交。

## 测试覆盖

阶段验证：

```powershell
python -m pytest tests/test_release_readiness_drift_contract.py tests/test_release_readiness_drift_contract_smoke.py tests/test_ci_workflow.py -q
```

结果：

```text
14 passed
```

同时真实运行：

```powershell
python -B scripts/check_release_readiness_drift_contract_smoke.py --out-dir runs/release-readiness-drift-contract-smoke-v378
python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-v378
```

结果：

```text
drift contract smoke: status=pass
CI workflow hygiene: status=pass, check_count=18, required_order_count=5, order_violation_count=0
```

最终全量验证：

```text
678 passed
```

source encoding hygiene 结果：

```text
status=pass
source_count=312
clean_count=312
bom_count=0
syntax_error_count=0
```

## 运行证据

运行证据归档在：

```text
d/378/图片/01-release-readiness-drift-contract-ci-smoke-evidence.png
d/378/解释/说明.md
```

证据页展示 smoke fixture、checker sidecar、CI step 和 workflow hygiene guard 的连接关系。

## 一句话总结

v378 让 release readiness failed-reason drift contract 不再只是一个本地检查器，而是进入 CI 前置 smoke 和 workflow hygiene 守护，保证后续字段迁移不会悄悄绕过契约检查。
