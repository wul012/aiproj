# v284 promoted seed handoff inline receipt check

## 本版目标和边界

v284 的目标是把 v282-v283 的 receipt checker 接回 promoted seed handoff 执行入口。

v283 已经可以单独运行：

```powershell
python scripts/check_promoted_seed_handoff_receipt.py <handoff-output-dir> --out-dir <receipt-check-dir>
```

但真实自动化里更常见的场景是：

1. 先执行 promoted seed handoff。
2. 生成 handoff JSON/CSV/Markdown/HTML 和 automation receipt。
3. 立刻校验这份刚生成的 receipt。
4. 即便最终 automation decision 是 `stop`，也要留下 receipt-check artifact 供 CI 或人工复盘。

v284 解决的是第 3-4 步的衔接问题。

本版不改变 receipt schema，不改变 `automation_gate`、`automation_summary`、clean-evidence gate、clean batch-review gate，也不改变默认执行行为。只有显式传入 `--receipt-check-out-dir` 时才会额外写 receipt-check JSON/text。

## 前置链路

相关前置版本：

- v281：promoted seed handoff 生成 compact automation receipt JSON/text。
- v282：新增独立 receipt checker CLI。
- v283：checker 支持 handoff 输出目录输入，并可写 check artifacts。
- v284：执行脚本内联调用 checker，把生成和检查连成一个可选闭环。

这版属于自动化取证闭环增强，不是模型能力提升版本。

## 关键修改文件

### `scripts/execute_promoted_training_scale_seed.py`

新增参数：

```text
--receipt-check-out-dir <path>
```

它的语义是：

- 从本次 `write_promoted_training_scale_seed_handoff_outputs()` 生成的 `automation_receipt_json` 读取 receipt。
- 调用 `check_promoted_training_scale_seed_handoff_automation_receipt()` 做结构和决策一致性校验。
- 调用 `write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs()` 写出 check JSON/text。
- 在 stdout 打印 `receipt_check_status`、`receipt_decision`、`receipt_check_json`、`receipt_check_text` 等 key/value。

新增内部函数：

```python
def _write_receipt_check(outputs: dict[str, str], out_dir: Path | None) -> dict[str, object] | None:
```

输入：

- `outputs`：handoff 输出 writer 返回的路径字典。
- `out_dir`：receipt-check artifact 输出目录。

输出：

- 没有传 `out_dir` 时返回 `None`。
- 传入 `out_dir` 时返回 receipt check dict，并写入 JSON/text。

这个函数只消费已经写出的 receipt 文件，而不是从内存中的 report 重新构造 receipt。这样测试的是最终落盘产物，和 CI 读取的对象一致。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增两个执行链路测试：

1. `test_execute_script_can_write_receipt_check_outputs`
   - 执行 promoted seed handoff。
   - 开启 `--execute` 和 `--require-clean-evidence`。
   - 传入 `--receipt-check-out-dir`。
   - 断言 check JSON/text 存在，且 decision 为 `continue`。

2. `test_execute_script_writes_receipt_check_before_stop_exit`
   - 构造 clean batch-review 为 `review` 的 seed。
   - 开启 `--require-clean-batch-review`。
   - 传入 `--receipt-check-out-dir`。
   - 命令最终非零退出，但 receipt-check JSON/text 必须已经写出。
   - 断言 check 本身结构有效，decision 为 `stop`，blocking source 为 `automation_gate`。

第二个测试是本版关键保护点：阻塞不是问题，阻塞后没有证据才是问题。

## 输入输出格式

执行命令示例：

```powershell
python scripts/execute_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-seed --execute --out-dir runs/training-scale-workflow/promoted-seed-handoff --receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/receipt-check
```

新增输出目录：

```text
runs/training-scale-workflow/promoted-seed-handoff/receipt-check/
  promoted_training_scale_seed_handoff_automation_receipt_check.json
  promoted_training_scale_seed_handoff_automation_receipt_check.txt
```

新增 stdout key：

```text
receipt_check_status=pass
receipt_decision=continue|stop
receipt_exit_code=0|1|...
receipt_checker_exit_code=0|1
receipt_blocking_source=...
receipt_check_outputs={...}
receipt_check_json=...
receipt_check_text=...
```

这些字段和独立 checker 的输出保持一致，只是现在可以由 handoff 执行脚本直接产出。

## 运行流程

v284 后的可选流程是：

```text
build handoff report
  -> write handoff outputs
  -> write automation receipt JSON/text
  -> if --receipt-check-out-dir:
       load generated receipt JSON
       check receipt contract
       write receipt-check JSON/text
       print receipt-check diagnostics
  -> print automation summary
  -> exit from automation_summary decision
```

注意 receipt-check 写入发生在最终 `automation_summary` 退出前。这样 `stop` 场景也能留下 check 证据。

## 测试覆盖

本版重点测试包括：

- receipt checker focused tests。
- promoted seed handoff receipt 相关链路测试。
- promoted training-scale comparison / decision / seed / handoff 相关测试。
- full unittest。
- source encoding hygiene。
- inline receipt-check smoke。

新增测试保护的不是某个展示字段，而是自动化闭环顺序：

- 先落盘 receipt。
- 再检查 receipt。
- 再由 automation summary 决定退出。

## 运行证据

运行截图和解释归档在 `c/284`。

其中包含：

- 聚焦测试截图。
- 相关链路测试截图。
- 全量单测截图。
- source encoding hygiene 截图。
- inline receipt-check smoke 截图。
- Playwright/Chrome 渲染的 handoff HTML 截图。
- 文档一致性检查截图。

这些证据说明 v284 是在已有 handoff/receipt 产物基础上补自动化取证闭环，而不是改变主链路判断。

## 一句话总结

v284 让 promoted seed handoff 执行脚本可以在生成 receipt 后立刻自检并归档 receipt-check 证据，使 blocked automation run 也能留下可追溯诊断。
