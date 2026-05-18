# v239 test coverage baseline report 代码讲解

## 本版目标

v239 的目标是把“aiproj 测试比提升 + coverage gate”建议里的第一步落地：先建立可复现、可归档的 coverage baseline，再决定后续是否启用 fail-under 门槛。

这版把 CI 的 unittest 入口改为覆盖率报告脚本，让每次 GitHub Actions 都能产出覆盖率 JSON/CSV/Markdown/HTML 证据。它补的是测试治理的观测能力，不是模型训练能力。

## 不做什么

本版不启用覆盖率失败门槛。

本版不改变现有 unittest 的发现范围、测试断言或模型训练逻辑。

本版不把 coverage 数字包装成生产质量结论。当前覆盖率只说明测试执行触达了多少 Python 语句，不能替代真实训练效果、benchmark 质量或线上稳定性。

## 来自哪条路线

前一版 v238 补了 Dependabot，让 Actions 和 Python 依赖更新有自动 PR 入口。

v239 顺着“测试纪律”短板继续推进：先让 CI 每次运行测试时留下 coverage baseline。后续如果要做 coverage gate，可以基于真实 baseline 逐步加阈值，而不是凭感觉设置一个可能误伤开发节奏的数字。

## 关键文件

### `requirements.txt`

新增：

```text
coverage>=7.0
```

这是运行 coverage.py 的唯一新增依赖。项目没有引入 pytest-cov 或额外测试框架，仍然沿用 `unittest discover`。

### `.github/workflows/ci.yml`

CI 的 Unit tests 步骤从直接运行：

```text
python -B -m unittest discover -s tests -v
```

调整为：

```text
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci
```

这样 CI 仍然执行全量 unittest，但同时生成覆盖率报告。脚本失败时 CI 也会失败；覆盖率数字本身暂时不参与失败判断。

### `scripts/run_test_coverage.py`

这个脚本是命令入口。

运行流程：

1. 创建输出目录。
2. 执行 `coverage run --source=src/minigpt -m unittest discover -s tests -v`。
3. 执行 `coverage json -o <out-dir>/coverage.json`。
4. 调用 `build_test_coverage_report()` 汇总覆盖率数据。
5. 写出 JSON/CSV/Markdown/HTML 四种报告。
6. 在终端打印核心摘要，便于 CI 日志和截图归档读取。

关键输出字段包括：

- `status`
- `decision`
- `line_coverage_percent`
- `covered_lines`
- `num_statements`
- `missing_lines`
- `file_count`
- `threshold_enabled`
- `outputs`

其中 `threshold_enabled=False` 是本版边界：它明确告诉后续自动化，这份报告是 baseline 记录，不是覆盖率门禁。

### `src/minigpt/test_coverage_report.py`

这是报告构建和渲染模块。

核心入口是：

```python
build_test_coverage_report(coverage_json_path, project_root=ROOT, test_command=test_command)
```

它读取 coverage.py 的 JSON 文件，形成统一 schema：

```text
schema_version
title
generated_at
summary
test_command
files
recommendations
```

`summary` 保存全局覆盖率：

```text
decision=record_coverage_baseline
line_coverage_percent
covered_lines
num_statements
missing_lines
file_count
measured_file_count
threshold_enabled=False
fail_under=None
```

`files` 保存每个被 coverage 计量的源码文件：

```text
path
line_coverage_percent
covered_lines
num_statements
missing_lines
```

路径会统一转换为 `/` 分隔，避免 Windows 下的反斜杠影响 Markdown、CSV 和测试断言。

报告输出函数包括：

- `write_test_coverage_json`
- `write_test_coverage_csv`
- `write_test_coverage_markdown`
- `write_test_coverage_html`
- `write_test_coverage_outputs`

Markdown/HTML 会展示覆盖率最低的文件，并给出两条建议：先把当前数字当 baseline，再优先补最低覆盖文件的 focused tests。

### `src/minigpt/ci_workflow_hygiene.py`

CI hygiene 的必需命令片段同步更新。

旧检查要求 workflow 中直接出现：

```text
unittest discover -s tests -v
```

v239 改为要求：

```text
scripts/run_test_coverage.py
```

这样 CI hygiene 不会误把新的测试入口判为缺失，同时仍然保护 source encoding 和 CI workflow hygiene 两条已有检查。

### `tests/test_test_coverage_report.py`

新增两个 focused tests。

`test_builds_summary_from_coverage_json` 使用临时 coverage JSON fixture，验证：

- schema version 是 1。
- decision 是 `record_coverage_baseline`。
- line coverage 能正确四舍五入。
- threshold 没有启用。
- 文件数量和路径规范化正确。

`test_outputs_and_renderers_escape_html` 验证：

- JSON/CSV/Markdown/HTML 四类输出都存在。
- CSV 表头包含 `line_coverage_percent`。
- Markdown 能展示 baseline decision。
- HTML 会 escape 标题里的 `<report>`，避免报告渲染时出现 HTML 注入。

### `tests/test_ci_workflow.py`

测试里的 fake workflow 同步改为新的 coverage 脚本入口。

它保护的是 CI hygiene 规则本身：后续如果有人把 workflow 改回旧入口、删掉 coverage script 或缺少 source encoding/CI hygiene 步骤，测试会先暴露出来。

## 输入输出格式

输入：

- `coverage.py` 生成的 `coverage.json`
- 项目根目录
- 实际执行的 unittest 命令

输出：

```text
test_coverage_report.json
test_coverage_report.csv
test_coverage_report.md
test_coverage_report.html
```

这些是测试治理证据，可被 CI artifact、README 说明、后续 maturity summary 或 coverage gate 消费。

## 运行证据

本版运行证据归档在 `c/239`：

- `图片/01-coverage-report-tests.png`
- `图片/02-coverage-report-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

本地 smoke 显示：

```text
Ran 471 tests
line_coverage_percent=90.14
covered_lines=12308
num_statements=13655
missing_lines=1347
threshold_enabled=False
```

这说明覆盖率报告链路可运行，但仍然是非阻塞 baseline。

## 测试覆盖

本版验证分四层：

1. `tests.test_test_coverage_report` 保护 coverage JSON 解析、summary 字段、路径规范化和 HTML escape。
2. `tests.test_ci_workflow` 保护 CI workflow hygiene 对新测试入口的识别。
3. `scripts/run_test_coverage.py --out-dir runs/test-coverage-v239-smoke` 真实跑全量 unittest 并生成 coverage 报告。
4. `python -B -m unittest discover -s tests -q` 再跑一次全量测试，确认新增脚本和报告模块没有破坏现有 471 个测试。

## 证据链角色

v239 是测试治理层，不是发布门禁层。

它把“项目测试覆盖率到底是多少”从人工猜测变成可复现产物。后续如果要推进 coverage gate，应该先看几轮 baseline 是否稳定，再从低阈值、非核心文件排查、最低覆盖模块补测开始，而不是直接让 CI 因覆盖率数字失败。

## 一句话总结

v239 给 aiproj 增加了非阻塞 coverage baseline，让测试纪律从“全量测试通过”推进到“CI 可持续记录覆盖率证据”。
