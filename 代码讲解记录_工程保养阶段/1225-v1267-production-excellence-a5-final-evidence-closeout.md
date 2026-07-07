# v1267 production-excellence A5 final evidence closeout 代码讲解

## 本版目标与边界

v1267 做的是 production-excellence A-track 的 A5 收口。前面 v1260 到 v1266 已经把 A0 到 A4 分别落成了实际工程门：A0 有 archive/runs census，A1 有 ruff 与 scoped mypy，A2 有 coverage floor ratchet，A3 有 honest-measurement gate 和 artifact schema guard，A4 有 file-size ratchet。A5 的问题不是再发明一条治理链，而是回答一个更后期的问题：这些分散的门、文档、证据路径和边界声明能不能被统一复核，并且以后不会因为 README 或 CI 漂移而失效。

所以本版新增的是 closeout gate。它把“生产卓越 A-track 已经收口”从一句叙述变成一组会失败的检查。检查对象包括最终证据文档、A0-A4 分项证据文档、no-promotion boundary、README 和 docs 索引，以及 GitHub Actions 里的 closeout step。这样 A5 不只是写一篇漂亮总结，而是把总结本身纳入维护面。后续如果有人删掉 `docs/aiproj-track-final-evidence.md`、改坏 `docs/no-promotion-boundary.md`、把 CI 里的 closeout step 移走，或者忘记把最终证据入口挂进 README，`scripts/check_aiproj_track_closeout.py` 会直接失败。

本版明确不做模型训练，不重跑科学线实验，不修改缓存 artifact，不改变任何 `decide()` 判定逻辑，也不把工程治理通过解释成模型质量提升。A-track 的价值是工程可维护性、证据完整性和边界诚实，不是宣称 tiny GPT 已经具备生产级生成能力。这个边界在 `docs/no-promotion-boundary.md` 和 `docs/aiproj-track-final-evidence.md` 里都被重新声明。

## 输入与输出

本版的主要输入是已有 A-track 的六类文档和当前 CI 配置。具体包括 `docs/aiproj-track-a0-census.md`、`docs/aiproj-track-a1-static-analysis.md`、`docs/aiproj-track-a2-coverage.md`、`docs/aiproj-track-a3-honest-measurement.md`、`docs/aiproj-track-a3-artifact-schema-guard.md`、`docs/aiproj-track-a4-code-health.md`、`docs/no-promotion-boundary.md`、`README.md`、`START_HERE.md`、`docs/README.md`、`docs/script-entrypoints.md` 和 `.github/workflows/ci.yml`。这些文件本来就存在，但 A5 以前它们之间的关系更多靠人工阅读维护。v1267 把这些关系做成检查规则。

输出分两类。第一类是面向维护者的最终证据文档：`docs/aiproj-track-final-evidence.md`。它按 A0-A5 列出每条 gate 的实现位置、失败条件、证据路径和边界说明，并单独列出 A4 的八个 file-size waiver。第二类是机器生成的 closeout report：`aiproj_track_closeout.json`、`aiproj_track_closeout.csv`、`aiproj_track_closeout.md` 和 `aiproj_track_closeout.html`。归档版本位于 `f/1267/解释/aiproj-track-closeout/`，截图位于 `f/1267/图片/aiproj-track-closeout-v1267.png`。

## 核心模块：`src/minigpt/aiproj_track_closeout.py`

`src/minigpt/aiproj_track_closeout.py` 是本版的核心。它不是通用 Markdown lint，也不是自然语言理解器，而是一个针对 A-track closeout 的结构化证据检查器。这样设计的好处是边界清楚：它检查哪些路径、哪些关键术语、哪些 CI 命令是当前 A-track 必须保留的事实；它不试图判断所有文档的文学质量，也不把历史版本叙述重新解释成当前状态。

