# v1131 project docs readability 代码讲解

## 本版目标和边界

v1131 是工程后期保养五版的第二版，目标是做 README/docs 拆分。这里的“拆分”不是把根 README 里的历史内容一口气删除，也不是重写所有版本记录，而是先把新读者最需要的稳定概念放进 `docs/`，并在 README 顶部提供明确导航。这样做的重点是降低入口负担：读者打开项目后，可以先看项目概览、模型训练、publication receipt、no-promotion boundary 和 versioned artifacts，而不是直接被上万行版本历史淹没。

本版不做三件事。第一，不迁移旧 README 的完整历史 ledger，因为这些历史记录和已有版本说明仍然有索引价值，贸然拆分会增加链接断裂风险。第二，不把 docs 写成新的流水账目录，docs 只承接稳定概念和阅读地图，不重复每一版的细节。第三，不把文档拆分当成纯人工约定，而是新增可运行检查器，确认 README 链接、目标文档、标题和关键术语都存在。这样后续维护时，如果 docs 被改坏，测试和 CLI 都能发现。

外部建议指出 README 已经很大，信息密度高但入口负担重，这个判断是合理的。aiproj 的 README 既承担项目简介，又承担当前版本、历史版本、目录结构、运行截图索引、能力矩阵和大量治理链说明。对于熟悉项目的人，完整 ledger 有价值；对于第一次打开项目的人，它的阅读成本太高。v1131 的策略是先在顶部加 `Documentation Map`，让 README 变成导航入口，然后把稳定解释放进 `docs/`。这是一种低风险拆分，避免为了“看起来清爽”把历史证据切碎。

## 新增文档结构

`docs/README.md` 是 docs 目录自己的索引。它告诉读者这个目录保存稳定读者文档，根 README 仍然是项目 landing page 和历史 ledger，但概念理解应该从 docs 开始。这个文件的作用类似目录门牌，不承担复杂解释。

`docs/overview.md` 说明 MiniGPT 的两层定位：一层是 tokenizer、dataset、training、evaluation、tiny GPT inspection 等模型学习路径；另一层是 publication receipt、contract check、index、review、no-promotion boundary 等 AI governance 路径。这个概览解决“项目到底是训练脚本还是治理项目”的问题，避免读者误以为后期版本只是在堆报告。

`docs/model-training.md` 把模型训练和评估主线单独拎出来。它强调 training、evaluation、holdout 的含义，并提醒后期治理不能压住模型能力验证主线。这个文件为后续 v1133 的模型能力回归节奏做铺垫：每隔若干治理版本，项目应该回到 required-term coverage、loss signal bridge、decoder anchor distribution、unassisted repair 或 exact surface repair 等能力问题。

`docs/publication-receipts.md` 解释 receipt 链路。它把常见节奏写成 `record receipt -> contract check -> index -> review -> next receipt`，并明确 lookup-only receipt 的含义：它可以用于下游治理查询、审计和追溯，但不能被解释成生产晋级许可。这个文件还列出 receipt 版本通常包含 script、src module、artifact renderer、test、f 目录证据、截图和代码讲解，为后续模板化版本做准备。

`docs/no-promotion-boundary.md` 是边界说明的集中位置。它写清 `status=pass` 通常只表示 artifact 内部一致、可追溯、适合声明的治理用途，不表示模型 production ready、checkpoint 应该 promotion、生成质量已经提升，或 holdout 结果可以泛化。这个文件可以减少后续 README 和讲解里重复写 no-promotion 声明的负担。

`docs/versioned-artifacts.md` 解释 `f/<version>/图片` 和 `f/<version>/解释` 的结构，说明 JSON 是机器可读事实来源，CSV 适合比较，Markdown/text 适合命令行审阅，截图证明 HTML 报告能打开。这个文件让证据归档规则不再只藏在 AGENTS.md 和历史版本说明里。

## 新增检查器

`src/minigpt/project_docs_readability.py` 是 v1131 的核心检查模块。它定义 `DOC_TARGETS`，列出五个必须存在的 docs 文件、每个文件的标题和必要术语。`build_project_docs_readability_report` 会读取根 README 和每个 docs 文件，检查文件是否存在、标题是否出现、README 是否包含对应链接、必要术语是否齐全。最终 report 会给出 `status`、`decision`、`summary`、`rows` 和 `recommendations`。

