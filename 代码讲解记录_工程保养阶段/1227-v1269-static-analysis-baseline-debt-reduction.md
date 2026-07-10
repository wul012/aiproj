# v1269：静态分析 baseline 深度压缩与 shrink-only 更新门

## 1. 本版为什么做，以及不做什么

v1261 把 ruff 引入 CI 时采用了分阶段策略：新写和高频维护文件必须严格 clean，历史 `src/` 与 `scripts/` 则先登记 545 条 baseline，后续只允许减少。这个策略让项目能在不发动一次高风险全仓改写的情况下获得“新增问题立即失败”的能力。它是正确的起点，但 baseline 长期停在 545 会带来两个问题。第一，真实缺陷与有意兼容结构混在一起，维护者看到 `F401` 或 `E402` 时无法判断它究竟需要修复，还是项目架构要求。第二，`--update-baseline` 虽然文档写着只能收紧，代码却可以把新增 issue 直接写进文件，规则依赖人的自觉，没有机械失败条件。

v1269 因此不是追求一个漂亮的“ruff 全绿”数字，而是重新分类并实质压缩 baseline。可以被结构和测试证明为有意行为的条目，改成精确行级说明；能确认是无用导入或重复绑定的条目直接修复；剩余问题继续如实保留。与此同时，baseline 更新入口从“文档要求 shrink-only”升级成“代码只接受旧 issue 多重集合的子集”。

本版不做全仓自动 `ruff --fix`，因为 F401 的自动修复会删除兼容 facade 的再导出，E702 自动拆行也可能触碰科学实验脚本的执行结构。它不修改 `pyproject.toml` 增加全局或目录级 ignore，因为那会让未来新增违规也被静默隐藏。它不碰训练参数、数据、checkpoint、缓存产物、模型判定和 fixture 期望。它也不声称剩余 271 条都是无害问题；它们仍是需要后续审计的真实历史债务。

## 2. Step-0 census：545 条到底是什么

开工前使用 committed baseline 做分类，原始分布为：`F401=360`、`E702=92`、`E402=62`、`E741=15`、`F841=6`、`F541=5`、`F811=4`、`F821=1`。这组数字揭示了 baseline 并不是一种单一债务。

62 条 E402 全部位于 `scripts/`。这个仓库采用 `src/` layout，又要求许多脚本可以在未执行 `pip install -e .` 的情况下从仓库根直接运行，所以脚本必须先把 `src` 放进 `sys.path`，之后才能 import `minigpt`。从 Python 样式角度看，这些 import 不在文件最前面；从直接脚本契约看，它们必须在 path bootstrap 之后。把它们永久留在 baseline 会让架构性例外看起来像未处理缺陷。

对 F401 的进一步分组发现，179 条来自 `*_artifacts` writer 被 facade 导入但未在 facade 内部调用。历史消费者仍从 `minigpt.training_scale_handoff`、`minigpt.release_gate`、`minigpt.model_card` 等旧模块导入 writer；拆分后的 facade 必须继续暴露这些名字。测试中有明确的 identity 断言，例如 legacy module 的 writer 必须就是 artifacts module 的同一函数对象。这些不是可删除的 unused import，而是兼容 API。

此外，`scripts/run_tiny_scorecard_comparison_smoke.py` 也承担兼容表面：自身主流程只直接使用部分 summary helper，但 `tests/test_tiny_scorecard_comparison_smoke.py` 会从该脚本导入 `render_summary`、`decision_summary` 与 `remediation_gate_status`。自动删除同样会破坏调用方。相反，`model_card.py` 的 `_list_of_dicts` 没有任何引用，`training_portfolio_batch_artifacts.py` 的 datetime/timezone 也没有调用，这几项才是可以删除的真实无用导入。

## 3. 为什么使用精确行级 noqa，而不是配置忽略

