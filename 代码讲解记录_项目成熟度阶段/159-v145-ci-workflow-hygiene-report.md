# 第一百四十五版代码讲解：CI workflow hygiene report

## 本版目标

v145 的目标是把 v144 的 GitHub Actions 修复做成可持续检查的工程门禁。

v144 已经把 `.github/workflows/ci.yml` 从 `actions/checkout@v4`、`actions/setup-python@v5` 升级到 v6，并删除 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`。这个修复解决了 Node 20 action target annotation，但如果后续有人改 workflow，原来只有一个单元测试在检查字符串。

v145 解决的问题是：让 CI workflow 策略有自己的报告模块、CLI gate、CI 步骤和运行证据。它不修改模型结构、训练逻辑、生成质量评分或推理服务。

## 前置路线

本版承接两条已有路线：

1. v142 的 source encoding hygiene gate
   - v142 把 CI 暴露出的 Python 3.11 parser mismatch 做成可运行检查器。
   - v145 复用这种思路，把 workflow 策略也做成可运行检查器。
2. v144 的 Node 24 native action 修复
   - v144 解决的是 workflow action 版本。
   - v145 解决的是 workflow action 策略如何被持续守住。

所以 v145 不是新增模型能力，而是把 CI 维护从“一次性修复”推进到“可重复验证的治理证据”。

## 关键文件

```text
src/minigpt/ci_workflow_hygiene.py
scripts/check_ci_workflow_hygiene.py
.github/workflows/ci.yml
tests/test_ci_workflow.py
README.md
c/145/解释/说明.md
```

`src/minigpt/ci_workflow_hygiene.py` 是核心模块。它读取 workflow 文本，抽取 `uses:` action，检查 action major、禁止的 env、Python 版本和必需命令，然后渲染 JSON/CSV/Markdown/HTML 证据。

`scripts/check_ci_workflow_hygiene.py` 是 CLI 门禁。它调用核心模块，默认输出到 `runs/ci-workflow-hygiene`，如果报告状态不是 `pass` 就返回非零退出码。

`.github/workflows/ci.yml` 新增 `CI workflow hygiene check` 步骤。这样 CI 不只运行 source encoding 和 unittest，也会检查 workflow 本身有没有退回旧策略。

`tests/test_ci_workflow.py` 从单纯的字符串守护升级为行为测试：当前 workflow 必须通过，旧 force-runtime workflow 必须失败，报告输出必须存在。

## 核心数据结构

`build_ci_workflow_hygiene_report()` 返回一个字典：

```text
schema_version
title
generated_at
workflow_path
policy
summary
actions
checks
recommendations
```

`policy` 是检查规则：

```text
required_actions:
  actions/checkout -> v6
  actions/setup-python -> v6
forbidden_env_vars:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24
required_command_fragments:
  scripts/check_source_encoding.py
  scripts/check_ci_workflow_hygiene.py
  unittest discover -s tests -v
required_python_version:
  3.11
```

这里的策略刻意保持窄范围，只覆盖项目真实需要守住的 CI 契约，而不是写一个通用 GitHub Actions linter。

`actions` 记录 workflow 中出现的 action：

```text
repository
version
raw
line
node24_native
```

`node24_native` 在本版中按项目策略判断：`actions/checkout` 和 `actions/setup-python` 的 major 版本达到 v6，视为符合 v144 核对过的 Node 24 native action 目标。

`checks` 是逐条门禁结果：

```text
id
category
target
expected
actual
status
detail
```

这些字段用于 CSV、Markdown 和 HTML 输出，也方便以后接入更高层 release gate 或 maturity narrative。

## 运行流程

CLI 运行链路如下：

```text
scripts/check_ci_workflow_hygiene.py
 -> build_ci_workflow_hygiene_report()
 -> write_ci_workflow_hygiene_outputs()
 -> print summary
 -> status != pass 时退出 1
```

核心模块内部流程如下：

1. 读取 `.github/workflows/ci.yml`。
2. 用轻量正则扫描 `uses: owner/action@version`。
3. 检查 `actions/checkout` 和 `actions/setup-python` 是否为 v6。
4. 检查是否还存在 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`。
5. 检查 workflow 是否保留 source encoding gate、CI workflow hygiene gate 和 unittest discovery。
6. 检查 `python-version` 是否仍然是 `3.11`。
7. 汇总 `summary`，并写出四类只读证据。

本版没有引入 PyYAML 依赖，因为当前检查只需要稳定识别少量字符串和 action 引用。这样更贴近项目现有轻量脚本风格，也减少 CI 依赖面。

## 输出产物

`write_ci_workflow_hygiene_outputs()` 写出：

```text
ci_workflow_hygiene.json
ci_workflow_hygiene.csv
ci_workflow_hygiene.md
ci_workflow_hygiene.html
```

这些文件都是只读证据，不反向修改 workflow，也不参与模型训练。它们的作用是：

- JSON 给后续程序消费。
- CSV 给表格审计或差异检查。
- Markdown 给命令行和版本说明引用。
- HTML 给截图和人工检查。

## 测试覆盖

`tests/test_ci_workflow.py` 覆盖四类风险：

- `test_ci_uses_node24_native_action_versions`
  - 保留 v144 的快速字符串守护，确保 workflow 里没有退回 `checkout@v4`、`setup-python@v5` 或 force env。
- `test_ci_workflow_hygiene_report_passes_current_workflow`
  - 读取真实 `.github/workflows/ci.yml`，断言 `status=pass`、`node24_native_action_count=2`、`forbidden_env_count=0`、`missing_step_count=0`、`python_version=3.11`。
- `test_ci_workflow_hygiene_report_fails_old_runtime_policy`
  - 构造一个旧 workflow fixture，包含 v4/v5 action、force env、Python 3.12，并缺少两个必需 gate，断言报告失败。
- `test_ci_workflow_hygiene_outputs_json_csv_markdown_and_html`
  - 证明四类 artifact 都能写出，并验证 HTML 转义与 Markdown 内容。

这组测试不只是检查“字符串存在”，还验证当前策略能通过、旧策略会失败、证据输出可渲染。

## CI 集成

`.github/workflows/ci.yml` 现在的质量链路是：

```text
checkout@v6
setup-python@v6 with Python 3.11
install requirements
source encoding and syntax check
CI workflow hygiene check
unittest discovery
```

这意味着 workflow 本身也被纳入 CI 检查。未来如果有人删除 source encoding gate、退回 action major、重新加入 force env，CI workflow hygiene gate 会直接失败。

## 截图与归档

v145 的运行截图和解释放在 `c/145`：

- `01-ci-workflow-tests.png`
- `02-ci-workflow-hygiene-smoke.png`
- `03-source-encoding-smoke.png`
- `04-maintenance-smoke.png`
- `05-full-unittest.png`
- `06-docs-check.png`

这些证据证明 v145 的新增 gate 可以单独运行、可以接入 CI、可以输出报告，并且没有破坏现有 source hygiene、maintenance policy 和全量测试。

## 边界说明

v145 不验证远端 action metadata。远端 metadata 已在 v144 里核对过：`checkout@v6` 和 `setup-python@v6` 使用 `node24`。本版把这个结论固化为项目内策略。

如果未来 GitHub 发布新的 action major，正确做法不是直接改常量，而是先重新核对远端 metadata，再更新 workflow、测试和 hygiene report。

## 一句话总结

v145 把 CI workflow 的 Node 24 native action 策略从一次性修复推进为可运行、可失败、可归档的治理门禁。
