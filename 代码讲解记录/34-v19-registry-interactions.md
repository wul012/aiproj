# 34. v19 Registry HTML 交互控件

## 文件角色

v19 延续 v18 的 `registry.html`，把它从“静态实验表格”推进成“可交互实验索引页”。本版不改变 registry 的 JSON 数据结构，也不改变 `scripts/register_runs.py` 的命令行参数，而是在 HTML 渲染阶段增加搜索、质量筛选、排序、升降序切换和可见行计数。

相关文件：

- `src/minigpt/registry.py`：新增 HTML 行数据属性、控件区、原生 JavaScript 过滤/排序逻辑和样式。
- `tests/test_registry.py`：增加交互控件存在性测试，并调整 HTML 转义测试以兼容页面脚本。
- `scripts/playwright_chrome_smoke.ps1`：继续用本机 Google Chrome 做浏览器截图验证。
- `README.md`、`a/19/解释/说明.md`：记录 v19 能力和验证截图。

## 核心流程

v19 的数据流仍然保持简单：

```text
build_run_registry
 -> registry dict
 -> render_registry_html
 -> table rows with data-* attributes
 -> static controls + inline script
 -> browser-side search/filter/sort
```

这里的关键点是：所有 run 仍然先完整写进 HTML。搜索、筛选和排序只是浏览器端对已有 `<tr>` 的显示与顺序调整，所以没有服务端依赖，也不需要额外构建工具。

## 关键代码讲解

每一行 run 现在带有一组 `data-*` 属性：

```python
'<tr data-run-row'
f' data-search="{_e(_row_search_text(run))}"'
f' data-quality="{_e(quality)}"'
f' data-name="{_e(run.get("name"))}"'
f' data-best-val="{_e(_sort_number(run.get("best_val_loss")))}"'
f' data-params="{_e(_sort_number(run.get("total_parameters")))}"'
f' data-artifacts="{_e(_sort_number(run.get("artifact_count")))}"'
f' data-eval="{_e(_sort_number(run.get("eval_suite_cases")))}">'
```

这些属性是给浏览器脚本读取的。`data-search` 里放 run 名、路径、commit、tokenizer、数据来源、数据指纹和质量状态；`data-best-val`、`data-params`、`data-artifacts`、`data-eval` 用于数值排序。展示给人的 `<td>` 内容仍然保持原样。

控件由 `_registry_controls` 生成：

```python
<input id="registry-search" type="search">
<select id="quality-filter">...</select>
<select id="sort-key">...</select>
<button id="sort-direction">Asc</button>
<output id="registry-count">0 / 0</output>
```

质量筛选选项不是写死的，而是从当前 registry 的 run 列表里提取。这样如果某次实验只有 `pass`，就只出现 `pass`；如果同时有 `pass` 和 `warn`，页面会自动给出两个选项。

浏览器脚本的核心函数是 `apply`：

```javascript
const query = (search.value || "").trim().toLowerCase();
const wantedQuality = quality.value;
const visible = [];
rows.forEach((row) => {
  const matchesQuery = !query || (row.dataset.search || "").includes(query);
  const matchesQuality = !wantedQuality || row.dataset.quality === wantedQuality;
  const shown = matchesQuery && matchesQuality;
  row.hidden = !shown;
  if (shown) visible.push(row);
});
```

它先根据搜索词和质量状态决定每一行是否显示，再把可见行按选择的字段排序。排序分两类：loss、参数量、artifact 数、eval case 数走数值比较；run 名走文本比较。缺失数值会排在最后，避免 `missing` 干扰最好 loss 排名。

升降序切换只改变 `ascending` 状态：

```javascript
ascending = !ascending;
direction.textContent = ascending ? "Asc" : "Desc";
direction.setAttribute("aria-pressed", String(!ascending));
apply();
```

然后重新调用 `apply`，页面不刷新，表格顺序即时变化。

## 测试与验证

单测新增 `test_render_registry_html_has_interactive_controls`，检查：

- 搜索框、质量筛选、排序选择、升降序按钮和计数器存在。
- run 行带有 `data-run-row` 与排序属性。
- `pass`、`warn` 质量选项会按 registry 数据生成。
- 页面包含事件监听脚本。

原来的转义测试也保留，但现在页面本身有合法 `<script>` 标签，所以测试改为确认 run 名里的 `<script>` 被渲染为 `&lt;script&gt;`，不会出现在 `<strong><script>` 或 `data-search="<script>` 这类位置。

端到端 smoke 会准备两个小 run，导出 registry HTML，再用 Playwright 的 Chrome channel 打开页面，执行搜索、质量筛选、排序和计数检查。

## 一句话总结

v19 让 `registry.html` 从“能看”升级到“能查”，适合 run 数量变多之后快速定位实验、筛选质量状态并按关键指标排序。
