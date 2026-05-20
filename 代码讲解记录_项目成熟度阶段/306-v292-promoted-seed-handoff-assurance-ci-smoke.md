# v292 promoted seed handoff assurance CI smoke

## 本版目标和边界

v292 的目标是把 v291 已经能 inline 产出的 promoted seed handoff assurance 链路接入 GitHub Actions。

v291 证明一条执行命令可以写出主 handoff report、automation receipt、receipt-check、embedded receipt-check 和 handoff assurance。v292 进一步提供一个轻量 smoke 脚本，在 CI coverage 前先跑这条最小闭环，避免核心自动化交接证据链只在本地测试里存在。

本版不改变 handoff 报告 schema，不改变模型训练逻辑，不改变 coverage 阈值，也不把 smoke 结果解释为模型质量提升。它只证明“自动化交接证据链可以在 CI 中跑通”。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt。
- v282-v283：提供 receipt checker 与 checker artifact。
- v284-v285：执行脚本 inline receipt-check 并写回主报告。
- v286-v289：embedded receipt-check 与 sidecar integrity 写回主报告。
- v290：目录级 handoff assurance checker。
- v291：执行脚本 inline handoff assurance。
- v292：把 inline assurance 链路提升为 CI smoke gate。

这版属于“把本地证据链提升为持续集成保护”。

## 关键修改文件

### `.github/workflows/ci.yml`

新增步骤：

```yaml
- name: Promoted seed handoff assurance smoke
  run: python -B scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke-ci
```

该步骤位于 source encoding、CI workflow hygiene 之后，coverage 之前。

含义是：如果 promoted seed handoff 的 receipt/check/embedded/assurance 链路已经断裂，CI 会在进入完整 coverage 前先失败，并保留 smoke 输出目录。

### `scripts/check_promoted_seed_handoff_assurance_smoke.py`

这是本版新增的 CI-ready smoke 入口。

它内部先生成一个最小 promoted seed tree：

- `corpus.txt`：最小训练语料。
- `promoted_training_scale_seed.json`：包含 selected baseline、suite、suite guard、next plan command。
- next plan command 指向 `scripts/plan_training_scale.py`，用于模拟真实 promoted seed handoff 的下游计划。

然后它运行：

```powershell
python scripts/execute_promoted_training_scale_seed.py <seed> `
  --out-dir <out>/handoff `
  --execute `
  --require-clean-evidence `
  --receipt-check-out-dir <out>/receipt-check `
  --embedded-receipt-check-out-dir <out>/embedded-receipt-check `
  --assurance-out-dir <out>/assurance
```

执行完成后，它读取主报告：

```text
<out>/handoff/promoted_training_scale_seed_handoff.json
```

并检查：

- `handoff_assurance.status == pass`
- `handoff_assurance.decision == continue`
- `handoff_assurance.embedded_receipt_check_status == pass`
- `handoff_assurance.embedded_receipt_check_sidecar_status == pass`
- assurance JSON/text sidecar 存在。
- 主报告记录的 output path 能解析到真实文件。

脚本输出稳定 key/value 行，例如：

```text
status=pass
decision=continue
handoff_assurance_status=pass
handoff_assurance_embedded_receipt_check_sidecar_status=pass
```

这些行可以被 CI log、人工检查或后续脚本直接消费。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增测试：

```python
test_handoff_assurance_smoke_script_passes
```

该测试直接调用新增 smoke 脚本，而不是只测库函数。它保护三件事：

- CI 入口脚本可以独立运行。
- 主报告确实嵌入了 `handoff_assurance`。
- `handoff_assurance_outputs.json` 指向真实 sidecar 文件。

## 输入输出格式

推荐本地命令：

```powershell
python scripts/check_promoted_seed_handoff_assurance_smoke.py --out-dir runs/promoted-seed-handoff-assurance-smoke
```

输出目录结构：

```text
runs/promoted-seed-handoff-assurance-smoke/
  seed-source/
  handoff/
  receipt-check/
  embedded-receipt-check/
  assurance/
  execute_stdout.txt
  execute_stderr.txt
```

其中 `handoff/` 是主报告目录，`assurance/` 是最终复核 sidecar 目录。

## 测试覆盖

本版验证包括：

- 新 smoke 脚本 py_compile。
- `scripts/check_promoted_seed_handoff_assurance_smoke.py` 真实执行。
- `scripts/check_ci_workflow_hygiene.py` 确认 GitHub Actions 结构仍通过。
- `tests.test_promoted_training_scale_seed_handoff_receipt` 覆盖新增 smoke 入口和既有 receipt/embedded/assurance 链路。
- handoff、promoted comparison、decision、seed、receipt 相关链路回归。
- full unittest、source encoding、coverage gate。

这些测试保护的是 CI smoke 与现有 evidence chain 的连接，而不是模型生成质量。

## 运行证据

运行截图和解释归档在 `c/292`。

关键截图：

- `01-assurance-smoke.png`
- `02-ci-workflow-hygiene.png`
- `03-focused-receipt-tests.png`
- `04-handoff-tests.png`
- `05-related-chain-tests.png`
- `06-full-unittest.png`
- `07-source-encoding.png`
- `08-coverage-gate.png`
- `09-docs-check.png`

## 一句话总结

v292 把 promoted seed handoff assurance 从“执行脚本可选归档”推进为“GitHub Actions coverage 前会自动验证的 CI smoke gate”。
