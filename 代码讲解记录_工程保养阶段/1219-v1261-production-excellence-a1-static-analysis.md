# v1261 production-excellence A1 static analysis 代码讲解

## 一、本版目标与边界

v1261 继续执行 `docs/production-excellence-aiproj-brief.md` 里的 A-track。v1260 已经完成 A0：确认 CI 真实形状、记录 archive/runs 体量、刷新入口文档。本版进入 A1 的第一步：把 Python 静态分析真正接入项目，而不是只在文档里说“以后要 lint”。

这件事看起来像工具配置，但它在 aiproj 里很关键。当前仓库有大量历史版本脚本、治理报告生成器、实验分析模块和 CLI 入口。它们来自一千多个版本的累积，其中很多文件保留了当时的实验痕迹。如果直接对 `src/` 和 `scripts/` 做一次全仓 `ruff --fix` 或 `ruff format`，短期看起来会很整洁，但风险很大：一是会制造海量机械 diff，真实行为变化被淹没；二是历史证据链会被无意义扰动；三是违反 brief 里的失败条件，即“Lint/type adoption via repo-wide mechanical sweep in one commit = revert”。所以 v1261 的策略不是“假装历史都干净”，而是先让静态分析进入 CI，再把历史问题显式 baseline 化，让后续新增问题不能继续流入。

本版明确不做几件事：不改变模型训练语义，不修改 cached artifact verdict，不重跑历史模型能力实验，不把 governance `status=pass` 包装成模型质量提升，不引入 mypy。mypy 是 A1 的下一段工作，本版只处理 ruff 的 lint/format 接入和 CI 门禁。

## 二、前置路线：从 A0 census 到 A1 gate

v1260 的 A0 已经把“当前 CI 到底跑什么”写进 `docs/aiproj-track-a0-census.md`。A0 的一个结论是：`pyproject.toml` 有 pytest 配置，但没有 ruff、black、mypy 这类静态工具。A1 就是接着这个缺口做。

本版遵循两个原则。

第一，工具必须可运行、可失败、可测试。只新增 `pyproject.toml` 里的 `[tool.ruff]` 不够，因为这只是配置，不是门禁。v1261 增加了 `scripts/check_static_analysis.py`，把 ruff 执行、baseline 对比、strict path 检查、报告输出和退出码统一起来，并把它加入 CI。

第二，历史债务必须可见但不能一次性重写。真实运行发现 `src/` 和 `scripts/` 在当前 ruff 规则下有 545 个 historical findings。v1261 把它们写入 `docs/static-analysis/ruff-baseline.json`。以后当前 findings 和 baseline 对比，如果出现 baseline 外的新 finding，脚本返回失败；如果历史 finding 被修掉，则报告会显示 resolved baseline issue。这样做的好处是：历史问题不会继续挡住工具落地，但新增问题会被挡住。

## 三、关键文件与职责

### 1. `scripts/check_static_analysis.py`

这是本版核心入口。它做四件事。

第一，运行 ruff lint：

```text
python -m ruff check --output-format=json src scripts
```

它不直接把 ruff 的退出码当作最终结果。ruff 发现 lint issue 时通常返回 1，但在 baseline 模式下，发现“已知历史 issue”不应该让本版失败。因此脚本会解析 JSON 输出，把当前 issue 规范化为稳定结构，再和 baseline 比较。

第二，计算 issue key。脚本没有只用行号，因为历史文件以后插入几行注释时，行号可能漂移。如果仅用 `path + code + line`，轻微移动就会把旧问题误判成新问题。本版使用的比较 key 是：

```text
path + code + message + source_line
```

这意味着同一文件里同一条源代码触发同一类问题，即使行号移动，也仍然被认为是同一个历史 finding。它不是完美的语义指纹，但比单纯行号稳定，也比只统计数量更严格。数量统计会漏掉“删掉一个旧 F401，同时新增一个新 F401”的情况；source-line key 能更好地保护新增问题。

第三，执行 strict path 检查。baseline 只兜住历史债，不能兜住本版新维护面。脚本里有 `DEFAULT_STRICT_PATHS`，包括本版和当前工程健康链路的维护入口，例如：

