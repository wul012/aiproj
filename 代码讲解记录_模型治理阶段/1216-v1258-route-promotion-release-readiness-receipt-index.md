# v1258 route-promotion release readiness receipt index 代码讲解

## 本版目标与边界

v1258 接在 v1257 后面，目标是把“已经 granted 的 route-promotion release readiness downstream receipt”变成“可被后续治理模块按 lookup key 检索的 receipt index”。v1255 做 release readiness summary，v1256 做 summary contract check，v1257 做 downstream receipt，v1258 则是下一层索引。它不重新解释上游 packet、review、snapshot，也不重新判断模型是否 ready；它只验证 v1257 的 receipt 仍然可用，并把 receipt 中的 consumer、route、scope、claim、digest 和 blocked uses 放进稳定的 index 结构。

本版明确不做模型训练，不做新的能力评测，不把 `seed_stable_pair_probe_route_accepted` 扩展成生产模型质量声明，也不允许 promotion。`promotion_ready` 和 `approved_for_promotion` 在 index 中始终为 `False`。index 的 lookup scope 是 `bounded_route_promotion_release_readiness_receipt_lookup_only`，说明这份 index 只能作为发布治理中的 receipt lookup 使用，而不能成为无边界发布授权或训练数据复用证明。

为什么需要这一版？v1257 已经把 checked summary 授权给了 `release-readiness-index-builder` 这个下游消费者，但那仍是一份单独 receipt。后续如果要做 index review、release bundle、manifest 或更大范围的证据聚合，直接消费单份 receipt 会让每个下游都重复解析 receipt 的细节。v1258 把它收束成一条 lookup row：lookup key、entry id、consumer、route、granted scope、boundary、claim、source check digest、receipt digest、source digest count 和 blocked uses 都在一处。这是治理链路里常见的“先交接，再索引，再 review”的节奏。

## 关键文件与职责

`src/minigpt/model_capability_route_promotion_release_readiness_receipt_index.py` 是核心逻辑。它定义 receipt index 的五种输出文件名常量、ready receipt decision、v1257 的 expected next step、本版 index id、lookup scope 和 index next step。对外函数包括 `locate_route_promotion_release_readiness_downstream_receipt`、`read_json_report`、`build_model_capability_route_promotion_release_readiness_receipt_index` 和 `resolve_exit_code`。

builder 的输入是一份 v1257 downstream receipt report，外加可选的 `downstream_receipt_path` 和 required boundary。它读取 receipt report 的 `summary`、`receipt` 和 `receipt.source_digest_rows`，生成一组 check rows。如果全部通过，就生成 `receipt_index`；如果任何检查失败，就生成 fail report，并把 `model_quality_claim` 降成 `not_claimed`。这里的设计继续沿用前几版的 failure-safe 规则：失败产物不能保留看起来可用的能力声明，也不能暴露 ready lookup row。

`src/minigpt/model_capability_route_promotion_release_readiness_receipt_index_artifacts.py` 是输出层。它把同一份 report 写成 JSON、CSV、TXT、Markdown 和 HTML。CSV 的粒度是 lookup row，而不是 check row，因为 index 的主要消费者关心的是“有哪些可查条目”。Markdown 和 HTML 同时展示 source evidence、lookup rows 和 checks，方便人工 review 时不用打开 JSON 也能看到 receipt digest、route、scope、claim 和 promotion boundary。

`scripts/build_model_capability_route_promotion_release_readiness_receipt_index.py` 是薄 CLI。它只做参数解析、输入定位、输出目录准备、调用 builder、写 artifact、打印文本摘要和处理 `--require-index-ready`。领域规则没有写在脚本里，这一点很重要：脚本只是入口，核心判断必须能被单元测试直接覆盖。

`tests/test_model_capability_route_promotion_release_readiness_receipt_index.py` 是本版测试。它先复用 v1257 测试里的 ready checked summary，再生成 granted downstream receipt，最后构建 receipt index。测试覆盖 root facade export、ready index、ungranted receipt failure、missing receipt file failure、artifact writer 和 CLI。这样既覆盖成功路径，也覆盖最容易发生的两类失败：receipt 本身没有 granted，或者 receipt path 丢失导致 digest 不能固定。

