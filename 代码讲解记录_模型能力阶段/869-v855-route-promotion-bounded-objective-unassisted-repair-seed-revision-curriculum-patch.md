# v855：bounded objective unassisted repair seed revision curriculum patch

## 本版目标和边界

v855 的目标是把 v854 的 partial-hit 诊断转成可训练语料补丁。

边界：

- 不训练模型。
- 不运行 replay。
- 不使用 decoder anchor。
- 不声明模型能力提升。

这版只交付下一轮训练输入：patched corpus 和 patch examples。

## 前置链路

v854 给出的核心诊断是：

```text
first_term_only_uptake
loss_term_not_stabilized
prompt_surface_still_zero_hit
```

所以 v855 的 patch 不再泛泛扩语料，而是专门补：

- `fixed -> loss` bridge。
- `loss` second-term repeat。
- `completion:` surface。
- `fixed loss` 与 `fixed t` 的 contrast。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.py`
  - 读取 partial-hit diagnostic、seed revision、objective contract 和 source corpus，生成 patch examples 与 patched corpus。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_artifacts.py`
  - 输出 JSON/CSV/JSONL/corpus/TXT/Markdown/HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.py`
  - 覆盖 ready patch、diagnostic not ready 失败、writer/CLI。
- `e/855/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-curriculum-patch/`
  - 保存真实 patch 产物。
- `e/855/图片/v855-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-html.png`
  - Playwright MCP 截图。

## 核心数据结构

每条 patch example 包含：

```text
example_id
kind
prompt
completion
text
required_terms
decoder_anchor
purpose
```

其中 `decoder_anchor` 固定为 `False`，确保这条路线仍然是 no-anchor 能力路线。

## patch 类型

v855 生成 7 类 patch kind：

```text
loss_second_term_repeat
fixed_to_loss_bridge
full_completion_contrast
loss_after_fixed_short
loss_after_fixed_label
two_token_target_repeat
completion_surface_short
```

这些类型对应 v854 的 root causes。

## 真实运行结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready
patch_example_count=18
loss_focus_example_count=18
completion_surface_example_count=2
decoder_anchor_example_count=0
original_corpus_char_count=2028
patched_corpus_char_count=2996
model_quality_claim=curriculum_patch_only
next_action=train_bounded_objective_unassisted_repair_seed_revision_curriculum_patch
```

## 产物角色

`model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_examples.jsonl` 是结构化 patch 样本。

`model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_corpus.txt` 是下一版训练可直接使用的语料。

JSON/CSV/Markdown/HTML 是证据和讲解产物，不直接参与训练。

## 测试覆盖

focused pytest 覆盖：

- 生成 no-anchor loss/completion patch。
- diagnostic not ready 时失败。
- CLI 和 writer 输出完整产物。

```text
3 passed
```

全量验证：

```text
py_compile: pass
full pytest: 1744 passed
source encoding: source_count=1280 clean_count=1280 bom_count=0 syntax_error_count=0
git diff --check: pass
```

## 运行证据

HTML 截图：

```text
e/855/图片/v855-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Patch examples=18
Loss focus=18
Completion surface=2
Corpus chars=2996
Claim=curriculum_patch_only
Next action=train_bounded_objective_unassisted_repair_seed_revision_curriculum_patch
```

## 一句话总结

v855 把 partial-hit 诊断落成 no-anchor patched corpus，让下一版可以用真实训练验证 loss second-term 和 completion-surface 修复是否有效。
