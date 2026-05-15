# v128 registry artifact split 代码讲解

## 本版目标

v128 的目标很明确：把 registry 里“把数据写成文件”的那一层从 `registry_render.py` 中拆出去，形成独立的 `registry_artifacts.py`。
这一版解决的是治理链条里的一个小而真实的问题: `registry_render.py` 同时负责 HTML 渲染、文件写出和旧 facade 兼容，职责开始变厚。
本版不做的事情也要说清楚: 不改 registry schema，不改 HTML 交互，不改 `scripts/register_runs.py` 的使用方式，也不碰训练、模型或数据生成逻辑。

## 前置路线

这一版接在 v116 之后。
v116 已经把 registry 拆成 data assembly、render/output 和 facade 三层，但那一版里“输出写出”还主要跟着 renderer 走。
v127 先把 source encoding hygiene gate 收口，说明项目现在可以把注意力放回模块治理本身。
v128 就是在这个基础上，把 registry 的写出边界再往前推一步。

## 关键文件

- `src/minigpt/registry_artifacts.py`: 新的输出层，负责 `registry.json`、`registry.csv`、`registry.svg`、`registry.html` 的落盘。
- `src/minigpt/registry_render.py`: 保留 `render_registry_html()`，同时留下兼容旧入口的薄 wrapper，避免调用方立刻改口。
- `src/minigpt/registry.py`: 对外 facade，继续让旧 import 路径可用。
- `tests/test_registry_split.py`: 锁住 data/render/artifact 分层和公共函数身份，避免拆完又悄悄长回去。
- `README.md` 和 `c/128/*`: 把这次拆分的目的、证据和截图归档到版本说明里。

## 核心数据流

这次没有改 registry 数据结构，数据还是先走 `registry_data.build_run_registry()`。
新的流程变成：

1. run 目录被发现并汇总成 registry dict。
2. `registry_render.render_registry_html()` 只负责 HTML 字符串渲染。
3. `registry_artifacts.write_registry_outputs()` 负责把 registry 写成 JSON/CSV/SVG/HTML 文件。
4. `registry.py` 继续提供 facade，保持旧调用方不必立刻迁移。

这里最重要的是边界语义:

- `registry.json` 是结构化证据。
- `registry.csv` 是表格式索引证据。
- `registry.svg` 是轻量可视化证据。
- `registry.html` 是浏览器可读证据。

它们都是只读产物，不参与训练，不反向修改数据。

## 关键函数

- `write_registry_json()` / `write_registry_csv()` / `write_registry_svg()` / `write_registry_html()`: 单项写出函数。
- `write_registry_outputs()`: 一次生成四类输出，是脚本和测试最常用的入口。
- `render_registry_html()`: 仍然保留在 renderer 里，只处理页面内容。

这版里 `registry_render.py` 里的同名函数只是薄包装，真正的写文件逻辑已经搬走。
这样做的好处是：HTML 还能继续复用原来的页面构建逻辑，但文件输出的责任已经单独收口。

## 测试覆盖

`tests/test_registry_split.py` 主要锁三件事：

1. `registry_data` 可以单独构建 registry，不依赖渲染层。
2. `registry_render` 仍能通过旧入口写出完整输出。
3. `registry` facade 仍然保持公共 API 身份，旧 import 不会断。

再加上 `compileall`、`unittest discover`、maintenance batching smoke 和 Playwright HTML 截图，这一版就不是“只改了几个函数名”，而是把拆分后的边界真的跑通了。

## 证据意义

这版的截图和归档不是装饰，而是说明拆分后的边界还活着:

- `c/128/图片/` 里的截图证明输出、结构和页面都能看见。
- `c/128/解释/说明.md` 说明这些截图为什么算证据。
- README 里记录版本号和 tag，说明这版已经收口成一个可追踪版本。

## 一句话总结

v128 把 registry 从“一个厚 renderer”推进成“renderer + artifact writer”的双层结构，治理边界更清楚了，但运行契约没有被打碎。
