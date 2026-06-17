# v1180 MiniGPT grokking evidence check 代码讲解

## 本版目标与边界

v1180 接在 v1179 之后。v1179 是这一阶段非常重要的一版：它不再是连续几个版本里的“诚实空结果”，而是在 toy-scale modular addition 上复现了 grokking，也就是训练集很早被记住，验证集在很长时间里接近随机，然后很晚突然泛化。v1179 的真实 RTX 4060 运行给出 `grokking_reproduced_wd_driven`：with weight decay 的 5 个 seed 全部 grok，no weight decay 的 5 个 paired ablation 全部只记忆不泛化。

正因为 v1179 是正结果，它比空结果更需要复核。空结果一般只要证明“没有看到提升”即可；正结果会被后续 README、路线总结、能力说明反复引用。如果正结果只停留在文字叙述里，长期维护时很容易出现两个风险：第一，summary 写错但 rows 里不是这样；第二，后续有人引用“grokking 已复现”时忘了它的 toy-scale boundary。v1180 的目标就是把 v1179 的核心声明从 JSON rows 里重新推导出来，形成一个独立的 evidence check。

本版明确不做训练，也不重新跑 40k step。它只读取：

```text
f/1179/解释/grok_v1179/grok_v1179.json
```

然后检查这个 artifact 是否足以支持三个主张：

```text
1. with weight decay 的 5 个 seed 都记忆且 grok
2. no weight decay 的 5 个 seed 都记忆但没有 grok
3. grok 是真实延迟泛化，不是 train/val 一起慢慢升高
```

这是一版证据复核，不是新模型能力实验。它的边界字段也写得很清楚：

```text
artifact_reconstruction_only_no_training_rerun
```

## 为什么要做这个 check

v1179 的结果非常漂亮：`t_mem` 基本是 100 step，而 `t_gen` 平均约 14880 step；`val_at_mem` 平均只有 0.147，说明模型在记住训练集时验证集仍然接近随机；with-decay 最终验证准确率接近 0.96，而 no-decay 最终验证准确率约 0.16。这个现象符合 grokking 的经典定义。

但工程上不能只说“看起来像”。v1179 JSON 里有两类信息：一类是 summary，例如 `wd_on_grok_rate=1.0`、`wd_off_grok_rate=0.0`；另一类是 rows，例如每个 seed、每个 weight decay arm 的 `memorized`、`grokked`、`t_mem`、`t_gen`、`grok_gap`、`val_at_mem`。v1180 做的就是用 rows 重新算一遍 summary 关键结论。

这有点像对账：如果 summary 说 5/5 grok，但 rows 里只有 4 个 seed grok，check 必须失败；如果 summary 说 no-decay 没有 grok，但 rows 里某个 no-decay seed 有 `grokked=True`，check 也必须失败；如果所有 seed 都 grok 了，但 `val_at_mem` 已经很高，那就是普通慢学习，不是 grokking，check 也要失败。

## 新增模块 `grok_evidence_check_v1180.py`

核心模块是 `src/minigpt/grok_evidence_check_v1180.py`。模块只依赖通用 report helpers，不依赖 PyTorch，也不导入 `grok_v1179` 的训练代码。这个选择是有意的：证据复核器不应该重建训练环境，也不应该因为训练模块的实现变化而改变对旧 artifact 的解释。

入口常量：

```python
GROK_EVIDENCE_CHECK_STEM = "grok_evidence_check_v1180"
GROK_SOURCE_DEFAULT_NAME = "grok_v1179.json"
```

和之前的 report/check 模式一样，`locate_grok_report` 支持目录或文件输入。如果传入目录，就寻找 `grok_v1179.json`；如果传入具体 JSON 文件，就直接读取。`read_json_report` 使用 `report_utils.read_json_object`，确保输入是 JSON object。

主函数是：

```python
build_grok_evidence_check(grok_report_or_path, min_delay_steps=1000, max_val_at_mem=0.5)
```

默认要求平均 grok gap 至少 1000 step，并且 memorization 时验证准确率低于 0.5。这里不用 v1179 的 `eval_every` 作为唯一阈值，是为了让复核器更严格：只晚一个 eval interval 不能算强 grokking；v1179 的真实 gap 是 14780，远高于 1000，因此通过得很宽裕。

## 输入分组和指标重算

函数首先读取 summary 和 rows：

```python
summary = as_dict(grok_report.get("summary"))
rows = list_of_dicts(grok_report.get("rows"))
seed_count = int(number_or_default(summary.get("seeds"), 0, int))
wd_on = float(number_or_default(summary.get("weight_decay_on"), 1.0))
wd_off = float(number_or_default(summary.get("weight_decay_off"), 0.0))
```

随后 `_group_rows` 把 rows 分成两组：

```text
wd_on
wd_off
```

分组依据是每行的 `weight_decay`。v1179 的 paired design 是同一 seed 下只改变 weight decay，因此这两组应该各有 5 行。这个 grid 是否完整是 check 的核心条件之一。

`_metrics` 从两组 rows 重算：

```text
wd_on_mem_count
wd_on_grok_count
wd_off_mem_count
wd_off_grok_count
wd_on_mean_gap
wd_on_mean_val_at_mem
```

这几个数就足以重建 v1179 的核心 claim。真实 artifact 得到：

```text
wd_on_mem_count = 5
wd_on_grok_count = 5
wd_off_mem_count = 5
wd_off_grok_count = 0
wd_on_mean_gap = 14780.0
wd_on_mean_val_at_mem = 0.14693769365549086
```

