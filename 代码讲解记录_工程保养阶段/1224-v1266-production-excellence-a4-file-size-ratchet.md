# v1266 production-excellence A4：file-size ratchet

## 本版目标与边界

v1266 接在 v1265 后面，进入 production-excellence A4。前面几版已经把 A0 到 A3 的主线补齐：A0 做仓库事实和 archive/runs census，A1 做 ruff 与 scoped mypy，A2 做 coverage floor ratchet，A3 做 honest-measurement 与 artifact schema guard。A4 的主题不是继续堆一个新的治理概念，而是回到代码健康本身：项目已经推进到一千多版，不能只靠“以后注意不要写大文件”的口头规则来维持可维护性。真正可靠的做法，是把文件大小的事实、例外、失败条件和输出证据都交给一个可运行的门。

本版新增 file-size ratchet。它扫描 `src/`、`scripts/` 和 `tests/` 下的 Python 文件，按两个阈值分类：超过 500 行进入报告视野，超过 800 行成为硬限制。硬限制不是简单粗暴地要求历史文件立刻全部拆掉；这种做法风险很高，尤其是测试文件常常承载大量回归样例，一次大拆容易改变断言语义或漏掉 fixture 组合。因此 v1266 采取更稳的方式：把现有超过 800 行的历史测试显式登记成 waiver，并记录当前 baseline 行数、原因和后续拆分方向。waiver 的含义不是“这个文件永远合法膨胀”，而是“这是已知历史债，本版暂不冒险拆，但从今天起不能再长”。如果这些文件未来继续增加行数，门禁会失败；如果出现新的未豁免超 800 行文件，门禁也会失败。

边界也很重要：本版不改模型训练、不重新运行科学线实验、不修改 cached artifact verdict、不改变 `decide()` 语义、不提升模型能力声明，也不迁移历史归档。它只处理工程线的维护性问题：让“大文件不得继续恶化”从人脑提醒变成 CI 可失败条件。

## 输入：code-health registry

本版的事实源是 `docs/code-health/file-size-ratchet.json`。这个文件记录四类信息。

第一类是 schema 和 policy 字段：`schema_version=1`、`policy=aiproj_file_size_ratchet`。这让 checker 能判断自己读到的是正确用途的配置，而不是误读其他 JSON。

第二类是阈值：`warning_line_limit=500` 与 `max_line_limit=800`。500 行对应 AGENTS 里“接近 500-800 行要关注拆分”的软边界；800 行是本版执行的硬边界。软边界进入报告，但不阻断；硬边界必须要么拆掉，要么有明确 waiver。

第三类是扫描目标：`src`、`scripts`、`tests`。这个范围故意覆盖生产代码、维护脚本和测试，因为三者都会影响长期维护成本。v1266 的事实显示，当前 `src/` 和 `scripts/` 没有超 800 的 Python 文件，真正的大文件集中在历史测试里。

第四类是 waiver 列表。初始登记八个历史测试文件：`tests/test_promoted_training_scale_seed_handoff.py`、`tests/test_promoted_training_scale_seed_handoff_receipt.py`、`tests/test_registry.py`、`tests/test_maturity_narrative.py`、`tests/test_release_readiness_comparison.py`、`tests/test_promoted_training_scale_decision.py`、`tests/test_promoted_training_scale_seed.py`、`tests/test_server.py`。每条 waiver 都有 `baseline_lines`、`reason`、`followup`。这里的 baseline 不是随手估算，而是 checker 自己按 UTF-8 文本读取并 `splitlines()` 得到的当前行数。开发过程中曾经用 PowerShell 的 `Measure-Object -Line` 做过一次粗测，结果低估了真实行数；最终以本版 checker 的实际读数为准，这也符合“现实赢”的对账原则。

## 核心实现

核心模块是 `src/minigpt/file_size_ratchet.py`。它的主入口是 `build_file_size_ratchet_report()`，接收 config path、project root 和可选 generated_at，返回一个完整报告对象。报告顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`config_path`、`summary`、`targets`、`waivers`、`files`、`checks`、`recommendations`。

