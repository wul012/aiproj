# 第一百四十三版代码讲解：GitHub Actions Node 24 runtime

## 本版目标

v143 的目标是处理 GitHub Actions 在 v142 CI 里出现的 Node.js 20 deprecation 提醒。CI 本身已经通过，但 GitHub 提示 `actions/checkout@v4` 和 `actions/setup-python@v5` 当前运行在 Node 20 action runtime 上，后续 hosted runner 会默认切到 Node 24。

本版不修改模型代码，不改训练、评估、报告 schema，也不扩展 CI test matrix。它只做一件事：让当前 CI 主动 opt in 到 Node 24 JavaScript action runtime，并用一个轻量测试防止这个设置被后续改动误删。

## 前置路线

v142 修的是 Python 解释器版本漂移：本地 Python 3.13 和 CI Python 3.11 对语法的接受范围不同。v143 接着修 CI 运行时层面的另一类漂移：GitHub Actions 的 JavaScript action runtime 即将从 Node 20 切到 Node 24。

这两版都属于工程可靠性增强，不证明模型能力提升，但能减少“远端平台环境变化导致突然失败或出现警告”的风险。

## 关键文件

`.github/workflows/ci.yml` 是核心修改点。它新增顶层环境变量：

```yaml
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"
```

这个变量让 GitHub Actions 在当前 workflow 中提前使用 Node 24 来运行 JavaScript actions。现有步骤仍然保持不变：checkout、setup-python、install dependencies、source encoding gate、unittest discovery。

`tests/test_ci_workflow.py` 是新增守护测试。它读取 `.github/workflows/ci.yml`，断言 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"`、`actions/checkout@v4` 和 `actions/setup-python@v5` 同时存在。

README、`c/143` 和本讲解文件负责记录这次变更的目标和证据，避免后续误以为 v143 是模型功能版。

## 为什么加测试

workflow 文件本身不是 Python 业务代码，最容易在后续清理或复制时被忽略。加一个非常小的测试，可以把 CI runtime 策略变成仓库契约：

- 如果有人删掉 Node 24 opt-in，测试会失败。
- 如果有人重写 workflow，但保留核心 action 和 env，测试继续通过。
- 如果未来 GitHub Actions 不再需要这个 opt-in，可以在同一个测试里显式改策略，而不是静默删除。

这个测试不是 YAML 语义解析器，只是守住本项目当前最关心的 CI runtime 关键字。

## 运行流程

本版没有新增脚本。CI 在 GitHub 上的顺序仍然是：

1. `actions/checkout@v4`
2. `actions/setup-python@v5` with Python 3.11
3. `pip install -r requirements.txt`
4. `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-ci`
5. `python -B -m unittest discover -s tests -v`

区别是 workflow 顶层环境变量会让 JavaScript action runtime 先切到 Node 24。Python 运行时仍然是 3.11，和 v142 的 source encoding target compatibility 继续对齐。

## 测试覆盖

`tests/test_ci_workflow.py` 覆盖 workflow runtime policy。`scripts/check_source_encoding.py` smoke 覆盖新增测试文件没有 BOM、语法错误或 Python 3.11 compatibility 问题。全量 unittest discovery 覆盖既有模型、评估、治理、服务和维护模块没有被 workflow 改动影响。

维护 smoke 仍然显示 module pressure 为 pass，说明这次只新增一个小测试，没有引入新的大模块压力。

## 截图与归档

v143 的运行截图和解释放在 `c/143`：

- `01-ci-workflow-tests.png`：CI workflow 守护测试。
- `02-source-encoding-smoke.png`：source encoding smoke。
- `03-maintenance-smoke.png`：maintenance batching 和 module pressure。
- `04-full-unittest.png`：全量 unittest discovery。
- `05-docs-check.png`：README、归档、讲解索引和 workflow 关键字检查。

这些证据证明 v143 是一次 CI runtime maintenance closure，而不是报告功能或模型能力推进。

## 边界说明

本版没有升级 action 版本，因为当前提示的直接解决路径是设置 Node 24 runtime opt-in。未来如果 GitHub 发布新的 major action 版本，可以再做一次专门的 CI dependency update，而不是和本版混在一起。

本版也没有把 CI 扩成多 Python 版本矩阵。v142 已经明确 source encoding target 是 Python 3.11，v143 继续保持这一点，避免一次小修变成 CI 策略重设计。

## 一句话总结

v143 把 GitHub Actions 的 Node.js 20 deprecation 提醒前移处理成仓库契约，让 CI 在平台默认切换前就按 Node 24 runtime 运行。
