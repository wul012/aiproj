# v1268：CI 执行经济与 Stage-1 评审遗留收口

## 1. 本版目标、问题与明确边界

v1267 已经把 production-excellence A0 到 A5 的证据链收口，并且 branch 与 tag 两次远端 CI 都成功。Claude 随后的独立评审给出 `PASS`，同时指出两个仍需处理的工程遗留：第一，Stage-2 aiproj 简报虽然已经写好，但还处于未跟踪状态，仓库中的其他维护者无法稳定读取它；第二，每次完成版本后先推 `main`、再推 tag，会让同一个 commit 触发两次内容完全相同的 GitHub Actions。后者没有增加新的输入、平台或测试矩阵，只是重复安装依赖并重新执行同一套门，属于可以消除的计算浪费。

因此 v1268 的目标不是继续新增模型治理能力，也不是再增加一条报告链，而是把评审意见转成仓库事实：将 Stage-2 简报以明确的 `INACTIVE` 状态纳入版本控制；把 branch-only push、tag 去重、依赖缓存和同 ref 取消旧任务写入 CI；更重要的是，让这些优化被现有 CI hygiene 检查器机械保护。这样后续维护者不能在不触发失败的情况下悄悄恢复 tag 双跑、删除 pip cache 或移除 concurrency。

本版明确不做四件事。其一，不激活 Stage-2，因为跨项目 capstone 还没有满足简报的前置条件；提交简报只解决“仓库是否拥有这份计划”，不等于授权执行服务化、部署或 standing eval。其二，不删减任何既有 CI 质量门，也不改变门的先后顺序。其三，不降低 `88.98` coverage floor，不修改 ruff baseline、mypy scope 或 file-size waiver。其四，不进入科学线，不运行训练，不修改 checkpoint、缓存实验产物、`decide()` 判定或模型 promotion 结论。

## 2. 前置链路与为什么此时做

这项工作直接承接 v1261 到 v1267 的 production-excellence 链。v1261 引入 staged ruff，v1262 引入 scoped strict mypy，v1263 建立 coverage floor，v1264 和 v1265 分别保护 honest measurement 与 artifact schema，v1266 增加 file-size ratchet，v1267 最终验证 A-track 证据与 no-promotion 边界。到 v1267 为止，CI 已经具备较完整的“检查什么”能力，但还没有系统回答“怎样以更低的重复成本检查”。

Claude 评审提供了外部视角：同一 commit 的 branch run 与 tag run 不是两种证据。GitHub Actions 的输入由 commit 内容、workflow、runner 与依赖决定；当 tag 仅仅指向刚推到 `main` 的同一 commit 时，再跑一次不会覆盖新的代码路径。继续双跑会让每版产生两条约七到八分钟的任务，消耗 runner 时间，也让状态列表更嘈杂。v1268 因此把“证据经济”落实为代码：可信度来自不同失败模式的覆盖，而不是相同命令的重复次数。

## 3. 关键文件及各自角色

`.github/workflows/ci.yml` 是执行面的唯一真实入口。它现在把 `push` 限定为 `main` branch，同时继续保留 `pull_request`。没有 `tags` 或 `tags-ignore` 配置意味着 tag push 不参与该 workflow。文件顶层新增 `concurrency`，group 由 workflow 名与 Git ref 共同组成，`cancel-in-progress: true` 让同一分支或同一 PR 上被新提交取代的旧任务停止。`actions/setup-python@v6` 的 `with` 段新增 `cache: "pip"` 和 `cache-dependency-path: requirements.txt`，使普通源码提交复用 wheel 下载，而依赖清单变化时自动换 cache key。

`src/minigpt/ci_workflow_hygiene_policy.py` 是策略源。新增的 `REQUIRED_EXECUTION_POLICY_FRAGMENTS` 没有把规则散落在测试中，而是给每条执行经济要求一个稳定 ID：`main_branch_push_scope`、`pip_dependency_cache`、`pip_cache_manifest`、`same_ref_concurrency_group` 和 `cancel_superseded_runs`。测试、报告和运行时检查都消费同一个常量，避免文档说一套、检查器写另一套。