`src/minigpt/_root_lazy_exports_route_promotion.py`、`src/minigpt/_root_public_exports.py`、`tests/test_public_api_policy.py` 和 `docs/public-api.md` 记录 public API 变化。本版新增两个稳定出口：`build_model_capability_route_promotion_release_readiness_receipt_index` 和 `write_model_capability_route_promotion_release_readiness_receipt_index_outputs`。预算从 v1257 的 all-export 284/lazy-export 314 提高到 286/316，并在 public API 文档中明确说明这是有意提升。

## 核心数据结构

receipt index report 顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`downstream_receipt_path`、`downstream_receipt_digest`、`source_downstream_receipt_summary`、`source_downstream_receipt`、`source_digest_rows`、`check_rows`、`receipt_index`、`summary` 和 `interpretation`。

`downstream_receipt_digest` 是 v1258 的关键新证据点。v1257 已经记录了 v1256 check JSON 的 digest，以及 v1256 对 v795、v796、v800 的 source digest rows；v1258 则对 v1257 receipt JSON 本身计算 SHA-256。这样证据链从上游三份源证据，到 summary check，再到 downstream receipt，再到 receipt index，都有可追踪摘要。后续 review 如果要证明 index 没有引用错误的 receipt，就可以比对这个 digest。

`source_downstream_receipt_summary` 和 `source_downstream_receipt` 保留 v1257 的摘要和 receipt body。前者让下游快速判断 `downstream_receipt_ready=True`、`receipt_status=granted`、`route_id=objective_level_contrast`、`granted_scope=bounded_route_promotion_release_governance_only`、`source_digest_count=3`；后者保留 `receipt_id`、`source_check_digest`、`source_digest_rows`、`blocked_uses` 和 `next_step`。index 不重新计算上游 digest rows，但要求这些 rows 存在并且每行带 SHA-256。

`receipt_index` 是本版核心输出。成功时它包含 `index_ready=True`、`index_id=route-promotion-release-readiness-receipt-index-v1258`、`lookup_scope=bounded_route_promotion_release_readiness_receipt_lookup_only`、`downstream_receipt_path`、`downstream_receipt_digest`、`entry_count=1`、`index_rows`、`lookup_keys`、`lookup_ready=True`、`consumer_name`、`route_id`、`granted_scope`、`boundary`、`model_quality_claim`、`source_check_digest`、`source_digest_count`、`source_digest_rows`、`blocked_uses`、`promotion_ready=False`、`approved_for_promotion=False`、`evidence_count=2` 和 `next_step=review_indexed_route_promotion_release_readiness_receipt`。

`index_rows` 是下游最可能直接消费的结构。每一行包含 `lookup_key`、`entry_id`、`consumer_name`、`route_id`、`granted_scope`、`boundary`、`model_quality_claim`、`source_check_digest`、`downstream_receipt_digest`、`source_digest_count`、`blocked_uses`、`promotion_ready` 和 `lookup_ready`。当前真实运行只有一条 row，lookup key 是 `route-promotion-release-readiness:objective_level_contrast`。这条 row 的意义不是“模型可以生产发布”，而是“这条 route 的 release readiness downstream receipt 可以在 bounded governance lookup 中被找到”。

## 核心检查流程

`_check_rows` 是本版最重要的防线。第一组检查 receipt 文件本身：`downstream_receipt_file_exists` 要求传入路径存在，`downstream_receipt_digest_present` 要求能够对这个文件算出 digest。这样 index 不会只引用一个内存里的 dict，而是固定真实文件。

第二组检查 v1257 receipt 的状态：`downstream_receipt_passed` 要求 report status 为 pass，`downstream_receipt_decision_granted` 要求 decision 是 `model_capability_route_promotion_release_readiness_downstream_receipt_granted`，`downstream_receipt_ready` 要求 summary ready，`receipt_status_granted` 要求 body 里也是 granted。这四项一起防止“顶层通过但 body 没通过”或“body 写 granted 但 decision 不对”的不一致。

第三组检查消费边界：`consumer_name_present` 和 `route_id_present` 确认 index row 有消费者和 route；`granted_scope_bounded` 要求 scope 仍是 `bounded_route_promotion_release_governance_only`；`boundary_required` 要求 boundary 仍是 `tiny_required_term_pair_probe_only`；`claim_bounded` 要求模型能力声明仍以 pair-probe route 为界。这些检查保证 index 没有在索引时悄悄扩大语义。

