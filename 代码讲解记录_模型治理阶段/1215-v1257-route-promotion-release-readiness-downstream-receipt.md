# v1257 route-promotion release readiness downstream receipt 代码讲解

## 本版目标与边界

v1257 接在 v1255 和 v1256 后面，做的是模型治理链路里一个很小但很关键的动作：把“已经通过 contract check 的 release readiness summary”变成“可以被一个具体下游消费者接收的 receipt”。v1255 的职责是把真实的上游证据 `e/795`、`e/796`、`e/800` 汇总成 route-promotion release readiness summary；v1256 的职责是检查这份 summary 是否仍然结构自洽、source digest 可复验、route/boundary/claim/scope 没有漂移；v1257 的职责则更靠后，它不再重新做 summary，也不再重新解释上游 evidence，而是问一个下游交接问题：某个 consumer 是否可以在指定 route 上、以指定 bounded scope 消费这份已经检查过的 release readiness 证据。

这版明确不做模型训练，不做新的能力实验，不扩大 `seed_stable_pair_probe_route_accepted` 的含义，也不把 toy-scale pair-probe 的结论包装成生产模型质量声明。它只记录一个 bounded downstream handoff。成功 receipt 的授权范围是 `bounded_route_promotion_release_governance_only`，来源范围仍然必须是 `bounded_model_capability_governance_only`，边界仍然必须是 `tiny_required_term_pair_probe_only`。如果这些条件中任意一项变宽，receipt 就不能 granted，而是 fail，并把能力声明降为 `not_claimed` 或不授予 route。

这样设计的原因是：v1256 只能说明“contract check 通过了”，但还没有说明“谁要消费它、消费哪条 route、允许做什么、不允许做什么”。在真实的软件工程治理里，生成报告、检查报告、授权消费报告是三个不同的责任点。v1257 补上的就是第三个责任点，避免后续 index、bundle、release note 或人工交接直接拿 v1256 的检查结果进行口头扩写。

## 关键文件与职责

`src/minigpt/model_capability_route_promotion_release_readiness_downstream_receipt.py` 是本版核心逻辑。它定义 receipt 产物的文件名常量、允许的 scope、来源 scope、被阻止的用途，以及四个对外函数：`locate_route_promotion_release_readiness_summary_check`、`read_json_report`、`build_model_capability_route_promotion_release_readiness_downstream_receipt` 和 `resolve_exit_code`。其中 builder 是主函数，输入 v1256 的 contract-check report，再加上 `consumer_name`、`route_id`、`requested_scope`、`required_boundary` 和可选的 source path，输出完整 receipt report。

`src/minigpt/model_capability_route_promotion_release_readiness_downstream_receipt_artifacts.py` 是输出层。它把同一份 report 渲染成 TXT、CSV、Markdown、HTML，并通过统一 writer 写出 JSON、CSV、TXT、Markdown、HTML 五种格式。TXT 面向 CLI 快速查看，CSV 面向 check row 审查，Markdown 和 HTML 面向人工阅读，JSON 是后续脚本消费时最完整的证据。

`scripts/build_model_capability_route_promotion_release_readiness_downstream_receipt.py` 是命令行入口。脚本层只负责解析参数、定位输入、读取 JSON、调用 builder、写出 artifact、打印摘要和处理 `--require-receipt-ready` 退出码。领域判断没有放在脚本里，而是留在 package module 中，这符合项目后期的规范化方向：active scripts 要薄，业务逻辑要能被测试和复用。

`tests/test_model_capability_route_promotion_release_readiness_downstream_receipt.py` 是本版测试。它复用 v1256 测试里的 ready checked summary 构造函数，先构造一份通过检查的 release readiness summary check，再验证 downstream receipt 的 granted path、unknown route failure、unbounded requested scope failure、writer 输出和 CLI 接线。测试还验证 root facade export，说明这两个新符号是有意提升为稳定 route-promotion governance API，而不是偶然暴露。

`src/minigpt/_root_lazy_exports_route_promotion.py`、`src/minigpt/_root_public_exports.py`、`tests/test_public_api_policy.py` 和 `docs/public-api.md` 一起记录 public API 变化。本版新增两个稳定出口：`build_model_capability_route_promotion_release_readiness_downstream_receipt` 和 `write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs`。对应预算从 v1256 的 all-export 282/lazy-export 312 提高到 284/314，并在 public API 文档中说明这是有意提升。

## 核心数据结构

downstream receipt report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`source_release_readiness_summary_check`、`source_release_readiness_summary_check_digest`、`request`、`source_check_summary`、`source_downstream_policy`、`source_digest_rows`、`check_rows`、`receipt`、`summary` 和 `interpretation`。

