# v1256 route-promotion release readiness summary contract check 代码讲解

## 本版目标与边界

v1256 接在 v1255 后面，目标是把“发布就绪 summary 已经生成”再推进一步，变成“这份 summary 在下游消费前可以被独立校验”。v1255 已经把 v795 release packet、v796 release packet review、v800 governance snapshot 聚合成一份 release readiness summary，解决了人工跨文件核对 route、boundary、claim 和 downstream policy 的问题。但如果后续脚本、文档或人工流程要继续消费这份 summary，还需要一层更像 contract check 的东西：它不重新生成 summary，不替上游做判断，而是验证 summary 自己的结构、计数、source rows、route alignment、boundary claim、downstream scope 仍然一致，并确认 summary 指向的三份上游源文件仍然存在、可读、可计算摘要。

本版不做模型训练，也不改变 v1255 的判断结果；它只检查 v1255 的产物是否仍然可信。它也不把 `seed_stable_pair_probe_route_accepted` 扩大成生产模型质量声明。所有字段都继续收束在 `tiny_required_term_pair_probe_only` 和 `bounded_route_promotion_release_governance_only` 范围内。更具体地说，v1256 的 contract check 只能证明“这份 release readiness summary 可作为 bounded route-promotion release governance evidence 被下游使用”，不能证明模型已经具备生产质量，也不能证明 toy-scale pair-probe 之外的能力。

## 前置链路与输入输出

v1256 的唯一输入是 v1255 的 `model_capability_route_promotion_release_readiness_summary.json`。这份 JSON 里包含 `source_rows`，指向 `e/795`、`e/796`、`e/800` 三份真实上游证据；包含 `route_alignment`，说明 packet/review/snapshot 都指向 `objective_level_contrast`；包含 `boundary_claim`，说明 boundary 与 claim 一致且 bounded；包含 `downstream_policy`，说明下游使用范围是 `bounded_route_promotion_release_governance_only`。v1256 不再读 packet/review/snapshot 的语义内容，但会读取这些源文件字节，计算 SHA-256 digest，证明 source rows 不只是字符串，而是当前工作区里可追溯、可摘要的证据文件。

输出仍然遵循项目治理产物习惯：JSON 是完整证据，CSV 是 check rows，TXT 是 CLI 摘要，Markdown 和 HTML 面向人工阅读。真实运行证据写入 `f/1256/解释/model-capability-route-promotion-release-readiness-summary-check/`，并在 `f/1256/解释/说明.md` 中记录输入、输出和边界。因为本版没有网页交互或训练曲线，所以 `f/1256/图片/README.md` 明确说明没有截图。

## 关键文件与职责

`src/minigpt/model_capability_route_promotion_release_readiness_summary_check.py` 是核心逻辑。它定义 check 产物的五个文件名常量、`locate_route_promotion_release_readiness_summary`、`read_json_report`、`build_model_capability_route_promotion_release_readiness_summary_check` 和 `resolve_exit_code`。主函数先抽取 v1255 summary 的 `summary`、`route_alignment`、`boundary_claim`、`downstream_policy` 和 `source_rows`，再调用 `_source_digest_rows` 计算每个 source row 的存在性和 SHA-256，最后生成 `check_rows`、`issues`、`summary` 与 `interpretation`。

`src/minigpt/model_capability_route_promotion_release_readiness_summary_check_artifacts.py` 是输出层。它提供 text、CSV、Markdown、HTML 四种渲染函数和一个统一 writer。Markdown 和 HTML 增加了 `Source Digests` 表，列出 kind、exists、sha256 和 path。这样读者不用打开 JSON，也能知道 contract check 不是只看 summary 字段，而是实际触碰了上游文件。

`scripts/check_model_capability_route_promotion_release_readiness_summary.py` 是 CLI 入口。它接收 `--release-readiness-summary`，既可传 JSON 文件，也可传 summary 输出目录；locator 会自动补 `model_capability_route_promotion_release_readiness_summary.json`。CLI 支持 `--required-boundary`、`--out-dir`、`--require-pass` 和 `--force`。这与相邻 route-promotion 脚本保持一致：脚本层只做参数、读写和退出码，不把领域判断塞进 CLI。

`tests/test_model_capability_route_promotion_release_readiness_summary_check.py` 是本版测试。它复用 v1255 测试里的 ready summary 构造函数，先生成 summary JSON，再做 contract check。测试覆盖根门面导出、干净 pass、源文件缺失 failure、claim 扩大 failure、artifact writer 和 CLI。源文件缺失测试故意把 source row 的 path 改成不存在文件，同时保留 `exists=True`，用于证明 v1256 不盲信 v1255 的 source row 标记，而是自己重新检查文件系统并尝试 digest。claim 扩大测试把 summary 和 boundary_claim 改成 `production_model_quality`，确认 `claim_bounded` 会失败，并且失败 summary 会降为 `not_claimed`。

