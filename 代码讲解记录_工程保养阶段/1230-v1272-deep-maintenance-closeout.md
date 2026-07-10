# v1272 深度工程保养收口：用全仓验证结束清理，而不是继续制造治理版本

## 一、本版目标、前置路线与不做什么

v1272 是 v1268-v1271 深度保养批次的收口版。它要回答的不是“还能不能再拆一个 helper”，而是三个更严格的问题：前四版的修改放回 3700 多个测试的仓库历史中是否仍然兼容；现有 coverage 门是否真正覆盖了活跃工程线；继续做同类保养是否还有足够边际收益。

前置路线很清楚。v1268 治理重复 CI 执行；v1269 压缩并锁住静态分析债务；v1270 拆开 CI hygiene 的混合职责；v1271 收敛治理 JSON loader，并把跨过文件警戒线的 handoff guard 提取成严格类型组件。四版都没有改变模型训练或实验结论，但它们共同触及共享工具、CI 门和治理调用链，因此不能只靠每版几十或一百个聚焦测试宣告完成。

本版明确不做新模型能力、不运行训练、不修改任何 `decide()`、阈值或缓存 checkpoint，也不新增一个名为“deep maintenance checker”的治理链。收口结果用现有 `pytest`、coverage runner、engineering health、GitHub Actions 和文件/静态 ratchet 证明。若验证发现当前批次引入的问题，只修问题本身；若发现冻结科学模块覆盖率低，只记录，不越线改写。

## 二、为什么必须同时跑 pytest 与 CI unittest discovery

项目历史上出现过本地 pytest 可以运行、GitHub Actions 的 stdlib `unittest discover` 却因测试依赖 pytest marker 而失败的情况。因此，“全量测试”不能只写一个模糊总数。v1272 先执行：

```powershell
python -m pytest -q -o cache_dir=runs/pytest-cache-v1272
```

这次在 v1271 已提交维护快照上得到 `3747 passed in 1058.47s`，约 17 分 38 秒。它证明共享 JSON reader、handoff guard 拆分、compatibility facade、报告渲染和历史脚本在 pytest 发现口径下没有回归。

随后执行仓库 CI 同款入口：

```powershell
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-v1272 --fail-under 88.98
```

这个脚本内部调用 `coverage run --source=src/minigpt -m unittest discover -s tests -v`。最终 discovery 数为 3,538。它与 pytest 的 3,747 不相等并不表示少跑了 209 个失败测试，而是两个收集器支持的测试形式不同。v1272 保留两个数字和各自命令，不把它们拼成一个看似更大的“总测试数”。

两轮各耗时约 17 分钟。这是昂贵的最终 closeout 验证，不应成为每个小改动的默认路径。日常仍应先跑涉及模块的 focused tests，再跑 40 秒级 engineering health；只有阶段收口、共享边界重构或发版前才承担双全量成本。

## 三、coverage 输出如何暴露一个真正值得修的缺口

第一次 coverage 运行结果已经通过：`91.01%`，高于 `88.98%` floor。但 HTML 的 Lowest Coverage Files 第一行是 `promoted_training_scale_seed_handoff_assurance_smoke_contract.py`，覆盖 `0/63`。如果只看总百分比，本版可以立刻收尾；但“向完美靠近”的保养不能在活跃 CI 契约模块为 0% 时只庆祝平均数。

只读调查发现，该模块不是废弃历史壳。`scripts/check_promoted_seed_handoff_assurance_smoke.py` 在 CI 中直接导入它，负责把 handoff receipt contract summary、summary check、schema readiness、CI boundary count、reason scope 和八个 sidecar 路径聚合成 smoke checks。现有大型测试确实执行该 smoke，但方式是启动子进程。子进程里的模块执行没有被父进程 coverage 数据文件合并，所以报告显示 0%。

