# v1090 publication receipt index review

## 本版目标

v1090 的目标是复核 v1089 生成的 digest-backed receipt index，确认它可以进入下一轮 lookup-only receipt 记录。

它解决的是“index 生成后是否真的仍然符合下游只读消费边界”的问题：一份 index 不应该因为存在 HTML/JSON 产物就被默认信任，必须继续检查 lookup row、source evidence、contract check、source path 和 no-promotion 边界。

本版不做的事：

- 不训练模型。
- 不修改 v1089 index。
- 不接受 candidate。
- 不放开 production promotion。
- 不把治理 review 解释成模型质量提升。

## 路线来源

v1089 已经把 v1087 receipt 和 v1088 contract check 合并成一份 digest-backed index。v1090 接在 v1089 后面，复用 v1086 的 review 模式，把 source index 从 v1085 升级到 v1089。

这让链路保持四步节奏：

1. receipt index
2. receipt index review
3. receipt recording
4. receipt contract check

v1090 正好是第二步，目标是让下一版 receipt recording 不直接消费未经复核的 index。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1090.py`
  - 核心 review builder。
  - 读取 v1089 index report，执行 22 项 check，输出 review summary 和 review body。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1090_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 输出。
- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1090.py`
  - CLI 入口。
  - `receipt_index` 是位置参数，支持目录或 JSON 文件。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1090.py`
  - 覆盖正常 review、granted use 篡改、缺失 source evidence、promotion ready 篡改和 CLI 输出。
- `e/1090/解释/receipt-index-review-v1090/`
  - 真实运行证据目录。

## 核心数据结构

`review` 是本版的主结构，关键字段包括：

- `review_ready`
  - 所有 check 通过时为 `True`。
- `review_status`
  - 固定为 lookup-only approval，不代表 production promotion。
- `receipt_index_path`
  - 指向被复核的 v1089 index JSON。
- `lookup_keys`
  - 从 v1089 index row 继承，只允许一个 lookup key。
- `source_receipt_path` 和 `source_receipt_check_path`
  - 继续保留 v1087 receipt 与 v1088 check 的可追踪路径。
- `promotion_ready`
  - 固定为 `False`。

`check_rows` 保护的边界包括：

- v1089 index 文件存在。
- source index status 和 decision ready。
- index summary 与 index body 都 ready。
- receipt index row 只有一行。
- source evidence rows 恰好两条且都为 pass。
- lookup key 使用 v1089 命名空间。
- source receipt/check/review/origin index 路径仍然存在。
- consumer boundary 与 model quality claim 保持治理口径。
- promotion 和 approved_for_promotion 都为 false。
- source next step 必须从 v1089 指向 v1090 review。

## 核心流程

1. CLI 接收 v1089 index 目录或 JSON 文件。
2. `locate_receipt_index_v1090` 定位 v1089 JSON。
3. builder 读取 `summary`、`receipt_index`、`receipt_index_rows` 和 `source_evidence_rows`。
4. `_checks` 执行 22 项 review check。
5. `_review` 生成 review body，继承 lookup-only use 和 source paths。
6. artifact writer 输出五种 sidecar。
7. Playwright MCP 打开 HTML 并截图。

## 测试覆盖

- 正常 v1089 index 可以通过 review。
- 篡改 granted use 会失败，保护 lookup-only 边界。
- 删除 source evidence 会失败，保护 digest-backed source chain。
- 把 promotion ready 改成 true 会失败，保护 no-promotion 边界。
- CLI 能输出 JSON/CSV/TXT/Markdown/HTML，且文本、Markdown、HTML 都包含 review summary。

这些断言让 v1090 不是“展示性文档版本”，而是真正防止 v1089 index 被错误消费的 contract-preserving review。

## 运行证据

真实命令消费了 `e/1089/解释/receipt-index-v1089`，输出确认：

- `status=pass`
- `review_ready=True`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

Playwright MCP 页面快照确认 HTML 中存在 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`，截图保存为 `e/1090/图片/v1090-receipt-index-review.png`。

## 验证

- focused v1090 tests：`5 passed in 0.35s`
- full pytest：`2843 passed in 482.23s`
- source hygiene：`2223/2223 clean`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1090/图片/v1090-receipt-index-review.png`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1090 把 v1089 digest-backed index 从“可查找证据”推进成“已复核、可进入下一轮 lookup-only receipt 记录”的证据入口。
