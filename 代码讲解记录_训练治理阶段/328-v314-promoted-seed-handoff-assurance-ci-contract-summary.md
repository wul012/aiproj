# v314 promoted seed handoff assurance CI contract summary

## 本版目标和边界

v313 已经把 promoted seed handoff automation receipt 升级到 `schema_version=2`，并要求 receipt/check/embedded sidecar 都比较 CI-regression 字段。这个契约已经足够严，但还有一个可观察性缺口：最外层 handoff assurance 和 assurance smoke summary 只显示 `pass/fail`、sidecar 状态和输出路径，CI 日志里看不到本次到底验证了哪个 receipt schema，以及 selected/aggregate CI regression counters 是否真的进入最终交接摘要。

v314 的目标是把 v313 的 schema-v2 receipt CI contract 向外层提升：

- embedded receipt check 输出扁平 receipt contract 字段。
- handoff assurance 把这些字段作为自己的顶层 key/value diagnostics。
- assurance smoke summary 断言并输出这些字段。
- main handoff CSV/Markdown/HTML 也显示 assurance 层 receipt contract。

本版不改变训练计划生成、模型训练、clean-evidence gate、clean-batch gate 或 automation decision 的判定规则。它只增强 receipt evidence chain 的最终摘要可见性。

## 前置能力

本版承接 v313：

- `promoted_training_scale_seed_handoff_automation_receipt.json` 已经是 `schema_version=2`。
- schema-v2 receipt 必须包含 `selected_handoff_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_count` 和 `comparison_exclusion_reasons`。
- embedded receipt check 已经能打开 receipt JSON、check JSON、check text sidecar，并拒绝 tampered CI-regression sidecar。

v314 让这些已校验字段继续出现在 assurance/smoke 的外层摘要里。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`
  - `check_promoted_training_scale_seed_handoff_embedded_receipt_check()` 新增扁平 receipt contract 字段。
  - `render_promoted_training_scale_seed_handoff_embedded_receipt_check()` 输出这些字段，方便 CLI 和 text sidecar 被直接 grep。
- `src/minigpt/promoted_training_scale_seed_handoff_assurance.py`
  - assurance 比较键加入 receipt schema 和 CI-regression 字段，防止 main embedded check 与 recomputed check 在这些字段上漂移。
  - assurance JSON/text 顶层输出 `embedded_receipt_check_receipt_schema_version`、selected/aggregate CI counts 和 comparison exclusion reasons。
- `scripts/check_promoted_seed_handoff_assurance_smoke.py`
  - smoke summary 的 `checks` 字段加入 assurance 层 receipt contract。
  - smoke 断言 schema version 必须为 2，CI regression counts 和 exclusion reasons 必须符合干净 smoke corpus 的预期。
- `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`
  - main handoff CSV、Markdown、HTML 加入 assurance receipt contract 字段，避免报告只显示 assurance status。
- `tests/test_promoted_training_scale_seed_handoff_receipt.py`
  - 扩展 inline assurance 测试，断言 JSON/text/CSV/Markdown/HTML/CLI 都展示 schema-v2 receipt contract。
  - 新增带 `handoff_ci_regression_count=2` 的 assurance 测试，证明非零 CI regression count 和 exclusion reason 能穿透到 assurance。
  - 扩展 smoke summary 测试，证明最终 CI smoke artifact 暴露这些字段。

## 数据结构和字段语义

embedded receipt check 新增字段：

```text
receipt_schema_version
receipt_selected_handoff_batch_maturity_ci_regression_count
receipt_handoff_batch_maturity_ci_regression_count
receipt_comparison_exclusion_reasons
```

这些字段来自 recomputed `expected_check`，也就是由当前 handoff report 重新生成的 automation receipt check。它们不是人工填充的说明文本，而是 receipt checker 已经验证过的机器字段。

handoff assurance 再把它们改名为 assurance 语境的顶层字段：

```text
embedded_receipt_check_receipt_schema_version
embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count
embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count
embedded_receipt_check_receipt_comparison_exclusion_reasons
```

smoke summary 最终输出：

```text
handoff_assurance_embedded_receipt_check_receipt_schema_version=2
handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_ci_regression_count=0
handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_ci_regression_count=0
handoff_assurance_embedded_receipt_check_receipt_comparison_exclusion_reasons=[]
```

这使 CI 日志和 JSON summary 不再需要打开 nested `expected_embedded_receipt_check.expected_check` 才能知道 receipt contract 是否被检查。

## 运行流程

1. `execute_promoted_training_scale_seed.py` 生成 handoff report 和 schema-v2 automation receipt。
2. receipt checker 生成 `receipt_check` 与 receipt check sidecar。
3. embedded receipt check 重算 expected receipt check，比较 main report、receipt sidecar、check sidecar，并输出扁平 receipt contract 字段。
4. handoff assurance 重算 embedded receipt check，比较 main report 和 embedded check sidecar，并把 receipt contract 字段提升到 assurance 顶层。
5. assurance smoke 读取 main handoff report 中的 `handoff_assurance`，把 receipt schema/CI fields 写入 smoke summary，并对这些字段做断言。

## 测试覆盖

- `tests.test_promoted_training_scale_seed_handoff_receipt`
  - 28 个 receipt/embedded/assurance 测试通过。
  - 覆盖 schema-v2 字段在 assurance JSON/text、main handoff CSV/Markdown/HTML 和 CLI stdout 中的输出。
  - 覆盖 `handoff_ci_regression_count=2` 时，aggregate CI count 和 comparison exclusion reason 能进入 assurance。
- 训练链路组合测试
  - `tests.test_promoted_training_scale_seed_handoff`
  - `tests.test_promoted_training_scale_seed_handoff_receipt`
  - `tests.test_promoted_training_scale_seed_handoff_review`
  - 共 60 个测试通过，证明主 handoff、receipt、review helper 未被破坏。
- 全量测试
  - `python -B -m unittest discover -s tests`
  - 583 个测试通过。
- 编码与静态检查
  - `scripts/check_source_encoding.py` 通过，283 个 Python source clean。
  - `git diff --check` 通过。

## 运行证据

运行截图和解释归档在 `d/314`：

- `d/314/图片/01-receipt-assurance-tests.png`
- `d/314/图片/02-chain-tests.png`
- `d/314/图片/03-py-compile.png`
- `d/314/图片/04-source-encoding.png`
- `d/314/图片/05-full-unittest.png`
- `d/314/图片/06-diff-check.png`
- `d/314/解释/说明.md`

这些证据分别覆盖聚焦测试、链路测试、语法编译、source encoding、全量测试和 whitespace/diff 检查。

## 一句话总结

v314 把 promoted seed handoff 的 schema-v2 receipt CI contract 从内层 sidecar 校验提升到最终 assurance 和 CI smoke 摘要，让最外层自动化交接也能直接看到并验证 CI 回归证据。