`src/minigpt/ci_workflow_hygiene.py` 是验证与报告模型。`_build_checks()` 会为五个必需片段分别产生 `execution:<id>` 检查，并额外产生 `execution:no_tag_push_trigger`。tag 检查不是简单地把“出现 main branch”当成充分条件，而是同时确认 push block 没有四空格层级的 `tags` 或 `tags-ignore`。这让“main 仍运行但 tag 也被重新打开”的配置明确失败。所有检查继续进入统一的 `checks` 数组，所以 JSON、CSV、Markdown、HTML 和 CLI 不会出现不同判定。

`CiWorkflowSummary` 新增五组可读字段。`execution_policy_check_count` 与 `execution_policy_violation_count` 给出数量；`main_branch_push_scope_ready` 表示主分支范围存在；`tag_push_suppressed` 要求主分支范围与无 tag trigger 同时成立；`pip_dependency_cache_ready` 要求 cache 类型和 invalidation manifest 同时成立；`concurrency_cancel_ready` 要求 group 与 cancel 开关同时成立；最终 `ci_execution_economy_ready` 是后三类能力的合取。合取模型很重要，因为单独有 cache 并不能解决双跑，单独取消旧任务也不能解决 tag 再跑。

`src/minigpt/ci_workflow_hygiene_artifacts.py` 把上述字段放进 Markdown summary 和 HTML stats。`scripts/check_ci_workflow_hygiene.py` 将它们打印到终端，便于 CI 日志与人工复核。原有 `decision=continue_with_node24_native_ci` 没有改名，这是刻意保留的公共契约：v1268 扩展了 summary，而没有迫使历史消费者适配一个无必要的新 decision 字符串。

`tests/test_ci_workflow.py` 同时承担正向和负向保护。正向测试要求当前 workflow 的六个 `execution:*` 检查存在，所有 readiness 字段为真，violation count 为零。负向测试以当前真实 workflow 为基础，重新加入 `tags: ['v*']`，同时删除 pip cache 配置，再调用真实 builder。它断言整体状态变为 fail，tag suppression 与 cache readiness 为假，至少出现三条执行策略失败，并要求 recommendation 明确提示恢复执行经济策略。这不是只匹配源码片段的测试，而是验证输入配置经过 builder 后形成的结构化行为。

`tests/test_project_configuration.py` 从仓库配置视角锁定 workflow 文本，防止有人绕过 builder 测试后误改关键 YAML。`docs/ci-execution-economy.md` 则面向维护者解释为什么 tag 不再触发、cache 如何失效以及 concurrency 的隔离单位。`docs/stage2-aiproj-operational-brief.md` 被纳入文档地图，但首行状态仍是 `INACTIVE`，它提供未来路线而不扩大当前授权。

## 4. 输入、处理流程与输出模型

本版检查器的主输入仍是一份 workflow 文本。`build_ci_workflow_hygiene_report()` 读取文件后，先收集 action 版本，再调用 `_build_checks()`。新增执行策略检查与原有 action、forbidden env、required command、required order、Python version 检查处在同一层级。任何一条 `status != pass` 都进入 `failed_checks`，因此执行经济不是警告性建议，而是 fail-closed 门。

处理流程可以概括为：workflow 文本进入原子检查；原子检查形成统一列表；summary 从稳定 check ID 派生组合状态；report 同时保存 policy、summary、actions、checks 和 recommendations；writers 再把同一 report 投影为四种格式。输出 JSON 适合机器消费，CSV 适合逐行审计，Markdown 适合代码评审，HTML 适合浏览器检查。四种输出都是只读证据，不会反向修改 workflow，也不会触发 GitHub Actions。

`policy.required_execution_policy_fragments` 会把策略常量写进报告。这一字段使评审者可以判断“报告依据什么”，而不需要先打开源码。summary 的 `tag_push_suppressed=True` 表示当前配置不会因 tag 单独启动该 workflow；它不声称 GitHub 绝不会运行任何 tag 相关自动化，因为仓库未来可能有其他 workflow。这里的结论严格限定在 `.github/workflows/ci.yml`。

## 5. CI 成本优化的真实语义