模块顶部定义了 `DEFAULT_FINAL_EVIDENCE_PATH`，默认指向 `docs/aiproj-track-final-evidence.md`。随后定义 `TrackEvidenceDoc` 数据类，用来描述每个 A-track 分项文档应该存在什么路径、属于哪条 track，以及必须包含哪些关键术语。比如 A0 文档必须能看到 `archive + runs inventory`、`f/1260` 和 `no training` 这类边界词；A1 文档必须能看到 `scripts/check_static_analysis.py`、`scripts/check_type_analysis.py`、`f/1261` 和 `f/1262`；A4 文档必须能看到 `scripts/check_file_size_ratchet.py`、`docs/code-health/file-size-ratchet.json` 和 waiver 说明。这里选择术语而不是解析复杂 Markdown 表格，是为了让检查保持稳定、低依赖、容易审计。

`FINAL_EVIDENCE_TERMS` 是最终证据表自身的最低契约。它要求 `docs/aiproj-track-final-evidence.md` 同时出现 A0 到 A5、各分项文档路径、`docs/no-promotion-boundary.md`，以及 v1266 主分支和 tag 的 GitHub Actions 成功链接。这里放入 v1266 CI 链接，是因为 v1266 是 A4 的完成版本，并且本版开始时已经确认 main 与 tag CI 均为 success。v1267 自己的远端 CI 会在提交推送后再由 GitHub Actions 验证，因此最终证据文档里写的是已经存在、可复核的 A4 收尾 CI 链接，而不是预填未来链接。

`NO_PROMOTION_TERMS` 则保护模型质量边界。它要求 `docs/no-promotion-boundary.md` 保留 `promotion_ready=False`、`approved_for_promotion=False`、`model_quality_claim`、`lookup-only` 和 `does not automatically mean`。这几个词不是装饰，它们代表本项目后期治理链的一条核心约束：通过一个 governance check 只说明 artifact 内部一致、可追踪、适合某个限定用途，不等于模型可生产、不等于 checkpoint 可推广、不等于生成质量提升。

`DOC_INDEX_TERMS` 和 `CI_COMMAND_TERMS` 分别检查索引与 CI。索引检查覆盖 `README.md`、`docs/README.md`、`START_HERE.md` 和 `docs/script-entrypoints.md`，确保新 closeout 文档和脚本入口不会只存在于文件系统里而没人找得到。CI 检查要求 `.github/workflows/ci.yml` 包含 A1-A4 的关键 gate，以及新增的 `scripts/check_aiproj_track_closeout.py`，并保留 `scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98`。这使 A5 closeout 成为 CI 前置门，而不是本地一次性操作。

## 报告构建流程

核心入口是 `build_aiproj_track_closeout_report()`。调用者可以传入 final evidence 路径和 project root；默认就是当前仓库根目录。函数会解析根目录，定位最终证据文件，然后调用 `_build_checks()` 生成所有 check row。所有 check row 都是统一结构：`check_id`、`target`、`expected`、`actual`、`status`。这种结构和项目里其他报告风格保持一致，便于输出 CSV、Markdown 和 HTML。

`_build_checks()` 的职责很直接。第一步遍历 `TRACK_EVIDENCE_DOCS`，检查每个文档是否存在，并检查每个文档是否包含预期术语。第二步读取 `docs/aiproj-track-final-evidence.md`，检查 `FINAL_EVIDENCE_TERMS`。第三步读取 `docs/no-promotion-boundary.md`，检查 no-promotion 关键边界词。第四步检查 README 和 docs 索引。第五步检查 CI workflow 是否包含必须的命令。它不在这里重跑 A0-A4 的所有 gate，因为 A0-A4 已经各自有 gate 和 CI 入口；A5 的职责是验证“证据地图和收口门”本身没有断。

`build_aiproj_track_closeout_report()` 会根据 failed check 数量计算 `status` 和 `decision`。全部通过时，`status=pass`，`decision=aiproj_track_closeout_ready`；有任何失败时，`decision=repair_aiproj_track_closeout`。`summary` 中记录 `evidence_doc_count`、`check_count`、`passed_check_count`、`failed_check_count`，以及三个聚合布尔值：`no_promotion_boundary_ready`、`final_evidence_ready`、`ci_closeout_gate_ready`。这些字段让命令行、HTML 截图和后续评审都能快速判断问题在哪里。