```text
scripts/check_static_analysis.py
scripts/check_archive_runs_inventory.py
scripts/check_engineering_health.py
scripts/_bootstrap.py
scripts/_engineering_health.py
src/minigpt/ci_workflow_hygiene.py
src/minigpt/ci_workflow_hygiene_policy.py
```

这些 strict path 上如果还有 ruff lint issue，就算该 issue 在 baseline 里，也会失败。原因很简单：当前维护入口应该比历史脚本更干净。脚本还会对 strict path 跑：

```text
python -m ruff format --check ...
```

这样本版不是只做 lint，也把 format check 纳入了 A1 的第一步。

第四，输出证据。脚本写出 JSON、CSV、Markdown、HTML 四种格式：

```text
static_analysis.json
static_analysis_issues.csv
static_analysis.md
static_analysis.html
```

JSON 是机器可读的主证据；CSV 方便看 issue 行；Markdown 方便文档归档；HTML 方便截图审查。

### 2. `docs/static-analysis/ruff-baseline.json`

这是本版最重要的 contract 文件之一。它不是“通过证明”，而是“历史债务清单”。v1261 的 baseline 数字是：

```text
issue_count=545
```

这些 issue 来自 `src/` 和 `scripts/`。后续如果做分批清理，应该让这个文件的 issue 数量下降，或者在重构移动代码时发生可解释的 re-key。不能用 `--update-baseline` 偷偷把新增问题吞掉。`docs/static-analysis.md` 里也专门写了这一点。

### 3. `pyproject.toml` 与 `requirements.txt`

`requirements.txt` 新增：

```text
ruff>=0.8,<1.0
```

CI 安装 requirements 后就可以运行 ruff，不依赖开发者本机是否预装。

`pyproject.toml` 新增：

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F"]
```

这里没有一上来选择所有规则。`E4/E7/E9/F` 更偏 Python 语法、运行时风险和 pyflakes 级别的问题，例如未定义变量、未使用导入、重复定义等。它比纯格式规则更接近“会造成维护或运行风险”的问题，也更适合 A1 第一版。后续如果要扩展到 import order、bugbear、复杂度或 docstring，需要先观察噪声，再按目录批次推进。

### 4. CI workflow 与 CI hygiene

`.github/workflows/ci.yml` 新增：

```yaml
- name: Static analysis gate
  run: python -B scripts/check_static_analysis.py --out-dir runs/static-analysis-ci