这里有三种可能做法。第一，忽略 0%，理由是“其实跑过”；这会让 coverage 对活跃代码失真。第二，配置 coverage subprocess 并行数据收集；这会扩大工具配置和环境复杂度，仅为一个合同模块不划算。第三，增加进程内 contract tests，直接验证这个模块自己的输入输出边界。v1272 选择第三种，因为它同时改善测量与故障定位。

## 四、新增测试的真实输入、输出和失败语义

新增文件 `tests/test_promoted_training_scale_seed_handoff_assurance_smoke_contract.py` 不启动训练，也不执行完整 seed handoff。它用 `unittest.mock.patch` 替换四个上游构建/写出函数，把 contract 模块当作一个纯编排器测试。这样被测对象仍是真实 `build_receipt_contract_smoke_checks()`，只把昂贵上游替换成可控输入。

成功用例构造 schema v5 summary：`status=pass`、`decision=continue`、v4/v5 ready、handoff count 2、selected count 1、selected reason 在 handoff 范围内、sidecar pass、issue count 0；同时在临时目录实际写出 JSON/text/Markdown/HTML 四种 summary 和四种 check 文件。断言不仅看 `issues=[]`，还逐一确认八个 `CONTRACT_SMOKE_OUTPUT_KEYS` 存在。

失败用例把多个边界同时推向错误：status/decision/schema/readiness 漂移，selected count 2 大于解析失败后回落为 0 的 handoff count，reason scope 为 false，summary/check issue count 非零，八个输出路径全部指向不存在文件。断言保护了“selected 不得超过 handoff”“reason 必须在范围内”“check 无 issue”“sidecar 必须是文件”等具体错误消息。

第三个用例把 scope collection 改成字符串和 `None`，验证 `_boundary_scope_field` 保守返回 0、`_reason_scope_field` 返回 `None`，最终只产生 reason-scope issue。这防止 malformed 上游结构在比较表达式中抛出偶然异常，也证明默认值不是凭空当作通过。

聚焦执行为 `3 passed`。单模块 coverage 为 `59/63`，即 `93.65%`。剩余四个未覆盖语句是少见路径分支，不值得为了 100% 写与行为无关的测试。这里的完成标准是关键合同路径受保护，不是数字崇拜。

## 五、为什么必须重跑完整 coverage

第一次 coverage 通过后新增测试，意味着第一次 HTML 已不再代表最终工作区。v1272 删除本地旧 coverage 输出并完整重跑，而不是把定向 94% 手工加到全仓数字。第二次结果为：

- `status=pass`
- `decision=continue_with_coverage_gate`
- `line_coverage_percent=91.06`
- `covered_lines=90,861`
- `num_statements=99,778`
- `missing_lines=8,917`
- `file_count=1,381`
- `fail_under=88.98`

全仓提升 0.05 个百分点不是主要价值；主要价值是活跃工程合同从错误的 0% 变为 93.65%，且 floor 没有下调、文件没有 exclude、历史测试没有删除。最终只把 1.6 KB Markdown 和约 4 KB HTML 放入 `f/1272`，不归档 7.6 MB 原始 coverage JSON。Markdown/HTML 包含整体摘要和最低覆盖列表，足以复核本版结论；完整 JSON 属于本地中间验证文件，提交它会违反证据经济。

Playwright MCP 打开最终 HTML，accessibility snapshot 明确看到 `Status=pass`、`Line coverage=91.06`、`Covered lines=90861/99778`、`Threshold >= 88.98`。浏览器控制台错误与警告均为 0，截图保存为 `f/1272/图片/deep-maintenance-coverage-v1272.png`。

## 六、v1268-v1272 到底改善了什么

第一类收益是执行成本。v1268 让同一个 commit 的 main push 与 tag 不再各跑一次 CI。v1271 同时推送 commit 与 `v1271.0.0` 后，只产生一个 push run `29061484360`，并成功完成。这是远端事实，不只是 workflow 文本推断。