输出函数 `write_aiproj_track_closeout_outputs()` 使用项目已有的 `write_output_bundle()`，一次性写 JSON、CSV、Markdown 和 HTML。Markdown 由 `render_aiproj_track_closeout_markdown()` 生成，适合命令行或代码评审阅读；HTML 由 `render_aiproj_track_closeout_html()` 生成，适合截图归档。HTML 页面用朴素表格展示所有检查行，顶部统计显示 Checks、Failures、No-promotion 和 CI closeout，避免报告只看起来漂亮但缺少关键数字。

## CLI 入口

`scripts/check_aiproj_track_closeout.py` 是命令行入口。它沿用当前项目的 bootstrap 约定：先从 `scripts._bootstrap` 读取 `PROJECT_ROOT` 和 `ensure_src_path()`，再导入 `minigpt.aiproj_track_closeout`。命令支持 `--final-evidence`、`--project-root`、`--out-dir`、`--require-pass` 和 `--no-fail`。默认情况下它会输出到 `runs/aiproj-track-closeout`，CI 中输出到 `runs/aiproj-track-closeout-ci`，归档时输出到 `f/1267/解释/aiproj-track-closeout/`。

CLI 打印的摘要是可复核的最小证据：`status`、`decision`、`evidence_doc_count`、`check_count`、`failed_check_count` 和输出路径。`resolve_exit_code()` 保证失败时返回非零码，所以这个脚本可以直接作为 CI gate 使用。这里没有使用训练框架、torch 或外部服务，因为 A5 是文档与工程证据收口，保持 stdlib 加项目公共 helper 就足够。

## CI、engineering health 与 workflow hygiene 接入

本版把 closeout gate 接入 `.github/workflows/ci.yml`，位置在 `File size ratchet` 之后、`Archived path portability check` 之前。这个顺序有意保持 A-track 内部的自然顺序：A3 artifact schema guard 先保护 artifact envelope，A4 file-size ratchet 再保护代码健康，A5 closeout 最后检查证据总表和索引，然后才进入更早已有的历史 governance smoke 与 coverage。

`scripts/_bootstrap.py` 的 `HEALTH_ENGINEERING_ENTRYPOINTS` 增加了 `scripts/check_aiproj_track_closeout.py`。这意味着本地运行 `python -B scripts/check_engineering_health.py` 时，也会执行 closeout gate。`scripts/_engineering_health.py` 增加了 `aiproj_track_closeout` step id 和命令构造，输出目录为 `runs/engineering-health/.../aiproj-track-closeout`。本版本真实运行中，engineering health 通过，新增子步骤显示 `status=pass`、`decision=aiproj_track_closeout_ready`、`failed_check_count=0`。

`src/minigpt/ci_workflow_hygiene_policy.py` 增加了 `aiproj_track_closeout` required command，并增加两个顺序检查：`aiproj_track_closeout_after_file_size_ratchet` 和 `aiproj_track_closeout_before_coverage`。`src/minigpt/ci_workflow_hygiene.py` 的 summary 也新增 `aiproj_track_closeout_present`、`aiproj_track_closeout_order_ready`、`aiproj_track_closeout_ready`。这样如果 CI 里删掉 A5 step，或者把它移到 coverage 后面，CI workflow hygiene 会先失败。`src/minigpt/ci_workflow_hygiene_artifacts.py` 也把这些字段写进 Markdown 和 HTML 输出，方便评审查看。

## 静态分析与类型范围

由于新增了一个当前维护脚本和一个当前维护模块，本版同步收紧静态分析和类型检查范围。`scripts/check_static_analysis.py` 的 strict path 默认值加入了 `scripts/check_aiproj_track_closeout.py` 和 `src/minigpt/aiproj_track_closeout.py`，`docs/static-analysis/ruff-baseline.json` 里的 committed strict path 也同步更新。这个同步很重要：如果只改默认值，不改 baseline 里的 strict path，实际运行会继续使用 baseline 旧列表，README 说“已纳入 strict paths”就会变成不准确陈述。

`docs/static-analysis/mypy-scope.json` 的 `scope_floor` 从 14 提升到 16，并新增 `scripts/check_aiproj_track_closeout.py` 与 `src/minigpt/aiproj_track_closeout.py`。新增组名为 `aiproj_track_closeout_gate`。本版真实类型检查结果为 `target_count=16`、`diagnostic_count=0`、`scope_issue_count=0`。这说明 A5 不是只把脚本挂进 CI，而是把它纳入当前严格类型维护面。

