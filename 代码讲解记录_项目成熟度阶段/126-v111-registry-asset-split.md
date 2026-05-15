# 第一百一十一版代码讲解：Registry Asset Split

## 本版目标

v111 的目标是把 v110 的 module pressure audit 真正用起来，做第一处轻量、定向、可测试的代码膨胀治理。

v110 已经量化指出 `registry.py` 是 critical-size 模块之一。v111 不直接改 registry 的 run discovery、JSON 汇总、CSV/SVG/HTML 输出契约，也不改排序、leaderboard 或 release readiness/pair/rubric 数据语义，而是先把 registry HTML 的 CSS 和 JavaScript 资产抽到独立模块 `registry_assets.py`。

本版明确不做：

- 不改变 `build_run_registry`、`summarize_registered_run` 或 `write_registry_outputs` 的数据契约。
- 不改变 registry HTML 的 DOM id、data attribute、排序 key、CSV 导出、分享链接或筛选逻辑。
- 不拆 `server.py`、`benchmark_scorecard.py` 或 `playground.py`。
- 不为了行数减少而做大范围重构。

## 路线来源

本版来自 v110 的模块压力治理线：

```text
v110 module pressure audit
 -> identify registry.py as critical-size
 -> choose low-risk display asset boundary
 -> v111 registry asset split
```

`registry.py` 的 CSS/JS 是适合第一步抽取的原因：

- 它是纯展示资产边界，不参与 registry JSON 的计算。
- 它有现成测试覆盖 HTML 控件、排序字段、CSV 导出和链接。
- 抽取后可以明显降低 `registry.py` 行数，同时不改变用户可见能力。

## 关键文件

- `src/minigpt/registry_assets.py`
  - 新增模块。
  - 提供 `registry_style()` 和 `registry_script()`。
  - 保存 registry HTML 的 `<style>` 和 `<script>` 字符串。
- `src/minigpt/registry.py`
  - 新增对 `registry_assets` 的导入。
  - `_registry_style()` 和 `_registry_script()` 变成薄包装，继续被 `render_registry_html()` 调用。
  - registry 数据汇总、文件写出、HTML 表格、leaderboard 和链接逻辑保持不变。
- `tests/test_registry_assets.py`
  - 新增资产契约测试。
  - 验证 CSS 布局类、交互控件、排序 key、hash state、CSV export、share link 和 render 集成。
- `README.md`
  - 当前版本、版本标签和截图说明更新到 v111。
- `c/111`
  - 保存本版运行截图和解释。

## 核心数据结构

本版没有新增业务数据结构。

registry 的核心数据仍然是 `build_run_registry()` 输出的字典，包含：

- `runs`
- `loss_leaderboard`
- `benchmark_rubric_leaderboard`
- `pair_delta_leaderboard`
- `release_readiness_delta_leaderboard`
- `quality_counts`
- `tag_counts`

v111 只移动 HTML 资产字符串，不改变这些字段。

## 核心函数

`registry_style()`

返回完整 `<style>...</style>`。它包含 registry 页面的基础布局、toolbar、table、pill、leaderboard 和移动端响应式规则。

关键契约包括：

- `.toolbar`
- `.leaderboard`
- `.pill.pass/.warn/.fail/.missing`
- `@media (max-width:760px)`

这些类名被现有 HTML 直接引用，所以测试会保护它们。

`registry_script()`

返回完整 `<script>...</script>`。它承载 registry HTML 的浏览器交互：

- 搜索框：`registry-search`
- 质量筛选：`quality-filter`
- 排序选择：`sort-key`
- 升降序按钮：`sort-direction`
- 可见行计数：`registry-count`
- 分享当前视图：`share-view`
- 导出当前可见 CSV：`export-visible-csv`
- hash state：`URLSearchParams`

排序 key 仍然是：

```text
rank, bestVal, delta, params, artifacts, rubric, pair, readiness, eval
```

这保证抽取后 HTML 行为和 v110 之前一致。

`_registry_style()` / `_registry_script()`

这两个函数仍留在 `registry.py`，但只做委托：

```python
def _registry_style() -> str:
    return registry_style()

def _registry_script() -> str:
    return registry_script()
```

这样做的目的是降低迁移风险。`render_registry_html()` 不需要大改，后续如果有内部测试或引用点仍然依赖旧函数名，也不会突然断掉。

## 运行流程

registry HTML 渲染链路保持为：

```text
build_run_registry()
 -> render_registry_html()
 -> _toolbar()
 -> _registry_style() -> registry_assets.registry_style()
 -> _registry_script() -> registry_assets.registry_script()
 -> write_registry_outputs()
```

也就是说，外部命令和输出文件没有变：

```powershell
python scripts/register_runs.py runs --out-dir runs/registry
```

## 为什么这是轻量质量优化

v110 的压力报告指出 registry 是大模块，但直接拆 registry 业务逻辑风险更高。v111 先拆展示资产，因为：

- CSS/JS 字符串长，占据不少行数。
- 它们和数据汇总逻辑边界清楚。
- 测试能直接判断资产是否仍被 HTML 使用。
- Playwright 能验证真实浏览器仍能打开 registry HTML。

本版完成后，`registry.py` 从约 1511 行降到约 1352 行，新增 `registry_assets.py` 约 170 行。模块总行数不会神奇消失，但职责边界更清楚：registry 数据逻辑留在 `registry.py`，HTML 资产留在 `registry_assets.py`。

## 测试覆盖

`tests/test_registry.py` 继续覆盖原有 registry 行为：

- run discovery。
- run summary。
- registry 聚合。
- pair delta leaderboard。
- release readiness deltas。
- HTML 控件和可见文本。
- HTML 转义。

`tests/test_registry_assets.py` 新增覆盖：

- `registry_style()` 返回 `<style>`，并包含 toolbar、leaderboard 和响应式布局。
- `registry_script()` 返回 `<script>`，并包含搜索、筛选、排序、hash state、CSV 导出和分享链接。
- `render_registry_html()` 实际嵌入了 `registry_style()` 和 `registry_script()` 的返回值。

这些断言保护的是抽取边界，而不是只检查文件存在。

## 证据闭环

v111 证据放在 `c/111`：

- `01-unit-tests.png`：registry asset tests、registry regression、compileall 和全量 unittest。
- `02-registry-asset-smoke.png`：显示 registry 行数变化和 module pressure smoke。
- `03-registry-asset-structure-check.png`：证明源码、测试、README、讲解和 c 归档对齐。
- `04-registry-asset-output-check.png`：证明 registry HTML 仍包含 CSS/JS 资产、控件、排序字段和链接。
- `05-playwright-registry-asset-html.png`：证明生成后的 registry HTML 可以在真实 Chrome 渲染。
- `06-docs-check.png`：证明 README、c/README 和项目成熟度阶段索引引用 v111。

## 一句话总结

v111 把 v110 的模块压力扫描转化为第一处低风险实际拆分：先抽 registry HTML 资产，减少 critical 模块体量，同时保持 registry 数据契约和浏览器交互不变。
