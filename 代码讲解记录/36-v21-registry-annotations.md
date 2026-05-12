# 36. v21 Registry Annotations

## 文件角色

v21 给 registry 增加轻量实验注释能力。每个 run 目录可以放一个可选的 `run_notes.json`，用来记录人写的实验备注和标签。注册多个 run 时，registry 会把这些 notes/tags 一起写进 JSON、CSV、SVG 和 HTML。

相关文件：

- `src/minigpt/registry.py`：读取 `run_notes.json`，扩展 `RegisteredRun`、CSV 字段、HTML Notes 列、SVG 注释行和搜索文本。
- `scripts/register_runs.py`：命令行输出新增 `tag_counts`。
- `tests/test_registry.py`：覆盖 notes/tags 读取、tag 统计、HTML 展示和转义。
- `README.md`、`a/21/解释/说明.md`：记录使用方式和验证截图。

## run_notes.json 格式

一个最小示例：

```json
{
  "note": "Stable baseline for dataset v1.",
  "tags": ["baseline", "keep"]
}
```

把这个文件放在某个 run 目录下：

```text
runs/tiny/run_notes.json
```

然后正常运行：

```powershell
python scripts/register_runs.py runs/tiny runs/wide --name tiny --name wide --out-dir runs/registry
```

registry 会自动读取它，不需要新增命令行参数。

## 核心流程

```text
run directory
 -> run_manifest.json / history_summary.json / dataset_quality.json / eval_suite.json
 -> run_notes.json
 -> summarize_registered_run
 -> build_run_registry
 -> registry.json / registry.csv / registry.svg / registry.html
```

也就是说，notes/tags 和指标、质量状态、数据指纹一样，都是 registry 的 run summary 字段。

## 关键代码讲解

`RegisteredRun` 新增两个字段：

```python
note: str | None
tags: list[str]
```

`summarize_registered_run` 会读取 `run_notes.json`：

```python
run_notes = _read_run_notes(root)
note=_as_str(_pick(run_notes, "note") or _pick(run_notes, "summary")),
tags=_as_str_list(_pick(run_notes, "tags")),
```

这里兼容 `note` 和 `summary` 两种命名；`tags` 可以是数组，也可以是逗号分隔字符串，最终都会规整成 `list[str]`。

`build_run_registry` 会额外统计 tag 频次：

```python
"tag_counts": _counts(tag for run in runs for tag in run.tags),
```

这样 registry 顶层可以知道哪些标签出现最多。`scripts/register_runs.py` 也会在终端输出 `tag_counts`，方便快速确认注释有没有读到。

CSV 写出时，list 会被转换成分号分隔：

```python
def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value
```

所以 `["candidate", "review"]` 在 `registry.csv` 里会成为：

```text
candidate; review
```

HTML 表格新增 `Notes` 列。tags 会渲染成轻量 chip，note 显示在下面：

```python
f"<td>{_tag_chips(run.get('tags'))}<br><span>{_e(run.get('note'))}</span></td>"
```

搜索文本也加入了 `note` 和 `tags`，所以在浏览器搜索 `candidate`、`baseline`、`review` 都能定位对应 run。

## 测试与验证

单测覆盖：

- `summarize_registered_run` 能读取 `run_notes.json`。
- `build_run_registry` 能生成 `tag_counts`。
- HTML 有 Notes 列、tag chip 和 note 文本。
- note/tag 中的 HTML 特殊字符会被转义。

端到端 smoke 覆盖：

- 训练两个小 run。
- 给两个 run 写入不同的 `run_notes.json`。
- 把其中一个 run 的数据质量标为 `warn`。
- 注册 registry，并检查 JSON/CSV/SVG/HTML 都包含 notes/tags。
- 用 Playwright Chrome 搜索 `candidate`，确认页面只显示对应 run。

## 一句话总结

v21 让实验 registry 不只记录“机器指标”，也能记录“人的判断”：哪个是 baseline，哪个需要 review，哪个值得保留。