## 文档诚实性修正

A5 期间发现 `docs/aiproj-track-a0-census.md` 里原先写的是 A0 当时的“current workflow”。这在 A0 当时是事实，但 A1-A4 之后会被读者误解成当前最终状态。v1267 把该节改成 “CI Reverification At A0 Start”，并明确说明后续 A1-A4 已经添加 ruff、mypy、coverage floor、honest measurement、artifact schema guard 和 file-size ratchet。这个修正不是文字润色，而是 A5 的核心要求：历史证据可以保留，但不能让历史时点的事实伪装成当前事实。

`docs/aiproj-track-a3-honest-measurement.md` 补充了 `tests/test_model_capability_honest_measurement.py`，让文档里的 contract-test marker 说法有明确测试文件引用。`docs/aiproj-track-a3-artifact-schema-guard.md` 补充 `f/1265` 证据路径。`docs/aiproj-track-a4-code-health.md` 补充 `f/1266` 证据路径。`docs/aiproj-track-final-evidence.md` 则新增 `No-Promotion Boundary` 小节，让 docs readability gate 能直接保护这条核心边界。

此外，`src/minigpt/project_docs_readability.py` 把 `docs/aiproj-track-final-evidence.md` 加入稳定文档目标，要求它包含 `Gate-By-Gate Evidence Matrix`、`No-Promotion Boundary` 和 `scripts/check_aiproj_track_closeout.py`。这意味着 final evidence 不只被 A5 closeout gate 检查，也被项目已有的 docs readability gate 检查。

## 测试覆盖

`tests/test_aiproj_track_closeout.py` 覆盖四类行为。第一类是当前仓库通过：断言 `status=pass`、`decision=aiproj_track_closeout_ready`、`failed_check_count=0`，并检查 final evidence、no-promotion 和 CI closeout 三个聚合状态。第二类是 final evidence 负例：在临时仓库里删掉 `docs/aiproj-track-a4-code-health.md` 链接，检查器必须失败。第三类是 no-promotion 负例：删掉 `approved_for_promotion=False` 后必须失败。第四类是输出和 CLI：确认 JSON/CSV/Markdown/HTML 都能写出，CLI 返回码为 0，渲染函数包含预期标题。

现有集成测试也同步更新。`tests/test_ci_workflow.py` 增加 A5 gate 的 presence/order 断言，要求 workflow 中出现 closeout 命令，并保持 file-size ratchet 之后、coverage 之前。`tests/test_engineering_health.py` 确认 engineering health 的第九个步骤是 `scripts/check_aiproj_track_closeout.py`。`tests/test_project_configuration.py` 确认 CI 和 START_HERE 都包含 closeout 命令。`tests/test_project_docs_readability.py` 更新 fixture，让新增 final evidence 文档目标也能通过。

## 运行证据

本版关键本地验证包括：

```text
python -B scripts/check_aiproj_track_closeout.py --out-dir f/1267/解释/aiproj-track-closeout
status=pass
decision=aiproj_track_closeout_ready
evidence_doc_count=6
check_count=57
failed_check_count=0
```

`python -B scripts/check_engineering_health.py --out-dir runs/engineering-health-v1267-probe` 也通过，内部包括 source encoding、project docs readability、CI workflow hygiene、static analysis、type analysis、honest measurement、artifact schema guard、file-size ratchet、A-track closeout 和 normalization guard。normalization guard 继续跑 133 个聚焦测试并通过。

截图使用 Playwright MCP 打开本地 HTTP server 提供的 HTML 报告，保存为 `f/1267/图片/aiproj-track-closeout-v1267.png`。第一次尝试直接打开 `file://` 被浏览器安全策略阻止，因此采用临时 `python -m http.server 8767 --bind 127.0.0.1`。截图完成后该进程会在收尾清理中停止。

## 一句话总结

v1267 把 production-excellence A-track 从“多个已完成的工程门”收束成“有最终证据表、可失败 closeout gate、CI/health/docs 多重保护的可评审阶段成果”。
