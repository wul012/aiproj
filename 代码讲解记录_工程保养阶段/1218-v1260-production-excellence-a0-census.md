# v1260 aiproj production-excellence A0 census 代码讲解

## 本版目标与边界

v1260 执行 `docs/production-excellence-aiproj-brief.md` 的 A0。A0 不是继续模型能力实验，也不是给现有治理链再加一个 release receipt，而是把项目进入 production-excellence 轨道前的事实基线钉住：CI 到底跑什么、历史证据目录现在有多大、`runs/` 是否已经开始膨胀、入口文档是否仍指向当前版本。

本版明确不做四件事：不引入 ruff/black/mypy（那是 A1），不调整 coverage floor（那是 A2），不改任何能力版本的 verdict 或 cached artifact（A0 不能触碰 ML capability lane），也不搬迁 `a/` 到 `f/` 的历史证据。计划书写得很清楚：这些 archive roots path-stable，只能 measure，不能 move。

## 新增脚本：`check_archive_runs_inventory.py`

脚本位于 `scripts/check_archive_runs_inventory.py`，故意只使用 Python 标准库。它不导入 `minigpt`，也不依赖 torch/numpy。这样做的原因是 A0 census 属于仓库卫生和证据体积管理，即使运行环境还没装训练依赖，也应该能得到文件系统事实。

核心数据模型是 `InventoryBudget`：

```text
archive_total_warning_mb = 512
archive_root_warning_mb  = 300
runs_warning_mb          = 64
```

这三个值不是失败阈值，而是 warning budget。脚本输出中的 `status` 永远可以是 `pass`，只要脚本本身成功测量；预算超了会写入 `warnings`，但退出码仍然是 0。这符合计划书对 A0 的要求：warning-only inventory，先建立 baseline，后续 A-track 才能决定哪些预算要 ratchet 成失败门。

主要流程：

1. `measure_path()` 扫描一个 root，统计存在性、文件数、目录数、总字节数、MB 值、是否超出对应 warning budget。
2. `build_inventory()` 固定扫描 `a/ b/ c/ d/ e/ f/` 和 `runs/`，再汇总 archive total。
3. 如果单个 root 超预算、archive total 超预算、或 root 缺失，就产生 warning row。
4. `write_outputs()` 写出 JSON、CSV、TXT、Markdown、HTML 五种格式。

本版真实输出为：

```text
status=pass
decision=archive_runs_inventory_recorded
warning_only=True
archive_total_mb=390.0008
warning_count=0
e=224.7105 MB
runs=11.349 MB
```

这里最重要的是 `e/`：它已经是最大 archive root，但仍低于 300 MB 单目录 warning budget。这个数字不是让我们现在清理旧证据，而是给后续版本一个明确的观察基线，避免它像其它项目那样悄悄长到 GB 级再回头处理。

## 测试覆盖

`tests/test_archive_runs_inventory.py` 覆盖三个层面：

- 正常 fixture 下扫描 6 个 archive roots + `runs/`，行数、summary、warning count 都可预测。
- 人为设置极低预算时，报告仍然 `status=pass`，但 `decision` 变成 `archive_runs_inventory_recorded_with_warnings`，证明 warning-only 语义没有被误写成失败门。
- CLI 和五格式输出被真实调用，确保后续维护者能直接运行脚本并得到 JSON/CSV/TXT/Markdown/HTML。

这类测试不是为了证明仓库当前体积永远健康，而是保护脚本契约：A0 只记录事实和 warning，不迁移文件，不隐藏警告，也不因为预算警告破坏 CI。

## 文档与入口修正

新增 `docs/archive-runs-inventory.md` 作为稳定规则页，说明 archive roots 的 path-stable 语义、命令、输出和 warning budgets。

新增 `docs/aiproj-track-a0-census.md` 作为 A0 closeout 表，记录当前 CI step、最新 green CI run、test 文件数、archive/runs fresh census、START_HERE 的修正边界，以及 A0 没做什么。

`START_HERE.md` 原先还停在 v1098-v1099 的“模型治理文档模板”描述。v1260 把它更新成当前 A0 production-excellence census，并显式保留 no-promotion/model-quality boundary：治理证据 `status=pass` 不是生产级模型质量许可。

README 和 `docs/README.md` 只做索引修正，加入 production-excellence brief、A0 census 和 archive inventory。`docs/engineering-workflow.md` 增加 inventory 命令，提醒 archive roots 只能测量，不能例行搬迁。

## 运行证据

运行证据归档在 `f/1260`：

- `f/1260/解释/archive-runs-inventory/archive_runs_inventory.json`
- `f/1260/解释/archive-runs-inventory/archive_runs_inventory.csv`
- `f/1260/解释/archive-runs-inventory/archive_runs_inventory.txt`
- `f/1260/解释/archive-runs-inventory/archive_runs_inventory.md`
- `f/1260/解释/archive-runs-inventory/archive_runs_inventory.html`
- `f/1260/图片/archive-runs-inventory-v1260.png`

截图通过 Playwright MCP 从本地 HTTP 服务读取 HTML 生成；快照确认页面里能看到 `status=pass`、`warning-only=True`、`e=224.7105MB`、`runs=11.349MB` 和未超预算状态。临时 HTTP 服务只用于截图，完成后停止。

## 一句话总结

v1260 把 aiproj 的 production-excellence A-track 从口头计划变成可复核的 A0 基线：CI 现状、archive/runs 体积、入口文档新鲜度和 no-promotion 边界都有了文件化证据，且没有触碰模型能力实验语义。