本版对 62 条 E402 使用 ruff 自带 `--add-noqa`，生成精确到 import 行或 import block 的 `# noqa: E402`。对确认属于兼容再导出的 facade 使用 `# noqa: F401`。这种处理有三个重要性质。

第一，作用域最小。`pyproject.toml` 没有出现 `scripts/*.py = ["E402"]` 一类 blanket ignore，所以未来新脚本若随意把普通 import 放到执行语句之后，ruff 仍会报告；只有本次已审核的具体 import 被豁免。第二，原因与代码相邻。评审者不需要在 545 条 JSON baseline 中反查某一行，看到 import 就知道它是有意兼容或 bootstrap。第三，运行字节不变。注释不会改变导入对象、导入顺序、函数身份或输出结构。

本次机械命令共添加 62 条 E402 directive 和 206 条 F401 directive。F401 数量不仅包括 178 条非科学线 artifacts 再导出和 tiny scorecard 的 22 条兼容导入，还包括 `maturity` 的 capability constants、`release_gate` 的 policy profile、`training_portfolio` 的 plan builder 等已有测试引用的再导出。每一类都先通过 baseline 来源和调用搜索确认，再保留 API。

## 4. 真实缺陷修复与一次被主动否决的错误简化

`model_card.py` 删除未使用的 `_list_of_dicts` import。`training_portfolio_batch_artifacts.py` 删除未使用的 `datetime` 与 `timezone`。该文件原本还有四个共享 helper import，文件末尾又定义同名 `_dict`、`_list_of_dicts`、`_string_list` 和 `_md`，产生四条 F811。

最初直觉是删除本地函数、直接使用共享 helper，但深度核对发现它们并不完全等价。本地 `_string_list` 会过滤空字符串，共享 `list_of_strs` 不过滤；本地 `_list_of_dicts` 保留原 dict 对象，共享版本会复制；本地 `_dict` 返回原 dict，共享版本也会复制。即使当前测试可能没有覆盖这些微差异，直接替换也会让报告输出存在潜在漂移。

因此最终选择是删除四个错误的共享 import，保留原有本地实现。这样 F811 消失，运行语义保持逐字一致。这个处理体现了本轮“向完美靠近”的核心：优化不是看到重复就强行抽象，而是先证明语义等价；证明不了时，选择更保守的去重方向。真正的共享 helper 收敛会在后续版本通过显式新 helper 和 parity 测试完成，而不是在 baseline 清理版暗中改变行为。

## 5. shrink-only baseline 更新算法

旧实现中，`update_baseline=True` 会先令 `baseline_issues=current_issues`，然后比较当前与当前，自然得到零新增，再把当前结果写入 baseline。只要命令可运行，哪怕当前新增一百条问题，也能被一次 update 合法化。这与文档中的 ratchet 约定矛盾。

新实现先记录 baseline 文件是否已存在，再始终读取旧 issue 集合并与当前集合比较。issue key 由 `path`、`code`、`message` 与去空白后的 `source_line` 组成，不含行号，因此只因前方新增注释导致的行号移动不会被误判成新问题；同时 source line 或错误语义变化仍会得到不同 key。比较使用 `Counter`，所以同一 key 的重复次数也受保护。

当 baseline 已存在且请求 update 时，任何 `comparison["new_issues"]` 都进入 `baseline_update_blockers`，`baseline_update_allowed=False`，整体 status 失败，并且 `write_baseline()` 不会被调用。只有当前 issue 多重集合是旧集合的子集时，update 才允许写入。首次初始化是唯一例外：文件尚不存在时允许把当前集合建立为第一份 baseline，否则项目无法启动该机制。

报告新增 `baseline_update_requested`、`baseline_update_allowed` 与 `baseline_update_blocker_count`。普通检查也会输出这些字段，CLI 明确打印 allowed 与 blocker count。更新前的证明命令显示 `current_issue_count=271`、`baseline_issue_count=545`、`new_issue_count=0`，说明当前集合是严格子集；受保护的 update 随后写入 271；第三次普通检查得到 271/271 和零新增。更新不是直接编辑 JSON 数字，而是由 gate 在 subset 证明成立后生成。

