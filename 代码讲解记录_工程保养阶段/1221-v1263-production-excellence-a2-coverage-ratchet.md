# v1263 production-excellence A2 coverage ratchet 代码讲解

## 本版目标与边界

v1263 做的是 `docs/production-excellence-aiproj-brief.md` 里的 A2：把测试覆盖率从“能生成报告”推进到“CI 里有真实 floor 的机械门”。这件事看起来只是把 `--fail-under 80` 改成 `--fail-under 88.98`，但它的工程含义不只是调高一个数字。A2 要求 floor 来自实际测量，且初始值等于“观测基线减两个百分点”。v1262 收口时已经跑过完整 `scripts/run_test_coverage.py`，结果是 `line_coverage_percent=90.98`。因此 v1263 的合理起点是 `88.98`，它给正常波动留出两点空间，同时比旧的保守占位 `80` 更接近项目真实状态。

本版明确不做几件事。第一，不为了抬高覆盖率临时补测试，不用“加无意义断言”的方式制造漂亮数字。第二，不改变科学线，也就是不改训练、缓存产物、`decide()` 判定、模型能力 verdict、promotion 相关字段。第三，不把 coverage 结果包装成模型质量证明。覆盖率只说明 Python 工程链路被测试覆盖到什么程度，它不能说明 tiny GPT 的生成能力更强，也不能证明实验结论更成熟。第四，不把历史 README 里早期版本提到的 `--fail-under 80` 全部回写掉；那些是当时版本的历史事实。当前 gate、当前入口文档、当前 workflow hygiene 和当前配置测试必须指向 `88.98`，历史段落可以保留历史语境。

## 前置路线与为什么现在做

A-track 的顺序是 A0 census、A1 static/type analysis、A2 coverage。v1260 先记录项目当时 CI 跑了什么、archive/runs 有多大、README/START_HERE 是否新鲜。v1261 把 ruff 接成 staged static-analysis gate，但没有做仓库级大扫除，而是把历史 545 个发现记成 baseline。v1262 再把 scoped mypy 接上，对八个承重文件做严格类型检查，并用 `scope_floor=8` 防止范围静默缩小。

在这三步之后再做 A2 是合理的：覆盖率门应该站在基本工程门之后。否则 coverage 先跑，可能把编码、文档导航、CI hygiene、ruff、mypy 这些更早更明确的失败信号盖住。当前 `.github/workflows/ci.yml` 的顺序是 source encoding、docs readability、CI workflow hygiene、static analysis、type analysis、各种治理 smoke、normalization guard，最后才是 `scripts/run_test_coverage.py`。v1263 没改变这个顺序，只把最后 coverage gate 的阈值从宽松占位变成基于 v1262 实测的 floor。

## 关键文件与职责

`.github/workflows/ci.yml` 是真正执行的远端门。本版把最后一步改成：

```powershell
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98
```

这意味着 GitHub Actions 上的完整 unittest coverage 低于 88.98 就会失败。这个门是 fail-closed 的，因为 `scripts/run_test_coverage.py` 在生成 coverage JSON 后会调用 `build_test_coverage_report()`，当 `summary.status != "pass"` 时返回 2。换句话说，coverage 报告不是只读展示，它的状态会真实影响 CI。

`docs/static-analysis/coverage-floor.json` 是本版新增的 floor manifest。它记录四个关键事实：`observed_baseline_version=v1262.0.0`、`observed_baseline_percent=90.98`、`floor_policy=observed_baseline_minus_two_points`、`fail_under=88.98`。这个文件的意义是把“为什么是 88.98”从口头解释变成仓库里的可审查证据。后续如果要提高 floor，应先跑新的 coverage 证据，再更新这里；如果有人想降低 floor，就必须改 manifest 和测试，不能只在 workflow 里偷偷改命令。