```

它放在 `CI workflow hygiene check` 后面、其他 evidence checks 和 coverage 前面。这样 CI 会更早发现 Python 静态问题，不必等到 20 多分钟 coverage 才失败。

更重要的是，`src/minigpt/ci_workflow_hygiene_policy.py` 也新增了 required command 和 ordering：

```text
static_analysis_gate -> scripts/check_static_analysis.py
static_analysis_after_ci_hygiene
static_analysis_before_coverage
```

这表示 static analysis 不只是 workflow 里的一行命令，而是被 CI hygiene 自己监督。以后如果有人删掉这一步，或者把它移到 coverage 后面，`scripts/check_ci_workflow_hygiene.py` 会失败。`src/minigpt/ci_workflow_hygiene.py` 也新增了 summary 字段：

```text
static_analysis_present
static_analysis_order_ready
static_analysis_ready
```

这些字段会进入 JSON/Markdown/HTML 报告，便于 reviewer 直接看 gate 状态。

### 5. `scripts/_bootstrap.py` 与工程健康聚合

`scripts/_bootstrap.py` 的 `HEALTH_ENGINEERING_ENTRYPOINTS` 新增：

```text
scripts/check_static_analysis.py
```

`scripts/_engineering_health.py` 增加 `static_analysis` step。这样本地维护者运行：

```powershell
python -B scripts/check_engineering_health.py
```

时，会同时跑 source encoding、docs readability、CI workflow hygiene、static analysis、normalization guard。它不是 CI 的替代品，但能把当前工程健康的快照集中到一个命令里。

## 四、Windows 解码问题与修复

本版实现时遇到一个真实的小坑：第一次跑 baseline 时，ruff JSON 输出里包含非 GBK 字符，Windows 上 `subprocess.run(text=True, capture_output=True)` 默认按系统编码解码，后台 reader thread 报了：

```text
UnicodeDecodeError: 'gbk' codec can't decode byte ...
```

这会导致 stdout 捕获不完整，从而产生误判。v1261 在 `run_ruff_check` 和 `run_ruff_format_check` 里显式设置：

```python
encoding="utf-8"
errors="replace"
```

这是一个很典型的跨平台工程细节。CI 在 Linux 上不一定暴露这个问题，但本地 Windows 会暴露；如果不修，静态分析报告本身就不可靠。

## 五、测试覆盖

`tests/test_static_analysis.py` 是本版新增测试。它覆盖几类关键行为。

第一，baseline comparison。测试证明：baseline 里已有的 issue 不算新增，真正多出来的 source line 会进入 `new_issues`。这保护了“历史债不挡门、增量债要失败”的核心语义。

第二，strict lint。测试构造一个 strict path，即使 issue 已经在 baseline 里，只要 strict path 还有 lint finding，报告也必须失败。这避免维护入口退化成“反正 baseline 里有，就继续放任”。

第三，strict format。测试模拟 `ruff format --check` 返回失败，报告必须失败，并记录 `strict_format_status=fail`。

第四，CLI baseline update。测试用 fake runner 模拟 ruff 输出，调用 `main([... --update-baseline ...])`，确认 baseline 文件和 report 文件都被写出。这证明命令行路径不是只在函数层面可用。

第五，输出格式。测试确认 JSON/CSV/Markdown/HTML 都生成，避免后续维护时删掉某个输出格式却没有反馈。

此外，已有测试也被扩展：

- `tests/test_ci_workflow.py` 现在检查 static analysis required command、order 和 summary 字段。
- `tests/test_engineering_health.py` 检查工程健康步骤顺序。
- `tests/test_project_configuration.py` 检查 requirements、CI、START_HERE 和 docs 入口。
- `tests/test_script_surface_registry.py` 通过 `docs/script-entrypoints.md` 确认新的 maintainer script 被文档索引。

## 六、运行证据与输出解释

本版真实运行命令：

```powershell
python -B scripts/check_static_analysis.py --out-dir f/1261/解释/static-analysis --update-baseline
```

得到：

```text
status=pass
decision=continue_with_static_analysis_gate
current_issue_count=545
baseline_issue_count=545
new_issue_count=0
strict_lint_issue_count=0
strict_format_status=pass
```

这里的 `status=pass` 不能读成“全仓没有问题”。正确读法是：当前 findings 与 committed baseline 一致，没有新增问题；strict path 没有 lint issue；strict path format check 通过。这个边界很重要，因为 aiproj 一直强调 honest measurement，不把治理工具的 pass 夸大成模型能力或生产成熟度。

证据保存在：

```text
f/1261/解释/static-analysis/
```

截图保存在：

```text
f/1261/图片/static-analysis-v1261.png
```

## 七、本版在项目链路里的位置

从项目成熟度看，v1261 做的是“工程底座加固”，不是模型能力提升。它的价值在于把未来改动的最低质量线抬起来：以后新增脚本或修改维护入口时，ruff 会给出早期反馈；CI hygiene 会保证这个 gate 继续存在；engineering health 会让本地维护者用一个命令看到它。

这也为后续 A1.2 mypy 做铺垫。ruff 先解决语法、导入、未定义变量、格式等低层问题；mypy 再进入 load-bearing 模块的类型边界。顺序上先 ruff 后 mypy是合理的，因为 mypy 的噪声和类型设计成本更高，需要先稳定静态分析入口和 CI 位置。

## 一句话总结

v1261 把 aiproj 从“没有静态分析工具”推进到“ruff 已进入 CI，历史问题有 baseline，新增问题会失败，维护入口必须 lint/format 干净”的可持续工程保养阶段。
