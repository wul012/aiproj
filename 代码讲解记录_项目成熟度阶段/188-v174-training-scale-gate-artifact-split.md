# v174 training scale gate artifact split 代码讲解

## 本版目标

v174 的目标是把 `training_scale_gate.py` 中的 artifact 输出层拆到 `training_scale_gate_artifacts.py`，让训练规模 gate 继续向“政策检查”和“证据发布”分离。原模块同时负责 policy profile、plan loading、check 构建、overall status 汇总、recommendations、JSON/CSV/Markdown/HTML 写出和 HTML 渲染。前半部分是 gate 语义，后半部分是发布和展示层。把输出层拿出来，可以避免后续调整页面或 CSV 格式时挤占 gate 判定逻辑。

本版明确不做这些事：不改变 `POLICY_PROFILES` 的任何阈值，不改变 review/standard/strict 的结果判定，不改变 check code、message、recommendation 和 details schema，不改变 `scripts/check_training_scale_gate.py` 用法，也不改变旧的 `minigpt.training_scale_gate` writer/render 导出入口。

## 前置路线

v174 接在训练规模链路和 artifact split 收束路线后面。v70 建立 training scale planner，v71 引入 gate，v72-v75 把 gate 和 run/comparison/decision/workflow 连成一条可执行路线。后面 v160、v165、v168-v169、v173 都在做同一件事：把训练规模链路里的证据产物写出从主语义模块拆出来。

从维护角度看，本轮 maintenance probe 显示 module pressure 仍然是 `pass`，但最大模块是 `training_scale_gate.py`。这说明 v174 不是因为模块已经超红线才补救，而是在还可控时先把输出层收束掉。这比等到文件超过阈值再大拆更稳。

## 关键文件

- `src/minigpt/training_scale_gate.py`：保留 gate 主语义。它继续负责加载 plan、合成 policy、构建 checks、汇总 pass/warn/fail 和生成 recommendations。
- `src/minigpt/training_scale_gate_artifacts.py`：新增 artifact 模块。它只消费已经构造好的 gate report，把它写成 JSON、CSV、Markdown 和 HTML。
- `tests/test_training_scale_gate.py`：原有测试继续覆盖 review/standard profile、缺失 baseline、token budget、HTML escaping 和 writer outputs，新增 facade identity 测试。
- `README.md`、`c/174/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：记录本版能力、证据目录和讲解索引。

## Gate 主逻辑

`POLICY_PROFILES` 仍然是 gate 的策略基础，目前有 `review`、`standard` 和 `strict` 三个 profile。它们定义最小字符数、tiny corpus 状态、数据质量 warning 上限、variant 数量范围、token budget 上限和 corpus pass 估算上限。v174 不修改这些策略值。

`build_training_scale_gate()` 是主入口。它先通过 `_policy()` 合成 profile 和 overrides，再调用 `_build_checks()` 生成每个 gate check，然后用 `_status_summary()` 计算 `overall_status`、`pass_count`、`warn_count` 和 `fail_count`。最后返回的 report 包含 `schema_version`、`title`、`generated_at`、`profile`、`policy`、`plan_summary`、`checks`、`batch` 和 `recommendations`。

`_build_checks()` 继续构建 gate 的核心证据：`plan_schema`、`source_count`、`dataset_fingerprint`、`min_char_count`、`tiny_corpus`、`quality_warnings`、`variant_count`、`baseline_variant`、`batch_handoff`、`variant_dataset_versions`、`token_budget` 和 `corpus_pass_estimate`。这些 check 的 status 仍然只能是 `pass`、`warn` 或 `fail`。

## Artifact 模块

`training_scale_gate_artifacts.py` 接管了这些函数：

- `write_training_scale_gate_json()`：写出完整 gate report，这是机器可消费的主证据。
- `write_training_scale_gate_csv()`：把每个 check 写成 CSV 行，包含 code、status、message、recommendation 和 details。
- `render_training_scale_gate_markdown()`：生成人可读 Markdown，展示 profile、overall status、plan summary、checks table、recommendations 和 batch command。
- `render_training_scale_gate_html()`：生成浏览器可读 HTML，展示状态 card、checks table、recommendations 和 batch handoff。
- `write_training_scale_gate_outputs()`：统一写出 JSON、CSV、Markdown 和 HTML，并返回路径字典。

这个 artifact 模块不加载 plan，不解释 policy，不决定某个 check 是 pass、warn 还是 fail。它的边界是“发布已有 report”，不参与 gate 判定。

## 兼容性

旧调用方式仍然有效：

```python
from minigpt.training_scale_gate import write_training_scale_gate_outputs
```

原因是 `training_scale_gate.py` 从 `training_scale_gate_artifacts.py` 重新导入并导出了 writer/render 函数。这保证 `scripts/check_training_scale_gate.py`、`training_scale_run.py` 和其他旧消费方不需要同步改路径。

`tests/test_training_scale_gate.py` 新增的 identity 断言保护这个兼容层：

```python
self.assertIs(
    training_scale_gate.write_training_scale_gate_outputs,
    training_scale_gate_artifacts.write_training_scale_gate_outputs,
)
self.assertIs(
    training_scale_gate.render_training_scale_gate_html,
    training_scale_gate_artifacts.render_training_scale_gate_html,
)
```

它保护的是函数对象一致，防止未来旧模块里重新复制一份 writer 实现，造成新旧入口行为分叉。

## 测试覆盖

v174 的测试覆盖四层：

- `tests.test_training_scale_gate`：覆盖 review profile warn、standard profile fail、缺失 baseline、token budget fail、HTML escaping、output writing 和 facade identity。
- 全量 unittest discovery：确认 run、comparison、decision、workflow 等 gate 下游链路没有因为 re-export 受影响。
- source encoding hygiene：确认新模块没有 BOM、语法错误或 Python 3.11 兼容问题。
- maintenance batching：确认 module pressure 继续为 `pass`，没有新 warn/critical 模块。

## 运行证据

v174 的运行截图归档在 `c/174`：

- `01-training-scale-gate-tests.png`：定向 gate 测试通过。
- `02-training-scale-gate-artifact-smoke.png`：旧 facade 和新 artifact 函数对象一致，且行数收束符合预期。
- `03-maintenance-smoke.png`：module pressure 为 `pass`。
- `04-source-encoding-smoke.png`：编码、语法和目标 Python 兼容检查通过。
- `05-full-unittest.png`：全量 396 个测试通过。
- `06-docs-check.png`：README、`c/174`、讲解索引、source/test 关键词对齐。

临时 `tmp_v174_*` 日志和 `runs/*v174*` 输出会在提交前按 AGENTS 清理门禁删除，`c/174` 是保留的正式证据。

## 边界说明

`training_scale_gate_artifacts.py` 不是新的 gate 判定器。它不决定什么数据规模该 pass、warn 或 fail，也不生成 recommendations。它只把主模块交给它的 report 发布成文件。因此后续修改时，策略和 check 变更找 `training_scale_gate.py`，输出格式和页面样式找 `training_scale_gate_artifacts.py`。

## 一句话总结

v174 把 training scale gate 的 JSON/CSV/Markdown/HTML 输出层独立成 `training_scale_gate_artifacts.py`，让 `training_scale_gate.py` 从 508 行降到 314 行，同时保持 policy profile、gate check、status summary、CLI 和旧 facade 导出不变。