tag 去重最容易被误解为“tag 没有测试”。准确说法是：tag 指向的 commit 已由 `main` push 运行完整 CI，tag 不再对相同 commit 重放同一 workflow。若 tag 指向未进入 main 的 commit，当前发布流程本身就不满足本版约定；这不是由 tag workflow 补救的问题。后续如需真正不同的 release job，应建立只做发布签名、制品核验或部署的独立 workflow，而不是重复整个测试 job。

pip cache 只缓存依赖下载，不缓存测试结果。每次 CI 仍会重新运行 source encoding、docs readability、workflow hygiene、ruff、mypy、evidence gates、file-size ratchet、normalization guard 和 coverage。`requirements.txt` 参与 cache key，因此依赖变化不会沿用错误缓存。该优化减少网络与安装成本，不降低测试新鲜度。

concurrency 的 group 包含 `${{ github.workflow }}` 与 `${{ github.ref }}`。前者避免未来不同 workflow 互相取消，后者避免 main 与某个 PR 互相取消。只有同一个 workflow、同一个 ref 的旧 run 会在新 run 到达时停止。该行为对快速连续提交尤其有价值：旧 commit 已经不是待合并的最终候选，继续把它跑完通常不会改变决策。

## 6. 测试、静态门与浏览器证据

聚焦测试执行 `python -m pytest tests/test_ci_workflow.py tests/test_project_configuration.py -q`，结果为 `17 passed`。这里既覆盖真实 workflow 的通过路径，也覆盖恢复 tag trigger 和删除 cache 的失败路径。`python -B scripts/check_ci_workflow_hygiene.py` 生成 `63` 条检查，`63` 条通过，`failed_check_count=0`、`execution_policy_violation_count=0`、`order_violation_count=0`。这说明新增策略没有让原有 31 条命令顺序检查漂移。

scoped mypy 继续得到 `target_count=16`、`diagnostic_count=0`、`scope_issue_count=0`，证明新增 TypedDict 字段与聚合逻辑仍满足严格类型约束。staged ruff gate 保持 `current_issue_count=545`、`baseline_issue_count=545`、`new_issue_count=0`，strict lint 和 format 均通过。本版没有借机更新 baseline，也没有把新问题藏进历史债务。

运行证据写入 `f/1268/解释/ci-execution-economy/`。Playwright 通过本地只读 HTTP 页面打开 HTML，先取可访问性 snapshot，再生成完整页面截图 `f/1268/图片/ci-execution-economy-v1268.png`。snapshot 中可直接看到 Status、Failures、Execution economy、Tag push suppressed、Pip cache 与 Cancel superseded，且 checks 表显示六条执行策略检查全部 pass。截图证明渲染层确实呈现了新增字段，但最终判定仍以 JSON 与测试输出为准。

## 7. 需求-证据闭环与最强质疑

需求一“减少 main/tag 双跑”由 branch-only push 与 no-tag check 实现，证据是 `tag_push_suppressed=True`。需求二“降低重复依赖安装”由 setup-python cache 与 requirements invalidation 实现，证据是 `pip_dependency_cache_ready=True`。需求三“新提交替代旧提交时停止浪费”由 concurrency group 与 cancel 开关实现，证据是 `concurrency_cancel_ready=True`。需求四“优化不能靠约定”由 policy 常量、builder、负向测试和 CI 自检实现。需求五“不能削弱原门”由 `missing_step_count=0`、`order_violation_count=0` 和 coverage 命令仍存在来证明。

最强质疑是：取消 tag run 是否让发布标签缺少独立验证？回应是，本仓库的 tag 与 main 指向同一 commit，原 tag run 没有引入不同平台、依赖、参数或 release-only 检查，因此它不是独立验证，只是重复验证。v1268 保留完整 main CI，并把 tag 策略写入可失败契约；若未来出现真正独立的 release 验证需求，应新增职责不同的 release workflow，而不是恢复内容相同的第二次运行。

## 8. 一句话总结

v1268 把 Stage-1 外部评审的遗留条件全部落实，并把“少跑重复 CI、完整保留质量门”从人工经验升级为可测试、可报告、可回退的工程契约。
