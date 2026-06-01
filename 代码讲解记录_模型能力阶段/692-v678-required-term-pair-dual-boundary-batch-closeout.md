# v678 required-term pair dual-boundary batch closeout

## 本版目标和边界

v678 的目标是收口 v669-v678 这一组 dual-boundary 实验，把 generation seed stability 和 forced-choice internal scoring 合并成一份可复核 closeout。

本版不训练新模型，不新增 corpus mode，不把 partial seed stability 说成稳定能力。它只回答一个问题：dual-boundary 到底修好了什么，还剩什么没修好。

## 前置链路

本批次的关键链路是：

- v669: 诊断 constrained decode 后仍缺 `fixed`。
- v670: 规划 explicit dual-objective boundary。
- v671: 注册 dual-boundary corpus mode。
- v672: seed 3535 自由生成 pair-full。
- v673: seed 3535 forced-choice 内部 pair match。
- v674: alignment matrix 选出 dual-boundary 为唯一双对齐候选。
- v675: route decision 要求进入多 seed repeat。
- v676: 三 seed generation stability 只有 2/3 pair-full。
- v677: 三 seed forced-choice internal scoring 全部 pair match。

v678 把 v676 和 v677 放到同一张 seed 表里收口。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_dual_boundary_batch_closeout.py`: 读取 seed stability 和 forced-choice 报告，按 seed 对齐 generation/internal 两层信号。
- `src/minigpt/model_capability_required_term_pair_dual_boundary_batch_closeout_artifacts.py`: 输出 JSON、CSV、text、Markdown、HTML closeout evidence。
- `scripts/run_model_capability_required_term_pair_dual_boundary_batch_closeout.py`: CLI 入口。
- `tests/test_model_capability_required_term_pair_dual_boundary_batch_closeout.py`: 覆盖 internal-stable/generation-unstable、promotion-ready、bad-source 和输出格式。

## 输入输出

输入：

- `e/676/解释/model-capability-required-term-pair-dual-boundary-seed-stability/`
- `e/677/解释/model-capability-required-term-pair-dual-boundary-multi-seed-forced-choice/`

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_dual_boundary_batch_closeout.py e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability e\677\解释\model-capability-required-term-pair-dual-boundary-multi-seed-forced-choice --out-dir e\678\解释\model-capability-required-term-pair-dual-boundary-batch-closeout --require-pass --force
```

输出：

- `model_capability_required_term_pair_dual_boundary_batch_closeout.json`
- `model_capability_required_term_pair_dual_boundary_batch_closeout.csv`
- `model_capability_required_term_pair_dual_boundary_batch_closeout.txt`
- `model_capability_required_term_pair_dual_boundary_batch_closeout.md`
- `model_capability_required_term_pair_dual_boundary_batch_closeout.html`

## 核心字段语义

- `generation_pair_full`: 该 seed 是否自由生成 pair-full。
- `internal_pair_full`: 该 seed 是否 forced-choice 内部 pair match。
- `aligned_pair_full`: 两层是否同时通过。
- `classification`: seed 级分类，例如 `generation_internal_pair_full` 或 `internal_only_generation_surface_miss`。
- `promotion_ready`: 所有 seed 是否同时 generation/internal 都通过。

## 本版结果

v678 的真实结果：

- generation pair-full: `2/3`
- internal pair-full: `3/3`
- aligned pair-full: `2/3`
- promotion ready: `False`

最终决策：

- `required_term_pair_dual_boundary_internal_stable_generation_surface_unstable`

这说明 dual-boundary 确实改进了内部偏好，但还没有让自由生成稳定。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_dual_boundary_batch_closeout.py src\minigpt\model_capability_required_term_pair_dual_boundary_batch_closeout_artifacts.py scripts\run_model_capability_required_term_pair_dual_boundary_batch_closeout.py tests\test_model_capability_required_term_pair_dual_boundary_batch_closeout.py
python -m pytest tests\test_model_capability_required_term_pair_dual_boundary_batch_closeout.py -q -o cache_dir=runs\pytest-cache-v678-unit
```

批次收口验证还包括 targeted tests、全量 pytest、source encoding hygiene 和 `git diff --check`。

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/678/解释/model-capability-required-term-pair-dual-boundary-batch-closeout/`
- 截图: `e/678/图片/v678-dual-boundary-batch-closeout.png`
- 解释: `e/678/解释/说明.md`

一句话总结：v678 把 dual-boundary 批次的能力边界定为“内部偏好已稳定，生成表面仍需下一阶段修复”。
