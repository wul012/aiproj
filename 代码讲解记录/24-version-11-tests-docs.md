# 24. v11 测试、文档和归档

这一篇记录 v11 的验证材料：新增 playground 单元测试、README 更新、`a/11` 截图归档和版本标签说明。

## 新增测试

`tests/test_playground.py` 覆盖四件事：

- `build_playground_payload` 能读取 run 目录和 `sample_lab.json`
- `render_playground_html` 会转义 HTML 文本，并包含 prompt 控件和命令输出区域
- `build_playground_commands` 会正确引用路径和 prompt
- `write_playground` 会写出 `playground.html`

## smoke 验证

v11 smoke 会临时训练一个极小 checkpoint，再生成 sampling lab 产物，最后运行：

```powershell
python scripts/build_playground.py --run-dir tmp/v11-playground-smoke
```

期望结果是 run 目录下出现 `playground.html`，并且 HTML 中能看到 prompt 控件、命令区域、采样结果和 artifact 链接。

## 截图归档

`a/11/图片` 保存五张关键截图：

- `01-unit-tests.png`
- `02-playground-artifacts-smoke.png`
- `03-build-playground.png`
- `04-playground-html-check.png`
- `05-docs-check.png`

`a/11/解释/说明.md` 对每张截图做简短说明，方便以后回看这个版本的验收范围。

## 版本标签

v11 会使用 `v11.0.0` 标签。标签说明应概括 playground UI、命令生成、采样结果展示、测试和截图归档。

## 一句话总结

v11 的验收重点不是模型效果，而是“把已有 MiniGPT 工程能力做成一个可打开、可检查、可继续操作的本地学习界面”。
