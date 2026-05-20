# v283 promoted seed handoff receipt checker artifacts

## 本版目标和边界

v283 的目标是让 v282 的 receipt checker 更适合 CI 和归档。

v282 已经可以检查 receipt JSON 并按 decision 退出，但还有两个使用摩擦：

1. 调用方必须知道 receipt JSON 的完整文件名。
2. checker 输出只在 stdout 中，不会留下自己的 check artifact。

v283 解决这两个问题：

- checker 可以接收 handoff 输出目录。
- checker 可以用 `--out-dir` 写出 check JSON/text。

本版不改变 receipt schema，不改变 `automation_summary`、`automation_gate` 或 seed handoff 业务判断。它只增强 checker 的输入解析和输出归档能力。

## 前置链路

相关前置版本：

- v281：生成 compact automation receipt JSON/text。
- v282：新增 receipt checker CLI。
- v283：checker 支持目录解析和 check artifact 输出。

这版属于 CI 接入体验增强。

## 核心常量

位置：`src/minigpt/promoted_training_scale_seed_handoff_receipt.py`

```python
RECEIPT_FILENAME = "promoted_training_scale_seed_handoff_automation_receipt.json"
```

这个常量让 resolver、测试和脚本共享文件名，避免散落字符串。

## 核心函数

### `resolve_promoted_training_scale_seed_handoff_automation_receipt_path(path)`

输入可以是：

- receipt JSON 文件路径。
- handoff 输出目录。

如果是目录，则自动拼接：

```text
<handoff_dir>/promoted_training_scale_seed_handoff_automation_receipt.json
```

如果文件不存在，抛出 `FileNotFoundError`。

### `write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs(check, out_dir)`

输出：

```text
promoted_training_scale_seed_handoff_automation_receipt_check.json
promoted_training_scale_seed_handoff_automation_receipt_check.txt
```

JSON 适合程序消费，text 适合 CI 日志和人工读取。

## CLI 行为

位置：`scripts/check_promoted_seed_handoff_receipt.py`

现在可以这样调用：

```powershell
python scripts/check_promoted_seed_handoff_receipt.py runs/training-scale-workflow/promoted-seed-handoff --out-dir runs/training-scale-workflow/promoted-seed-handoff/receipt-check
```

CLI 会打印：

```text
receipt_path=...
receipt_check_json=...
receipt_check_text=...
```

默认仍然遵循 v282 规则：

- receipt invalid：退出 1。
- receipt valid + decision continue：退出 0。
- receipt valid + decision stop：默认非零退出。
- `--allow-stop`：允许结构有效的 stop receipt 退出 0。

## 测试覆盖

位置：`tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增覆盖：

- checker 接收 handoff output directory。
- resolver 能从目录找到 receipt JSON。
- `--out-dir` 写出 check JSON/text。
- library writer 可单独写出 check artifact。

这组测试保护的是 checker 的 CI 集成能力。

## 运行证据

运行截图和解释归档在 `c/283`。

验证覆盖：

- receipt checker focused tests。
- promoted chain + receipt checker related tests。
- full unittest。
- source encoding hygiene。
- receipt checker smoke。
- Playwright/Chrome HTML 截图。

## 一句话总结

v283 让 promoted seed handoff receipt checker 支持目录输入和 check artifact 输出，进一步降低 CI 接入成本。