`src/minigpt/_root_lazy_exports_route_promotion.py`、`src/minigpt/_root_public_exports.py`、`tests/test_public_api_policy.py` 和 `docs/public-api.md` 共同记录 public API 变化。因为相邻的 decision index check 已经是根门面能力，v1256 也把 `build_model_capability_route_promotion_release_readiness_summary_check` 和 `write_model_capability_route_promotion_release_readiness_summary_check_outputs` 提升为稳定 route-promotion governance API。对应预算从 v1255 的 all-export 280/lazy-export 310 提高到 282/312，并在 public API 文档里写明这是有意提升，而不是无意膨胀。

## 核心数据结构

check report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`source_summary`、`source_summary_exists`、`source_summary_digest`、`source_summary_summary`、`route_alignment`、`boundary_claim`、`downstream_policy`、`source_rows`、`source_digest_rows`、`check_rows`、`summary` 和 `interpretation`。

`source_summary_digest` 是 v1256 相比 v1255 新增的一个关键证据点。它对输入 summary JSON 本身计算 SHA-256。`source_digest_rows` 则对 v1255 summary 指向的三份上游源文件计算 SHA-256。每行包括 `kind`、`path`、`exists` 和 `sha256`。这让下游拿到 check JSON 后，不只知道“source path 存在”，还知道当时检查过的源文件内容摘要是什么。后续如果要做更强的锁定或 drift 检查，可以直接以这些 digest 为入口。

`check_rows` 是 contract check 的主体。它既检查顶层状态，也检查内部一致性。顶层状态包括 `summary_passed`、`summary_decision_ready`、`summary_ready_flag`、`summary_failed_count_zero`、`summary_issues_empty`。内部一致性包括 `summary_check_rows_clean`、`summary_check_counts_match`、`source_rows_present`、`source_kinds_match`、`source_rows_mark_existing`、`source_files_digestible`、`source_digest_kinds_match`、`source_evidence_count_matches`。领域边界包括 `active_routes_align`、`active_routes_match_summary`、`active_route_count_matches`、`boundary_consistent`、`boundary_required`、`claim_consistent`、`claim_bounded`、`claim_matches_summary`、`handoff_ready`、`downstream_policy_allowed`、`downstream_scope_bounded` 和 `source_downstream_scope_bounded`。

`summary` 字段是人和脚本最常读的缩略视图。它包含 `contract_check_ready`、`source_summary_ready`、`active_route_count`、`active_routes`、`boundary`、`model_quality_claim`、`source_evidence_count`、`source_digest_count`、`passed_check_count`、`failed_check_count` 和 `next_step`。如果 status 不是 pass，`model_quality_claim` 会被写成 `not_claimed`。这个规则延续 v1255：失败产物不能保留看起来可用的能力声明。

## 核心流程

运行 CLI 时，第一步是定位 v1255 summary JSON。若用户传的是目录，locator 补上固定文件名；若传的是文件，直接使用。第二步读取 JSON，并确认顶层必须是 object。第三步进入 builder：抽取 summary 子结构，计算 source digest rows，生成所有 check rows。第四步根据 failed rows 派生 status、decision、issues 和 summary。第五步 artifact writer 写出五种格式，CLI 打印文本摘要与 outputs JSON；如果传了 `--require-pass` 且 status 不是 pass，就返回退出码 1。

这个流程刻意保持“检查者”角色。它不会根据 source rows 重新构建 v1255 summary，因为那会把 v1256 变成另一个 summary builder，导致职责重叠。它做的是 contract check：v1255 自己说的 ready、route、boundary、claim、downstream scope、check count 是否自洽，source rows 是否仍然存在并可摘要。这样的层次更适合治理链路：生成者给出报告，检查者验证报告，下游再消费检查过的报告。

## 测试与真实证据

本版目标测试 `tests/test_model_capability_route_promotion_release_readiness_summary_check.py` 共 5 个用例。根门面导出测试保证新 builder/writer 可从 `minigpt` 懒加载。pass 测试确认 ready summary 能通过 contract check，且 `source_digest_count=3`。源缺失测试证明 check 会重新访问文件系统。claim 扩大测试证明 bounded claim 不能被绕过。output/CLI 测试确认目录定位、多格式输出、`--require-pass`、文本、Markdown 和 HTML 都接通。

真实运行命令消费 `f/1255/解释/model-capability-route-promotion-release-readiness-summary/`，输出到 `f/1256/解释/model-capability-route-promotion-release-readiness-summary-check/`。结果为 `status=pass`、`decision=model_capability_route_promotion_release_readiness_summary_contract_check_passed`、`contract_check_ready=True`、`source_summary_ready=True`、`active_routes=objective_level_contrast`、`boundary=tiny_required_term_pair_probe_only`、`model_quality_claim=seed_stable_pair_probe_route_accepted`、`source_digest_count=3`。

## 链路角色

v1256 位于 v1255 summary 之后、后续 downstream/consumer 之前。它把 v1255 的“发布就绪汇总”变成“可被校验过的发布就绪汇总”。这听起来只多了一层，但在治理系统里很关键：生成报告和校验报告是两个不同职责。生成报告负责组织结论，校验报告负责确认结论没有被字段漂移、路径丢失、claim 放大或 downstream scope 放大破坏。v1256 让这条 route-promotion release governance 链路更接近真正的软件工程证据链。

## 一句话总结

v1256 为 v1255 的 route-promotion release readiness summary 增加了一层可复验、带源文件 digest、保持 bounded claim 的 contract check。
