# v1129 publication receipt 代码讲解

## 本版目标和边界

v1129 的目标，是把 v1128 已经完成 review 的 receipt index 再记录成一份新的 downstream lookup-only receipt。换句话说，v1128 负责回答“上一版索引是否仍然适合被下游查询”，v1129 负责回答“这个已经被 review 过的索引，是否可以作为新的只读收据交给下游治理消费方”。这两个问题看起来接近，但边界不一样：review 偏向审核既有索引，receipt 偏向建立新的消费凭据。v1129 正是在这个边界上做了一次收束。

本版不做三件事。第一，不做模型质量提升，不训练新的 tiny GPT，不生成新的 checkpoint，不声明困惑度、生成质量或 benchmark 指标变好。第二，不做 production promotion，不把任何 receipt、index、review 或 check 的 pass 状态解释为模型可以进入生产。第三，不创建新的治理链大方向，只复用 v1125 到 v1128 已经形成的 receipt、contract-check、index、review 节奏，把本轮五版闭环收在一份新的 receipt 上。

这种设计符合 aiproj 当前“模型治理阶段”的定位。项目已经不只是一个 MiniGPT 训练脚本集合，而是在训练、评估、交接、收据、索引、复核、归档之间建立可追溯的证据链。治理链的价值不是替代模型能力，而是避免能力证据在版本推进中丢失、漂移或被误读。v1129 继续沿用 `downstream_governance_lookup_only` 这个使用范围，就是为了让消费方明确知道：这份产物可以用于下游治理查询，可以用于定位 source evidence，可以用于后续 contract check，但不能作为模型上线许可。

## 前置路线和本版位置

本版直接承接 v1128。v1125 先把 v1124 的 review 记录成 receipt，v1126 对 v1125 receipt 做 contract check，v1127 把 v1125 receipt 与 v1126 check 建成 index，v1128 再 review 这个 index。到 v1129 时，项目回到 receipt 节点，把 v1128 的 review 记录成一份新的 lookup-only receipt。这样五版形成一个完整小环：

```text
v1125 receipt
v1126 receipt contract check
v1127 receipt index
v1128 receipt index review
v1129 receipt
```

这个小环不是为了无限堆版本，而是为了验证治理产物之间的可消费关系是否稳定。每一版都要求读取真实上游 JSON，而不是只在测试里构造对象；每一版都写出 JSON、CSV、text、Markdown、HTML 多种格式；每一版都保留运行截图和解释，方便后续人工审阅。v1129 的输入是 `f/1128/解释/receipt-index-review-v1128`，输出是 `f/1129/解释/receipt-v1129`，截图归档在 `f/1129/图片/v1129-receipt.png`。

从路线角色看，v1129 是“被 review 的索引到新 receipt”的转换层。它不重新判断 v1127 index 的每一个字段，也不重新执行 v1126 contract check 的 rebuild 逻辑，而是检查 v1128 review 是否已经把这些关键事实保留下来，并确认这些事实仍然满足 receipt 记录的最低条件。这样可以避免重复实现所有上游逻辑，同时又不会盲信上游输出。

## 关键文件和职责

核心代码文件是 `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129.py`。这个文件承担 builder 职责：定位 v1128 review JSON，读取 JSON，执行 `_checks`，构造 `_receipt`，生成 `summary`、`interpretation`、`consumer_receipts` 和 `check_rows`。它是本版语义的中心。

输出渲染文件是 `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129_artifacts.py`。它不负责业务判断，只负责把 report 写成 JSON、CSV、text、Markdown、HTML。这样的拆法避免 builder 文件继续膨胀，也让输出格式可以独立测试。HTML 报告中的 `Receipt Boundary`、`Consumer Receipts` 和 `Checks` 三个区域，就是从这里渲染出来的。

CLI 入口是 `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129.py`。它负责接收上游目录或 JSON 文件、解析 `--out-dir`、`--require-receipt-ready` 和 `--force`，调用 builder 与 artifact writer，并把关键状态打印到终端。真实运行证据显示，CLI 输出了 `status=pass`、`receipt_ready=True`、`failed_count=0`、`lookup_key_count=1`、`promotion_ready=False` 等字段，说明 CLI 并不是空壳。

测试文件是 `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129.py`。测试覆盖 ready 路径，也覆盖 requested use 被改成 `production_promotion`、source review path 漂移、source evidence status 变成 fail、CLI 在 require receipt ready 下返回 1、以及 artifact writer 能输出五种格式。它保护的是“receipt 只能从合格 review 生成，并且生成之后仍然只允许 lookup-only 消费”。

