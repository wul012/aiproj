# v1127 publication receipt index

## 本版目标与边界
v1127 的目标是把 v1125 lookup-only receipt 和 v1126 contract check 合并成新的 receipt index。v1125 回答“v1124 review 是否可以被记录成 receipt”，v1126 回答“这份 receipt 是否能从 v1124 review 重新构建并保持关键字段一致”，而 v1127 回答的是第三个问题：下游如果要查这条治理链，是否可以通过一个稳定 index 同时看到 receipt、contract check、lookup key、source evidence 和 no-promotion 边界。

本版不训练模型，不改动上游 receipt/check，不新增生产发布许可，也不改变模型质量声明。`index_ready=True` 的含义非常具体：receipt 文件存在，contract check 文件存在，receipt 本身通过，contract check 通过，lookup key 数量正确，source evidence 数量正确，granted use 仍是 downstream governance lookup only，promotion 仍然关闭。它不是“模型已经上线”，也不是“候选模型质量提升”。

## 前置路线

```text
v1124 review
  -> v1125 receipt
  -> v1126 contract check
  -> v1127 receipt index
```

这一版处在 receipt/check 之后、review 之前。没有 v1125，v1127 就没有可索引的 receipt；没有 v1126，v1127 就无法知道 receipt 是否可重建；没有 v1127，v1128 review 就只能直接读两份上游报告，缺少一个稳定 lookup 入口。这个位置决定了 v1127 的核心价值：把分散证据压成下游可消费索引，同时保留足够的反查路径。

