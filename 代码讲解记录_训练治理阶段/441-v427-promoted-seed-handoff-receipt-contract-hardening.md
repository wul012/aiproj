# v427 promoted seed handoff receipt contract hardening 代码讲解

## 本版目标与边界

v427 的目标是加固 v426 已经升级到 schema v3 的 promoted seed handoff automation receipt。v426 证明 suite-design regression count/name 能进入 receipt、receipt check、embedded receipt check 和 handoff assurance；v427 继续补上两类风险：

- assurance smoke 过去只强检查 suite-design count，names 只是在 sidecar 里存在。
- 如果 receipt JSON 或 receipt-check JSON 的 suite-design 字段被旧产物覆盖，测试需要明确证明 embedded receipt check 会拒绝。

本版不改训练流程，不改 handoff 选择策略，不新增治理报告。它只强化 schema-v3 receipt sidecar 的一致性和防篡改证据。

## 前置链路

本版接在 v426 后面：

- v425：final promoted seed handoff 报告能看到 selected/global/comparison-ready suite-design regression context。
- v426：automation receipt schema v3、receipt check、embedded check 和 assurance 都能传播这些字段。
- v427：smoke 和测试开始保护 suite-design names 与 sidecar drift，不让合同只停留在“字段出现过”。

## 关键文件

### `scripts/check_promoted_seed_handoff_assurance_smoke.py`

本脚本是 CI/本地交接时的轻量 smoke。v427 在 `checks` 中新增三组 suite-design regression names：

```text
handoff_assurance_embedded_receipt_check_receipt_selected_handoff_batch_maturity_suite_design_regression_names
handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_names
handoff_assurance_embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_names
```

随后 `_check()` 明确断言它们等于空列表。这里用空列表，是因为 smoke fixture 走的是 clean handoff；重要的是 smoke 现在会读取并判断 names 字段，而不是只看 count。

### `tests/test_promoted_training_scale_seed_handoff_receipt_suite_design.py`

本测试文件继续作为 schema-v3 suite-design receipt contract 的聚焦测试，不把逻辑塞回更大的主测试文件。

新增 `SuiteDesignHandoffSidecars` TypedDict 和 `write_suite_design_handoff_with_sidecars()` helper，把一次脚本执行产生的五类输出放在一起：

```text
handoff
receipt_check
embedded_check
assurance
stdout
```

这样三个测试共享同一套 fixture 生成方式，后续再加 receipt sidecar 场景时不会重复整段 `subprocess.run()`。

本版新增两个防篡改测试：

- `test_embedded_receipt_check_rejects_tampered_suite_design_receipt_sidecar`
  - 先生成真实 schema-v3 handoff sidecar。
  - 再把 receipt JSON 里的 `handoff_batch_maturity_suite_design_regression_count` 从 2 改成 0。
  - 最后调用 embedded receipt check，断言状态为 `fail`，并且 issue 指向 receipt sidecar 的 count drift。

- `test_embedded_receipt_check_rejects_tampered_suite_design_check_names`
  - 先生成真实 receipt-check JSON。
  - 再把 `handoff_batch_maturity_suite_design_regression_names` 改成 `["beta-suite"]`。
  - 最后断言 embedded receipt check 失败，并且 issue 指向 receipt-check output JSON 的 name drift。

## 核心数据流

```text
suite-design promoted seed fixture
  -> execute_promoted_training_scale_seed.py
  -> handoff report + automation receipt
  -> receipt check sidecar
  -> embedded receipt check
  -> assurance smoke
  -> tamper tests mutate receipt/check sidecars
  -> embedded receipt check rejects stale sidecars
```

v427 的重点是最后两步：正常链路必须通过，篡改链路必须失败。这样 receipt contract 才是可执行合同，而不是只读展示字段。

## 测试覆盖

定向验证：

- `python -m pytest tests\test_promoted_training_scale_seed_handoff_receipt_suite_design.py tests\test_promoted_training_scale_seed_handoff_receipt.py -q`：`32 passed`
- `python -B scripts\check_promoted_seed_handoff_assurance_smoke.py --out-dir runs\v427-assurance-smoke`：`status=pass`

收口验证：

- `python -m pytest -q`：`722 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v427`：`status=pass`
- `git diff --check`：通过

这些断言保护了三层合同：

- smoke 保护 clean schema-v3 assurance 输出包含 suite-design names。
- receipt-sidecar tamper 测试保护 receipt JSON count 不会被旧值覆盖。
- receipt-check-sidecar tamper 测试保护 check JSON names 不会被旧值覆盖。

## 运行证据

`d/427` 归档了本版截图和说明：

- `d/427/图片/01-seed-handoff-receipt-contract-hardening.png`
- `d/427/解释/v427-seed-handoff-receipt-contract-hardening.html`
- `d/427/解释/v427-seed-handoff-receipt-contract-hardening-snapshot.md`
- `d/427/解释/v427-assurance-smoke-summary.json`
- `d/427/解释/v427-assurance-smoke-summary.txt`
- `d/427/解释/v427-suite-design-receipt-tamper-check.json`
- `d/427/解释/v427-suite-design-receipt-tamper-check.txt`
- `d/427/解释/说明.md`

`assurance-smoke/` 是干净链路原始输出，`tamper-evidence/` 是篡改检查使用的 sidecar 输入。它们都是本版证据的一部分，但不是新的训练成果。

一句话总结：v427 把 promoted seed handoff schema-v3 receipt contract 从“能传播 suite-design 字段”推进到“suite-design names 和 sidecar drift 都被 smoke 与测试保护”的硬化阶段。
