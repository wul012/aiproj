# v1259 route-promotion release readiness receipt index review 代码讲解

## 本版目标与边界

v1259 接在 v1258 之后，做的是 receipt index 的 review 层。v1258 已经把 v1257 的 granted downstream receipt 收束成一条 lookup row，并记录了 v1257 receipt 文件的 digest；v1259 不再生成新的 index，也不重新判断 release readiness，而是检查这个 index 是否可以被后续下游作为 bounded lookup 证据消费。换句话说，v1258 负责“建索引”，v1259 负责“审索引”。

本版明确不做模型训练、不做新的能力评测、不扩大 `seed_stable_pair_probe_route_accepted` 的语义、不打开 promotion。review 通过只表示 v1258 index 可用于 `bounded_route_promotion_release_readiness_receipt_lookup_only`，不能被解释为生产模型质量声明、无边界发布晋级、训练数据复用证明，或 pair-probe route 之外的能力声明。

这一层 review 有实际价值。没有 review 时，下游只能看到 index 自己说它 ready，但无法确认 index 文件存在、index digest 可计算、lookup row 与 summary/body 一致、row 里的 receipt digest 仍然能和真实 v1257 receipt 文件对上、blocked uses 没有缺项、promotion flag 没有被打开。v1259 把这些检查写成代码、测试和版本化证据，让后续消费方可以读取 review report，而不是重复实现同一套校验。

## 关键文件与职责

`src/minigpt/model_capability_route_promotion_release_readiness_receipt_index_review.py` 是核心逻辑。它定义 review 产物的文件名常量、ready index decision、review id 和 next step。对外函数包括 `locate_route_promotion_release_readiness_receipt_index`、`read_json_report`、`build_model_capability_route_promotion_release_readiness_receipt_index_review` 和 `resolve_exit_code`。

builder 的输入是 v1258 的 receipt index report 和可选 `receipt_index_path`。它从 report 中读取 `summary`、`receipt_index`、`receipt_index.index_rows` 和 `receipt_index.source_digest_rows`，生成 check rows，再派生 status、decision、review、summary 和 interpretation。成功时 decision 是 `model_capability_route_promotion_release_readiness_receipt_index_review_ready`，失败时是 `fix_model_capability_route_promotion_release_readiness_receipt_index_review`。

`src/minigpt/model_capability_route_promotion_release_readiness_receipt_index_review_artifacts.py` 是输出层。它把 review report 写成 JSON、CSV、TXT、Markdown 和 HTML。CSV 输出 check rows，因为 review 的主要价值是“哪些检查通过或失败”。Markdown 和 HTML 展示 lookup keys 与 checks，便于人工确认 review 不是只看一个 ready flag。

`scripts/review_model_capability_route_promotion_release_readiness_receipt_index.py` 是薄 CLI。它接收 `--receipt-index`，支持传 JSON 文件或输出目录；传目录时 locator 自动补 `model_capability_route_promotion_release_readiness_receipt_index.json`。脚本负责准备输出目录、调用 builder、写 artifact、打印摘要和处理 `--require-review-ready` 退出码，不把领域判断写进脚本。

`tests/test_model_capability_route_promotion_release_readiness_receipt_index_review.py` 是本版测试。它复用 v1258 测试里的 ready downstream receipt 构造函数，先生成 receipt，再生成 index，最后做 review。测试覆盖 root facade export、ready review、missing index file failure、promoted row failure、artifact writer 和 CLI。

`src/minigpt/_root_lazy_exports_route_promotion.py`、`src/minigpt/_root_public_exports.py`、`tests/test_public_api_policy.py` 和 `docs/public-api.md` 记录 public API 变化。本版新增两个稳定出口：`build_model_capability_route_promotion_release_readiness_receipt_index_review` 和 `write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs`。预算从 v1258 的 286/316 提升到 288/318，并在 public API 文档中明确说明这是有意提升。