这里 `wd_off_mem_count=5` 很关键。它说明 no-decay ablation 并不是训练坏了，而是能记忆训练集却不能泛化。这样才能把“weight decay 驱动泛化”与“no-decay 优化失败”区分开。

## 十个检查项

v1180 输出的 `rows` 其实是 check rows。每个 check 都有：

```text
id
status
expected
actual
detail
```

第一个检查是 `source_status_pass`。如果 v1179 source report 自身不是 pass，本版不能继续引用它作为正结果。

第二个检查是 `source_verdict_wd_driven`。v1180 专门复核的是 v1179 的 headline claim，因此期望 verdict 是：

```text
grokking_reproduced_wd_driven
```

第三个检查是 `seed_arm_grid_complete`。它要求 with-decay 和 no-decay 两组各有 `seed_count` 行，总行数为 `seed_count * 2`。如果某个 seed 缺少 paired ablation，weight decay 的因果判断就不完整。

第四个检查是 `wd_on_memorized_all`，要求 with-decay 的所有 seed 都先记忆训练集。grokking 是“先记忆再泛化”，如果没有记忆阶段，后面就不是这个现象。

第五个检查是 `wd_on_grokked_all`，要求 with-decay 的所有 seed 都达到 grok。v1179 的强 claim 是 5/5，不是 3/5 或 4/5。

第六个检查是 `wd_off_memorized_all`，要求 no-decay ablation 也能记忆。这个检查很容易被忽视，但它对解释很重要：如果 no-decay 没记住训练集，那只能说优化失败；现在它能记忆但不泛化，才支持 weight decay 与泛化转变相关。

第七个检查是 `wd_off_did_not_grok`，要求 no-decay 的 grok count 为 0。这是 “wd-driven” verdict 的关键。

第八个检查是 `delay_real`，要求平均 gap 足够长且 `val_at_mem` 足够低。它防止把普通共同收敛误认成 grokking。测试里专门构造了 `val_at_mem=0.82` 的伪 grok 场景，check 会失败。

第九个检查是 `summary_rates_match_rows`。它把 rows 重算出的 rate 和 summary 里的 `wd_on_grok_rate` / `wd_off_grok_rate` 对齐。这个检查防止 summary 和 rows 不一致。

第十个检查是 `boundary_present`，要求 v1179 保留：

```text
toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim
```

因为 v1179 是正结果，更容易被过度外推。本检查强制 boundary 留在 artifact 里。

## CLI 入口

脚本是 `scripts/check_grok_evidence_v1180.py`。运行示例：

```powershell
python scripts\check_grok_evidence_v1180.py f\1179\解释\grok_v1179 --out-dir f\1180\解释\grok_evidence_check_v1180 --require-pass --force
```

它支持：

```text
grok_report
--out-dir
--min-delay-steps
--max-val-at-mem
--require-pass
--force
```

默认阈值足以复核 v1179 的强延迟。`--require-pass` 让它能进入 CI 或后续 release gate：只要任何 check fail，脚本返回 1。

输出仍然走 readability artifacts：

```text
grok_evidence_check_v1180.json
grok_evidence_check_v1180.csv
grok_evidence_check_v1180.txt
grok_evidence_check_v1180.md
grok_evidence_check_v1180.html
```

HTML 已用 Playwright MCP 打开并截图：

```text
f/1180/图片/grok-evidence-check-v1180.png
```

## 测试覆盖

新增测试文件是 `tests/test_grok_evidence_check_v1180.py`。

第一个测试 `test_reconstructs_v1179_grokking_claim_from_rows` 构造一个 5 seed 的 fixture，with-decay 全部 grok、no-decay 全部不 grok，检查报告必须 pass，并且计数正确。

第二个测试 `test_fails_when_validation_was_already_high_at_memorization` 把 with-decay 行的 `val_at_mem` 改成 0.82。这样虽然它可能最终 grok，但 memorization 时验证集已经很高，不是“先记忆、后泛化”的 grokking。报告必须 fail，失败项包含 `delay_real`。

第三个测试 `test_fails_when_no_decay_ablation_groks` 让一个 no-decay seed 也 grok，并同步修改 summary 的 rate。报告必须 fail，失败项包含 `wd_off_did_not_grok`。这保护 weight-decay-driven 这个主张。

第四个测试 `test_outputs_and_cli_are_wired` 验证目录输入、输出五件套和 CLI。

focused 验证命令：

```powershell
python -m py_compile src\minigpt\grok_evidence_check_v1180.py scripts\check_grok_evidence_v1180.py tests\test_grok_evidence_check_v1180.py
python -m pytest tests\test_grok_evidence_check_v1180.py tests\test_grok_v1179.py -q -o cache_dir=runs\pytest-cache-v1180-focused
```

结果是 `20 passed`。

## 在项目链路中的位置

v1179 是训练动力学线的正结果，v1180 是它的证据保险丝。它不是在“多做一个报告”，而是在项目里确立一个原则：凡是重要正结果，尤其是会被后续版本引用的正结果，都应该能从 artifact 反推。这样项目不会只有漂亮叙述，也有可审计的 JSON rows 和 check rows。

如果后续继续推进 grokking 线，合理方向可以是 train_frac sensitivity 的正式 artifact、weight decay 强度 sweep、或小模型容量变化对 grok delay 的影响。但这些都应该建立在 v1180 通过之后，因为 v1180 确认 v1179 这个正结果本身可以被复核。

## 一句话总结

v1180 把 v1179 的 grokking 正结果从 README 叙述提升为可审计证据：5/5 with-decay grok、0/5 no-decay grok、平均延迟 gap 14780 step、memorization 时验证准确率仍接近随机，这些都能从归档 rows 重新推导出来。
