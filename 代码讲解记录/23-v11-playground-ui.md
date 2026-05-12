# 23. v11 Playground UI

这一版新增 `src/minigpt/playground.py` 和 `scripts/build_playground.py`，目标是把一个 MiniGPT run 目录变成可以直接用浏览器打开的本地学习界面。

## 文件角色

`playground.py` 负责读取 run 目录、复用 dashboard 的摘要信息、读取 `sample_lab/sample_lab.json`，然后生成 `playground.html`。

`build_playground.py` 是命令行入口，默认读取 `runs/minigpt`，也可以通过 `--run-dir` 和 `--out` 指定输入输出。

## 核心流程

```text
run_dir
 -> build_dashboard_payload
 -> read sample_lab/sample_lab.json
 -> collect playground links
 -> build command snippets
 -> render_playground_html
 -> write playground.html
```

## 关键代码

`build_playground_payload` 是数据入口。它把 dashboard 摘要、采样实验结果、文件链接和默认 prompt 控件值放进同一个 payload。

`render_playground_html` 是渲染入口。它输出一个单文件 HTML，里面包含 CSS、少量 JavaScript、prompt 输入框、参数输入框、命令片段、采样结果表格和 run 文件链接。

`build_playground_commands` 负责生成初始命令，例如 `generate.py`、`chat.py`、`sample_lab.py`、`inspect_model.py`、`build_dashboard.py` 和 `build_playground.py`。页面里的 JavaScript 会根据 prompt、max tokens、temperature、top-k、seed 实时刷新命令。

## 和 dashboard 的区别

`dashboard.html` 偏向“看结果”：展示 loss、perplexity、模型结构、预测和注意力等报告。

`playground.html` 偏向“动手试”：用浏览器组合 prompt 与采样参数，再复制对应命令去终端运行。

## 一句话总结

v11 把前面几版产出的训练、采样和检查命令收束成一个静态 Playground，让学习者不用记很多脚本参数，也能理解每个命令会触发哪条 MiniGPT 链路。
