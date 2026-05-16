# 第一百四十四版代码讲解：GitHub Actions Node 24 native actions

## 本版目标

v144 的目标是修正 v143 的不充分之处。v143 给 workflow 加了 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`，CI 通过了，但 GitHub annotation 仍然提示 `actions/checkout@v4` 和 `actions/setup-python@v5` 本身 target Node 20，只是被强制运行在 Node 24 上。

本版不修改模型、训练、评估或报告 schema。它只把 GitHub Actions 依赖升级到原生 Node 24 action major 版本，让 CI 不再依赖 force flag。

## 前置判断

v143 的方向是合理的第一步，但不是最终解法。它证明 CI 能在 Node 24 runtime 下运行，却没有消除 action metadata 仍然 target Node 20 的事实。

v144 先用远端 action metadata 核对：

- `actions/checkout@v6` 的 `action.yml` 中 `runs.using` 是 `node24`。
- `actions/setup-python@v6` 的 `action.yml` 中 `runs.using` 是 `node24`。

所以正确收口不是继续加 env，而是升级 action major。

## 关键文件

`.github/workflows/ci.yml` 是核心修改点：

```yaml
- uses: actions/checkout@v6

- uses: actions/setup-python@v6
  with:
    python-version: "3.11"
```

同时删除 v143 新增的：

```yaml
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"
```

`tests/test_ci_workflow.py` 更新为守住新的真实契约：workflow 必须使用 `actions/checkout@v6` 和 `actions/setup-python@v6`，不能退回 `checkout@v4`、`setup-python@v5`，也不能继续依赖 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`。

## 为什么这比 v143 更准确

GitHub Actions 的 deprecation 提醒有两层：

1. runtime 是否能被强制到 Node 24。
2. action 本身的 metadata 是否 target Node 24。

v143 解决的是第一层，所以 annotation 变成“Node 20 action 被强制跑在 Node 24”。v144 解决第二层：直接使用 target Node 24 的 action 版本。

这也是为什么 v144 保留了 v143 的测试思路，但改了测试内容。现在测试保护的是 action version contract，而不是 force flag。

## 运行流程

CI 主流程保持不变：

1. checkout 仓库。
2. setup Python 3.11。
3. 安装 `requirements.txt`。
4. 运行 source encoding hygiene gate。
5. 运行全量 unittest discovery。

变化只在 GitHub action 自身版本。Python 运行时仍是 3.11，继续服务 v142 的 target compatibility 策略。

## 测试覆盖

`tests/test_ci_workflow.py` 检查 workflow 里的 action major 和 force flag 缺失。`scripts/check_source_encoding.py` smoke 证明新增或修改的 Python 文件仍然满足 BOM、语法和 Python 3.11 compatibility。全量 unittest discovery 证明 action 版本升级没有伴随业务代码回归。

维护 smoke 的 module pressure 仍为 pass，说明这次是 CI dependency maintenance，不是大模块功能推进。

## 截图与归档

v144 的运行截图和解释放在 `c/144`：

- `01-ci-workflow-tests.png`：workflow action version 守护测试。
- `02-source-encoding-smoke.png`：source encoding smoke。
- `03-maintenance-smoke.png`：maintenance batching 和 module pressure。
- `04-full-unittest.png`：全量 unittest discovery。
- `05-action-metadata-check.png`：远端 action metadata 证明 v6 使用 `node24`。
- `06-docs-check.png`：README、归档、讲解索引和 workflow 关键字检查。

这些证据说明 v144 是对 v143 的纠偏和闭环，不是新的模型功能。

## 边界说明

本版没有调整 Python 版本、依赖缓存、矩阵策略或 workflow 权限。那些都可以单独讨论，但不应该混进“消除 Node 20 action target annotation”这件事里。

如果未来 GitHub Actions 再发布新的 major 版本，可以按同样方式先查 metadata，再升级 workflow 和测试。

## 一句话总结

v144 把 CI 从“强制 Node 24 runtime”修正为“使用原生 Node 24 action”，真正对准 GitHub Actions 的 Node.js 20 deprecation annotation。
