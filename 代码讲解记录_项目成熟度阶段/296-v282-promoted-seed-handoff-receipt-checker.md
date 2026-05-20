# v282 promoted seed handoff receipt checker

## 本版目标和边界

v282 的目标是给 v281 新增的 automation receipt 增加一个专门 checker CLI。

v281 已经把最终自动化决策写成 compact receipt。但外部 CI 如果要使用它，还要自己完成三件事：

1. 读取 JSON。
2. 判断字段是否自洽。
3. 按 `automation_decision` 和 `automation_exit_code` 退出。

v282 把这三件事收进一个脚本：

```powershell
python scripts/check_promoted_seed_handoff_receipt.py <receipt.json>
```

本版不重新计算 seed handoff，不修改 `automation_summary` 或 `automation_gate` 的判断规则，也不改变 receipt 生成格式。它只消费 v281 的 receipt。

## 前置链路

相关前置版本：

- v278：建立 `automation_gate`。
- v279：gate 增加决策和 exit code。
- v280：新增 `automation_summary` 作为最终自动化出口。
- v281：把最终出口写成 compact receipt JSON/text。
- v282：新增 receipt checker CLI，让 receipt 成为可直接运行的 CI gate 输入。

这版属于自动化消费链路增强，不是模型能力增强。

## 核心模块

位置：`src/minigpt/promoted_training_scale_seed_handoff_receipt.py`

### `load_promoted_training_scale_seed_handoff_automation_receipt(path)`

负责读取 receipt JSON。

约束：

- 文件必须是 JSON object。
- 使用 `utf-8-sig` 读取，兼容 BOM。
- 不做业务重算，只返回 dict。

### `check_promoted_training_scale_seed_handoff_automation_receipt(receipt)`

负责结构和一致性校验。

检查内容：

- `receipt_type` 必须是 `promoted_training_scale_seed_handoff_automation`。
- `schema_version` 必须 >= 1。
- `automation_decision` 必须是 `continue` 或 `stop`。
- `continue` 必须配 `automation_exit_code=0`。
- `stop` 必须配非零 `automation_exit_code`。
- `stop` 必须有 `automation_blocking_source`。
- `continue` 不应携带 blocking source。
- 当 blocking source 是 `automation_gate` 时，必须有 failed requirements。

返回对象包括：

- `status`
  - `pass` 或 `fail`，表示 receipt 结构是否有效。
- `decision`
  - receipt 的 automation decision。
- `exit_code`
  - receipt 的 automation exit code。
- `checker_exit_code`
  - checker 建议退出码。
- `blocking_source`
  - 阻塞来源。
- `failed_requirements`
  - 失败 requirement。
- `issues`
  - 结构问题列表。

### `render_promoted_training_scale_seed_handoff_automation_receipt_check(check)`

把 check 结果渲染成 key/value 文本：

```text
receipt_check_status=pass
receipt_decision=stop
receipt_exit_code=1
receipt_checker_exit_code=1
receipt_blocking_source=automation_gate
receipt_failed_requirements=["clean_evidence"]
```

这让 CI 日志和截图都能直接看到关键字段。

## CLI 行为

位置：`scripts/check_promoted_seed_handoff_receipt.py`

默认行为：

- receipt 结构无效：退出 1。
- receipt 结构有效且 decision 是 `continue`：退出 0。
- receipt 结构有效但 decision 是 `stop`：按 receipt exit code 非零退出。

`--allow-stop`：

- receipt 结构有效时，即使 decision 是 `stop` 也退出 0。
- 适合“只验证 receipt 是否格式正确”的测试或归档场景。

## 测试覆盖

位置：`tests/test_promoted_training_scale_seed_handoff_receipt.py`

覆盖场景：

- continue receipt：checker pass，exit code 0。
- stop receipt：checker 结构 pass，但 checker exit code 为 1。
- 不一致 receipt：checker status fail。
- 从真实 seed handoff 输出中读取 receipt，并用 CLI 检查 continue receipt。
- 对 stop receipt 默认非零退出，`--allow-stop` 则可通过。

这组测试保护的是 CI 消费行为，而不是 seed handoff 业务规则本身。

## 运行证据

运行截图和解释归档在 `c/282`。

验证覆盖：

- receipt checker focused tests。
- promoted seed handoff + receipt checker 相关链路 tests。
- full unittest。
- source encoding hygiene。
- receipt checker smoke。
- Playwright/Chrome HTML 截图。

## 一句话总结

v282 给 promoted seed handoff automation receipt 增加 checker CLI，让 compact receipt 从“可读取的证据”升级为“可直接作为 CI gate 的输入”。
