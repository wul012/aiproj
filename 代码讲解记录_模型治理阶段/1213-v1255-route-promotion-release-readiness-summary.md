# v1255 route-promotion release readiness summary 代码讲解

## 本版目标与边界

v1255 的目标是把 route-promotion 这条模型治理链路从“若干单点证据都已经通过”推进到“可以给人和后续脚本读取的一份发布就绪汇总”。在这之前，链路里已经有 v795 的 release packet、v796 的 release packet review、v800 的 governance snapshot。它们分别解决不同层面的问题：packet 负责把 portfolio、regression monitor 和 gate 打成包；review 负责检查这个包没有把范围放大；governance snapshot 负责把经过索引和 contract check 的 route card 变成可供下游治理使用的只读快照。问题是，这三份证据分散存在时，人要判断“这一组证据能不能作为一次 bounded route promotion 的发布依据”，仍然需要手工跨文件核对 status、decision、route id、boundary、claim 和 downstream policy。v1255 新增的 `model_capability_route_promotion_release_readiness_summary` 正是为了解决这个聚合判断。

本版明确不做三件事。第一，它不重新训练模型，不声称模型能力有新增提升；它消费的是已有治理证据，不是新的能力评测。第二，它不把 `seed_stable_pair_probe_route_accepted` 扩展成生产级模型质量声明；所有检查都围绕 `tiny_required_term_pair_probe_only` 和 `seed_stable_pair_probe_route` 前缀收束。第三，它不替代上游 packet、review、snapshot 的职责；任何上游失败、路径缺失、route 不一致、boundary 不一致，都会让 summary 自己失败，而不是“补救”上游证据。这个边界很重要，因为本项目的治理价值来自证据链的可追溯性，而不是把多个失败源揉成一个好看的最终结论。

## 前置链路

本版沿用模型能力阶段已经建立的 route-promotion 路线。`e/795` 里的 release packet 是第一层发布包，它确认 portfolio、regression monitor、gate 三个输入都通过，且 evidence path 存在。`e/796` 的 release packet review 是第二层人工审查式约束，它要求 packet 的 review scope 仍是 `bounded_route_promotion_review_only`，boundary 不越过 `tiny_required_term_pair_probe_only`，model quality claim 仍以 pair-probe route 为范围。`e/800` 的 governance snapshot 是更靠后的治理快照，它消费 decision index 和 index contract check，确认 route card 已经 contract verified，并给出 bounded downstream policy。v1255 不重新构造这些上游材料，而是在运行证据里直接读取这些历史产物，生成 `f/1255/解释/model-capability-route-promotion-release-readiness-summary/` 下的 JSON、CSV、TXT、Markdown 和 HTML。

因此，这一版的价值不是“多一个报告文件”，而是把上游证据之间的关系显式编码成检查项。过去一个人要看 packet 的 `summary.active_routes`、review 的 `summary.active_routes`、snapshot 的 `summary.route_ids` 是否都是同一个 route；要看三者的 `boundary` 是否一致；要看 claim 有没有从 seed-stable pair probe 变成更大的生产质量声明；还要看 snapshot 的 downstream policy 是否允许下游 bounded governance。现在这些都变成结构化 `check_rows`，可以被 CLI、测试和后续治理脚本直接消费。

## 关键文件

`src/minigpt/model_capability_route_promotion_release_readiness_summary.py` 是本版核心模型。它提供文件名常量、三个 locator、通用 JSON reader、主构建函数 `build_model_capability_route_promotion_release_readiness_summary`、退出码函数 `resolve_exit_code`，以及内部的 route alignment、boundary/claim、source rows、check rows、summary、downstream policy 和 interpretation 生成逻辑。这个文件不写磁盘，不渲染 HTML，也不处理命令行参数；它只做纯数据判断，便于测试和后续复用。

