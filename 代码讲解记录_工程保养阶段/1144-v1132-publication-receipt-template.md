# v1132 publication receipt template 代码讲解

## 本版目标和边界

v1132 是工程后期保养五版的第三版，目标是把 publication receipt 风格版本模板化，并检查新的 scripts 分层目录是否已经具备承接新入口的能力。v1130 解决“新命名不要继续变长”的问题，v1131 解决“README 不再是唯一概念入口”的问题，v1132 则解决“下一次做 receipt、contract check、index、review 时应该先按什么清单准备”的问题。

本版不做历史迁移，不移动旧脚本，不重命名 v1098 到 v1129 的长文件，也不改变任何已有 publication receipt JSON schema。原因很简单：历史 receipt 链路虽然命名长，但它已经被测试、README、f 目录证据、tag 和后续版本引用。真正适合当前阶段的保养动作，是建立一个新版本模板，让后续新增工作不再临时发明文件清单、不再漏掉 no-promotion 说明、不再把脚本继续堆在平铺 `scripts/` 目录下。

外部建议里把“publication receipt 模板化”和“scripts 分层”都列为 aiproj 的可读性保养方向。v1132 把这两件事合并成一个版本，是因为它们天然相关：模板会要求新脚本路径优先使用 `scripts/publication/`，而检查器会确认 `scripts/publication/` 和 `scripts/devtools/` 这两个目录存在。这样后续新增入口时，读者能从目录结构先判断脚本用途，而不是在几百个平铺脚本里搜索长文件名。

## 新增模板文档

`docs/publication-receipt-template.md` 是本版最重要的文档产物。它不是泛泛而谈的说明，而是给下一次 receipt 风格版本使用的 checklist。模板分为五个主要部分。

第一部分是 `Version Scope`。这里要求写清版本号、版本类型、source artifact、输出目录、截图路径、新脚本路径、新源码模块路径和新测试路径。这个部分解决的是“版本从哪里来、写到哪里去、入口在哪里”的问题。过去每一版都能靠 README 和运行证据找到答案，但新读者需要跨多个文件查；模板把这些字段提前列出来。

第二部分是 `Required Files`。这里列出 CLI script、source builder module、artifact writer 或共享输出 helper、focused test、runtime JSON/CSV/text/Markdown/HTML、`f/<version>/解释/说明.md`、代码讲解、README 和 archive index 更新。它的意义是防止保养版本只写代码不写证据，或者只写文档不测 CLI。对于 aiproj 这种证据链项目来说，版本是否完整不只看源码，还要看测试、运行产物、截图和讲解是否能互相指向。

第三部分是 `Boundary Statements`。这是 publication receipt 最容易被误读的地方。模板要求明确 artifact 是 lookup-only、plan-only、review-only 还是 promotion-blocking；当版本不能证明生产就绪时，必须保留 `promotion_ready=False` 和 `approved_for_promotion=False`；模型质量声明必须 bounded；receipt chain consistency 不能被当成 training improvement。这个部分延续了 v1131 的 no-promotion docs，但把它变成每个 receipt 风格版本的必填提醒。

第四部分是 `Verification`。模板列出 py_compile、focused pytest、真实 CLI、source encoding hygiene、`git diff --check` 和浏览器截图。它强调真实 CLI 要 against repository evidence，而不只是 fixture。这个要求来自过去多个 receipt 版本的经验：测试 fixture 能覆盖结构，但只有真实 CLI 才能证明仓库里的上游产物路径、JSON 和输出目录没有漂移。

第五部分是 `Evidence Archive`。模板要求 runtime outputs 放进 `f/<version>/解释/<report-name>/`，截图放进 `f/<version>/图片/`，阶段性讲解 README 要更新，并且不要无授权迁移旧证据目录。这个部分把仓库规则转成文档模板，减少后续版本遗漏归档索引的概率。

## 新增检查模块

`src/minigpt/publication_receipt_template.py` 是本版的业务检查模块。它定义 `TEMPLATE_PATH`、`REQUIRED_SECTIONS` 和 `SCRIPT_LAYERS`。`REQUIRED_SECTIONS` 包含 `# Publication Receipt Version Template`、`## Version Scope`、`## Required Files`、`## Boundary Statements`、`## Verification` 和 `## Evidence Archive` 六个必需标题。`SCRIPT_LAYERS` 当前要求 `scripts/publication` 和 `scripts/devtools` 两个目录存在。

