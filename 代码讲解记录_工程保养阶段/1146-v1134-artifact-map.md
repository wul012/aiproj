# v1134 artifact map 代码讲解

## 本版目标和边界

v1134 是工程后期保养五版的第五版，也是这一批可读性保养的收束版。前四版已经做了命名止血、README/docs 拆分、publication receipt 模板、模型能力 cadence watch；最后还缺一个很实际的问题：版本证据越来越多，读者怎样快速找到某个版本的截图、说明和 JSON/CSV/Markdown/HTML 产物？v1134 的目标就是建立 versioned artifact map，把 `f/<version>` 里的材料整理成一张可运行生成的对照表。

本版不替代任何具体版本的 JSON 报告，不重新解释每个 receipt 或维护版本的业务语义，也不迁移旧 evidence 目录。artifact map 只做“索引和可读性保养”：它告诉读者某个版本有没有 `解释/说明.md`，有没有截图，有多少报告目录，有多少 JSON、CSV、Markdown 和 HTML 文件。真正的机器可读事实仍然在各版本自己的 JSON 里。

这个边界很重要。aiproj 的证据链特点是产物多、版本密、目录深。直接把所有细节再复制进一个总表会制造新的冗余；但完全没有总表，读者又要手工打开多个 `f/<version>` 文件夹。v1134 选择中间路线：只统计关键存在性和数量，帮助定位，不复制业务内容。

## 新增模块

`src/minigpt/artifact_map.py` 是本版核心模块。它定义 `build_artifact_map_report`、`write_artifact_map_outputs` 和 `resolve_exit_code`。默认扫描 `f/` 下最近 12 个数字版本目录，按版本号倒序排列，然后为每个版本生成一行 artifact map。

每一行包含 `version`、`evidence_dir`、`has_summary`、`screenshot_count`、`report_dir_count`、`json_count`、`csv_count`、`markdown_count`、`html_count`、`status` 和 `recommendation`。其中 `has_summary` 检查 `f/<version>/解释/说明.md` 是否存在；`screenshot_count` 统计 `f/<version>/图片` 下的文件数量；`report_dir_count` 统计 `解释` 下的报告子目录；四类 count 分别统计报告子目录中的 JSON、CSV、Markdown 和 HTML 文件。

`status` 的判断保持克制：如果有说明且截图数量大于 0，就认为这个版本的 evidence entry 是 pass；否则是 watch。它不要求每个版本都必须有同样数量的 JSON 或 HTML，因为不同版本的产物形态可能不同；但说明和截图是当前阶段的最低可读性要求。真实运行中最近 12 个版本全部满足这两个条件，因此 `status=pass`、`ready_version_count=12`。

`summary` 提供总览字段，包括 `evidence_root`、`scanned_version_count`、`ready_version_count`、`missing_summary_count`、`missing_screenshot_count`、`limit` 和 `artifact_map_ready`。真实运行结果是 `scanned_version_count=12`、`ready_version_count=12`、`missing_summary_count=0`、`missing_screenshot_count=0`，说明最近证据目录的最低可读性是完整的。

## CLI 入口

`scripts/devtools/build_artifact_map_v1134.py` 是本版 CLI，放在 `scripts/devtools/` 下。它和 v1131 的 docs checker 同属开发辅助/可读性检查，而不是 publication 业务入口，也不是 evaluation 入口。这个路径继续落实 scripts 分层：publication 工具放 `scripts/publication/`，模型能力节奏放 `scripts/evaluation/`，文档和索引保养放 `scripts/devtools/`。

CLI 支持 `--root`、`--out-dir`、`--limit`、`--require-ready`、`--require-complete` 和 `--force`。真实运行使用：

```powershell
python -B scripts\devtools\build_artifact_map_v1134.py --out-dir f\1134\解释\artifact-map-v1134 --limit 12 --require-ready --force
```

这里使用 `--require-ready`，要求 artifact map 工具本身能生成。`--require-complete` 可以作为未来更严格的检查，当某些近期版本缺少说明或截图时返回 1。当前真实仓库已经 pass，因此即使用 complete 也应该能通过，但本版保留两个级别，是为了让未来可以区分“工具可用”和“所有证据完整”。

## 文档配套

`docs/artifact-map.md` 是本版新增稳定文档。它说明 artifact map 是 `f/<version>` evidence directories 的维护视图，记录 version、evidence directory、`解释/说明.md` 是否存在、screenshot count、report directory count、JSON/CSV/Markdown/HTML artifact counts 和 completion status。它强调 artifact map 不替代 JSON 报告，只是指向报告的位置。

`docs/versioned-artifacts.md` 增加了到 artifact map 的链接，README 的 Documentation Map 也加入 `Artifact map`。这样新读者从首页能先理解证据目录规则，再看 artifact map 如何帮助查找。这个连接把 v1131 的 docs 拆分和 v1134 的证据对照表串了起来。

## 测试覆盖

`tests/test_artifact_map.py` 覆盖三类行为。第一，构造一个完整的临时 `f/1130` 目录，包含 `解释/说明.md`、截图和四类报告文件，report 应该 pass，ready version count 为 1，`require_complete` 返回 0。第二，构造两个不完整版本，一个缺说明，一个缺截图，report 应该 watch，missing summary count 和 missing screenshot count 都是 1，`require_ready` 返回 0，而 `require_complete` 返回 1。第三，覆盖 artifact 输出和 CLI，确认 JSON、CSV、text、Markdown、HTML 都能生成，CLI 在 `--require-ready` 下返回 0。

这组测试保护的是 artifact map 的核心语义：说明和截图是最低可读性证据；缺失时要 watch；工具本身可用和证据完全齐备可以用不同 exit policy 表达。这样后续如果某个版本漏了截图或说明，artifact map 可以在不破坏所有工作的情况下给出明确提醒。

## 运行证据

v1134 的真实输出写入 `f/1134/解释/artifact-map-v1134`，包含 JSON、CSV、text、Markdown 和 HTML。Playwright MCP 打开 HTML 后，快照显示 `MiniGPT versioned artifact map v1134`、`Versioned Artifact Map` 表格和 `Recommendations` 区域。截图保存为 `f/1134/图片/v1134-artifact-map.png`。

真实 CLI 输出显示 `status=pass`、`decision=versioned_artifact_map_ready`、`scanned_version_count=12`、`ready_version_count=12`、`missing_summary_count=0`、`missing_screenshot_count=0`。这说明最近 12 个 `f/` 版本目录都具备最低证据可读性。对于后期维护来说，这个结果很有价值：它证明证据目录没有因为快速推进而漏掉说明或截图。

## 与前四版的关系

v1130 解决命名止血，v1131 解决入口文档，v1132 解决 receipt 模板和 scripts 分层，v1133 解决模型能力回归节奏，v1134 则解决证据查找。五版合起来形成一个可读性保养闭环：新文件不继续无限长，新读者有 docs 入口，新 receipt 版本有模板，新治理/维护节奏不会遮住模型能力，已有 evidence 可以用 artifact map 查找。

这五版没有做大规模重构，是有意的。工程后期保养不应该为了“整理”破坏已稳定的证据链。更合理的方式是先建立规则、模板、检查和索引，让未来增量变干净，同时保留历史兼容。v1134 的 artifact map 正是这种思路的收尾：它接受历史目录存在，并在其上建立可读对照。

## 一句话总结

v1134 把近期 `f/` 版本证据从分散目录整理成可运行生成的 artifact map，让读者能快速定位说明、截图和机器可读报告，为本批五版工程保养完成证据查找层的收束。