实现流程分四步。

第一步读取配置。模块复用 `minigpt.report_utils.read_json_object()`，因此配置必须是 JSON object。`_positive_int()` 负责把阈值解析成正整数，解析失败时回退到默认 500 和 800。`_waivers_by_path()` 把 waiver 列表整理成以 repository-relative path 为 key 的字典，便于扫描文件时快速判断某个文件是否豁免。

第二步扫描文件。`_scan_files()` 对每个 target 做 root 内路径解析，目录用 `rglob("*.py")` 查找 Python 文件，单文件 target 也能支持。每个文件都会形成一行 file record：`path`、`line_count`、`bucket`、`waived`、`waiver_status`、`waiver_baseline_lines`。`bucket` 有三类：`within_limit`、`over_warning`、`over_limit`。`waiver_status` 也有几类：未豁免是 `not_waived`；豁免文件等于 baseline 是 `at_baseline`；低于 baseline 是 `shrunk`；高于 baseline 是 `grew`。这一点很关键，因为它允许未来拆分历史测试后自然变成 shrunk，而不是要求同时改一堆测试期望。

第三步生成 checks。`_config_checks()` 检查 schema、policy、targets、config 是否在项目内、target 是否存在、每个 waiver 文件是否存在、baseline 是否正整数、reason 是否非空。`_file_checks()` 则对每个文件检查 `max_lines` 和 `waiver_no_growth`。未豁免文件超过 800 会让 `max_lines:<path>` 失败；豁免文件当前行数超过 baseline 会让 `waiver_no_growth:<path>` 失败。最终只要有失败 check，顶层 `status` 就是 `fail`，`decision` 就是 `repair_file_size_ratchet`。

第四步输出报告。`write_file_size_ratchet_outputs()` 复用 `write_output_bundle()` 生成 JSON、CSV、Markdown、HTML 四种格式。CSV 适合排序审计，Markdown 适合版本说明引用，HTML 适合截图确认。HTML 页面显示四个关键统计：扫描文件数、warning 数、over-limit 数、failure 数，并列出超过 warning 阈值的文件。

## CLI 与 CI 接入

CLI 是 `scripts/check_file_size_ratchet.py`。默认读取 `docs/code-health/file-size-ratchet.json`，默认输出到 `runs/file-size-ratchet`。它打印 `status`、`decision`、`scanned_file_count`、`over_warning_count`、`over_limit_count`、`unwaived_over_limit_count`、`waiver_growth_violation_count` 和输出路径。和其他工程门一样，默认失败会返回非零；`--no-fail` 只用于调试输出。

CI 中新增 `File size ratchet` 步骤，放在 `Artifact schema guard` 之后、`Archived path portability check` 之前，并且在 coverage 之前。这一顺序表达得很明确：A3 的 artifact envelope 先被保护，随后 A4 的代码健康被保护，再进入后续更重的历史证据和 coverage 检查。

为了避免 CI workflow 被人改坏，本版也更新 `src/minigpt/ci_workflow_hygiene_policy.py`。它新增 required command fragment `file_size_ratchet`，并新增两条顺序规则：`file_size_ratchet_after_artifact_schema_guard` 和 `file_size_ratchet_before_coverage`。同时 `src/minigpt/ci_workflow_hygiene.py` 和 `src/minigpt/ci_workflow_hygiene_artifacts.py` 增加 `file_size_ratchet_present`、`file_size_ratchet_order_ready`、`file_size_ratchet_ready` 三个 summary 字段。这样 workflow hygiene 的 JSON/Markdown/HTML 里不只是有 check 行，也能在 summary 层直接看到这个 gate 是否 ready。

本版还把新脚本加入 `scripts/_bootstrap.py` 的 `HEALTH_ENGINEERING_ENTRYPOINTS`，并在 `scripts/_engineering_health.py` 里新增 step builder。因此本地执行 `python -B scripts/check_engineering_health.py` 时也会跑 file-size ratchet。A4 不是只在 CI 上存在，维护者本地也能一条命令提前发现问题。

## 静态与类型范围

