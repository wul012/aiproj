# 33. v18 Registry HTML 报告

## 文件角色

v18 主要改动在 `src/minigpt/registry.py`。v17 的 registry 已经能把多个训练 run 汇总成 `registry.json`、`registry.csv` 和 `registry.svg`，但这些产物更偏机器读取或静态图。v18 增加 `registry.html`，让多个实验可以直接在浏览器里浏览，并从总表跳到每个 run 的 dashboard、manifest 和 eval suite。

相关文件：

- `src/minigpt/registry.py`：新增 HTML 渲染和写出逻辑。
- `scripts/register_runs.py`：继续复用 `write_registry_outputs`，因此自动多输出 `registry.html`。
- `scripts/playwright_chrome_smoke.ps1`：用 Playwright 的 `--channel chrome` 调用本机 Google Chrome 验证本地 HTML。
- `tests/test_registry.py`：补充 HTML 输出存在性和转义测试。
- `README.md`、`a/18/解释/说明.md`：记录版本能力、验证截图和运行方式。

## 核心流程

v18 没有改变 registry 的数据来源，流程仍然是：

```text
run_manifest.json / history_summary.json / dataset_quality.json / eval_suite.json
 -> summarize_registered_run
 -> build_run_registry
 -> write_registry_outputs
 -> registry.json / registry.csv / registry.svg / registry.html
```

也就是说，HTML 是同一份 registry 数据的另一种展示形式。这样可以保证 JSON、CSV、SVG、HTML 四种产物看到的是同一次索引结果，不会出现“网页和数据文件不一致”的问题。

## 关键代码讲解

`render_registry_html` 负责把 registry 字典变成完整 HTML 字符串。它先取出 `runs`、`best_by_best_val_loss`、`quality_counts`，再生成顶部统计卡片和 run 表格：

```python
stats = [
    ("Runs", registry.get("run_count")),
    ("Best run", _pick(best, "name")),
    ("Best val", _fmt(_pick(best, "best_val_loss"))),
    ("Fingerprints", len(registry.get("dataset_fingerprints", []))),
    ("Quality", ", ".join(f"{key}:{value}" for key, value in quality_counts.items()) if isinstance(quality_counts, dict) else None),
]
```

这段代码把最重要的实验概览放到页面顶部：一共有几个 run、哪个 run 的验证损失最好、出现了多少个数据指纹、质量状态分布是什么。

每个 run 会渲染成表格中的一行：

```python
f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
f"<td>{_e(_fmt(run.get('best_val_loss')))}</td>"
f"<td>{_e(_fmt_int(run.get('total_parameters')))}</td>"
f"<td>{_e(run.get('git_commit'))}<br><span>dirty={_e(run.get('git_dirty'))}</span></td>"
```

这里展示 run 名称、路径、最好验证 loss、参数量、Git commit、dirty 状态、数据来源、数据指纹、质量状态、eval suite 覆盖数和 artifact 数量。`_e` 是 HTML 转义函数，避免 run 名称或路径里带 `<script>` 这类字符时破坏页面结构。

`_registry_links` 会检查每个 run 目录中是否存在关键 artifact：

```python
specs = [
    ("dashboard", root / "dashboard.html"),
    ("manifest", root / "run_manifest.json"),
    ("eval", root / "eval_suite" / "eval_suite.json"),
]
```

存在就生成链接，不存在就显示 `missing`。这样 registry 不只是一个汇总表，还能变成实验入口页：从 `registry.html` 可以继续打开单个 run 的 dashboard、manifest 或 eval suite。

`_href` 负责把 artifact 路径转换成相对 HTML 链接：

```python
try:
    return Path(os.path.relpath(path, Path(base_dir))).as_posix()
except ValueError:
    return path.as_posix()
```

在同一个盘符下优先使用相对路径，便于移动整个实验目录；如果 Windows 下遇到不同盘符导致 `relpath` 失败，就退回绝对路径，避免导出 HTML 时中断。

最后，`write_registry_outputs` 统一写出四类产物：

```python
paths = {
    "json": root / "registry.json",
    "csv": root / "registry.csv",
    "svg": root / "registry.svg",
    "html": root / "registry.html",
}
```

这让命令行脚本不需要新增参数。以前怎么运行 `scripts/register_runs.py`，现在就会自动多得到一个 `registry.html`。

## 测试与验证

v18 的单测重点有两个：

- `test_write_registry_outputs`：确认 `write_registry_outputs` 会写出 HTML，并且页面里包含 `MiniGPT run registry`。
- `test_render_registry_html_escapes_run_text`：构造带 `<script>` 的 run 名称，确认 HTML 中只出现转义后的 `&lt;script&gt;`。

端到端 smoke 会准备两个小型 run，分别生成 manifest、eval suite 和 dashboard，然后用 `register_runs.py` 导出 registry 四件套，再检查 HTML 里是否有表格、统计卡、链接和数据指纹。

浏览器验证使用 `scripts/playwright_chrome_smoke.ps1`：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/playwright_chrome_smoke.ps1 -UrlOrPath tmp\v18-registry-html-smoke\registry\registry.html -Out tmp\v18-logs\registry-html-browser-script.png
```

这里选择 `--channel chrome`，意思是让 Playwright 使用已经安装的 Google Chrome。它不是下载 Playwright 自带 Chromium，因此更适合这台机器当前的环境。

## 一句话总结

v18 把 run registry 从“实验索引数据文件”推进到“可直接浏览的实验入口页”，让多版本实验的比较、追踪和展示更接近真实 AI 工程工作流。