`build_publication_receipt_template_report` 会读取模板文件，并为每个必需章节生成一行 `template-section` 检查；同时为每个脚本层生成一行 `script-layer` 检查。只要有章节缺失或目录不存在，report 就会 fail。真实仓库运行结果显示 `ready_section_count=6`、`ready_script_layer_count=2`、`failed_count=0`，说明模板和目录层都已经 ready。

`write_publication_receipt_template_outputs` 继续复用 v1130 的 `write_readability_outputs`。这让本版不需要重复 Markdown/HTML/CSV 渲染细节。输出文件名统一为 `publication_receipt_template_v1132.*`，便于在 `f/1132/解释/publication-receipt-template-v1132` 下查找。

`resolve_exit_code` 很简单：当 `--require-pass` 开启并且 report status 不是 pass 时返回 1。这里没有 watch 状态，因为模板和目录层属于当前版本可以直接修好的结构性要求；如果模板缺章节，就应该阻断。

## CLI 分层

`scripts/publication/check_pub_receipt_template_v1132.py` 放在 `scripts/publication/` 下。这个路径本身就是 v1132 的验证对象之一。它说明 publication receipt 相关入口不再继续默认放到平铺 scripts 根目录。v1131 的 docs checker 放在 `scripts/devtools/`，v1132 的模板 checker 放在 `scripts/publication/`，两者合起来形成了最小可用的脚本分层示例。

CLI 支持 `--root`、`--out-dir`、`--require-pass` 和 `--force`。真实运行命令是：

```powershell
python -B scripts\publication\check_pub_receipt_template_v1132.py --out-dir f\1132\解释\publication-receipt-template-v1132 --require-pass --force
```

输出显示 `status=pass`、`decision=publication_receipt_template_ready`、`ready_section_count=6`、`ready_script_layer_count=2`、`template_ready=True`、`failed_count=0`。这些字段足够说明模板和脚本层不是只写了 Markdown，而是被程序检查过。

## 测试覆盖

`tests/test_publication_receipt_template.py` 覆盖三类行为。第一，临时仓库里写入完整模板章节并创建两个脚本目录，report 应该 pass，ready section count 等于 required sections 数量，`template_ready=True`。第二，故意省略 `## Verification` 章节，report 应该 fail，`require_pass` 返回 1。第三，测试 artifact 输出和 CLI，确认 JSON、CSV、text、Markdown、HTML 都能生成，CLI 在 `--require-pass` 下返回 0。

这组测试保护的是模板完整性，而不是模板文字风格。它确保后续如果有人删掉 verification 或 boundary statements，检查器能发现；如果脚本层目录被误删，检查器也能发现。对于工程后期保养来说，这类测试比“文档存在即可”更有价值，因为它把关键结构变成了契约。

## 运行证据

v1132 的真实输出在 `f/1132/解释/publication-receipt-template-v1132`，包含 JSON、CSV、text、Markdown 和 HTML。Playwright MCP 打开 HTML 后，快照显示 `MiniGPT publication receipt template and script layers v1132`、`Template And Script Layer Checks` 表格和 `Recommendations` 区域。截图保存为 `f/1132/图片/v1132-publication-receipt-template.png`。

这份证据说明两件事。第一，模板检查报告能被机器读取，也能被人从 HTML 审阅。第二，v1132 没有把 scripts 分层停留在口头建议，而是让分层目录成为检查项。后续如果新增 publication 工具还放在根 scripts 目录，至少会和 v1130/v1132 的规则相冲突，维护者可以据此要求短名和分层入口。

## 维护意义

v1132 的维护意义是把“下次怎么做 receipt 风格版本”提前标准化。过去每一版都能完成闭环，但文件清单、边界声明和证据归档需要依赖执行者记忆。模板化之后，版本开始前就能看到必填项；检查器则能确认模板没有被破坏。这样后续版本既可以保持速度，也能减少遗漏。

更重要的是，v1132 没有用大重构来解决可读性问题。它承认历史链路稳定，但要求新增入口更短、更分层、更有模板。对于一个已经有大量历史证据的项目，这比“一次性改名全部文件”更符合工程后期保养的节奏。

## 一句话总结

v1132 把 publication receipt 风格版本的范围、必备文件、边界声明、验证步骤和证据归档固化为模板，并用检查器确认模板和脚本分层可用，为后续治理版本减少遗漏和命名漂移。
