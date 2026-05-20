# v295 promoted seed handoff assurance workflow line evidence

## 本版目标和边界

v295 的目标是把 v294 的 promoted seed handoff assurance smoke 顺序检查升级为行号证据。

v294 已经确保 smoke 命令必须存在且必须在 coverage 前。v295 进一步让 CI workflow hygiene 报告直接给出 smoke 行号和 coverage 行号，便于人工复盘 workflow 漂移，也便于后续自动化处理。

本版不改变 GitHub Actions 文件本身，不改变 smoke 脚本，不改变 coverage 阈值，也不改变模型训练逻辑。

## 前置链路

相关前置版本：

- v292：把 assurance smoke 接入 GitHub Actions。
- v293：让 smoke 写出 summary artifacts。
- v294：把 smoke 及其 before-coverage 顺序纳入 CI workflow hygiene。
- v295：把顺序检查的证据升级为行号形式。

这版属于“CI policy 的证据精度提升”。

## 关键修改文件

### `src/minigpt/ci_workflow_hygiene.py`

新增 helper：

```python
_first_line_number(text: str, fragment: str) -> int
```

它按行扫描 workflow 文本，返回首次出现 fragment 的 1-based 行号。找不到时返回 0。

`REQUIRED_COMMAND_ORDER` 的检查从字符串位置比较改为行号比较：

```python
before_line = _first_line_number(text, before)
after_line = _first_line_number(text, after)
```

然后：

- `actual` 变成 `before_line=<n>;after_line=<n>`
- `detail` 变成包含 smoke 和 coverage 行号的自然语言描述

示例：

```text
before_line=30;after_line=33
```

如果顺序错误，detail 会写成：

```text
Promoted seed handoff assurance smoke must run before coverage: smoke line 40, coverage line 33.
```

这比单纯写 `before` / `after` 更适合审计和后续工具消费。

### `src/minigpt/ci_workflow_hygiene_artifacts.py`

Markdown 和 HTML 已经展示 `order_violation_count`，v295 保持不变，但新的行号证据会通过 JSON 和 checks 直接传到这些 artifact。

### `tests/test_ci_workflow.py`

新增断言：

- 当前 workflow 的 order check `actual` 包含 `before_line=` 和 `after_line=`.
- 当前 workflow 的 detail 包含 `line`.
- 错误顺序 workflow 的 detail 同时包含 `smoke line` 和 `coverage line`.

测试仍保留：

- 当前 workflow pass。
- 旧 runtime policy fail。
- semver/bare major action tag 兼容性。
- outputs writer 兼容性。

## 输入输出格式

命令不变：

```powershell
python scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene
```

输出 JSON 中新增的 order 证据形态：

```json
{
  "id": "order:promoted_seed_handoff_assurance_smoke_before_coverage",
  "category": "required_order",
  "target": "promoted_seed_handoff_assurance_smoke_before_coverage",
  "expected": "before",
  "actual": "before_line=30;after_line=33",
  "status": "pass",
  "detail": "Required CI command order is preserved: before line 30, after line 33."
}
```

这让 workflow hygiene 报告不只是知道“顺序对了”，还知道“对在第几行”。

## 测试覆盖

本版验证包括：

- `tests.test_ci_workflow`
- project audit / release bundle / release readiness / coverage governance chain 相关测试
- full unittest
- source encoding hygiene
- coverage gate
- CI workflow hygiene command

## 运行证据

运行截图和解释归档在 `c/295`。

关键截图：

- `01-ci-workflow-tests.png`
- `02-ci-workflow-hygiene.png`
- `03-ci-hygiene-line-evidence.png`
- `04-governance-chain-tests.png`
- `05-full-unittest.png`
- `06-source-encoding.png`
- `07-coverage-gate.png`
- `08-docs-check.png`

## 一句话总结

v295 把 promoted seed handoff assurance smoke 的 workflow 顺序检查从“逻辑顺序正确”推进为“带行号的可审计证据”。
