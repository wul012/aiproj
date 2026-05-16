# 第一百四十二版代码讲解：source encoding target compatibility

## 本版目标

v142 的目标是把 `source_encoding_hygiene` 从“UTF-8 BOM + 当前解释器语法检查”推进到“目标 Python 版本兼容性门禁”。这次来自 GitHub CI 暴露的问题：本地 Python 3.13 能通过的 f-string 写法，在 Python 3.11 CI 里会触发语法错误。

本版不新增模型训练能力，不改 Transformer、tokenizer、benchmark、maturity narrative 或 release gate 的业务规则。它只收紧源代码卫生检查，让 CI 失败原因可以在本地、报告和测试里更早出现。

## 前置路线

v127 已经建立了 source encoding hygiene gate，用来检查 Python 源码是否含 UTF-8 BOM、是否能被当前解释器 `ast.parse`。v142 接在这条线上，补上一个更具体的现实问题：当前解释器不一定等于 CI 解释器。

这类门禁属于 AI 工程治理项目的基础设施。它不证明模型变强，但能保护项目不会因为编辑器编码、解释器版本或语法漂移导致远端 CI 才暴露失败。

## 关键文件

`src/minigpt/source_encoding_hygiene.py` 是核心修改点。`build_source_encoding_report` 新增 `target_python` 参数，默认值是 `3.11`。报告的 `policy` 里会写入目标版本，并声明启用的兼容性检查。

`scripts/check_source_encoding.py` 是 CLI 入口。它新增 `--target-python` 参数，并在 stdout 打印 `compatibility_error_count` 和 `target_python`，让 GitHub Actions 日志能直接看到兼容性门禁的结果。

`tests/test_source_encoding_hygiene.py` 增加了目标兼容性样例。测试覆盖 Python 3.13 本机路径和 `uv run --python 3.11` 路径，承认同一段 Python 3.12+ f-string 在 3.11 下可能先表现为语法错误，但兼容性字段仍然必须能定位问题。

`README.md`、`c/142` 和本讲解文件负责把本版能力、证据和 tag 含义记录下来，方便后续回看“为什么 source encoding gate 突然有 target Python 概念”。

## 数据结构变化

每个文件记录新增两个字段：

```json
{
  "compatibility_ok": true,
  "compatibility_error": ""
}
```

`compatibility_ok` 表示该文件是否通过目标版本兼容性检查。`compatibility_error` 当前会写成类似 `python-3.11-fstring-compat:2` 的格式，冒号后的数字是源码行号。

summary 新增：

```json
{
  "compatibility_error_count": 0,
  "compatibility_error_paths": []
}
```

`clean_count` 也随之收紧：文件必须同时满足无 BOM、语法通过、目标兼容性通过，才算 clean。

## 核心流程

`build_source_encoding_report` 接收路径列表后，对每个 Python 文件调用 `_scan_source_file`。扫描分三层：

1. 读取 bytes，判断是否以 UTF-8 BOM 开头。
2. 用 `ast.parse` 检查当前解释器是否能解析。
3. 用 `_target_compatibility_error` 检查目标 Python 版本风险。

第三层是 v142 的新增能力。它先用 `tokenize.generate_tokens` 找到真实源码 token 中的 f-string 起点，再调用 `_python311_fstring_quote_risk_at` 检查 f-string 表达式里是否出现 Python 3.11 不接受的同引号嵌套形态。

这里特意没有做简单的逐行字符串搜索。原因是测试文件、文档字符串或普通字符串里可能包含“坏代码样例”，如果只靠文本搜索，会把 fixture 误判成项目源码错误。tokenize 让检查更接近真实源码结构。

## 输出格式

JSON 是最完整的机器可读证据，包含 policy、summary、files 和 recommendations。CSV 增加 `compatibility_ok` 与 `compatibility_error`，方便快速筛选。Markdown 和 HTML 都增加 compatibility 统计与 offending file 列。

HTML 的修复也很关键：compatibility-only 错误必须出现在 Offending Files 表格里。否则报告 summary 会失败，但页面看不到具体文件，这会降低排错价值。

这些输出是最终证据，可以被 CI 日志、README 截图、人工 review 或后续治理脚本消费；它们不是训练产物，也不代表模型质量。

## 测试覆盖

`test_report_detects_python311_fstring_compatibility_errors` 构造一段 Python 3.12+ f-string。它断言报告状态失败、compatibility error 计数为 1、路径和行号可追踪，并且 HTML 里能看到 offending file 与错误码。

`test_report_allows_compatibility_target_override` 证明目标版本可以覆盖为 `3.13`。在 Python 3.13 本机下它应通过；在 Python 3.11 下，即使 target override 取消兼容性错误，`ast.parse` 仍然可能报告语法错误。测试用 `sys.version_info` 明确表达这个差异。

CLI 测试继续保护 BOM fail 行为，同时新增 `target_python=3.11` 的 stdout 断言，保证 GitHub Actions 日志可读。

## 运行证据

v142 的截图和解释放在 `c/142`：

- `01-source-encoding-tests.png`：本机 source encoding hygiene 单测。
- `02-python311-tests.png`：同一组测试在 Python 3.11 下运行。
- `03-source-encoding-smoke.png`：仓库级 source encoding smoke，207 个 Python 源文件全部 clean。
- `04-maintenance-smoke.png`：维护批处理与 module pressure 检查。
- `05-full-unittest.png`：全量 unittest discovery。
- `06-docs-check.png`：README、归档、讲解索引和目标兼容性关键字检查。

这些证据说明 v142 的 CI 防护已经在本地和 Python 3.11 路径闭环。

## 边界说明

当前兼容性检查是定向门禁，只覆盖本次 CI 暴露出的 Python 3.11 f-string 风险，不是完整的跨版本 Python 语法分析器。如果后续 CI 目标版本变化，应该通过 `--target-python` 更新策略，而不是把所有语法差异都塞进一次改动。

本版也没有把 source encoding gate 接入更多 release gate 规则。它先保证 `scripts/check_source_encoding.py` 自己足够可靠，再决定是否让上层治理报告消费它。

## 一句话总结

v142 把 source encoding hygiene 从“当前解释器能不能解析”提升为“目标 CI Python 版本能不能接受”，让语法兼容性问题更早、更清楚地在本地门禁里暴露。
