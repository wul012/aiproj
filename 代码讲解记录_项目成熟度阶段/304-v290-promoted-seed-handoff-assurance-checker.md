# v290 promoted seed handoff assurance checker

## 本版目标和边界

v290 的目标是给 promoted seed handoff 输出目录增加一个总体验证入口：只要交给它主报告或 handoff 输出目录，就能确认主报告、embedded receipt-check 字段、embedded-check JSON/text sidecar 都一致。

v281-v289 已经完成三层证据链：

- automation receipt JSON/text
- receipt-check JSON/text
- embedded receipt-check JSON/text
- 主 handoff report 内嵌 receipt-check 和 embedded receipt-check 摘要

但这些证据仍然需要分层查看。v290 增加 assurance checker，把这些已经存在的证据作为一个整体校验。

本版不改变 handoff 决策，不改变 receipt schema，不新增训练能力，也不把治理证据包装成模型效果提升。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt。
- v282-v283：receipt checker 与 checker artifact 输出。
- v284-v285：inline receipt-check 并写回主报告。
- v286-v287：embedded receipt-check 与 sidecar integrity。
- v288-v289：inline embedded receipt-check 并写回主报告。
- v290：目录级 assurance checker。

这版属于证据链收口，不是新报告堆叠。

## 关键新增文件

### `src/minigpt/promoted_training_scale_seed_handoff_assurance.py`

这个模块负责核心校验逻辑。

核心函数：

```python
check_promoted_training_scale_seed_handoff_assurance(path)
```

输入：

- `promoted_training_scale_seed_handoff.json`
- 或包含该 JSON 的 handoff 输出目录

运行流程：

```text
resolve handoff report
  -> load main handoff report
  -> recompute embedded receipt-check
  -> compare recomputed result with embedded_receipt_check in main report
  -> resolve embedded_receipt_check_outputs JSON/text
  -> open and compare embedded-check JSON sidecar
  -> open and compare embedded-check text sidecar
  -> return assurance status
```

输出字段：

- `status`
- `decision`
- `checker_exit_code`
- `embedded_receipt_check_status`
- `embedded_receipt_check_sidecar_status`
- `embedded_receipt_check_output_json_exists`
- `embedded_receipt_check_output_text_exists`
- `issue_count`
- `issues`

它还保留：

- `expected_embedded_receipt_check`
- `main_embedded_receipt_check`
- `main_embedded_receipt_check_outputs`

这些字段用于诊断，不是新的 handoff 决策源。

### `scripts/check_promoted_seed_handoff_assurance.py`

这是 CLI 包装层。

典型命令：

```powershell
python scripts/check_promoted_seed_handoff_assurance.py runs/training-scale-workflow/promoted-seed-handoff --out-dir runs/training-scale-workflow/promoted-seed-handoff/assurance
```

CLI 输出稳定 key/value：

```text
handoff_assurance_status=pass
handoff_assurance_decision=continue
handoff_assurance_embedded_receipt_check_status=pass
handoff_assurance_embedded_receipt_check_sidecar_status=pass
handoff_assurance_output_json_exists=True
handoff_assurance_output_text_exists=True
```

`--out-dir` 会写：

- `promoted_training_scale_seed_handoff_assurance.json`
- `promoted_training_scale_seed_handoff_assurance.txt`

`--allow-stop` 的语义和前两个 checker 保持一致：结构一致的 stop 可以被当作“校验通过但业务停止”处理。

## 测试覆盖

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增三类 assurance 测试：

- 完整 inline handoff 输出目录通过。
- 篡改主报告里的 `embedded_receipt_check.sidecar_status` 会失败。
- 删除 embedded-check JSON sidecar 会失败。

这些断言保护的是：

- 主报告不能和 sidecar 不一致。
- sidecar 缺失不能被当成通过。
- assurance CLI 的 exit code 和 key/value 输出可以被 CI 消费。

## 运行证据

运行截图和解释归档在 `c/290`。

关键截图：

- `01-focused-tests.png`
- `02-handoff-tests.png`
- `03-related-chain-tests.png`
- `04-full-unittest.png`
- `05-source-encoding.png`
- `06-inline-handoff-smoke.png`
- `07-assurance-smoke.png`

## 一句话总结

v290 把 promoted seed handoff 的 receipt 证据链从“主报告和 sidecar 都可查”推进为“可由一个 assurance checker 整体确认”。