## 6. 测试如何保护行为而不只是保护数字

`tests/test_static_analysis.py` 新增两类对抗测试。增长测试先写一个只含 `os` F401 的已有 baseline，再让 fake ruff 返回 `os` 与新增 `sys` 两条。它要求报告 fail、`baseline_update_allowed=False`、blocker count 为 1，并重新读取文件确认 persisted payload 与调用前完全相等。该断言防止未来有人虽然返回失败，却仍在失败路径覆盖 baseline。

缩减测试让旧 baseline 含 `os` 与 `sys`，当前只剩 `os`。它要求报告 pass、allowed 为真、resolved count 为 1，并验证写回文件的 `issue_count=1`。原有“baseline 文件不存在时可以初始化”的 CLI 测试继续保留，从而覆盖首次建立、正常缩减和非法增长三种状态。

针对 facade，运行了 27 个相关测试文件，共 `294 passed`。范围覆盖 benchmark scorecard、dataset/experiment/model card、generation quality、maturity、project audit、promoted training scale、release gate/bundle/readiness、training portfolio、training scale workflow/handoff/promotion/run decision 与 tiny scorecard smoke。它们验证构建器、writer、CLI、compatibility identity 和报告输出，而不是只跑 import smoke。另一个聚焦批次包含 static analysis、portfolio batch、model card 与 tiny scorecard，共 `31 passed`。

## 7. 结果、报告与剩余债务

正式 `docs/static-analysis/ruff-baseline.json` 由 545 收紧到 271，净减少 274 条，约 50.3%。新分布为 `F401=152`、`E702=92`、`E741=15`、`F841=6`、`F541=5`、`F821=1`。E402 与 F811 已从 baseline 消失。这里特意保留分布，是为了避免只报告一个下降百分比，却不告诉维护者剩下什么。

`F821=1` 是优先级最高的潜在未定义名称，下一轮真实修复应先核对它。`F841/F541` 多半是低风险清理候选。`E741` 涉及短变量名，可在不改变算法的情况下逐批修正。`E702` 大量集中在科学实验脚本的一行多语句，工程线不能为了清零擅自机械改写；需要在不越过两线边界的前提下单独授权或由科学线维护。剩余 F401 也必须继续区分公共再导出与真正无用 import，不能使用一键删除。

正式证据位于 `f/1269/解释/static-analysis-ratchet/`。JSON 是机器真相，CSV 给出剩余 issue，Markdown/HTML 用于审阅。Playwright 第一次打开 HTML 时发现 favicon 404；本版在 renderer 加入 `data:,` 空 favicon 后重新生成，最终页面无控制台错误，快照清晰显示 `status=pass`、`current_issue_count=271`、`baseline_issue_count=271`、零新增与 strict format pass。

## 8. 最强质疑与回应

最强质疑是：“把 268 条问题改成 noqa，只是把 baseline 债务搬到源码注释，是否算真正优化？”如果这些条目本来是可修复缺陷，这个质疑成立。因此本版没有按错误码整类忽略，而是逐类证明：E402 是直接执行 bootstrap 的顺序约束；artifacts F401 是已有调用方和 identity 测试保护的再导出；tiny scorecard helper 是测试从脚本读取的兼容面。精确 noqa 把隐含例外变成代码旁的显式契约，同时让 baseline 只衡量尚未分类或尚未修复的问题。更重要的是，本版还删除了真实无用 import、解决 F811，并封死 baseline 增长入口，不只是移动数字。

## 9. 一句话总结

v1269 将静态分析历史债务从 545 条压缩到 271 条，把架构性例外显式化、真实重复修掉，并用 shrink-only 算法确保 baseline 从此只能变严、不能被新增问题反向扩张。