这个检查器的重点不是做复杂自然语言质量评估，而是守住文档拆分的最低契约。文档系统最常见的问题不是第一天写不好，而是后续改 README 或重命名文档时链接漂移。v1131 把这些容易漂移的点转成机器可检查字段：`exists`、`readme_link_present`、`heading_present`、`required_terms_present`。如果某个文件缺失，或者 README 没链接到它，report 会 fail。

`scripts/devtools/check_project_docs_readability_v1131.py` 是分层 CLI，放在 `scripts/devtools/` 下。它延续 v1130 的 scripts 分层思路：publication 命名扫描属于 `scripts/publication/`，文档和开发辅助检查属于 `scripts/devtools/`。CLI 支持 `--root`、`--out-dir`、`--require-pass` 和 `--force`，运行后打印 `status`、`decision`、`doc_target_count`、`ready_doc_count`、`missing_readme_link_count` 和 `failed_count`。真实运行中这些字段全部表明 docs 拆分 ready。

输出仍然复用 v1130 新增的 `readability_report_artifacts.py`。这说明 v1130 的通用 helper 不是一次性文件，而是开始承担工程保养阶段的公共输出层。v1131 不再重复写 HTML/Markdown/CSV 渲染代码，只把业务报告交给 helper 输出。这个复用点能减少后续 v1132-v1134 的样板代码。

## 测试覆盖

`tests/test_project_docs_readability.py` 覆盖三类场景。第一，临时仓库里写入完整 docs 和 README 链接，report 应该 pass，并且 `missing_readme_link_count=0`。第二，故意让 README 只保留 overview 链接，其他 docs 链接缺失，report 应该 fail，`require_pass` 返回 1。第三，检查 artifact writer 和 CLI 是否能输出 JSON、CSV、text、Markdown、HTML，且 CLI 在 `--require-pass` 下返回 0。

这组测试保护的是文档拆分的实用边界。如果只有 docs 文件，没有 README 链接，读者依然找不到；如果只有 README 链接，没有目标文件，导航会断；如果文档没有必要术语，说明文件可能被误删或写偏。测试不试图评判中文表达是否优美，而是确保“入口、目标、主题词”三件事持续成立。

本版还执行了 py_compile，覆盖业务模块、CLI 和测试。真实仓库运行命令是：

```powershell
python -B scripts\devtools\check_project_docs_readability_v1131.py --out-dir f\1131\解释\project-docs-readability-v1131 --require-pass --force
```

真实结果是 `status=pass`、`decision=project_docs_readability_split_ready`、`doc_target_count=5`、`ready_doc_count=5`、`missing_readme_link_count=0`、`failed_count=0`。这说明 README 顶部的五个链接都能对应到 docs 文件，docs 文件也包含预期标题和术语。

## 运行证据

v1131 输出写入 `f/1131/解释/project-docs-readability-v1131`，包含 JSON、CSV、text、Markdown 和 HTML。Playwright MCP 打开 HTML 后，页面快照显示标题 `MiniGPT project docs readability split v1131`、`Documentation Targets` 表格和 `Recommendations` 区域。截图保存为 `f/1131/图片/v1131-project-docs-readability.png`。

截图在这里的意义不是“文档漂亮”，而是证明最终 HTML artifact 能被浏览器打开，表格内容可见，人工审阅路径存在。对于工程保养版本来说，这类截图能帮助后续读者判断：该版本不是只改了 Markdown 文件，而是建立了文档检查和可视化证据。

## 维护意义

v1131 的维护意义在于让项目入口更像成熟工程。根 README 仍然保留版本历史和大量证据记录，但新读者不必从历史深处理解项目。`docs/overview.md` 解决项目定位，`docs/model-training.md` 保住模型主线，`docs/publication-receipts.md` 解释治理链，`docs/no-promotion-boundary.md` 集中边界语言，`docs/versioned-artifacts.md` 解释证据归档。后续版本可以引用这些 docs，而不是在每个版本说明里重复大段背景。

这也为后续几版保养铺路。v1132 可以围绕 scripts 分层和 receipt 模板继续做入口整理；v1133 可以根据 docs/model-training.md 的节奏要求建立模型能力回归检查；v1134 可以把 versioned artifacts 进一步做成 artifact 对照表。也就是说，v1131 不只是文档整理，它把后续维护路线放进了可链接、可验证的文档结构里。

## 一句话总结

v1131 把 aiproj 的根 README 从“所有信息都堆在一起”推进为“首页导航加 docs 分层说明”，并用可运行检查器保护这些新入口不会在后续版本中漂移。
