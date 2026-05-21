# v340 CI tiny scorecard plan checker

## 本版目标和边界
v339 已经让 CI tiny scorecard wrapper plan 记录 summary 与 summary-check sidecar 的 sha256。v340 的目标是补上独立验收入口：新增 `check_ci_tiny_scorecard_plan.py`，读取已完成的 plan，重新计算四个 artifact 的存在状态、大小和 sha256，并和 plan 中的 `summary_digest` 对比。

本版不做的事：
- 不重新跑 tiny scorecard smoke
- 不改变 GitHub Actions workflow
- 不改变模型训练、评分或 decision 逻辑
- 不把 digest check 解释成模型质量证明

## 前置路线

```text
v338 wrapper invocation plan
  -> v339 summary/check artifact digests
  -> v340 reusable plan digest checker
```

## 关键文件

- `scripts/check_ci_tiny_scorecard_plan.py`
  - 新增 plan checker CLI
  - 支持传入 plan JSON 或 smoke 输出目录
  - 重新计算 artifact exists/size/sha256
  - 输出 JSON/text check artifacts
  - 默认失败时非零退出，`--no-fail` 可只写报告
- `tests/test_ci_tiny_scorecard_plan_check.py`
  - 覆盖 digest 匹配通过
  - 覆盖 artifact 被篡改时失败
  - 覆盖 check 输出写入和目录解析
  - 覆盖真实 wrapper smoke 后再跑 plan checker 的端到端链路
- `README.md`
  - 更新当前版本、v340 checkpoint 和 tag 说明
- `d/340/`
  - 保存本版运行截图和解释

## 核心检查逻辑

checker 读取 plan 后检查四个固定 artifact：

```text
summary_json
summary_text
summary_check_json
summary_check_text
```

每个 artifact 都会生成一行对比：

```text
expected_exists
actual_exists
expected_size_bytes
actual_size_bytes
expected_sha256
actual_sha256
status
```

只有存在状态、大小和 sha256 全部一致，artifact 行才是 `pass`。

## 输入输出

输入：

```text
python -B scripts/check_ci_tiny_scorecard_plan.py <plan-or-smoke-dir> --out-dir <check-dir>
```

如果传入目录，checker 会自动寻找：

```text
ci_tiny_scorecard_smoke_plan.json
```

输出：

```text
ci_tiny_scorecard_smoke_plan_check.json
ci_tiny_scorecard_smoke_plan_check.txt
```

JSON 适合机器消费，text 适合 CI 日志直接查看。

## 失败语义

当前失败类型包括：

```text
artifact_digest_mismatch
summary_digest_missing
summary_digest_artifacts_missing
returncode_not_zero
```

其中最核心的是 `artifact_digest_mismatch`：它说明 plan 中记录的 artifact 和磁盘上的实际 artifact 已经不一致。

## 测试覆盖

测试覆盖五个风险点：

1. 完整 artifact digest 与 plan 一致时通过。
2. 修改 summary JSON 后，checker 能发现 sha256/size 不一致。
3. checker 能把 JSON/text 检查报告写到指定目录。
4. 传入 smoke 输出目录时能定位 plan。
5. 真实 wrapper smoke 产出的 plan 能被 checker CLI 验收。

## 链路角色

v340 后，CI tiny scorecard evidence chain 可以拆成两层：

```text
run_ci_tiny_scorecard_comparison_smoke.py
  -> 生成 summary/check artifacts
  -> 生成 plan + summary_digest

check_ci_tiny_scorecard_plan.py
  -> 读取 plan
  -> 重新 hash artifacts
  -> 输出 plan check
```

这让 digest 从“写出来的字段”升级为“可独立验收的契约”。

## 一句话总结
v340 把 CI tiny scorecard wrapper plan 的 digest 从记录能力推进到验收能力，让 tiny benchmark CI 证据链更完整。