`request` 记录这次下游消费请求本身，包括 `consumer_name`、`route_id`、`requested_scope` 和 `required_boundary`。这是 v1257 和 v1256 最大的区别之一：v1256 检查一份 summary 自己是否健康，v1257 必须把消费方写进证据里。没有 consumer，就无法把这份 receipt 当作后续 index 或 bundle 的明确来源。

`source_check_summary` 直接来自 v1256 的 `summary` 字段。这里保留 `contract_check_ready`、`source_summary_ready`、`active_routes`、`boundary`、`model_quality_claim`、`source_digest_count` 等信息，是为了让下游不用重新打开 v1256 JSON 的多个位置，也能看到 receipt 授权的依据。

`source_downstream_policy` 来自 v1256 的 downstream policy。v1257 不只检查自己传入的 requested scope，也检查来源 policy 是否允许 `bounded_route_promotion_release_governance_only`，并检查来源 scope 是否仍然是 `bounded_model_capability_governance_only`。这样可以防止两种错误：一种是下游请求自己变宽，另一种是上游 policy 被改宽或改窄但 receipt 没有发现。

`source_digest_rows` 是 v1256 对 v795、v796、v800 三份上游证据计算过的 digest 行。v1257 不重新计算这些上游文件 digest，因为它消费的是“已经被 v1256 检查过的 report”；但它会要求这些 digest 行存在、数量匹配、每行有 SHA-256，并且对 v1256 check JSON 本身计算 `source_release_readiness_summary_check_digest`。这相当于把证据链锁在两层：上游三份源证据的 digest 由 v1256 给出，v1256 检查产物本身的 digest 由 v1257 记录。

`receipt` 是本版最重要的新结构。成功时它包含 `receipt_id`、`receipt_status=granted`、`consumer_name`、`route_id`、`requested_scope`、`granted_scope`、`boundary`、`model_quality_claim`、`source_check_path`、`source_check_digest`、`source_summary_ready`、`source_digest_count`、`source_digest_rows`、`blocked_uses`、`policy_reason` 和 `next_step`。失败时，`receipt_status` 会变成 `blocked`，`route_id` 不授予，`granted_scope` 变成 `none`，`model_quality_claim` 变成 `not_claimed`，`source_digest_rows` 也不会继续作为 granted evidence 暴露。

`blocked_uses` 是一个显式边界字段，不是注释。它列出 `production_model_quality_claim`、`unbounded_release_promotion`、`training_data_reuse_proof`、`model_capability_claim_beyond_pair_probe_route`。这让下游消费者即使只读 receipt，也能看到“这份 receipt 不能被拿去做什么”。对于治理项目来说，这类负面边界和正面授权同样重要。

## 核心流程

CLI 运行时先调用 locator。`locate_route_promotion_release_readiness_summary_check` 支持用户传目录或文件；如果传目录，就补上固定文件名 `model_capability_route_promotion_release_readiness_summary_check.json`。然后 `read_json_report` 读取 JSON，并确认顶层是 object，避免数组或字符串被误当成 report。

builder 开始后，先从输入 report 里取出 `summary`、`downstream_policy`、`source_digest_rows` 和 `check_rows`。这些读取都使用 `report_utils` 里的 `as_dict`、`list_of_dicts`、`string_list` 等 helper，避免直接相信外部 JSON 的类型。接着 `_check_rows` 生成本版所有检查项。

检查项分成几组。第一组检查请求自身：`consumer_name_present` 和 `route_id_requested` 确认 receipt 有消费方和 route。第二组检查 v1256 report 本身：`summary_check_passed`、`summary_check_decision_ready`、`contract_check_ready`、`source_failed_count_zero`、`source_check_rows_clean` 确认 source check 是通过状态，decision 是正确的 ready decision，failed count 为零，内部 check rows 全部 pass。第三组检查 route 和 boundary：`route_id_in_checked_summary` 要求请求 route 在 v1256 的 active routes 中，`boundary_required` 要求边界仍然是 required boundary。第四组检查 claim 和 source digest：`claim_bounded` 要求 claim 仍以 `seed_stable_pair_probe_route` 开头，`source_digest_count_matches` 和 `source_digests_present` 要求 digest 数量和内容完整。第五组检查下游 scope：`requested_scope_allowed`、`downstream_scope_matches`、`source_scope_bounded`、`downstream_policy_allowed` 确认请求 scope、source policy 和 source scope 都没有变宽。

所有 check rows 生成后，builder 根据失败行派生 `status`、`failed_count` 和 `issues`。如果没有失败，`decision` 是 `model_capability_route_promotion_release_readiness_downstream_receipt_granted`；否则是 `fix_model_capability_route_promotion_release_readiness_downstream_receipt`。这个 decision 命名刻意与 v1255 summary ready、v1256 contract check passed 区分开，避免后续脚本把三种产物混在一起。