## 核心数据结构

review report 顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`receipt_index_path`、`receipt_index_digest`、`source_receipt_index_summary`、`source_receipt_index`、`lookup_rows`、`source_digest_rows`、`check_rows`、`review`、`summary` 和 `interpretation`。

`receipt_index_digest` 是本版新增的关键证据点。v1258 已经对 v1257 receipt 文件计算 digest，v1259 又对 v1258 index 文件计算 digest。这样链路从 source evidence 到 summary check，到 downstream receipt，到 receipt index，再到 index review，每一层都有自己的文件摘要。后续如果 review 被纳入 bundle 或 manifest，可以用这个 digest 证明 review 看的就是当前这份 index。

`source_receipt_index_summary` 和 `source_receipt_index` 是 v1258 的输入快照。summary 提供快速状态，例如 `receipt_index_ready=True`、`lookup_key_count=1`、`lookup_ready=True`、`promotion_ready=False`。body 提供具体 index row、lookup keys、downstream receipt path、downstream receipt digest、source digest rows 和 blocked uses。review 不只相信 summary，也同时检查 body 和 row。

`lookup_rows` 是从 `receipt_index.index_rows` 拿出来的行列表。本版真实运行只有一行，lookup key 为 `route-promotion-release-readiness:objective_level_contrast`，entry id 为 `route-promotion-release-readiness:objective_level_contrast:release-readiness-index-builder`。这行记录的是 bounded governance lookup，而不是生产发布授权。

`review` 是本版的核心输出。成功时它包含 `review_ready=True`、`review_id=route-promotion-release-readiness-receipt-index-review-v1259`、`review_status=approved_for_bounded_receipt_lookup`、`receipt_index_path`、`receipt_index_digest`、`entry_count=1`、`lookup_keys`、`lookup_ready=True`、`consumer_name`、`route_id`、`allowed_use`、`granted_scope`、`boundary`、`model_quality_claim`、`source_digest_count`、`promotion_ready=False`、`approved_for_promotion=False`、`blocked_uses` 和 `next_step=record_reviewed_route_promotion_release_readiness_receipt_index`。

## 核心检查流程

`_check_rows` 先检查 index 文件锚点：`receipt_index_file_exists` 确认传入路径存在，`receipt_index_digest_present` 确认能对 index 文件计算 SHA-256。没有这两项，review 就只是在审一个内存对象，不足以作为证据。

第二组检查 index 自身状态：`receipt_index_passed` 要求 v1258 report 顶层 status 为 pass，`receipt_index_decision_ready` 要求 decision 是 `model_capability_route_promotion_release_readiness_receipt_index_ready`，`receipt_index_ready` 要求 summary 和 body 都 ready。这样可以防止 summary、body 和顶层状态不一致。

第三组检查 lookup 语义：`lookup_scope_bounded` 要求 summary 和 body 的 lookup scope 都是 `bounded_route_promotion_release_readiness_receipt_lookup_only`；`lookup_ready` 要求 summary 和 body 都为 true；`lookup_rows_present` 要求 row 数量与 summary/body entry count 一致且大于零；`lookup_key_count_matches` 要求 lookup keys、row 数量和 summary 计数一致；`row_route_matches_summary` 要求 row、summary、body 的 route 都一致。

第四组检查边界和 claim：`granted_scope_bounded` 要求 row 和 body 都是 `bounded_route_promotion_release_governance_only`；`boundary_required` 要求 row 和 body 都是 `tiny_required_term_pair_probe_only`；`claim_bounded` 要求 row 和 body 的 model quality claim 都仍然以 `seed_stable_pair_probe_route` 开头。这些检查避免 index review 层悄悄把 bounded receipt 变成更大的能力声明。