`src/minigpt/model_capability_route_promotion_release_readiness_summary_artifacts.py` 是输出层。它把核心 report 渲染成文本、CSV、Markdown 和 HTML，并通过 `write_model_capability_route_promotion_release_readiness_summary_outputs` 一次性写出五种格式。CSV 选择写 `check_rows`，因为这份 summary 最有价值的机器可读部分就是每条检查是否通过；Markdown 和 HTML 则面向人阅读，先展示 status、decision、ready、handoff、route、boundary、claim、downstream scope，再列出 source rows 和 check rows。

`scripts/summarize_model_capability_route_promotion_release_readiness.py` 是 CLI 入口。它接收 `--release-packet`、`--release-packet-review`、`--governance-snapshot` 三个输入，这三个参数既可以是 JSON 文件，也可以是产物目录；locator 会把目录解析到约定文件名。CLI 支持 `--required-boundary`、`--out-dir`、`--require-pass` 和 `--force`。运行时先定位三个 JSON，再读入 report，调用核心构建函数，最后写出多格式产物并打印文本摘要和 outputs JSON。`--require-pass` 会在 summary status 非 pass 时返回失败退出码，这使它可以进入未来的 CI 或版本检查。

`tests/test_model_capability_route_promotion_release_readiness_summary.py` 是本版测试。它复用已有测试里的 `ready_release_packet` 和 `ready_snapshot_inputs` 构造真实形状的上游对象，再写出 review/snapshot 产物作为 summary 的输入路径。测试覆盖四类行为：根门面导出能拿到新 builder 和 writer；干净输入会得到 pass、ready、正确 route、正确 handoff 和 bounded downstream scope；route id 被篡改时会被 `active_routes_align` 阻断；artifact writer 和 CLI 都能写出 JSON/CSV/TXT/Markdown/HTML，并且文本、Markdown、HTML 都包含关键语义。

`src/minigpt/_root_lazy_exports_route_promotion.py` 和 `src/minigpt/_root_public_exports.py` 把新能力接进根门面。这样外部使用者可以通过 `minigpt.build_model_capability_route_promotion_release_readiness_summary` 和 `minigpt.write_model_capability_route_promotion_release_readiness_summary_outputs` 使用它，而不必记住内部模块名。这是小改动，但对项目工程化很重要：公共 API 的暴露面要清楚，不能每个功能都只靠深路径 import。

`f/1255/解释/` 是本版运行证据。真实 CLI 消费 `e/795`、`e/796`、`e/800` 后生成了 summary 的五种输出。因为本版是证据汇总型 CLI，没有网页交互和模型曲线，所以 `f/1255/图片/README.md` 明确说明不新增截图，证据重心在 JSON/CSV/TXT/Markdown/HTML。

## 核心数据结构

