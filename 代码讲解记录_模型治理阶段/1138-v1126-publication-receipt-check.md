# v1126 publication receipt contract check

## 本版目标与边界
v1126 的目标是对 v1125 lookup-only receipt 做重建式 contract check。v1125 已经把 v1124 receipt index review 记录成新的 downstream receipt，但 receipt 生成之后还不能直接进入下一轮 index。原因很简单：receipt 是下游会读取的治理对象，如果有人手动改了 receipt JSON、改了 source path、改了 granted use，或者把 promotion 字段悄悄打开，单看 receipt 自己的 `status=pass` 并不能发现问题。v1126 的作用就是把 receipt 拉回源头，从它记录的 v1124 review 重新构建一份 receipt，然后把 original 与 rebuilt 逐项比较。

本版不训练模型，不更新模型权重，不扩展数据集，不把任何报告解释成生产批准。它只回答一个问题：当前保存的 v1125 receipt 是否能从它声明的源 review 重新推导出来，并且关键治理字段是否完全一致。`contract_check_ready=True` 不是模型能力指标，而是 receipt 证据链完整性的指标。

## 前置路线

```text
v1124 receipt index review
  -> v1125 receipt
  -> v1126 contract check
```

v1124 是源 review，v1125 是对 review 的 receipt 记录，v1126 是对这份 receipt 的重建检查。这个顺序不能颠倒。如果先做 index，再补 check，就会让下游 index 消费一份未经重建验证的 receipt；如果跳过 v1126，后续 v1127 只能相信 v1125 的表面字段，而没有办法知道它是否与 v1124 源证据一致。

## 关键文件与职责

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_artifacts.py
scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1126.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126.py
```

主模块负责读取 receipt、定位源 review、重建 receipt、生成 check rows 和 summary。artifact 模块负责把 report 写成 JSON、CSV、TXT、Markdown 和 HTML。CLI 模块负责把目录参数解析成具体 JSON 文件，并在 `--require-pass` 打开时让失败 check 以非零退出码返回。测试模块则覆盖正常重建、字段篡改、source review 缺失、CLI 失败码和 sidecar 输出等场景。

本版还补充了常量 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1126_NEXT_STEP`。它把 v1126 的下一跳固定为 v1127 index，避免后续链路依赖硬编码字符串。

## 输入读取与重建流程
CLI 的输入是 `f/1125/解释/receipt-v1125`。如果传入的是目录，定位函数会自动找到 v1125 receipt JSON。builder 读取 receipt 后，不会只看顶层 `status`。它会先解析 `summary` 和 `receipt`，再读取 receipt body 中的 `receipt_index_review_path`。这个路径指向 v1124 review，是重建过程的源头。

重建时，v1126 会重新调用 v1125 receipt builder。也就是说，它不是拿原 receipt 做浅拷贝，也不是只比较几个字符串，而是从 v1124 review 再跑一遍 v1125 的业务逻辑。重建完成后，contract check 把 original 和 rebuilt 的关键字段放到同一张检查表里逐项比较。这样做的好处是：如果 v1125 builder 的逻辑、v1124 review 的内容、或者原始 receipt 文件发生了任何关键漂移，都能在 v1126 被发现。

## 输出结构
v1126 report 包含几个核心区域。

`summary` 是自动化消费的压缩结论，包含 `contract_check_ready`、`source_receipt_index_review`、`original_receipt_status`、`rebuilt_receipt_status`、`original_granted_use`、`rebuilt_granted_use`、`original_lookup_key_count`、`rebuilt_lookup_key_count`、`original_promotion_ready`、`rebuilt_promotion_ready`、`next_step`、`passed_check_count` 和 `failed_check_count`。这些字段足够让后续 v1127 index 判断：receipt 是否可被索引消费。

`check_rows` 是人工排查的主入口。它逐项记录检查 id、状态、actual 和 detail。如果某个字段失败，读者可以直接定位到是 source review 不存在、status 不一致、granted use 越界、lookup keys 漂移，还是 no-promotion 字段被改变。

`interpretation` 是给报告阅读者看的边界说明。它强调 v1125 receipt 能从 v1124 review 重建，并且仍然是 lookup-only。这里不能写“模型通过”或“可以上线”，因为 contract check 只保护证据链，不证明模型质量。