第五组检查 digest 链路：`source_check_digest_present` 确认 v1256 check digest 还在 row 和 body 中；`downstream_receipt_file_exists` 确认 index 指向的 v1257 receipt 文件还存在；`downstream_receipt_digest_matches` 会重新读取该 receipt 文件并计算 SHA-256，要求它和 index body、row 中记录的 digest 完全一致。这个检查是 v1259 的核心，因为它证明 index row 没有引用漂移的 receipt。

第六组检查 source digest 和 blocked uses：`source_digest_count_matches` 要求 index body、row 和 source digest rows 数量一致；`source_digests_present` 要求所有 source digest rows 都有 SHA-256；`blocked_uses_complete` 要求 row 和 body 的 blocked uses 与 v1257 定义的完整 blocked-use 集合一致。最后，`promotion_still_false` 要求 summary、body、row 和 approved flag 都没有打开 promotion；`source_index_checks_clean` 要求 v1258 failed count 为零；`source_next_step_matches` 要求 v1258 的 next step 确实指向 index review。

## Artifact 与真实证据

真实运行输出在 `f/1259/解释/model-capability-route-promotion-release-readiness-receipt-index-review/`。JSON 是完整证据，CSV 是 check rows，TXT 是 CLI 摘要，Markdown 和 HTML 是人工阅读版。由于本版没有浏览器页面或训练曲线，`f/1259/图片/README.md` 明确说明不生成截图。

真实运行结果为 `status=pass`、`decision=model_capability_route_promotion_release_readiness_receipt_index_review_ready`、`receipt_index_review_ready=True`、`review_id=route-promotion-release-readiness-receipt-index-review-v1259`、`review_status=approved_for_bounded_receipt_lookup`、`entry_count=1`、`lookup_key_count=1`、`lookup_ready=True`、`consumer_name=release-readiness-index-builder`、`route_id=objective_level_contrast`、`allowed_use=bounded_route_promotion_release_readiness_receipt_lookup_only`、`source_digest_count=3`、`promotion_ready=False`。这说明 v1258 index 已经通过独立 review，可以作为 bounded lookup 的治理证据。

## 测试覆盖

目标测试有五个用例。root facade export 测试确认 review builder 和 writer 已经稳定暴露。ready review 测试构造完整 v1257 receipt -> v1258 index -> v1259 review 链路，断言 status、decision、ready flag、lookup key count、route、source digest count、promotion flag、review digest 和 exit code。

missing index file failure 测试传入不存在的 index path，断言 `receipt_index_file_exists` 和 `receipt_index_digest_present` 失败。这个测试保护 review 的文件证据锚点。

promoted row failure 测试把 summary、body、row 和 approved flag 都改成 promotion-ready，断言 `promotion_still_false` 失败，并且 summary 的 `model_quality_claim` 变成 `not_claimed`。这证明 review 层不会让 index 越过 no-promotion boundary。

outputs/CLI 测试覆盖目录定位、五种输出、`--require-review-ready`、TXT 摘要、Markdown Lookup Keys 和 HTML 渲染。public API policy 测试保护新增 facade 出口预算。

## 链路角色

v1259 位于 v1258 receipt index 和后续 reviewed index receipt 或 release bundle 之间。它的输出比 v1258 更适合被后续自动化消费，因为它不仅包含 index 内容，还包含对 index 的独立审查结果。后续如果继续推进，合理方向是记录 reviewed index receipt，或者把 v1255-v1259 这条 release-readiness evidence chain 做成更上层的 bundle/manifest。

这版也继续修复项目的软件工程问题：不是把 README 当作唯一证明，也不是把所有逻辑塞到脚本里，而是把每一层证据都变成纯 builder、artifact writer、CLI、测试、真实证据和代码讲解。这样项目虽然版本很多，但每一层职责都更可追踪。

## 一句话总结

v1259 为 v1258 receipt index 增加了一层 digest-aware、boundary-aware、no-promotion 的独立 review，让 route-promotion release readiness 证据链从“可检索 index”推进到“已审查的可检索 index”。