新代码本身也要接受前几版建立的门。`scripts/check_static_analysis.py` 的 strict paths 增加 `scripts/check_file_size_ratchet.py` 和 `src/minigpt/file_size_ratchet.py`，要求新门代码 lint-clean、format-clean。`docs/static-analysis/mypy-scope.json` 的 `scope_floor` 从 12 提升到 14，并新增 `file_size_ratchet_gate` 组。也就是说，v1266 不是绕过 A1/A2/A3 另起一套规则，而是在已有工程门上继续加门。

这里还有一个小经验：不要把 JSON 配置交给 `ruff format`。开发中曾经误把 `docs/code-health/file-size-ratchet.json` 放进 ruff format 命令，结果 formatter 按 Python 风格添加尾逗号，JSON 解析失败。这个问题被 focused test 及时抓住，并已手工修复。之后本项目的格式化命令应继续只传 Python 文件。

## 测试覆盖

`tests/test_file_size_ratchet.py` 是本版最直接的保护。它覆盖四个场景。

第一，当前仓库配置必须通过。断言包括 `status=pass`、`decision=continue_with_file_size_ratchet`、扫描文件数大于 1000、硬阈值是 800、waiver 数是 8、未豁免超限数是 0、waiver 增长违规数是 0、最大文件仍是 promoted seed handoff 测试。这保护了当前 census 事实。

第二，临时创建一个 801 行且无 waiver 的测试文件，报告必须失败，并出现 `max_lines:tests/test_large.py` 失败 check。这证明硬阈值不是只展示不阻断。

第三，临时创建一个 805 行文件，但 waiver baseline 只有 804，报告必须失败，并出现 `waiver_no_growth:tests/test_legacy.py`。这证明 waiver 是 no-growth 合约，而不是永久免死金牌。

第四，CLI 和输出文件必须可用。测试调用 `scripts.check_file_size_ratchet.main()`，确认 exit code 为 0，并确认 JSON/CSV/Markdown/HTML 输出齐全。

此外，`tests/test_ci_workflow.py`、`tests/test_engineering_health.py`、`tests/test_project_configuration.py`、`tests/test_script_bootstrap.py`、`tests/test_script_surface_registry.py` 都被同步更新，分别保护 CI required command、顺序规则、工程健康步骤、前门文档和脚本表面索引。

## 运行证据

正式报告位于 `f/1266/解释/file-size-ratchet/`：

- `file_size_ratchet.json`
- `file_size_ratchet.csv`
- `file_size_ratchet.md`
- `file_size_ratchet.html`

正式运行输出显示 `status=pass`、`decision=continue_with_file_size_ratchet`、`scanned_file_count=2773`、`over_warning_count=20`、`over_limit_count=8`、`unwaived_over_limit_count=0`、`waiver_growth_violation_count=0`。Playwright MCP 打开 HTML 报告后，snapshot 确认页面显示 `Status pass`、`Files 2773`、`Warnings 20`、`Over limit 8`、`Failures 0`。截图保存为 `f/1266/图片/file-size-ratchet-v1266.png`。

Playwright 打开本地 `file://` 被浏览器策略阻止，所以本版短暂启动了本地 HTTP server。服务进程 PID 为 8896，截图完成后已经停止，端口只剩 `TimeWait`。这一点写入归档，是为了让运行证据透明，而不是让后续维护者以为有长驻服务。

## 后续维护策略

v1266 的价值不在于“宣称没有大文件”，而在于让大文件债务不再继续恶化。八个 waiver 文件的后续拆分应该按业务族逐个做：promoted seed handoff、receipt、registry、maturity narrative、release readiness comparison、server behavior 等，不应该为了降低行数而一次性机械切开。每次拆分都要用现有测试证明行为不变，并在文件变短后降低或删除对应 waiver baseline。这样 A4 才能从“止血”逐渐变成“还债”。

## 一句话总结

v1266 把“不要再写难维护巨型 Python 文件”变成了可运行、可截图、可 CI 失败的 file-size ratchet，同时用 no-growth waiver 稳住历史测试债务而不冒险改动科学线语义。