## 核心检查内容
v1126 的第一组检查关注源文件。`source_receipt_index_review_exists` 要求 v1125 receipt 中记录的 v1124 review 仍然存在。这个检查很关键，因为如果 source review 文件丢失，即使 receipt 自己看起来完整，也已经不能被重建。

第二组检查关注 original 和 rebuilt 的顶层字段，包括 `status`、`decision`、`failed_count` 和 `receipt_index_review_sha256`。如果 receipt 被手动改成别的 decision，或者 source review hash 对不上，就说明这份 receipt 不再是从声明源头自然生成的结果。

第三组检查关注 summary 和 receipt body 的字段一致性。它比较 receipt id、receipt type、receipt status、consumer name、granted use、receipt index row count、source evidence count、lookup key count、promotion flags、consumer boundary、model quality claim、next step、passed/failed check count 等。字段多并不是为了堆复杂度，而是因为 receipt 的消费面很宽，任何一个字段漂移都可能影响后续 index 或 review 的判断。

第四组检查关注 source paths。v1126 会比较 `receipt_index_review_path`、`source_receipt_index_path`、`source_receipt_path`、`source_receipt_check_path`、`source_review_path` 和 `source_receipt_index_origin_path`。这些路径是治理链路的可追溯骨架。如果路径被改错，后续报告仍然能打开，但证据已经断链。

第五组检查关注 no-promotion。original 和 rebuilt 都必须保持 `promotion_ready=False`，`approved_for_promotion=False`。这一步与模型质量无关，但与项目边界强相关。aiproj 当前很多治理报告都容易被误读成“模型可上线”，所以每一跳都要显式保留 no-promotion。

## CLI 入口和失败语义
真实命令如下：

```text
python -B scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1126.py f/1125/解释/receipt-v1125 --out-dir f/1126/解释/receipt-check-v1126 --require-pass --force
```

`--require-pass` 的含义是：只要 contract check 失败，进程就返回 1。它和 v1125 的 `--require-receipt-ready` 一样，是把报告变成 CI 可用工具的关键。如果没有这个开关，失败报告也可能以 0 退出，自动化就无法阻断错误链路。

## 真实运行证据
本版真实运行输出如下：

```text
status=pass
contract_check_ready=True
original_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

这份输出说明 original 与 rebuilt 在关键字段上匹配。Playwright MCP 截图保存为 `f/1126/图片/v1126-receipt-check.png`，页面展示 `Contract Summary` 和 `Checks`，说明 HTML 报告能被真实浏览器打开，且不是空白产物。

## 测试覆盖
focused tests 覆盖六类行为。第一，合法 receipt 可以通过 contract check。第二，篡改 receipt 的核心字段会导致失败。第三，删除或改错 source review 路径会失败。第四，`--require-pass` 在失败时返回 1。第五，artifact writer 能写出五种输出。第六，CLI 能消费目录输入并生成完整 sidecar。这些测试保护的是 contract check 的可执行性和阻断语义。

测试的重点不是“多跑几个断言显得扎实”，而是确保 contract check 真能发现 drift。v1126 如果只检查 `status=pass`，就无法防止 receipt body 被改；如果只检查 receipt body，不重建，就无法证明源 review 仍然能推导出 receipt；如果只重建不比较 source paths，就无法发现证据路径漂移。因此本版检查数量达到 46 项是合理的。

## 链路角色
v1126 位于 receipt 之后、index 之前。它把 v1125 receipt 从“已生成”提升到“可复核”。后续 v1127 才能把 receipt 和 check 合并成新的 index。如果 v1126 失败，正确动作不是绕过它继续 index，而是回到 v1125 或 v1124 修复源证据。

这也是本批五版的核心节奏：每一轮 receipt 都要经过 check，再进入 index，再进入 review。这样项目虽然仍是 AI 工程治理项目，不是生产 LLM 训练系统，但它的证据链越来越像一个可维护、可审计的工程管线。

## 一句话总结
v1126 用重建式 contract check 证明 v1125 receipt 没有偏离 v1124 review，并继续把模型治理边界限制在 lookup-only 和 no-promotion 内。