`src/minigpt/ci_workflow_hygiene_policy.py` 增加了 `COVERAGE_FAIL_UNDER_FLOOR = 88.98`，并让 `REQUIRED_COMMAND_FRAGMENTS["coverage_fail_under_gate"]` 使用这个值。这里的作用不是运行 coverage，而是检查 CI workflow 是否仍然携带正确的覆盖率门。CI hygiene 本身在 coverage 之前运行，所以如果最后的 Unit tests 命令被删掉、顺序错了，或 `--fail-under` 被降回旧值，CI 会在更早的 hygiene 步骤失败，给出更聚焦的错误。

`tests/test_project_configuration.py` 新增了 coverage floor ratchet 断言。测试读取 `docs/static-analysis/coverage-floor.json`，确认 schema、工具名、基线版本、基线百分比、策略名和 `fail_under` 都符合 A2 的起点。同时它检查 `COVERAGE_FAIL_UNDER_FLOOR` 与 manifest 一致，并确认 workflow 里的命令使用同一个 floor。这是本版最重要的“防松动”测试：CI 命令、政策常量和文档 manifest 三者必须同步。

`docs/aiproj-track-a2-coverage.md` 是面向读者的 A2 说明。它不替代 JSON manifest，而是解释 A2 的范围、边界、运行命令、证据要求和 ratchet policy。`docs/static-analysis.md` 也被扩展为 “Static, Type, And Coverage Gates”，因为 production-excellence A-track 的工程门已经从 ruff、mypy 走到 coverage。`docs/engineering-workflow.md` 和 `docs/script-entrypoints.md` 更新了维护者命令，明确当前本地覆盖率命令也应使用 `88.98`，避免开发者本地还按旧的 `80` 判断。

`README.md`、`START_HERE.md`、`docs/README.md`、`f/README.md` 和本目录 README 承担入口索引角色。A-track 已经进入 v1263，如果这些入口还只停在 v1262，读者会以为当前重点仍是 mypy，而不知道 coverage floor 已经收紧。因此本版把当前版本描述改成 A2 coverage ratchet，同时保留 v1262 作为历史上下文。

## 核心流程：从覆盖率报告到 CI 失败

覆盖率链路的输入是完整 unittest 发现：

```powershell
python -B -m coverage run --source=src/minigpt -m unittest discover -s tests -v
```

这一步由 `scripts/run_test_coverage.py` 内部构造，不要求用户手写。测试跑完后，脚本再执行：

```powershell
python -B -m coverage json -o <out_dir>/coverage.json
```

然后 `src/minigpt/test_coverage_report.py` 读取 `coverage.json`，抽取 totals 与每个文件的覆盖率数据。`build_test_coverage_report()` 计算 `line_coverage_percent`、`covered_lines`、`num_statements`、`missing_lines`、`file_count`、`measured_file_count`、`threshold_enabled`、`fail_under` 和 `coverage_gap`。当 `fail_under` 不为空时，`coverage_gap=max(0, fail_under - percent)`；如果 gap 为 0，则 `status=pass`、`decision=continue_with_coverage_gate`；如果 gap 大于 0，则 `status=fail`、`decision=improve_test_coverage`。

这个模型比较透明：没有隐藏评分，也没有把低覆盖文件吞掉。Markdown 和 HTML 会列出最低覆盖文件，用来告诉维护者下一步应该补哪里。v1263 不修改这个计算模型，因为它已经能表达 A2 所需的 threshold 行为。本版只改变门槛来源和 CI 绑定方式。

## 为什么 floor 是 88.98 而不是 90.98

计划书要求“observed baseline − 2 points”。这不是随便保守，而是为了避免初始 coverage gate 因环境、依赖版本、平台细节、少量路径差异而频繁抖动。v1262 的完整 coverage 是 `90.98%`，直接把 floor 设成 90.98 会让 gate 几乎没有波动空间。设成 88.98 则保持了两个判断：一是项目真实覆盖水平已经明显高于 80，不应该继续用 80 当作生产后期保养的门；二是当前还没有必要把 coverage 当成极限优化指标，A2 的目的只是防止测试覆盖倒退。

