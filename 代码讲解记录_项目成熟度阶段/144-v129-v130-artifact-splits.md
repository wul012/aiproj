# v129/v130 artifact split 合并代码讲解

## 本版目标

v129 和 v130 都属于同一类收口：把“计算/组装业务对象”和“把对象写成证据文件”拆开。v129 处理 `training_portfolio_batch.py`，v130 处理 `experiment_card.py`。这两步解决的是代码职责偏宽的问题，而不是新增模型能力。

本轮明确不做三件事：

- 不改变 training portfolio batch 或 experiment card 的 JSON schema。
- 不改变 CLI 脚本、输出文件名和旧 import 路径。
- 不把治理证据包装成模型质量提升；模型能力仍需要真实 checkpoint、固定 benchmark 和更大数据来证明。

## 前置路线

这两版接在 v110 module pressure audit 之后。v110 让项目有了可运行的模块压力判断，后续 v111-v128 已经陆续拆过 registry、server、dashboard、benchmark、maturity、comparison 等边界。v129/v130 继续沿用同一个原则：

```text
先找稳定边界
再拆 artifact writer/render helper
保留 facade 和旧脚本入口
用测试证明行为不变
```

这也回应了之前对版本粒度的判断：低风险、同类型迁移不应无限拆小。v129 没单独写一篇讲解，v130 把两次相邻 artifact split 合并说明，作为后续类似收口的参考。

## 关键文件

- `src/minigpt/training_portfolio_batch.py`: v129 后保留 batch 计划、执行编排和旧导出 facade。
- `src/minigpt/training_portfolio_batch_artifacts.py`: v129 新增，负责 training portfolio batch 的 JSON/CSV/Markdown/HTML 输出。
- `src/minigpt/experiment_card.py`: v130 后保留 run 目录读取、registry 匹配、summary/data/training/evaluation/artifact/recommendation 组装。
- `src/minigpt/experiment_card_artifacts.py`: v130 新增，负责 experiment card 的 JSON/Markdown/HTML 输出和 HTML/Markdown 渲染 helper。
- `tests/test_training_portfolio_batch.py`: 保护 v129 的 batch 输出契约和 facade identity。
- `tests/test_experiment_card.py`: 保护 v130 的 experiment card 输出契约、HTML escaping 和 facade identity。
- `README.md`、`c/130/解释/说明.md`: 记录版本目标、证据位置和边界说明。

## v129 的拆分语义

`training_portfolio_batch.py` 的核心价值是根据 variant matrix 生成训练组合批处理计划，并在需要时编排每个 variant 的 portfolio 运行。拆分前，它还直接承担了这些输出职责：

```text
training_portfolio_batch.json
training_portfolio_batch.csv
training_portfolio_batch.md
training_portfolio_batch.html
```

v129 把这些输出函数移入 `training_portfolio_batch_artifacts.py`。迁移后，核心模块更像“batch 计划与执行编排”，artifact 模块更像“证据发布层”。`training_scale_run.py` 也改为从 artifact 模块导入写出函数，说明新的依赖方向更清楚。

输出文件仍是只读证据，不参与训练，不反向修改配置。CSV 是索引型证据，Markdown/HTML 是人工审阅证据，JSON 是机器可消费证据。

## v130 的拆分语义

`experiment_card.py` 的核心价值是把一个 run 目录整理成 experiment card：

```text
train_config.json
history_summary.json
dataset_report.json
dataset_quality.json
eval_report.json
eval_suite/eval_suite.json
run_manifest.json
model_report/model_report.json
run_notes.json
registry.json
```

这些输入被归并成：

```text
summary
notes
data
training
evaluation
registry
artifacts
recommendations
warnings
```

拆分前，`experiment_card.py` 同时负责组装这些结构并把它们渲染成 JSON/Markdown/HTML。v130 把后半段移到 `experiment_card_artifacts.py`。这样 `build_experiment_card()` 的职责更清楚：只产出结构化 card dict；`write_experiment_card_outputs()` 的职责也更清楚：只发布证据文件。

## facade 为什么要保留

保留旧 facade 是为了让已有调用方不用立即迁移。例如：

```python
from minigpt.experiment_card import build_experiment_card, write_experiment_card_outputs
```

拆分后这条 import 仍然有效，只是 `write_experiment_card_outputs` 的真实实现来自 `experiment_card_artifacts.py`。测试里的 identity 断言保护的就是这一点：

```text
experiment_card.write_experiment_card_outputs
is experiment_card_artifacts.write_experiment_card_outputs
```

这类断言看起来小，但很有价值：它能防止后续重构时旧入口悄悄变成另一份 wrapper 或残留实现，导致行为分叉。

## 测试覆盖

v129 的测试重点是：

- batch 输出仍包含 JSON/CSV/Markdown/HTML。
- 新 artifact 模块渲染函数能被直接导入。
- 旧 facade 仍指向新 artifact 实现。
- 输出检查不依赖临时目录绝对路径，减少脆弱断言。

v130 的测试重点是：

- `build_experiment_card()` 仍能读取 run 与 registry 上下文。
- `write_experiment_card_outputs()` 仍生成同名 JSON/Markdown/HTML。
- HTML escaping 继续保护 note、tag、title 中的特殊字符。
- 旧 `minigpt.experiment_card` 导出仍和新 artifact 模块保持同一函数身份。

全量 unittest、维护 smoke、source encoding hygiene 和 Playwright HTML 打开一起证明：拆分没有破坏 Python 导入、输出文件、浏览器证据页和 CI 曾经出过问题的编码边界。

## 证据链意义

这两版不是“为了拆而拆”。它们把 AI 工程治理项目里最常见的重复形态继续收束：

```text
业务对象组装
  -> artifact writer/render helper
  -> README/代码讲解/c 目录证据
  -> git commit/tag
```

当后续再遇到大模块时，可以先问两个问题：

1. 这个模块是否同时承担计算和证据发布？
2. 拆出 artifact 层后，旧 schema、旧 CLI 和旧 import 是否能保持不变？

如果答案都成立，就适合做轻量 artifact split；如果没有清晰边界，就应该暂停而不是继续制造新版本。

## 一句话总结

v129/v130 把训练组合批处理和实验卡片从“厚模块直接发布证据”推进到“核心组装 + artifact 发布层”的结构，项目维护性提升了，但模型质量边界保持诚实不变。