第四组检查 digest 和 blocked uses：`source_check_digest_present` 确认 receipt 仍带 v1256 check digest；`source_digest_count_matches` 和 `source_digests_present` 确认三份上游 source digest row 完整；`blocked_uses_complete` 要求 blocked uses 与 v1257 定义完全一致。这里不是只检查列表非空，而是检查集合等于完整 blocked-use 集合，防止某个禁止用途在 index 层被漏掉。

第五组检查来源干净和路由：`source_receipt_checks_clean` 要求 v1257 的 failed_count 为零且 check rows 全部 pass；`source_next_step_matches` 要求 v1257 receipt 和 summary 的 next step 都是 `index_checked_route_promotion_release_readiness_receipt`。这个检查让 v1258 明确消费正确阶段的产物，而不是把任意 receipt report 硬塞进 index。

## Artifact 与真实证据

真实运行输出在 `f/1258/解释/model-capability-route-promotion-release-readiness-receipt-index/`。JSON 是完整证据，CSV 是 lookup row 表格，TXT 是 CLI 摘要，Markdown 和 HTML 用于人工阅读。本版没有浏览器页面或训练曲线，所以 `f/1258/图片/README.md` 说明不生成截图。

真实运行结果为 `status=pass`、`decision=model_capability_route_promotion_release_readiness_receipt_index_ready`、`receipt_index_ready=True`、`index_id=route-promotion-release-readiness-receipt-index-v1258`、`lookup_scope=bounded_route_promotion_release_readiness_receipt_lookup_only`、`entry_count=1`、`lookup_key_count=1`、`lookup_ready=True`、`consumer_name=release-readiness-index-builder`、`route_id=objective_level_contrast`、`granted_scope=bounded_route_promotion_release_governance_only`、`source_digest_count=3`、`promotion_ready=False`。这说明 v1258 成功把 v1257 receipt 固定成一条可查 index row，同时没有打开 promotion。

## 测试覆盖

目标测试有五个用例。root facade export 测试确认 builder 和 writer 已经稳定暴露到 `minigpt` facade。ready index 测试通过真实构造链生成 granted receipt，再构建 index，断言 status、decision、ready flag、lookup key count、route、source digest count、promotion flag、receipt digest 长度和 exit code。这保护的是完整成功路径。

ungranted receipt failure 测试把 v1257 receipt 的 requested scope 改成 `production_model_release`，使 downstream receipt fail，然后再尝试索引。测试断言 `downstream_receipt_passed` 和 `receipt_status_granted` 都会失败，并且 index summary 的 `model_quality_claim` 变成 `not_claimed`。这证明 index 层不会把失败 receipt 包装成可用 lookup row。

missing receipt file failure 测试传入不存在的 receipt path，断言 `downstream_receipt_file_exists` 和 `downstream_receipt_digest_present` 失败。这个用例保护的是 evidence chain 的文件锚点：即使内存里的 receipt dict 看起来 pass，如果文件不存在或无法 digest，也不能发布 index。

outputs/CLI 测试覆盖目录定位、五种输出、CLI 参数、`--require-index-ready`、TXT 摘要、Markdown Lookup Rows 和 HTML 页面。`tests/test_public_api_policy.py` 则保护 public API 预算变化，确认新增两个 facade 出口是有意的。

## 链路角色

v1258 位于 v1257 receipt 和后续 index review 之间。它的输出比 v1257 更适合被后续治理工具消费，因为它已经把 receipt 收束为 lookup row，并把 digest、scope、route 和 blocked uses 放在稳定位置。后续如果做 v1259，合理方向就是 review 这个 index：检查 index digest、lookup row、receipt path、bounded scope、source digest count 和 promotion boundary 是否一致。

这一版也回应了项目之前暴露出的命名和膨胀问题。历史 publication receipt 链路里出现过非常长的重复 `receipt_index` 文件名。v1258 没有复刻那个命名，而是使用较短的 `model_capability_route_promotion_release_readiness_receipt_index`，同时保持 module、artifact、CLI、test 的职责拆分。这样既延续治理链路，又不继续扩大可维护性债务。

## 一句话总结

v1258 把 v1257 的 granted downstream receipt 固定成一条带 digest、lookup key、bounded scope 和 blocked uses 的 receipt index，让发布治理链路从“可消费 receipt”推进到“可检索 receipt index”。