第二类收益是静态债务控制。v1269 把 ruff baseline 从 545 降到 271，减少 274 条；更新逻辑只能接受旧 issue 集合的真子集，出现新 finding 时 baseline 文件保持不变。后续 v1270/v1271 的修改都在 `271/271, new=0` 下通过，说明 ratchet 真正约束了后续版本。

第三类收益是职责与体积。v1270 的 parity artifact 记录 CI hygiene 入口从 523 到 80，同时 canonical report hash、63 checks 和 61 summary keys 完全一致。v1271 又在 file-size warning 从 21 回升 22 时停下来，把 handoff guard 提取到 113 行严格组件，主文件物理行从 v1270 的 477 降为 413，warning 回到 21。两次拆分都不是按行数平均切，而是按独立变化原因拆。

第四类收益是类型范围。mypy scope 从 v1267 的 16 个目标增长到 20，新加入的 CI hygiene 组件和 handoff guard 都是零诊断。scope floor 同步收紧，所以未来不能静默删掉难检查的目标来恢复绿色。

第五类收益是重复基础设施。v1271 把九个活跃治理 loader 的严格/宽容 JSON 读取合同收敛，并让既有 dedup checker 累计保护 14 个目标。本批目标私有副本为 0；广义历史 census 仍有 496，数字没有被隐藏。

第六类收益是验证可信度。v1272 用 pytest、unittest coverage、focused module coverage、engineering health、Playwright 和远端 CI 从不同层面验证同一批修改。它没有让“文档说完成”替代机械检查。

## 七、剩余债务为什么此时不继续处理

271 条 ruff baseline 仍然很多，但 v1269 已一次消除一半。继续批量处理可能触碰数百个冻结实验 facade；合理方式是活跃区域被真实修改时顺手缩小，不为版本数清零。

21 个 500 行以上文件中大部分是历史测试，八个超过 800 行的文件有 no-growth waiver。它们应在有清晰 fixture/helper 边界时拆分，而不是为了 warning count 把一个测试情景切成难导航碎片。

496 个历史 loader 形状更不适合一次迁移。很多属于版本化科学实验，工程线没有权限改其语义。v1271 已证明渐进路径：选择活跃区域、区分严格和宽容合同、补公开入口负向测试、让 checker 防回贴。

coverage 最低列表中的多个模型能力训练/语料模块只有约 17%-19%。这些低数字真实存在，但它们属于科学线，且完整训练分支可能需要 GPU 或昂贵数据。v1272 不通过 mocks 伪造科学结果，也不为提高平均覆盖修改实验判定。未来若科学线重新激活某个模块，应由那条线设计最小真实实验测试。

最后，两套全量发现各约 17 分钟。可以优化，但应另以 profile 证据决定是否并行、分片或缓存；不能在本版尾声仓促改变 CI 执行语义。

## 八、停止条件与后续建议

v1272 之后停止主动保养版本。当前状态已经具备：tag CI 去重、依赖缓存与并发取消；ruff shrink-only baseline；20 目标严格 mypy；coverage floor；file-size ratchet；14 个 loader dedup 目标；更小的 CI hygiene 与 handoff ownership surfaces；3747 pytest 与 3538 CI discovery 的当前全量证据。

下一步应回到真实需求，而不是继续“治理链 N 次重复”。后续只有以下信号触发保养：新 ruff finding；mypy scope 回退或诊断；活跃文件跨 500/800 阈值；同 commit 重复 CI；共享 loader 被重新粘贴；coverage floor 下降；生产接入提出明确可靠性需求。若没有这些信号，新增版本应服务真实模型能力或真实运行需求。

## 九、一句话总结

v1272 用两套全量发现和最终 coverage 结束 v1268-v1271 的深度保养，并把一个活跃 CI contract 从 0% 补到 93.65%；项目因此更易维护、更难静默退化，但科学能力结论完全未被改写，剩余债务也被如实保留。