这个 floor 后续可以上调。比如未来做 A4 文件拆分和测试补强后，如果完整 coverage 稳定到 91.5 或 92，再把 floor 提到 90 或 90.5 是合理的。但下调不应该是普通维护动作。如果某次重构导致 coverage 掉到 87，正确处理不是把 floor 改低，而是看掉的是哪些文件、是否缺测试、是否有合理 waiver。只有在项目测试定义本身经过明确评审调整时，才应该讨论 floor 降低。

## 测试如何保护这版

`tests/test_project_configuration.py` 是新增 ratchet 的主要保护点。它不是简单检查 README 文字，而是读取真实 JSON manifest，并对照 CI workflow 与 `ci_workflow_hygiene_policy.py`。因此三类回归会被拦住：第一，workflow 里有人把 `--fail-under 88.98` 改回 80；第二，policy 常量或 required fragment 和 workflow 不一致；第三，manifest 里的基线/floor 被改成不符合 A2 起点的值。

`tests/test_ci_workflow.py` 继续保护 workflow hygiene 的整体结构。由于 required fragment 已经变成 `--fail-under 88.98`，当前 workflow 通过说明 CI hygiene 能识别新 floor。测试里的临时 workflow fixtures 也同步成 88.98，避免单测还在教育代码接受旧门槛。

`tests/test_test_coverage_report.py` 仍然保护 coverage report 本体：低于 threshold 时返回 fail，高于 threshold 时返回 pass，CLI 可以写出 JSON/CSV/Markdown/HTML，HTML 转义正常。v1263 没改这个模块，说明 A2 可以复用已有覆盖率报告能力，而不是再造一条 report 链。

文档可读性测试保证新文档链接不破坏当前 docs navigation。`docs/README.md` 和 root `README.md` 都新增了 A2 文档入口，`START_HERE.md` 也把当前版本总结推进到 v1263。这样读者从任何入口进入，都能看到当前项目已经从 A1 static/type 走到 A2 coverage ratchet。

## 运行证据与截图

本版正式证据会归档在 `f/1263`：`f/1263/解释/test-coverage/` 保存 `test_coverage_report.json`、CSV、Markdown、HTML，`f/1263/解释/说明.md` 解释运行命令、关键字段和边界，`f/1263/图片/test-coverage-v1263.png` 用浏览器截图确认 HTML 报告能被人直接阅读。截图不是为了证明 coverage 数学正确，数学正确由 JSON 和测试保护；截图的作用是证明最终归档里的人类可读报告没有空白、乱码或明显布局问题。

本地验证还包括 ruff/py_compile、聚焦测试、CI workflow hygiene、project docs readability、source encoding、static analysis、type analysis、engineering health 和完整 coverage。远端验证以 GitHub Actions 的 `ci` workflow 为准。v1263 的 CI 通过才算收口，因为 A2 的目标本来就是让远端 CI 真的执行新 floor。

## 链路角色

v1263 让 A-track 从“已有 coverage 报告”变成“coverage 有接近真实基线的门”。在更早版本里，coverage 已经被 release readiness、maturity、portfolio comparison 等治理报告消费过，但那个时候门槛常常是保守的 80，用于证明“有 coverage 证据”。A2 的区别在于：现在 coverage 证据不只是存在，还必须不明显倒退。它是后续 A3 reproducibility、A4 code health、A5 docs honesty 的基础门之一。

这版也继续遵守两条线边界。工程线可以收紧 lint、type、coverage、docs、CI、hygiene；科学线的模型能力实验仍由对应会话推进。覆盖率上升或通过不代表模型更聪明，只代表工程代码在测试视角下更少裸奔。把这两个概念分清，是 aiproj 后期保养里最重要的诚实边界之一。

## 一句话总结

v1263 把 aiproj 的覆盖率检查从宽松占位升级为基于真实测量的 CI ratchet：`90.98%` 是基线，`88.98` 是当前 floor，manifest、workflow hygiene 和配置测试共同防止它静默倒退。
