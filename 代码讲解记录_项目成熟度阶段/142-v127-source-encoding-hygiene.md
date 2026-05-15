# v127 source encoding hygiene gate 代码讲解

## 本版目标

v127 的目标很明确：把一次 UTF-8 BOM 造成的 CI 失败，收口成一个可复用、可测试、可归档的 source encoding hygiene gate。

它解决的是“Python 源码里混入 BOM，导致解析阶段先炸掉，等不到单测”的问题。  
它不解决模型能力、不做训练规模提升，也不改推理 API 或比较逻辑。

## 前置路线

这版接在 v126 之后。v126 已经把 baseline comparison 的证据输出层收口完毕，说明项目的治理链条已经能稳定承载新的小门禁。v127 没有继续拆模型模块，而是沿着同一条治理路线，把“源文件编码卫生”变成了新的可执行约束。

实际触发点是 CI 里曾经出现 `src/minigpt/server.py` 的 BOM 报错。v127 不去回避这个问题，而是把它上升为一个独立的检查步骤，避免同类问题再次混进主流程。

## 关键文件

```text
src/minigpt/source_encoding_hygiene.py
scripts/check_source_encoding.py
.github/workflows/ci.yml
tests/test_source_encoding_hygiene.py
src/minigpt/__init__.py
README.md
c/127/图片/
c/127/解释/说明.md
```

- `src/minigpt/source_encoding_hygiene.py` 是核心报告模块，负责扫描 Python 源文件、识别 BOM、捕获语法错误，并渲染 JSON/CSV/Markdown/HTML 证据。
- `scripts/check_source_encoding.py` 是命令行门禁，CI 和本地都可以调用。
- `.github/workflows/ci.yml` 把这个门禁放到单测之前，确保解析级问题先暴露。
- `tests/test_source_encoding_hygiene.py` 锁住行为契约，防止以后把 BOM 识别、输出写入或失败退出悄悄改坏。
- `src/minigpt/__init__.py` 把新能力挂到顶层导出，便于复用。
- `README.md`、`c/127/*` 和本讲解记录一起组成版本证据链。

## 核心数据结构

`build_source_encoding_report()` 返回的是一个只读报告字典，核心字段如下：

```text
schema_version
title
generated_at
policy
summary
files
recommendations
```

其中：

- `policy.roots` 记录默认扫描范围，当前是 `src`、`scripts`、`tests`
- `policy.encoding` 固定为 `utf-8-sig`
- `policy.bom_marker` 明确说明检查对象是 UTF-8 BOM
- `summary.status` 只有 `pass` / `fail`
- `summary.decision` 会告诉下游是继续还是先修 BOM / syntax error
- `summary.source_count`、`clean_count`、`bom_count`、`syntax_error_count` 用于快速判断门禁状态
- `summary.bom_paths`、`syntax_error_paths` 直接列出问题文件
- `files[]` 逐文件记录 `path`、`absolute_path`、`has_bom`、`syntax_ok`、`parse_error`、`byte_count`

这里最重要的点是：`utf-8-sig` 负责正确解码，`has_bom` 负责单独把 BOM 事实保留下来，所以报告既能继续解析文件，也不会把 BOM 这件事吞掉。

## 运行流程

1. CLI 收集输入路径下的 `.py` 文件。
2. `build_source_encoding_report()` 对每个文件读字节、检查 BOM、做 `ast.parse()`。
3. 生成 JSON / CSV / Markdown / HTML 四类只读证据。
4. CLI 打印 `status`、`decision`、计数和输出路径。
5. 如果存在 BOM 或语法错误，进程返回非 0，CI 直接失败。

这个流程的价值不在于“多写了一个报告”，而在于把原本容易被忽略的编码问题提前到了 parse-safety 层。

## 测试覆盖

`tests/test_source_encoding_hygiene.py` 覆盖了四件事：

- 当前仓库源码没有 BOM，作为干净基线
- 临时构造 clean / bom / broken 三类文件，确认 BOM 和语法错误都能被识别
- 输出文件能正确写出，HTML 会转义 `<gate>` 这类文本
- CLI 在检测到 BOM 时返回 1，并且仍会产出 JSON 证据

这里的关键断言不是“测试能跑”，而是门禁的失败边界不能被悄悄改成“只是提示一下”。

## 证据与归档

v127 的运行证据放在 `c/127/图片/`，说明文字放在 `c/127/解释/说明.md`。README 和阶段索引也已经同步到 v127，所以这版不是孤立补丁，而是完整闭环。

`source_encoding_hygiene.json`、`.csv`、`.md`、`.html` 都是只读证据文件，不参与训练、不反向修改源码，只用于审计和展示。

## 不做什么

- 不改模型结构
- 不改训练流程
- 不改推理 API
- 不修复 BOM 文件内容本身，只做检测和阻断
- 不把编码卫生门禁扩展成新的大报告系统

## 一句话总结

v127 把一次 BOM 事故收口成可复用的源文件编码门禁，让 CI 从“单测前再发现问题”前移到了“解析安全先检查”。
