# v578 required-term pair route closeout summary

## 本版目标和边界

v578 是 v569-v577 的路线收口，不是新的训练实验。它解决的问题是：这一轮连续推进已经产生很多证据，必须把“能保留什么、不能声称什么、下一步做什么”收束到一份机器可读报告中。

本版不训练、不调参、不新增数据构造。它读取已有 evidence，把路线从“继续小变体”切换到“准备新 objective”。

## 前置证据

输入分为四类：

```text
v570 held-out expanded suite
v571/v573/v575 fresh-seed stability
v576 variable comparison
v577 route decision
```

v570 是正证据：同一路线在七个 held-out prompt surfaces 上都能 pair-full。

v571、v573、v575 是负证据：fresh seed `3535` 没有 pair-full。

v576 把三条 fresh-seed 变量统一比较，v577 把比较结论变成 route decision。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_route_closeout_summary.py
src/minigpt/model_capability_required_term_pair_route_closeout_summary_artifacts.py
scripts/run_model_capability_required_term_pair_route_closeout_summary.py
tests/test_model_capability_required_term_pair_route_closeout_summary.py
```

主模块负责输入定位、读取 JSON、生成 evidence rows、汇总 summary 和判断 closeout 是否 ready。

artifact 模块负责生成 CSV/text/Markdown/HTML。这样 closeout 可以被脚本消费，也能用浏览器人工检查。

CLI 使用 repeatable `--fresh-seed LABEL PATH`，避免把 v571/v573/v575 写死在模块里。

## 核心字段

summary 的关键字段是：

```text
heldout_all_pair_full
fresh_seed_route_count
fresh_seed_pair_full_count
fresh_seed_continuation_hit_count
comparison_union_hit_terms
route_decision
stop_first_token_route
stop_width_scaling
closeout_ready
```

`closeout_ready=True` 需要同时满足：

- held-out replay 全部 pair-full。
- fresh-seed route 没有 pair-full。
- v577 decision 已经停止 first-token 与 width scaling。

这组条件让报告表达的是“路线关闭”，而不是“模型成功”。

## 运行结果

输出目录：

```text
e/578/解释/model-capability-required-term-pair-route-closeout-summary/
```

关键字段：

```text
status=pass
decision=close_required_term_pair_route_before_new_objective
heldout_all_pair_full=True
fresh_seed_pair_full_count=0
route_decision=stop_first_token_and_width_for_fresh_seed
model_quality_claim=bounded_transfer_not_generalized
```

`bounded_transfer_not_generalized` 表示：这条路线在受控 held-out prompt surfaces 上成立，但没有跨到 fresh seed。

## 测试覆盖

测试覆盖四类行为：

- held-out pass 且 fresh-seed no pair-full 时 closeout ready。
- route decision 如果没有停止 width scaling，closeout 会 fail。
- JSON/CSV/text/Markdown/HTML 输出都可生成。
- 输入目录定位函数能自动补齐各自的 JSON 文件名。

这些断言保护的是路线收口本身：不能因为文档说“停止”，但机器产物仍然允许继续同一变量。

## 链路角色

v578 是十版推进的闸门。它把 v569-v577 的正负证据合并成一条明确路线：

```text
held-out transfer 有效，但 fresh-seed 泛化失败；下一步必须换 objective。
```

## 一句话总结

v578 将 required-term pair route 从连续实验推进到证据收口，明确关闭 first-token/width 分支，并把下一版方向切到 branch-binding objective。
