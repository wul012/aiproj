# 26. v12 测试、文档和归档

这一篇记录 v12 的验收材料：server 单元测试、真实 HTTP smoke、README 更新、`a/12` 截图归档和版本标签说明。

## 新增测试

`tests/test_server.py` 覆盖：

- 生成请求参数解析
- 非法 prompt、temperature、max_new_tokens 的错误处理
- `/api/health` 返回关键文件状态
- 用 stub generator 启动真实 `ThreadingHTTPServer` 并请求 `/api/generate`
- 错误请求返回 400

`tests/test_playground.py` 也增加了 `liveGenerateButton` 检查，确保页面包含 live generation 入口。

## smoke 验证

v12 smoke 会临时训练一个极小 checkpoint，再启动：

```powershell
python scripts/serve_playground.py --run-dir tmp/v12-server-smoke --device cpu --port 8765
```

然后请求：

```text
GET  /api/health
POST /api/generate
```

最后停止服务进程并清理临时目录。

## 截图归档

`a/12/图片` 保存五张关键截图：

- `01-unit-tests.png`
- `02-server-train-smoke.png`
- `03-serve-playground.png`
- `04-server-artifacts-check.png`
- `05-docs-check.png`

`a/12/解释/说明.md` 对每张截图做简短说明。

## 版本标签

v12 使用 `v12.0.0` 标签。标签说明应概括 local server、health/generate API、live playground、测试和截图归档。

## 一句话总结

v12 的重点是验证“浏览器 -> 本地 HTTP API -> MiniGPT checkpoint -> JSON 生成结果”这条链路已经打通。