## 关键文件与职责

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127_artifacts.py
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127.py
```

主 builder 文件负责真正的索引构建。它读取 receipt report 和 receipt check report，把 `summary`、`receipt`、`check_summary` 拆出来，生成检查行，再根据检查结果决定是否构建 index rows。artifact 文件只负责渲染，不改变判定。CLI 文件负责把 `--receipt` 和 `--receipt-check` 接到定位函数上，并通过 `--require-index-ready`、`--require-lookup-ready` 把失败索引变成非零退出。测试文件覆盖正常索引、granted use 漂移、contract check 不 ready、artifact/CLI wiring 等场景。

常量文件新增了 v1127 的 next step。这个 next step 指向 v1128 review，说明 v1127 不是链路终点。一个 index 只有经过 review，才能进入下一次 receipt 记录。如果没有这个 next step，后续自动化只能靠人记住版本节奏，维护成本会越来越高。

## 输入模型
v1127 的输入有两份。

第一份是 v1125 receipt。它提供 receipt status、consumer name、granted use、lookup keys、source evidence count、source review path、source receipt/index/check paths、promotion flags 和 model quality claim。第二份是 v1126 contract check。它提供 original/rebuilt receipt status、original/rebuilt granted use、lookup key count、promotion ready 对比结果，以及 `contract_check_ready=True`。

这两份输入的关系是互补的。receipt 说明“这是什么证据”，contract check 说明“这份证据是否能从源头重建”。v1127 不能只看 receipt，因为 receipt 可能被手工改过；也不能只看 check，因为 check 不提供下游 lookup 行。把两者合在一起，才形成可查索引。

## 输出模型
v1127 输出的核心是 `receipt_index`、`receipt_index_rows`、`source_evidence_rows`、`summary` 和 `check_rows`。

`receipt_index_rows` 是下游最可能消费的结构。本版只有一行，因为 v1125 receipt 只有一个 lookup key。该行包含 receipt index id、lookup key、receipt id、receipt status、granted use、source receipt path、source receipt check path、source review path、source receipt index path、contract check ready 和 promotion ready。它把一串分散路径压成一条可查记录。

`source_evidence_rows` 保存 receipt 与 receipt check 两条上游证据，并带有 sha256。这样下游 review 可以知道 index 不是凭空生成的，它可以反查到具体 receipt 和 check 文件。`summary` 则保留自动化需要的摘要，例如 `index_ready`、`lookup_scope`、`lookup_key_count`、`source_evidence_count`、`lookup_ready`、`contract_check_ready`、`promotion_ready`、`next_step`、`passed_check_count` 和 `failed_check_count`。

`check_rows` 是失败定位入口。v1127 只要失败，就会把失败原因放进 `issues`。这比只输出一个 `status=fail` 更适合工程维护，因为开发者可以直接知道是 receipt 文件不存在、contract check 不通过、lookup key 数量不对，还是 source path 丢失。

## 核心检查逻辑
v1127 的 `_checks()` 先检查 receipt 和 receipt check 文件是否存在，再检查两者的 status 与 decision。receipt 的 decision 必须等于 v1125 ready key，contract check 的 decision 必须等于 v1126 passed decision。这样可以防止把错误版本的报告塞进 index。

随后检查 receipt summary 和 receipt body 是否都 ready，receipt status 是否是 v1125 的 lookup receipted 状态。这里同时比较 summary 与 body，是为了避免一处字段被改而另一处未改。接着检查 contract check ready、receipt status 与 check summary 的 original/rebuilt status 是否一致、granted use 是否在 summary、body、original、rebuilt 四个位置都保持 lookup-only。

lookup key count 是另一项关键检查。v1127 要求 summary、contract check original count、contract check rebuilt count 和 receipt body 的 lookup keys 长度都等于 1。这个数字看似简单，但它决定了下游索引是否稳定。如果 lookup key 数量漂移，下游 consumer receipts 就无法确定应该查哪一条。

source evidence 和 source path 检查保证索引仍能反查。v1127 会要求 receipt 记录的 source review、source receipt index、source receipt、source receipt check、source origin index 都存在。只要路径断开，index 就不能通过。最后，promotion 与 model quality claim 检查继续把项目限制在治理查阅边界。

## 测试中的修正
本版开发时测试暴露了一个有价值的问题：最初从 v1123 模板抬升到 v1127 后，测试 helper 仍然伪造 v1120 review，导致 v1125 receipt 构建失败。这个失败不是生产 builder 的错，而是测试输入没有跟随版本语义抬升。修复方式是把测试 helper 的 review 输入抬到 v1124，使它符合 v1125 receipt 的真实前置条件。

这个小问题值得记录，因为它说明版本迁移不能只替换文件名。链路语义也要一起迁移。v1127 依赖的是 v1125 receipt，而 v1125 receipt 依赖 v1124 review；如果测试还拿 v1120 review 伪装输入，得到失败是合理的。修复后 focused tests 通过，说明测试现在覆盖的是正确链路。

## CLI 与真实运行
真实命令如下：

```text
python -B scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127.py --receipt f/1125/解释/receipt-v1125 --receipt-check f/1126/解释/receipt-check-v1126 --out-dir f/1127/解释/receipt-index-v1127 --require-index-ready --require-lookup-ready --force
```

关键输出如下：

```text
status=pass
index_ready=True
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图保存为 `f/1127/图片/v1127-receipt-index.png`。页面展示 `Receipt Index Rows`、`Source Evidence` 和 `Checks`，说明 index 的三类核心信息都已渲染出来。

## 测试覆盖
focused tests 覆盖四类场景。第一，合法 receipt/check 可以生成 ready index。第二，receipt 的 granted use 被改成 production promotion 时失败。第三，contract check 不 ready 时失败。第四，artifact writer 和 CLI 可以写出五种输出，并且目录定位函数可以消费输出目录。

这些测试不是为了证明模型质量，而是为了证明 index 能保护下游查询边界。只要 receipt/check 不一致，index 就不能 ready；只要 contract check 不 ready，index 就不能给下游消费；只要 granted use 越界，index 就必须失败。

## 链路角色
v1127 是本轮 receipt/check 的索引层。它把 v1125 和 v1126 的输出合并为一个可查入口，并把下一跳固定到 v1128 review。后续 v1128 的职责不是重新生成 receipt 或 check，而是复核这个 index 是否仍然保留单条 lookup row、两条 source evidence、contract-check-ready 和 no-promotion 边界。

从维护角度看，v1127 也让链路更容易阅读。人工查看时，不必同时打开 v1125 和 v1126 的完整 JSON，只需要先看 v1127 index，就能知道 receipt id、lookup key、source evidence 和下一步动作。需要追溯时，再从 index rows 和 source evidence 回到上游文件。

## 一句话总结
v1127 把 v1125 receipt 与 v1126 contract check 收束成可查、可复核、不可 promotion 的 lookup-only receipt index，为 v1128 review 提供稳定输入。