然后 `_receipt` 根据 status 生成 granted 或 blocked receipt。成功 receipt 会保留 route、scope、boundary、claim 和 source digest rows；失败 receipt 则不授予 route，不保留 granted scope，不声明模型能力。最后 `_summary` 给人工和脚本提供一个短视图，`_interpretation` 写出结论含义和下一步。CLI 如果带了 `--require-receipt-ready`，就用 `resolve_exit_code` 把 fail 转成退出码 1。

## Artifact 与只读证据

本版真实证据写入 `f/1257/解释/model-capability-route-promotion-release-readiness-downstream-receipt/`。JSON 是最终证据，包含完整字段、request、source check digest、source digest rows、check rows、receipt、summary 和 interpretation。CSV 只展开 check rows，适合快速查看哪一项失败。TXT 是命令行摘要，包含 `status`、`decision`、`downstream_receipt_ready`、`receipt_status`、`consumer_name`、`route_id`、`granted_scope`、`boundary`、`model_quality_claim`、`source_digest_count` 和 `next_step`。Markdown 和 HTML 面向人读，包含 Source Digests 表和 Checks 表。

真实运行结果为 `status=pass`、`decision=model_capability_route_promotion_release_readiness_downstream_receipt_granted`、`downstream_receipt_ready=True`、`receipt_status=granted`、`consumer_name=release-readiness-index-builder`、`route_id=objective_level_contrast`、`granted_scope=bounded_route_promotion_release_governance_only`、`boundary=tiny_required_term_pair_probe_only`、`model_quality_claim=seed_stable_pair_probe_route_accepted`、`source_digest_count=3`。这说明 v1257 成功把 v1256 的 checked summary 授权给一个具体的 downstream consumer，但没有越过 bounded release governance 的边界。

`f/1257/图片/README.md` 说明本版没有截图。原因很简单：这是 CLI 和文件证据版本，没有浏览器页面、训练曲线或交互 UI。为了避免制造空截图，证据以 JSON/CSV/TXT/Markdown/HTML 和本说明为准。

## 测试覆盖

目标测试 `tests/test_model_capability_route_promotion_release_readiness_downstream_receipt.py` 有五个用例。root facade export 测试保证 builder 和 writer 能从 `minigpt` 懒加载导出，说明 public API 表和 lazy export 表都接通。granted path 测试用 ready checked summary 构造一个合法 source report，再请求 consumer `release-readiness-index-builder` 和 route `objective_level_contrast`，断言 status、decision、`downstream_receipt_ready`、granted scope、source digest count 和 blocked uses。这个测试保护的是成功链路不会只生成表面 pass，而是真的把 receipt 字段写完整。

unknown route 测试把 route 改成不存在的 `missing_route`，断言 `route_id_in_checked_summary` 失败、`model_quality_claim` 变成 `not_claimed`，且 `resolve_exit_code(..., require_receipt_ready=True)` 返回 1。这个用例保护 route 授权边界，防止下游拿一份通过检查的 summary 去消费未被 summary 覆盖的 route。

unbounded requested scope 测试把 requested scope 改成 `production_model_quality_claim`，断言 `requested_scope_allowed` 失败。这个用例保护的是最容易发生的语义漂移：source check 本身可能是 pass，但如果消费方请求的用途变宽，receipt 仍然必须拒绝。

output/CLI 测试覆盖 locator、writer 五种输出、CLI 参数、`--require-receipt-ready`、TXT 摘要、Markdown Source Digests 表和 HTML 产物。它证明本版不只是 pure function 能返回 dict，实际脚本入口和 artifact 写出也能工作。`tests/test_public_api_policy.py` 则保护新增稳定出口的预算变化，避免 root facade 悄悄膨胀。

## 链路角色

v1257 在链路中的位置是：v1255 summary -> v1256 contract check -> v1257 downstream receipt。它不是 release readiness 的源头，也不是 contract check 的替代品，而是 downstream governance consumption 的交接凭证。后续如果要继续做 receipt index、index review、release bundle、tag note 或发布清单，这份 receipt 比直接消费 v1256 check 更合适，因为它已经写清 consumer、route、granted scope、blocked uses、source check digest 和 source digest rows。

从软件工程角度看，这版也是项目继续规范化的一小步。之前很多治理产物已经能生成和检查，但“检查通过后谁可以用”仍然容易靠 README 或人工约定来表达。v1257 把这个约定变成代码、测试、CLI 和版本化证据。这种做法看起来比直接改文档慢一点，但它降低了后续证据链膨胀时的歧义。

## 一句话总结

v1257 把通过 v1256 contract check 的 route-promotion release readiness evidence，收束成一份带 consumer、route、bounded scope、source digest 和 blocked uses 的下游 receipt，让发布治理链路从“检查通过”推进到“可被指定下游有边界地消费”。
