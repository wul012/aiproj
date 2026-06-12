# v1128 publication receipt index review

## 本版目标与边界
v1128 的目标是 review v1127 receipt index。v1127 已经把 v1125 receipt 和 v1126 contract check 合并成一个 lookup-only index，但 index 生成之后仍然不能直接进入下一次 receipt 记录。原因是 index 自己也可能出现漂移：lookup row 可能丢失，source evidence 可能缺 hash，source path 可能指向不存在的文件，contract-check-ready 可能被改成 false，或者 promotion 字段被错误打开。v1128 就是这个进入下一次 receipt 记录前的拦截点。

本版不训练模型，不改变模型质量声明，不把 review ready 解释为生产批准。它只说明 v1127 index 在当前文件系统和当前证据链下仍然满足 lookup-only 记录条件。`review_ready=True` 的边界是治理记录，不是模型上线。`promotion_ready=False` 和 `approved_for_promotion=False` 继续是本版必须保留的结论。

## 前置路线

```text
v1125 receipt
  -> v1126 contract check
  -> v1127 receipt index
  -> v1128 receipt index review
```

v1128 是这一轮 index 的审查层。它不会重新构建 receipt，也不会重新跑 contract check，而是审查 v1127 已经汇总出的 index 是否仍然可被下游 receipt 记录使用。如果 v1128 失败，下一步应该回到 v1127 或更早版本修复，而不是绕过 review 直接记录 receipt。

## 关键文件与职责

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1128.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1128_artifacts.py
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1128.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1128.py
```

主 builder 负责读取 v1127 index，拆出 `summary`、`receipt_index`、`receipt_index_rows` 和 `source_evidence_rows`，再生成 review body、summary、check rows 和 interpretation。artifact 模块只负责输出格式。CLI 模块提供目录输入和 `--require-review-ready`、`--require-lookup-ready` 阻断语义。测试模块覆盖 ready index、granted use 漂移、source evidence digest 缺失、source path 漂移、artifact 与 CLI wiring。

本版还新增 v1128 review next step 常量。它把下一步固定为 v1129 receipt 记录。这个常量让链路可读，也让后续 builder 能检查 source next step 是否匹配。如果没有它，后续版本只能依赖手写字符串，维护风险会更高。

## 输入模型
v1128 的唯一输入是 v1127 index。这个 index 包含两类信息：一类是下游查阅所需的 `receipt_index_rows`，另一类是反查证据所需的 `source_evidence_rows`。review 不能只看 summary，因为 summary 是压缩视图，可能漏掉 path 或 digest 问题；也不能只看 index rows，因为 source evidence 才说明 receipt/check 的来源。

因此 v1128 会同时读取 `index_report.get("summary")`、`index_report.get("receipt_index")`、`index_report.get("receipt_index_rows")` 和 `index_report.get("source_evidence_rows")`。这些结构被标准化成 dict/list of dict 后才进入检查逻辑，避免输入里出现非对象结构导致后续访问异常。

## 输出模型
v1128 输出的核心是 `review`。它包含 `review_ready`、`review_id`、`review_status`、`receipt_index_path`、`receipt_index_id`、`receipt_index_row_count`、`lookup_keys`、`source_evidence_count`、`lookup_ready`、`contract_check_ready`、`granted_use`、`promotion_ready`、`approved_for_promotion`、`consumer_boundary`、`model_quality_claim`、`source_receipt_path`、`source_receipt_check_path`、`source_review_path`、`source_receipt_index_path` 和 `next_step`。

这些字段的作用可以分成三组。第一组是可消费性字段，例如 row count、lookup keys、lookup ready。第二组是可追溯字段，例如 source receipt、source check、source review 和 source receipt index path。第三组是边界字段，例如 granted use、promotion flags、consumer boundary 和 model quality claim。三组字段缺一不可：只有可消费性没有可追溯性，index 就难以审计；只有可追溯性没有边界字段，index 可能被误读成生产批准；只有边界字段没有 ready 字段，后续自动化无法判断是否继续。

## 核心检查逻辑
v1128 的 `_checks()` 首先检查 receipt index 文件是否存在、index 是否 pass、decision 是否等于 v1127 ready decision、summary 和 body 是否都 ready。这些检查保护输入身份，防止错误版本或失败版本被拿来 review。

接着检查 lookup scope 与 granted use。两者必须保持 downstream governance lookup only。这里同时检查 summary 和 index body，是为了防止某一层被单独篡改。`lookup_ready` 和 `contract_check_ready` 也必须同时为 true，因为 review 的目标不是“有个 index 文件”，而是“这个 index 确实可以被下游查询，并且它包含 ready 的 contract check”。

然后检查索引行。v1128 要求只有一条 receipt index row，并且 lookup key 必须使用 v1127 namespace。这个 namespace 检查不是装饰，它能防止旧版本 lookup key 混进新版本 index。source evidence 检查要求两条 evidence、每条都有 sha256、每条 status 都是 pass。这样后续 receipt 记录时可以信任这份 review 没有吞掉上游证据。

路径检查也是本版重点。v1128 会确认 source receipt、source receipt check、source review、source receipt index 都仍然存在。只要任意路径断开，review 就失败。最后，consumer boundary、model quality claim、promotion false 和 source next step 检查负责把治理边界固定住，防止 review 被解释成模型质量或上线批准。

## CLI 与运行证据
真实运行命令如下：

```text
python -B scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1128.py f/1127/解释/receipt-index-v1127 --out-dir f/1128/解释/receipt-index-review-v1128 --require-review-ready --require-lookup-ready --force
```

关键输出如下：

```text
status=pass
review_ready=True
receipt_index_row_count=1
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

Playwright MCP 截图保存为 `f/1128/图片/v1128-receipt-index-review.png`。页面展示 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`，说明 review 摘要、索引行、证据行、检查表都能在浏览器里打开。

## 测试覆盖
focused tests 覆盖五类情况。合法 v1127 index 可以生成 ready review；granted use 漂移到 production promotion 会失败；source evidence digest 缺失会失败；source receipt path 漂移会失败；artifact writer 和 CLI 可以写出五种输出并支持目录输入。这些测试和真实 CLI 互补：测试保护边界和失败路径，真实 CLI 证明当前仓库中的 v1127 证据能被消费。

测试里比较重要的是 source path 漂移场景。它模拟 index body 仍然存在，但里面指向的 receipt 文件已经不见了。这样的报告如果不阻断，后续 receipt 记录会把断链证据继续传播下去。v1128 的职责就是在这里拦住。

## 链路角色
v1128 是 v1127 index 进入下一次 receipt 记录前的门。它不生成新的 lookup row，而是批准现有 lookup row 可以被记录。后续 v1129 应该读取 v1128 review，生成新的 downstream receipt，并再次保留 no-promotion 边界。这样链路继续保持 receipt、check、index、review 的节奏。

从维护角度看，v1128 让 index 不只是一个输出产物，而是一个需要被审查的输入。每次 index 被复核后再进入 receipt，可以减少“报告很多但证据漂移没人发现”的风险。

## 一句话总结
v1128 复核 v1127 receipt index，并确认它仍然是可记录、可查阅、不可 promotion 的 lookup-only 治理证据。
