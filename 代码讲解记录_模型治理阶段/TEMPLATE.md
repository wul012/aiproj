# 第 N 版代码讲解：主题

本版目标是说明这一版解决什么问题，以及它在 MiniGPT 模型治理链路中的位置。

它不做什么也要写清楚。例如：不训练模型、不接受 candidate、不放开 production promotion、不把治理证据解释成模型质量提升。

## 入口

写清楚用户或 CI 从哪里进入本版能力：

```text
scripts/example.py
src/minigpt/example.py
```

如果入口是 CLI，说明关键参数和失败退出码。如果入口是 report builder，说明调用方和输入目录。

## 输出模型

列出最外层 report 或 summary 的核心字段，并解释字段语义：

```text
status
decision
failed_count
ready_key
promotion_ready
next_step
outputs
```

这里要明确哪些字段是硬边界，例如 `promotion_ready=False`、`lookup_scope=downstream_governance_lookup_only`、`executionAllowed=false`。

## 上游证据

说明本版读取了哪些上游 artifact：

```text
e/<version>/解释/<artifact>
f/<version>/解释/<artifact>
```

要说明这些证据是不是只读、是否可重建、是否带 digest、是否能被后续模块消费。

## 核心流程

按真实执行顺序说明数据如何流动：

1. 定位输入 JSON 或目录。
2. 解析 summary、body、rows 或 source evidence。
3. 执行核心检查或构建。
4. 写出 JSON/CSV/TXT/Markdown/HTML sidecar。
5. 生成运行截图或说明。

## 关键检查

写清楚每类检查保护什么：

- ready/status/decision：保护上游确实完成。
- digest/path：保护证据未丢失、未被静默替换。
- lookup-only/granted use：保护只读消费边界。
- no-promotion：保护治理证据不越权成生产发布许可。
- next-step：保护链路路由没有断。

## 测试覆盖

不要只写“测试通过”。要写每个测试场景挡住什么风险：

- 合法输入通过。
- 篡改字段失败。
- 缺失路径失败。
- 错误 digest 失败。
- CLI require gate 返回正确退出码。

## 运行证据

列出真实命令和关键输出。截图或说明文件要说明它证明了什么，不要只贴路径。

## 链路角色

用一段话说明这一版在链路中扮演什么角色，例如：

```text
review -> receipt -> contract check -> index
```

如果本版只是文档分流或规则整理，也要说明它为什么没有运行截图或单独代码讲解。

## 一句话总结

用一句话说明这一版把项目推进到了哪一层。
