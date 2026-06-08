# v1011 publication receipt index receipt index publication index receipt index receipt index receipt index receipt index receipt

## 目标与边界

v1011 的目标是把 v1010 审阅通过的 receipt index review 记录成 lookup-only downstream receipt。v1010 已经证明 v1009 index 可以继续被下游治理链只读消费；v1011 负责把这个消费动作落成 receipt，并把后续动作推进到 contract check。

本版不训练模型，不生成 checkpoint，不更新 benchmark，不改变 promotion 结论，也不把治理证据解释成模型质量提升。

## 前置路线

1. v1007 记录上一轮 lookup-only receipt。
2. v1008 对 v1007 receipt 做 contract check。
3. v1009 把 receipt 与 check 收成 digest-backed index。
4. v1010 审阅 v1009 index，允许下一步 receipt recording。
5. v1011 执行这个 receipt recording，并准备 v1012 的 receipt contract check。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011.py`
  - 核心 receipt builder，读取 v1010 review，执行 21 项边界检查，然后生成 receipt、summary、consumer_receipts 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出，保持证据格式和前序 receipt 版本一致。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011.py`
  - CLI 入口，支持输入 JSON 或目录，支持 `--require-receipt-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011.py`
  - 覆盖 ready 路径、requested use 篡改、source path 缺失、CLI 失败码和输出渲染。
- `e/1011/解释/receipt-v1011/`
  - 真实运行证据，后续 v1012 contract check 会消费这里的 JSON。

## 核心数据结构

`receipt` 是本版最关键的对象：

- `receipt_ready`
  - 所有检查通过才为 `True`。
- `receipt_id`
  - v1011 的 lookup-only receipt 标识。
- `receipt_status`
  - pass 时为 `publication_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_receipted`。
- `consumer_name`
  - 固定为下游治理读取者，不代表生产调用方。
- `granted_use`
  - 只能是 `downstream_governance_lookup_only`。
- `lookup_keys`
  - 继承 v1010 review 中的 lookup key。
- `promotion_ready`
  - 固定为 `False`。
- `next_step`
  - 指向 `check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011`。

## 核心检查

v1011 的 `_checks()` 主要保护以下边界：

- v1010 review 文件必须存在。
- v1010 report 必须 `status=pass` 且 decision 为 ready。
- summary ready key 与 body `review_ready` 必须同时为真。
- `review_status` 必须是 lookup-only receipt recording。
- requested use 只能是 downstream governance lookup。
- blocked uses 必须完整保留。
- receipt index 和 lookup 必须 ready。
- contract check 必须 ready。
- receipt index row 数量必须为 1。
- source evidence 数量必须为 2。
- lookup key namespace 必须是 publication-index receipt-index receipt-index receipt-index receipt。
- index row 不能被提升为 promotion。
- promotion 和 approved_for_promotion 必须为 False。
- consumer boundary 与 model quality claim 不能扩大。
- source receipt index、source receipt、source receipt check 路径必须仍然存在。
- v1010 source check count 必须为 0。
- v1010 的 next_step 必须指向 receipt recording。

## 输入输出链路

输入是：

```text
e/1010/解释/review-v1010/...review_v1010.json
```

输出是：

```text
e/1011/解释/receipt-v1011/...receipt_v1011.json
e/1011/解释/receipt-v1011/...receipt_v1011.csv
e/1011/解释/receipt-v1011/...receipt_v1011.txt
e/1011/解释/receipt-v1011/...receipt_v1011.md
e/1011/解释/receipt-v1011/...receipt_v1011.html
```

JSON 是后续 contract check 的机器入口；CSV 是 consumer receipt 行的扁平证据；Markdown、TXT 和 HTML 是人读证据；截图只证明 HTML 可浏览和关键状态可见。

## 测试覆盖

focused 测试覆盖了五类情况：

- ready review 能生成 pass receipt。
- requested use 改成 production promotion 会失败。
- source receipt index 路径缺失会失败。
- CLI 在 `--require-receipt-ready` 下会对坏输入返回 1。
- artifact writer、CLI、文本、Markdown、HTML 渲染都能串起来。

这些测试保护的是 receipt recording 的契约边界，而不是模型生成质量。

## 一句话总结

v1011 把 v1010 review 变成可复核的 lookup-only receipt，让后续 contract check 有了稳定输入，同时继续把 production promotion 和模型质量声明锁在边界内。