主 report 的顶层字段沿用项目治理报告的常见形状：`schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`check_rows`、`summary`、`interpretation`。新增的领域字段包括 `source_release_packet`、`source_release_packet_review`、`source_governance_snapshot`、`source_rows`、`source_summaries`、`route_alignment`、`boundary_claim` 和 `downstream_policy`。

`source_rows` 是三行 evidence 表，每行有 `kind`、`path`、`exists`。它的作用不是证明上游内容正确，而是证明 summary 消费的是可追溯文件，而不是内存里凭空传入的字典。`source_summaries` 保留三个上游 summary 的快照，方便读者或下游工具回溯 packet、review、snapshot 各自给出的摘要字段。

`route_alignment` 是本版最重要的结构之一。它从 packet/review 的 `summary.active_routes` 和 snapshot 的 `summary.route_ids` 抽取三组 route id，排序去重后比较三组集合。只有三者非空且完全一致，`aligned` 才会为 true，并把 `active_routes` 和 `route_count` 写入统一视图。这个设计避免了一个常见治理漏洞：三个证据都 pass，但它们其实指向了不同 route。这样的情况过去靠人工读文件才能发现，现在会被 `active_routes_align` 检查直接阻断。

`boundary_claim` 负责把三份证据的 boundary 和 claim 放到同一个结构里。它记录 `required_boundary`、三份输入的 `boundaries`、归一后的 `boundary`、`boundary_consistent`、三份 claim、归一后的 `model_quality_claim`、`claim_consistent` 和 `claim_bounded`。这里的 `claim_bounded` 不是简单比较某个固定字符串，而是要求 claim 以 `seed_stable_pair_probe_route` 开头。这和上游 route-promotion 代码保持一致：允许在 pair-probe route 这个边界内有不同后缀，但不允许扩大到生产模型质量、通用模型能力或其他更强声明。

`downstream_policy` 有两层含义。输入侧读取 governance snapshot 的 `downstream_policy`，检查它是否允许 bounded model capability governance。输出侧如果 summary 通过，则生成自己的 downstream policy：`allowed=True`、`allowed_scope=bounded_route_promotion_release_governance_only`，并附带 route ids、boundary、claim 和 reason。注意这里的 scope 比 snapshot 更具体，它不是说“模型可以发布”，而是说“这份 release readiness summary 可以作为 bounded route-promotion release governance evidence 被消费”。

## 核心流程

CLI 的运行流程很短，但每一步都有边界意义。首先，三个 locator 函数把传入路径解析成确定 JSON 文件：release packet 目录会被补成 `model_capability_route_promotion_release_packet.json`，review 目录会被补成 `model_capability_route_promotion_release_packet_review.json`，snapshot 目录会被补成 `model_capability_route_promotion_governance_snapshot.json`。这让命令行既适合人输入目录，也适合脚本传文件。

其次，`read_json_report` 读取并确认 JSON 顶层必须是 object。这个项目里治理报告都以 dict 为根，若输入是 list 或其他类型，就不能参与 contract-style 的字段检查。随后 builder 抽出三个 summary、snapshot downstream policy、source rows、route alignment 和 boundary claim。它不会立即决定 pass/fail，而是先构造完整检查上下文。

第三，`_checks` 生成检查清单。前六条检查分别确认 packet、review、snapshot 的 `status` 和 `decision/ready flag`。这能防止某个上游报告只是 `status=pass` 但 decision 不对，或者 decision 对但 ready flag 没有同步。第七条检查 source files 是否存在。第八、第九条检查 route 是否对齐且非空。第十到第十二条检查 boundary 和 claim：boundary 必须是 `tiny_required_term_pair_probe_only`，claim 必须一致且 bounded。第十三条把三个上游 summary 的 `failed_check_count` 相加，要求为零。最后两条检查 governance snapshot 的 downstream policy 是否 allowed，且 allowed scope 是否仍为 `bounded_model_capability_governance_only`。

第四，builder 从 check rows 派生 `issues` 和 `status`。只有没有任何 failed row，summary 才是 pass。`summary` 字段会写入 `release_readiness_summary_ready`、`handoff_status`、`active_route_count`、`active_routes`、`boundary`、`model_quality_claim`、`evidence_count`、passed/failed check count 和 `next_step`。如果 status 失败，`model_quality_claim` 会被降为 `not_claimed`，避免失败产物还保留看似可用的质量声明。

最后，artifact writer 把 report 写出为五种格式。JSON 是完整证据；CSV 适合机器扫 check rows；TXT 适合 CLI 读；Markdown 适合版本说明和代码审阅；HTML 适合本地打开检查。五种格式来自同一 report，不存在多套口径。

## 关键检查解释

`release_packet_ready`、`release_packet_review_ready`、`governance_snapshot_ready` 是三条上游门禁。它们同时看 decision 和 summary ready flag，目的是防止只靠一个字段过关。治理系统里常见的问题是状态字段被手工改成 pass，但 summary 里的 ready flag、decision 或 failed count 没有同步；本版把这些组合起来看，降低伪通过的风险。

`active_routes_align` 是跨证据一致性检查。它要求 packet、review、snapshot 都谈论同一批 route。本版的真实运行中三者都指向 `objective_level_contrast`。如果 snapshot 的 route id 被改成 `different_route`，测试会确认 summary 失败，并在 issues 里出现 `active_routes_align`。这条测试保护的是一个真实工程问题：多阶段治理产物的文件名和 status 都可能正确，但如果引用对象错位，最终结论就不能发布。

`boundary_scoped` 和 `claim_bounded` 是防止能力声明膨胀的核心。项目规则反复强调，aiproj 的治理工具不能被说成生产模型质量证明。v1255 继续这个边界：boundary 必须是 `tiny_required_term_pair_probe_only`；claim 必须以 `seed_stable_pair_probe_route` 开头；输出 downstream scope 也只允许 `bounded_route_promotion_release_governance_only`。换句话说，这版让发布治理证据更好读，但没有把 toy-scale pair-probe route 变成生产能力承诺。

`source_checks_clean` 检查三个上游 summary 的 failed check count 总和。它不是替代上游的详细检查，而是确认上游自己没有公开失败项。这样设计的好处是 summary 不需要复制上游每个检查细节，避免耦合过深；同时也不会忽略上游暴露出来的失败状态。

`downstream_scope_bounded` 把 governance snapshot 的下游策略接进来。只有 snapshot 自己允许 bounded model capability governance，下游 release readiness summary 才允许发布为 bounded route-promotion release governance evidence。这个传递关系让 evidence chain 更像软件工程里的 contract handoff：上游没有授权，下游不能擅自授权。

## 测试覆盖

本版目标测试为 `tests/test_model_capability_route_promotion_release_readiness_summary.py`，共 4 个用例。第一个用例验证根门面导出，确保 `minigpt` 包可以懒加载新 builder 和 writer。第二个用例构造完整 ready 输入，断言 status、decision、ready flag、active route、handoff status、downstream scope 和退出码。第三个用例把 snapshot 的 route ids 改成不同 route，确认 report 失败、issues 包含 `active_routes_align`，且失败时 summary 不再保留 model quality claim。第四个用例同时验证 locator、writer 和 CLI：目录输入能解析到 JSON，writer 能输出五种格式，CLI 在 `--require-pass` 下正常退出，文本/Markdown/HTML 都包含关键可读信号。

除了目标测试，还进行了 py_compile，确保新核心模块、artifact 模块、CLI 和测试模块语法可编译。真实运行证据也通过 CLI 生成：命令消费 `e/795`、`e/796`、`e/800`，输出到 `f/1255/解释/model-capability-route-promotion-release-readiness-summary/`，结果为 `status=pass`、`decision=model_capability_route_promotion_release_readiness_summary_ready`、`failed_count=0`、`active_routes=objective_level_contrast`、`boundary=tiny_required_term_pair_probe_only`、`model_quality_claim=seed_stable_pair_probe_route_accepted`。

## 链路角色

v1255 在项目里扮演的是“上层发布就绪证据聚合器”。它位于 packet/review/snapshot 之后，downstream guard 或 consumer plan 之前。更直白地说，它把“这几个证据文件都存在且各自通过”升级成“这些证据文件指向同一条 route，边界一致，claim 一致，且被 governance snapshot 授权为 bounded downstream evidence”。这正是软件工程项目从脚本集合走向治理系统时需要的能力：把隐含人工判断变成显式合同。

它也延续了前面几版工程保养的成果。测试现在通过共享 test package bootstrap 能稳定导入；新增测试不再写手工 sys.path；根门面导出保持集中管理；artifact 输出遵循项目已有 JSON/CSV/TXT/Markdown/HTML 形状。功能版和规范化不是两条相互排斥的线：v1255 的功能能成立，正是因为前面把测试入口、导出和守门规则收稳了。

## 一句话总结

v1255 把分散的 route-promotion packet、review 和 governance snapshot 收束成一份可测试、可发布、可追溯且不放大模型质量声明的 bounded release-readiness summary。
