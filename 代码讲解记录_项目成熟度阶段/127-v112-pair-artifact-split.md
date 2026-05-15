# 第一百一十二版代码讲解：Pair Artifact Split

## 本版目标

v112 的目标是继续执行 v110 的 module pressure audit，对 `server.py` 做第二处轻量、定向、可测试的代码膨胀治理。

v111 已经证明展示资产可以安全拆分；v112 把同样的思路应用到本地推理服务：不改 HTTP 路由、不改模型生成、不改 request history schema，而是把 pair generation artifact 的 JSON/HTML 写入边界抽成 `pair_artifacts.py`。

本版明确不做：

- 不改变 `/api/generate`、`/api/generate-stream`、`/api/generate-pair` 或 `/api/generate-pair-artifact` 的请求/响应契约。
- 不改变 `GenerationRequest`、`GenerationPairRequest`、`GenerationResponse`。
- 不改变 pair comparison 字段。
- 不改 playground 按钮或 checkpoint 选择逻辑。
- 不拆 server handler 主流程。

## 路线来源

本版来自 v110-v111 的代码膨胀治理线：

```text
v110 module pressure audit
 -> identify server.py as largest critical-size module
 -> v111 registry asset split proves low-risk split style
 -> v112 pair artifact split
```

`server.py` 的 pair artifact 写入边界适合本版拆分，因为它负责的是“保存证据”，不是“执行推理”：

- 输入是已经生成好的 pair payload。
- 输出是本地 JSON/HTML artifact。
- HTTP handler 只需要拿到 artifact 路径并写日志。
- 测试可以直接验证文件名、href、HTML 转义和 server wrapper。

## 关键文件

- `src/minigpt/pair_artifacts.py`
  - 新增模块。
  - 提供 `write_pair_generation_artifacts()`、`render_pair_generation_html()`、`slug()`、`timestamp_slug()`、`artifact_href()` 和 `unique_pair_artifact_stem()`。
- `src/minigpt/server.py`
  - 保留原有公开函数 `write_pair_generation_artifacts()` 和 `render_pair_generation_html()`。
  - 这两个函数现在委托到 `pair_artifacts.py`。
  - `_slug()` 也委托到 `pair_artifacts.slug()`，让 checkpoint id 和 artifact file stem 使用一致的 slug 规则。
- `tests/test_pair_artifacts.py`
  - 新增测试。
  - 覆盖 slug、timestamp slug、唯一文件名、run-relative href、JSON/HTML 写入、HTML 转义和 server wrapper delegation。
- `tests/test_server.py`
  - 原有 server HTTP 测试继续覆盖 `/api/generate-pair-artifact`。
- `README.md`
  - 当前版本、版本标签和截图说明更新到 v112。
- `c/112`
  - 保存本版运行截图和解释。

## 核心数据结构

pair artifact record 结构保持不变：

```json
{
  "schema_version": 1,
  "kind": "minigpt_pair_generation",
  "created_at": "2026-05-15T01:02:03Z",
  "run_dir": "...",
  "request": {
    "prompt": "abc",
    "max_new_tokens": 5,
    "temperature": 0.8,
    "top_k": null,
    "seed": 7
  },
  "left": {},
  "right": {},
  "comparison": {},
  "artifact": {
    "json_path": "...",
    "html_path": "...",
    "json_href": "pair_generations/...",
    "html_href": "pair_generations/..."
  }
}
```

这些字段仍由 `/api/generate-pair-artifact` 返回并写入 request log：

- `artifact_json`
- `artifact_html`

## 核心函数

`write_pair_generation_artifacts(run_dir, payload, output_dir=None, created_at=None)`

这是 artifact 写入入口。它做四件事：

1. 解析 run 根目录和输出目录。
2. 根据时间戳、left checkpoint、right checkpoint 生成稳定文件名前缀。
3. 写出 JSON record。
4. 用同一 record 渲染并写出 HTML。

`render_pair_generation_html(record)`

它只负责把 record 渲染成可浏览 HTML。所有文本都通过 `html_escape()` 转义，防止 prompt 或 generated text 里的 `<...>` 被浏览器当成标签。

`slug(value)` / `timestamp_slug(value)`

这两个函数负责文件名安全化：

```text
Default/One -> default-one
Wide Two!   -> wide-two
2026-05-15T01:02:03Z -> 2026-05-15t01-02-03utc
```

server 的 `_slug()` 也委托到同一个函数，避免 checkpoint id 和 pair artifact 使用两套略有差异的规则。

`unique_pair_artifact_stem(out_dir, base)`

它检查同名 `.json` 或 `.html` 是否已经存在。如果存在，就追加 `-2`、`-3`，保证不会覆盖已有 pair artifact。

## 运行流程

HTTP 侧流程保持不变：

```text
/api/generate-pair-artifact
 -> parse_generation_pair_request()
 -> generator_for(left).generate()
 -> generator_for(right).generate()
 -> _pair_generation_payload()
 -> server.write_pair_generation_artifacts()
 -> pair_artifacts.write_pair_generation_artifacts()
 -> write JSON + HTML
 -> log artifact_json / artifact_html
 -> send JSON response
```

外部调用者仍然只看到 `/api/generate-pair-artifact` 和 artifact 字段，感知不到内部模块拆分。

## 为什么这是轻量质量优化

`server.py` 是 v110 扫描出的最大模块。直接拆 handler、request history、streaming 或 checkpoint discovery 风险更高，因为这些部分和 HTTP 行为强相关。

pair artifact 写入则更适合先拆：

- 它是输出证据，不是请求路由。
- 它的输入输出清楚。
- 可以用纯单元测试覆盖，不需要启动 HTTP server。
- 现有 server 测试仍能证明 API 层没有退化。

本版完成后，`server.py` 从约 1676 行降到约 1571 行，新增 `pair_artifacts.py` 约 144 行。更重要的是，server 的职责边界更清楚：HTTP handler 负责路由和日志，pair artifact 模块负责本地证据文件。

## 测试覆盖

`tests/test_pair_artifacts.py` 覆盖：

- slug 和 timestamp slug 稳定性。
- `.json` / `.html` 任一冲突时都能生成下一个唯一文件名。
- artifact href 优先使用 run-relative 路径。
- 写出 JSON/HTML 后 schema、checkpoint id、文件名和 HTML 转义正确。
- server wrapper 与新模块渲染结果一致。

`tests/test_server.py` 继续覆盖：

- `/api/generate-pair` 两 checkpoint 路由。
- `/api/generate-pair-artifact` 生成 JSON/HTML 文件。
- artifact 路径写入 request log。
- bad request 行为不变。

## 证据闭环

v112 证据放在 `c/112`：

- `01-unit-tests.png`：pair artifact tests、server regression、compileall 和全量 unittest。
- `02-pair-artifact-smoke.png`：显示 server 行数变化、pair artifact smoke 和 module pressure smoke。
- `03-pair-artifact-structure-check.png`：证明源码、测试、README、讲解和 c 归档对齐。
- `04-pair-artifact-output-check.png`：证明 pair artifact JSON/HTML、href、slug、转义和输出文件存在。
- `05-playwright-pair-artifact-html.png`：证明生成后的 pair artifact HTML 可以在真实 Chrome 渲染。
- `06-docs-check.png`：证明 README、c/README 和项目成熟度阶段索引引用 v112。

## 一句话总结

v112 把 server 的 pair generation 证据保存边界抽成独立模块，让本地推理服务大文件治理从不碰 HTTP 主流程的低风险 artifact 层继续推进。