常量更新发生在 `src/minigpt/randomized_holdout_publication_constants.py`。本版新增了 v1129 的 next step 常量，把下一步路由到 `check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129`。这个常量的意义不是启动下一版，而是让 report 自身携带下一步建议，后续 contract-check 模块可以从 report 中直接读取边界。

文档和归档文件包括 `README.md`、`f/README.md`、`f/1129/解释/说明.md`、`f/1129/图片/v1129-receipt.png` 和本讲解。README 负责让项目首页知道当前最新版本；`f/README.md` 负责让运行证据目录可检索；`说明.md` 负责解释这次真实运行；截图负责提供浏览器层面的可视化证据；本讲解负责解释代码链路、边界和测试保护点。

## 输入输出模型

v1129 的输入是 v1128 review report。builder 先从输入里提取 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`。这些字段分别代表上游 review 的摘要、review 详细体、索引行和源证据行。这里没有重新读取 v1127 index 的全部语义，而是要求 v1128 已经把必要字段传递出来，并且 v1129 会检查这些字段是否满足收据记录条件。

输出 report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`failed_count`、`issues`、`receipt_index_review_path`、`receipt_index_review_sha256`、`source_receipt_index_review_summary`、`source_receipt_index_review`、`receipt_index_rows`、`source_evidence_rows`、`consumer_receipts`、`check_rows`、`receipt`、`summary` 和 `interpretation`。其中真正给后续机器消费的主要是 `status`、`decision`、`receipt`、`summary` 和 `check_rows`；给人看的是 `interpretation` 和 HTML/Markdown 渲染。

`receipt` 是本版最核心的数据结构。它包含 `receipt_ready`、`receipt_id`、`receipt_type`、`receipt_status`、`consumer_name`、`requested_use`、`granted_use`、`receipt_index_review_path`、`receipt_index_review_sha256`、`receipt_index_row_count`、`source_evidence_count`、`lookup_keys`、`review_id`、`review_status`、`promotion_ready`、`approved_for_promotion`、`consumer_boundary`、`model_quality_claim`、source path 系列字段和 `next_step`。这些字段共同表达一个事实：本版给下游消费方发放的是查询凭据，不是晋级许可。

`summary` 是给 CLI、README 和后续 gate 快速读取的摘要。它包含 ready key、receipt id、receipt status、consumer name、granted use、row count、evidence count、lookup key count、promotion flags、consumer boundary、model quality claim、next step 和 check count。真实运行中 `lookup_key_count=1`、`source_evidence_count=2`、`promotion_ready=False`、`failed_check_count=0`，说明本版既成功建立了只读收据，又保留了不晋级的边界。

`consumer_receipts` 是给下游查找用的行级视图。它把每个 index row 的 lookup key、receipt index id、source receipt id 与本版 receipt id 连接起来。因为本版只有一条 lookup key，所以 consumer receipts 也只有一条。这个结构的意义在于后续消费方不必理解整个 report，就可以根据 lookup key 找到对应 receipt 和 source receipt。

## 核心检查逻辑

`_checks` 是 v1129 的保护核心。第一组检查确认输入本身可用：`receipt_index_review_file_exists` 要求 v1128 review 文件存在，`receipt_index_review_passed` 要求上游 status 是 pass，`receipt_index_review_decision_ready` 要求上游 decision 正好是 v1128 ready decision，`receipt_index_review_summary_ready` 要求 summary 和 body 都显示 review ready。

第二组检查确认使用范围没有扩大。`review_status_allowed` 要求上游 review status 是 lookup-only approved，`requested_use_allowed` 要求本次请求仍然是 `downstream_governance_lookup_only`，`lookup_only_granted_use` 要求 summary 和 review 中的 granted use 都保持 lookup-only。测试里特意把 requested use 改成 `production_promotion`，report 会 fail，并且 issues 中包含 `requested_use_allowed`。这说明本版不会因为 CLI 参数或调用方误传而放宽使用边界。

第三组检查确认 lookup 和 contract check 仍然有效。`receipt_index_lookup_ready` 要求 receipt index ready 与 lookup ready 同时为真，`contract_check_ready` 要求上游 contract check ready 为真，`index_rows_present` 要求索引行数量和 summary 中的 row count 同为 1，`source_evidence_count` 要求源证据行数量和 summary 同为 2。这些检查保护的是“只读收据不是空收据”，它必须带着明确索引行和明确源证据。

第四组检查确认源证据没有坏掉。`source_evidence_digests_present` 要求每条源证据都有 sha256，`source_evidence_status_pass` 要求源证据行都是 pass，`source_receipt_index_file_exists`、`source_receipt_file_exists`、`source_receipt_check_file_exists`、`source_review_file_exists` 和 `source_receipt_index_origin_file_exists` 要求路径仍然能在本地找到。测试里把 source review path 改成不存在的文件，会触发 `source_review_file_exists`；把 source evidence status 改成 fail，会触发 `source_evidence_status_pass`。这两类测试很重要，因为它们证明 v1129 不是只看 summary 的 happy path。

第五组检查确认不晋级边界。`index_rows_not_promoted` 要求 index rows 的 promotion_ready 都是 False，`promotion_still_false` 要求 summary、review 和 approved flag 都保持 False，`consumer_boundary_governance` 要求 consumer boundary 等于项目定义的治理查询边界，`model_quality_claim_bounded` 要求 model quality claim 仍然是 bounded。也就是说，即使 report pass，本版仍然只说明治理证据链干净，不说明模型能力已经达到生产标准。

最后的 `source_next_step_matches` 检查把 v1128 的 next step 与 v1129 的入口连接起来。如果 v1128 review 没有把下一步指向 receipt recording，v1129 就不应该继续发 receipt。这一点能防止链路被手工拼接错版本，也能防止后续版本从错误的上游产物继续滚动。

## CLI 和运行证据

本版真实运行使用的命令是：

```powershell
python -B scripts\record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129.py f\1128\解释\receipt-index-review-v1128 --out-dir f\1129\解释\receipt-v1129 --require-receipt-ready --force
```

这条命令不是读取测试 fixture，而是读取仓库中 v1128 的真实输出目录。CLI 自动定位其中的 v1128 JSON，构建 v1129 report，然后写出五类产物。终端输出显示 `status=pass`、`decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1129_ready`、`failed_count=0`、`receipt_ready=True`、`lookup_key_count=1`、`promotion_ready=False`、`passed_check_count=25`、`failed_check_count=0`。

HTML 报告通过 Playwright MCP 打开并截图，截图保存到 `f/1129/图片/v1129-receipt.png`。浏览器快照中可以直接看到 `Receipt Boundary`、`Consumer Receipts` 和 `Checks` 三块内容，且 source review、source receipt index、source receipt、source check、source origin review、source origin index 都可见。这种浏览器层面的检查不是替代单测，而是证明最终报告确实能被人审阅，不只是 JSON 文件存在。

## 测试覆盖和风险边界

focused test 结果是 `6 passed in 0.67s`。这 6 个测试覆盖了六个层次：ready review 能生成 pass receipt；requested use 漂移会失败；source review path 漂移会失败；source evidence status 变成 fail 会失败；CLI 在 require receipt ready 时遇到坏 review 会返回 1 并仍写出失败报告；artifact writer 和 CLI 能输出 JSON、CSV、text、Markdown、HTML，并且 render 函数里能看到 receipt、Consumer Receipts 等关键文本。

这些测试不是大而全的训练测试，但对本版来说足够有针对性。v1129 的风险不是模型训练崩掉，而是治理产物被错误消费：例如把 lookup-only 当成 production promotion，把 source path 丢失的 report 当成可追溯，把失败 evidence 当成可用 evidence，或者把 next step 接错。测试正是围绕这些风险展开。

全量验证还会包含 `python -m py_compile`、focused pytest、source encoding hygiene 和 `git diff --check`。其中 source encoding hygiene 曾经在项目历史里暴露过 BOM 和 syntax 问题，所以这里继续保留；`git diff --check` 保护 Markdown 和 Python 文件不要带尾随空格或冲突标记；py_compile 保护长文件名模块和脚本没有语法错误。

## 本版与维护性的关系

v1129 仍然延续了很长的模块名，这是当前模型治理阶段的历史包袱。短期内没有在本版强行改名，是因为改名会影响前后版本引用、README、测试和证据归档，不适合夹在 receipt 收口版里做。更合理的做法是在下一轮专门安排命名和公共组件收束，把 receipt、check、index、review 这几类重复形态抽成更短的 domain package 或 adapter 层。

不过本版仍然遵守了“不要制造巨型文件”的规则：业务 builder 和 artifact renderer 分开，CLI 单独放在 scripts，测试单独覆盖，文档和运行说明放在 `f/1129` 与模型治理阶段讲解目录。这样即使文件名长，单个文件的职责仍然清楚，后续拆分时也能按 builder、artifact、CLI、test、docs 五个面向逐步收束。

## 一句话总结

v1129 把 v1128 review 过的 receipt index 记录为新的 downstream lookup-only receipt，让本轮 v1125 到 v1129 的 receipt、contract check、index、review、receipt 小闭环完整收口，同时继续明确它只证明治理链可追溯，不证明模型可以生产晋级。
