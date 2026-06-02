# v693 surface branch final verification

## 本版目标和边界

v693 是 v679-v692 surface-policy 批次的验证收尾版。它不新增模型训练能力，不改 replay 逻辑，不新增治理链。它的目标是证明这一批新增代码、测试、文档和归档在本地完整通过。

本版的边界也很重要：验证通过不等于模型能力 promotion。v692 的结论仍然有效：当前成果是 contextual decode aid closed branch，minimal-prompt capability 仍待新 objective。

## 前置链路

本批次从 v679 到 v692 完成了以下路线：

- v679 定位剩余 free-generation surface failure。
- v680-v683 规划、复放、选择并最小性检查 surface policy。
- v684 记录 contextual-anchor leakage risk。
- v685 找到最小稳定 budget 8。
- v686 固化 execution profile。
- v687-v689 规划、复放并选择 surface variant。
- v690 对照 non-leaking baselines。
- v691 做路线决策。
- v692 做分支 closeout。

v693 在这些版本之上跑整体验证。

## 验证内容

### 全量测试

命令：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v693-full
```

结果：

```text
1335 passed in 166.24s (0:02:46)
```

这个结果覆盖了新增 v684-v692 的单测，也覆盖了项目既有测试集。

### Source encoding hygiene

命令：

```powershell
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v693
```

结果：

```text
status=pass
decision=continue_with_clean_sources
source_count=815
clean_count=815
bom_count=0
syntax_error_count=0
compatibility_error_count=0
target_python=3.11
```

这一步重点保护之前遇到过的 BOM/语法类 CI 问题，确认新增源码没有引入 encoding 回归。

### Diff check

命令：

```powershell
git diff --check
```

结果：通过。

## 归档文件

v693 新增：

- `e/693/解释/v693-final-verification.html`
- `e/693/解释/说明.md`
- `e/693/图片/v693-final-verification.png`
- `代码讲解记录_模型能力阶段/707-v693-surface-branch-final-verification.md`

HTML 页面不是新功能报告，而是验证入口。截图用于证明验证结果可视化归档。

## 清理边界

全量测试产生的 pytest cache 和 source-encoding 运行输出是本地验证临时产物，不作为主证据提交。主证据保留在 `e/693`。最终 cleanup 会删除本轮 Playwright 临时目录和测试缓存，并停止本轮启动的临时 HTTP server。

## 一句话总结

v693 用全量测试、source encoding hygiene 和 diff check 证明 v679-v692 的 contextual surface-policy 分支可以干净收口。
