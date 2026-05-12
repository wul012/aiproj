# 35. v20 Registry Saved Views 与 CSV 导出

## 文件角色

v20 继续增强 `registry.html`。v19 已经让页面支持搜索、质量筛选和排序；v20 新增两件更偏工程使用的能力：

- 当前搜索、筛选、排序和升降序状态会写进 URL hash，方便复制链接后恢复同一个视图。
- 当前可见行可以导出为 CSV，方便把筛选后的实验结果拿去表格软件或其他脚本里继续分析。

相关文件：

- `src/minigpt/registry.py`：扩展 HTML 控件、样式和浏览器脚本。
- `tests/test_registry.py`：检查 Share、CSV、URL 状态和导出逻辑相关标记。
- `README.md`、`a/20/解释/说明.md`：记录版本能力和验证方式。

## 核心流程

v20 仍然保持静态 HTML，不引入服务端和前端打包：

```text
registry dict
 -> render_registry_html
 -> 搜索/筛选/排序控件
 -> URL hash 保存视图状态
 -> Share 按钮复制当前链接
 -> CSV 按钮导出当前可见行
```

URL hash 示例：

```text
registry.html#q=run-b&quality=warn&sort=name&dir=desc
```

打开这个链接时，页面会自动恢复搜索词 `run-b`、质量筛选 `warn`、按名称排序和降序方向。

## 关键代码讲解

控件区新增了两个按钮和一个状态输出：

```html
<button id="share-view" type="button">Share</button>
<button id="export-visible-csv" type="button">CSV</button>
<output id="registry-status" for="share-view export-visible-csv"></output>
```

`readState` 从 URL hash 读取状态：

```javascript
const params = new URLSearchParams(window.location.hash.slice(1));
search.value = params.get("q") || "";
const wantedQuality = params.get("quality") || "";
if (hasOption(quality, wantedQuality)) quality.value = wantedQuality;
```

这里没有盲目信任 URL。比如 `quality=unknown` 这种页面里不存在的值，会被忽略，避免控件进入非法状态。

`writeState` 把当前控件状态写回 URL：

```javascript
if (query) params.set("q", query);
if (quality.value) params.set("quality", quality.value);
if (sortKey.value !== "bestVal") params.set("sort", sortKey.value);
if (!ascending) params.set("dir", "desc");
```

默认值不会写入 URL，所以普通视图仍然保持干净；只有用户真的筛选或改变排序时，链接才带上状态。

CSV 导出只使用当前可见行：

```javascript
const visible = rows.filter((row) => !row.hidden);
const records = visible.map((row) =>
  Array.from(row.cells).map((cell) =>
    (cell.innerText || cell.textContent).replace(/\s+/g, " ").trim()
  )
);
```

这里优先使用 `innerText`，是因为表格里有 `<br>`。`innerText` 会更接近用户在浏览器里看到的文本，导出的 CSV 也更容易读。最后用 `Blob` 和临时 `<a>` 触发下载：

```javascript
const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
link.download = `registry-visible-${visible.length}.csv`;
link.click();
```

开头加 `\ufeff` 是为了让部分表格软件更稳定地识别 UTF-8。

## 测试与验证

单测检查：

- `Share`、`CSV`、`registry-status` 控件存在。
- 页面脚本包含 `URLSearchParams`、`navigator.clipboard.writeText`、`Blob` 和 `registry-visible-`。
- 原有 HTML 转义保护仍然生效。

Playwright Chrome 验证：

- 打开带 hash 的 `registry.html#q=run-b&quality=warn&sort=name&dir=desc`。
- 确认控件自动恢复状态。
- 确认计数变成 `1 / 2`，可见行只有 `run-b`。
- 点击 `Share` 后状态输出非空。
- 点击 `CSV` 下载当前可见行，检查 CSV 包含 `run-b` 且不包含 `run-a`。

## 一句话总结

v20 让 registry 页面从“交互浏览”升级到“可分享、可导出”，更适合多人讨论实验结果和把筛选后的 run 交给其他工具继续处理。
