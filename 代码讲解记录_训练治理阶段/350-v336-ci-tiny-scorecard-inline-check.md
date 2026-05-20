# v336 CI tiny scorecard inline check

## 本版目标和边界
v335 让 `run_tiny_scorecard_comparison_smoke.py` 能可选地内联运行 summary checker。v336 的目标是把这条能力放进 GitHub Actions，并让 CI workflow hygiene 检查它必须存在、必须带 `--summary-check-out-dir`，且必须在 coverage 前运行。

本版不做的事：
- 不改变 tiny scorecard smoke 的训练配置和判定逻辑
- 不新增更重的 benchmark
- 不把 CI smoke 解释成模型质量提升
- 不移除 standalone checker

## 前置能力

```text
v334 standalone summary checker
  -> v335 inline summary-check sidecars
  -> v336 GitHub Actions + CI hygiene enforcement
```

## 关键文件

- `.github/workflows/ci.yml`
  - 新增 `Tiny scorecard comparison inline check smoke`
  - 命令运行 `scripts/run_tiny_scorecard_comparison_smoke.py`
  - 使用小预算 CPU smoke 参数
  - 传入 `--summary-check-out-dir runs/tiny-scorecard-comparison-smoke-check-ci`
- `src/minigpt/ci_workflow_hygiene.py`
  - `REQUIRED_COMMAND_FRAGMENTS` 新增 tiny scorecard smoke 命令
  - `REQUIRED_COMMAND_FRAGMENTS` 新增 `--summary-check-out-dir`
  - `REQUIRED_COMMAND_ORDER` 新增 tiny scorecard smoke before coverage
- `tests/test_ci_workflow.py`
  - 当前 workflow pass 测试覆盖新命令和 sidecar 参数
  - 缺失旧 runtime policy 测试更新 required step count
  - 顺序违规测试覆盖两个 smoke 都必须在 coverage 前
- `README.md`
  - 更新当前版本、v336 checkpoint 和 tag 说明
- `d/336/`
  - 保存本版运行截图和解释

## CI 链路角色

新增 CI 顺序：

```text
source encoding
  -> CI workflow hygiene
  -> promoted seed handoff assurance smoke
  -> tiny scorecard comparison inline check smoke
  -> test coverage
```

这让 tiny scorecard comparison 不再只是本地可选命令，而是进入 CI 的“证据契约”。如果未来有人删掉 smoke、删掉 summary-check sidecar 参数，或把它放到 coverage 后，CI hygiene 会失败。

## 核心检查

CI hygiene 现在要求：

```text
scripts/run_tiny_scorecard_comparison_smoke.py
--summary-check-out-dir
scripts/check_promoted_seed_handoff_assurance_smoke.py before scripts/run_test_coverage.py
scripts/run_tiny_scorecard_comparison_smoke.py before scripts/run_test_coverage.py
```

当前 hygiene 输出：

```text
check_count=13
required_step_count=7
required_order_count=2
order_violation_count=0
```

## 测试覆盖

`tests/test_ci_workflow.py` 保护三件事：

1. 当前 `.github/workflows/ci.yml` 必须包含 tiny scorecard inline check smoke 和 sidecar 参数
2. 旧/缺失 workflow 会因为 missing step count 增加而失败
3. 当两个 smoke 放在 coverage 后时，会产生两个 order violation

这些测试保护的是 CI 契约，不是模型分数。

## 一句话总结
v336 把 tiny scorecard inline summary-check 从“本地可选能力”推进为“CI 必跑契约”，让评估证据链真正进入自动化质量门。
